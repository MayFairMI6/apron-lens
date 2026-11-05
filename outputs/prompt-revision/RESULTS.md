# Readiness prompt revision: results

The original v5 comparison remains unchanged. This new instruction-only revision is evaluated first on 18 observed regression turns and then on 24 fresh authored questions for each version. Model weights, evidence, answer expansion, validator and retry policy are unchanged.

Observed regression: **18/18** for v6. This includes the known failure and is development evidence, not an unseen test.

| Fresh-question configuration | Task success | Validator accepted | Median seconds | Calls |
|---|---:|---:|---:|---:|
| v5 | 23/24 | 24/24 | 7.273 | 24 |
| v6 | 23/24 | 24/24 | 7.385 | 24 |

Paired improvements: 0; paired regressions: 0. Predeclared offline adoption gate: **failed**. Native/service acceptance is recorded separately.

| Version | Vehicle | Stand | Baggage | Explicit readiness |
|---|---:|---:|---:|---:|
| v5 | 6/6 | 6/6 | 6/6 | 5/6 |
| v6 | 6/6 | 6/6 | 6/6 | 5/6 |

Failed fresh answers:

- **v5 / explicit_readiness / turn 4:** Has the latest update changed its reported readiness?
  Expected facts: {"overall_readiness": "not ready: additional inspection required"}; requested unknowns: [].
  Display: {"resultStatus": "answer", "validatorVersion": "conversation-validator-v2", "answer": "Overall departure readiness: ready — superseded. Event 190 s; received 200 s. [EVAL_READY]\n\nOverall departure readiness: not ready: additional inspection required — current. Event 210 s; received 220 s. [EVAL_NOT_READY]\n\nChanged since the previous answer: EVAL_NOT_READY:overall_readiness, EVAL_READY:overall_readiness", "claims": [{"fact_id": "EVAL_READY:overall_readiness", "value": "ready", "status": "superseded", "evidence_ids": ["EVAL_READY"]}, {"fact_id": "EVAL_NOT_READY:overall_readiness", "value": "not ready: additional inspection required", "status": "current", "evidence_ids": ["EVAL_NOT_READY"]}], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}
- **v6 / explicit_readiness / turn 4:** Has the latest update changed its reported readiness?
  Expected facts: {"overall_readiness": "not ready: additional inspection required"}; requested unknowns: [].
  Display: {"resultStatus": "answer", "validatorVersion": "conversation-validator-v2", "answer": "Overall departure readiness: ready — superseded. Event 190 s; received 200 s. [EVAL_READY]\n\nOverall departure readiness: not ready: additional inspection required — current. Event 210 s; received 220 s. [EVAL_NOT_READY]\n\nChanged since the previous answer: EVAL_NOT_READY:overall_readiness, EVAL_READY:overall_readiness", "claims": [{"fact_id": "EVAL_READY:overall_readiness", "value": "ready", "status": "superseded", "evidence_ids": ["EVAL_READY"]}, {"fact_id": "EVAL_NOT_READY:overall_readiness", "value": "not ready: additional inspection required", "status": "current", "evidence_ids": ["EVAL_NOT_READY"]}], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}

The v6 prompt was fixed before fresh inference and was not adjusted afterward. Positive and negative readiness reports are synthetic evaluation fixtures, never added to app lessons. Questions immediately before and at receipt test evidence availability; service questions test against indiscriminate readiness abstention. There are four dependent episodes and one fresh scenario seed, not 48 independent samples. These results do not establish generalization, professional safety, learner benefit, graph benefit or weight-training benefit.

The inherited strict current-only scorer also rejects correctly labelled superseded facts. In the v5 readiness-change answer, both old ready and current not-ready reports were accurately labelled; its penalty must not be described as a factual error. The question wording can reasonably invite this history. Preserve the score but qualify any apparent fresh-question advantage.

All arms use the same selector/expansion/validator. Existing reference memory is not verbatim dialogue. No aircraft is selected; no images are supplied. Supported but irrelevant extras and prose quality are not fully scored. Offline latency uses fixed order and does not enforce native deadlines; engine stop reasons remain inferred. Actual prompts, raw selections, usage and retries are in the two audit sidecars. Source/case hashes are fixed in the pre-run lock.

See [protocol](../../docs/course/PROMPT_REVISION.md), [original comparison](../assistant-comparison/RESULTS.md), run JSON and summary JSON. No original result has been overwritten.

Final deployment decision: retain v5 as the app default; publish v6 as a tested
candidate only. No v6 native/app adoption is claimed. The known regression
improved, but the fresh-question gate did not pass and no prompt was retuned on
those outputs. Both historical-answer penalties reflect the current-only scorer,
not incorrect facts. The broader semantic issue remains open.
