"""Predeclared model-selection procedure and formal-run protocol constants.

Selection is ordered, not a single weighted sum:
  1. Engineering gates disqualify (any failure removes a candidate).
  2. Reliability and cost must meet their minimums.
  3. Remaining candidates are ranked by the quality factors (weights renormalised);
     ties go to the cheaper candidate.
The full weighted total from the plan is still computed and published for every
candidate, but it never overrides a gate failure.
"""

PROTOCOL = dict(
    # Each turn sees the model's own earlier answers in that family (on-policy).
    turn_construction='on_policy',
    report_first_error_turn=True,
    uncertainty_unit='family',
    formal_backward_seek='new_session',
    repair_policy='json-repair-v1',
)

GATES = dict(min_referent_accuracy=0.90, min_supported_claims=0.95,
             max_future_evidence_leaks=0, max_wrong_flight_memory_writes=0)
MIN_RELIABILITY = 0.95
WEIGHTS = dict(visual_reference=0.25, temporal_correction=0.25, evidence_uncertainty=0.20,
               latency=0.15, cost=0.10, reliability=0.05)
QUALITY = ('visual_reference', 'temporal_correction', 'evidence_uncertainty')


def latency_score(median_seconds):
    """100 at <=5 s median, falling linearly to 0 at 20 s."""
    return max(0.0, min(100.0, 100.0 * (20.0 - median_seconds) / 15.0))


def cost_score(cost_per_attempted_turn):
    """100 at <=$0.005 per attempted turn, falling linearly to 0 at $0.15."""
    return max(0.0, min(100.0, 100.0 * (0.15 - cost_per_attempted_turn) / 0.145))


def zero_event_upper_bound(n_cases):
    """Approximate 95% upper bound on a rate when 0 events are seen in n cases (rule of three)."""
    return min(1.0, 3.0 / n_cases) if n_cases else 1.0


def comparison_eligible(measured_cost_per_turn, calls=72, allocation=12.0, reserve_fraction=0.2):
    """A comparison model must fit its fixed call plan within the allocation minus a reserve."""
    return measured_cost_per_turn * calls <= allocation * (1.0 - reserve_fraction)


def gate_failures(m):
    failures = []
    if m['referent_accuracy'] < GATES['min_referent_accuracy']:
        failures.append('referent_accuracy')
    if m['supported_claim_rate'] < GATES['min_supported_claims']:
        failures.append('supported_claims')
    if m['future_evidence_leaks'] > GATES['max_future_evidence_leaks']:
        failures.append('future_evidence_leak')
    if m['wrong_flight_memory_writes'] > GATES['max_wrong_flight_memory_writes']:
        failures.append('wrong_flight_memory_write')
    return failures


def weighted_total(m):
    scores = dict(visual_reference=m['visual_reference'], temporal_correction=m['temporal_correction'],
                  evidence_uncertainty=m['evidence_uncertainty'], latency=latency_score(m['median_latency']),
                  cost=cost_score(m['cost_per_attempted_turn']), reliability=100.0 * m['reliability'])
    return sum(WEIGHTS[k] * v for k, v in scores.items()), scores


def select(candidates, planned_calls, allocation):
    """candidates: list of dict(name=..., metrics=...). Returns (ranking, excluded, report)."""
    report, eligible, excluded = {}, [], {}
    for c in candidates:
        m = c['metrics']
        total, components = weighted_total(m)
        report[c['name']] = dict(weightedTotal=round(total, 2), components=components,
                                 gateFailures=gate_failures(m),
                                 leakUpperBound=zero_event_upper_bound(m['cases']) if m['future_evidence_leaks'] == 0 else None)
        reasons = list(report[c['name']]['gateFailures'])
        if m['reliability'] < MIN_RELIABILITY:
            reasons.append('reliability')
        if m['cost_per_attempted_turn'] * planned_calls > allocation:
            reasons.append('cost_exceeds_allocation')
        if reasons:
            excluded[c['name']] = reasons
        else:
            eligible.append(c)
    quality_weight = sum(WEIGHTS[k] for k in QUALITY)

    def quality(c):
        return sum(WEIGHTS[k] * c['metrics'][k] for k in QUALITY) / quality_weight

    ranking = [c['name'] for c in sorted(eligible, key=lambda c: (-quality(c), c['metrics']['cost_per_attempted_turn']))]
    return ranking, excluded, report
