# Fresh typed-evidence evaluation

Complete: 160/160 records, with a separate deterministic baseline. The method was fixed after 5 development trials and 2 real-Unity M1 development smoke queries; source, configuration, model manifest and the independent fresh-suite hash were frozen before opening fresh questions.

| Condition | Raw exact | Missing-evidence exact | Guard accepted | Accepted incorrect | Median seconds | Mean forwards |
|---|---:|---:|---:|---:|---:|---:|
| legacy_state_text | 9/32 | 0/12 | 9/32 | 0 | 2.7458 | 45.5 |
| decisions_state_text | 31/32 | 12/12 | 31/32 | 0 | 0.5082 | 6.562 |
| decisions_unfiltered_text | 31/32 | 12/12 | 31/32 | 0 | 0.5694 | 7.656 |
| decisions_state_image | 10/32 | 10/12 | 10/32 | 0 | 4.4141 | 6.562 |
| deterministic_baseline | 32/32 | 12/12 | 32/32 | 0 | 0.0 | 0 |

Raw exactness requires every claim ID, value, status, citation and unknown-property flag. Malformed, interrupted and failed calls remain failures. Guard rejection never counts as a correct raw answer. The guard checks the deterministic query contract; its accepted-answer precision is not independent evidence of model competence.

| Condition | Claim precision | Claim recall | Invented ID | Unavailable ID | Wrong identity | Wrong status | Mean input/output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy_state_text | 0.667 | 0.545 | 0 | 0 | 0 | 5 | 754.312/45.5 |
| decisions_state_text | 0.978 | 1.000 | 0 | 0 | 0 | 0 | 579.125/0 |
| decisions_unfiltered_text | 0.978 | 1.000 | 0 | 0 | 0 | 0 | 681.188/0 |
| decisions_state_image | 0.732 | 0.682 | 0 | 0 | 0 | 0 | 3112.25/0 |
| deterministic_baseline | 1.000 | 1.000 | 0 | 0 | 0 | 0 | 0/0 |

ID error categories are exclusive in order: nonexistent scenario fact, fact not yet received, then received fact for another identity. Status/value/citation errors are checked only for available selected-identity facts. Malformed outputs have zero scored emitted claims but fail whole-answer accuracy; claim precision alone can therefore mislead.

| Query type | Legacy exact | Predicate selection exact | Deterministic exact |
|---|---:|---:|---:|
| change | 0/8 | 8/8 | 8/8 |
| current | 7/17 | 16/17 | 17/17 |
| latest | 2/7 | 7/7 | 7/7 |

Paired comparisons use the same fresh questions; no comparison mixes old held-out and new fresh accuracy.

- decisions_state_text versus legacy_state_text: +68.8 percentage points; 22 wins, 0 losses, 10 ties across 32 paired questions / 8 families.
- decisions_state_image versus decisions_state_text: -65.6 percentage points; 0 wins, 21 losses, 11 ties across 32 paired questions / 8 families.
- decisions_unfiltered_text versus decisions_state_text: +0.0 percentage points; 0 wins, 0 losses, 32 ties across 32 paired questions / 8 families.
- decisions_state_text versus deterministic_baseline: -3.1 percentage points; 0 wins, 1 losses, 31 ties across 32 paired questions / 8 families.

Questions within a scenario family are correlated. Per-family differences and query-type results are in summary.json; these comparisons are descriptive, with no significance or generalization claim.

The new condition is a hybrid: Qwen selects literal predicates; a deterministic resolver supplies temporal statuses; values and source links are copied from selected facts. Missing-evidence flags are composed from those decisions, and an empty table produces unknown without a model call. This can repair an engineered system while establishing neither learned temporal inference nor superiority to the separately measured deterministic baseline.

The image condition uses a non-diagnostic schematic as a negative control. The unfiltered condition stresses identity selection. Neither establishes visual reasoning, moving-aircraft prediction, longitudinal memory, operational safety or AR utility. Pairwise receipt comparisons cache repeated numeric pairs. Variable forward-pass counts, input lengths and output formats mean this is not a matched-compute causal comparison. Legacy forward passes are inferred from greedy generated-token count; predicate passes are directly counted. Model loading is excluded from call latency; failed/interrupted calls may lack compute counts.

Every legacy raw response, selector decision trace, error and guard result remains in fresh-runs.jsonl. attempts.jsonl prevents retries, including interrupted calls. Source snapshots and protocol.json fix the method; this report aggregates saved scores without rescoring. error-catalog.json preserves every non-exact result.

Broader research claims require independently reviewed data, more independent scenario families, visually necessary tasks, genuine temporal inference beyond supplied status labels, and user evaluation on Android.
