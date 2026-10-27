# Fresh temporal-evidence holdout

This directory contains **8 new composition families and 32 checkpoint queries**.
It is reserved for evaluation after the revised method is frozen. Do not use its
questions, gold selections, or model responses to tune the method being tested.

## Provenance and separation

The evaluation subagent authored the scenarios and gold fact/value/status/source
selections independently from the model-improvement task. The author inspected
the event schema and previous scenario construction to avoid simply renumbering
old cases. It did not execute a model on these fresh cases. The author knew the
requested failure categories and inherited project context; this is task-level
separation, not independent human domain expertise or full statistical blinding.
The method-development agent is given only directory/count/readiness metadata
until its method is frozen.

All records are fictional. They do not represent operational airport procedures,
validated service states, surveillance observations, or movement authority.
Target off-block times are estimates. Service completion does not establish
readiness or clearance.

## Files

- `scenarios/`: event records in the existing typed evidence schema.
- `queries.json`: questions, explicit query types, checkpoints, selected identity,
  and manually authored gold claims and unknown-property sets.
- `author_suite.py`: reproducible authoring source. Gold tuples are written
  explicitly and are never calculated by the deterministic resolver.
- `images/context.png`: optional non-diagnostic schematic negative control.
- `verification.json`: schema checks and comparison of the authored labels with
  the agreed deterministic policy. Agreement is not independent expert review.
- `manifest.json`: frozen file hashes, provenance, and counts.

## Policies fixed before model evaluation

Only receipt time at or before the checkpoint makes a report available. Both the
selected aircraft and flight-instance identity must match. An effective received
supersession takes priority over a future start date, so a replaced future plan
is **superseded**, not still scheduled. Supersession is transitive, and an expired
replacement never revives an explicitly superseded plan.

For `latest`, return all matching facts at the maximum receipt time, including
multiple reports received simultaneously. Event IDs do not establish authority
within a receipt-time tie. For `current`, include every unambiguous current fact
for each requested property; concordant records remain separate source-linked
claims. For `change`, retain the full matching received history with statuses.
A requested property with no current fact belongs in the unknown set for current
and change queries. Latest-report queries with no matching report use the
requested property set, or `overall_readiness` when no property was requested.

Intervals are start-inclusive and end-exclusive. Unresolved distinct active
values are conflicting. The input image conveys no service or plan-validity
answer; performance with it cannot substantiate visual reasoning.

## Freshness and limits

The families introduce combinations including multiple facts per report,
concordant estimates followed by partial replacement, identity-misrouted reports,
simultaneous receipts, cancelled future plans, and empty selected-flight context.
They are new compositions of the same schema, not proof of broad distributional
novelty. Some underlying mechanisms necessarily recur from development because
those are the capabilities under test. Four queries in one family are correlated.
Report family-level results, failed calls, malformed responses, withheld answers,
and raw model accuracy separately from the deterministic baseline.

After the first evaluation, these cases become an observed test set. Any tuning
based on their failures requires a different fresh holdout for a new performance
claim. Domain-expert review and visually necessary tasks remain outstanding.
