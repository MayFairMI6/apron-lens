# History-aware evaluation: new report families

24 new authored questions in four dependent report scenarios, each tested with frozen v5 and v6. The new scorer distinguishes current status, named history and before/after change. The earlier results and scorers are unchanged. This is a development evaluation, not a held-out operational benchmark.

| Version | Task success | Current | History | Change | Validator accepted |
|---|---:|---:|---:|---:|---:|
| v5 | 22/24 | 12/13 | 3/3 | 7/8 | 24/24 |
| v6 | 22/24 | 12/13 | 3/3 | 7/8 | 24/24 |

| Version | Weather route | Stand reassignment | Service withdrawal | Estimate correction |
|---|---:|---:|---:|---:|
| v5 | 5/6 | 5/6 | 6/6 | 6/6 |
| v6 | 5/6 | 5/6 | 6/6 | 6/6 |

A pass requires the expected flight, required fact coverage, permitted relevant evidence, correct source values/statuses/citations and exact requested uncertainty. A truthful but incomplete answer may pass the app validator and fail this evaluation. Correctly labelled superseded facts are accepted only when the declared history/change question permits them.

Failed answers:

- **v5 / weather_route / turn 6 / current**: Does its current ground restriction establish overall departure readiness?
  Required: []; unknowns: ["overall_readiness"].
  Checks: {"accepted": true, "citationValid": true, "claimsSupported": true, "errors": [], "identityCorrect": true, "mode": "current", "passed": false, "relevantScope": true, "requiredCoverage": true, "statusAllowed": true, "unknownsCorrect": false}.
  Display: {"resultStatus": "answer", "validatorVersion": "conversation-validator-v2", "answer": "Authored movement condition: hold: route inspection — current. Event 65 s; received 80 s. [W3]", "claims": [{"fact_id": "W3:movement_condition", "value": "hold: route inspection", "status": "current", "evidence_ids": ["W3"]}], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}
- **v5 / stand_reassignment / turn 5 / change**: Compare its E4 assignment with the latest replacement.
  Required: ["S2:stand", "S3:stand"]; unknowns: [].
  Checks: {"accepted": true, "citationValid": false, "claimsSupported": false, "errors": [], "identityCorrect": false, "mode": "change", "passed": false, "relevantScope": false, "requiredCoverage": false, "statusAllowed": true, "unknownsCorrect": true}.
  Display: {"resultStatus": "answer", "validatorVersion": "conversation-validator-v2", "answer": "Assigned stand: E4 — current. Event 4 s; received 6 s. [S5]", "claims": [{"fact_id": "S5:stand", "value": "E4", "status": "current", "evidence_ids": ["S5"]}], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}
- **v6 / weather_route / turn 6 / current**: Does its current ground restriction establish overall departure readiness?
  Required: []; unknowns: ["overall_readiness"].
  Checks: {"accepted": true, "citationValid": true, "claimsSupported": true, "errors": [], "identityCorrect": true, "mode": "current", "passed": false, "relevantScope": true, "requiredCoverage": true, "statusAllowed": true, "unknownsCorrect": false}.
  Display: {"resultStatus": "answer", "validatorVersion": "conversation-validator-v2", "answer": "Authored movement condition: hold: route inspection — current. Event 65 s; received 80 s. [W3]", "claims": [{"fact_id": "W3:movement_condition", "value": "hold: route inspection", "status": "current", "evidence_ids": ["W3"]}], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}
- **v6 / stand_reassignment / turn 5 / change**: Compare its E4 assignment with the latest replacement.
  Required: ["S2:stand", "S3:stand"]; unknowns: [].
  Checks: {"accepted": true, "citationValid": false, "claimsSupported": false, "errors": [], "identityCorrect": false, "mode": "change", "passed": false, "relevantScope": false, "requiredCoverage": false, "statusAllowed": true, "unknownsCorrect": true}.
  Display: {"resultStatus": "answer", "validatorVersion": "conversation-validator-v2", "answer": "Assigned stand: E4 — current. Event 4 s; received 6 s. [S5]", "claims": [{"fact_id": "S5:stand", "value": "E4", "status": "current", "evidence_ids": ["S5"]}], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}

The separate old-answer diagnostic re-scores only the two known readiness-change answers. Both correctly labelled histories pass under the new rule. That diagnostic is post-hoc, uses no new model calls, and does not replace either old result set or retrospectively promote v6.

All model prompts and model weights remain frozen. New report worlds are evaluation fixtures, not new in-app scenes or operational Heathrow data. Four dependent families, fixed version order, text-only inputs and no selected-aircraft cue limit generalisation. Only current and superseded statuses are covered; conflicting, expired and scheduled states are not tested. History consists of the existing reference state rather than a verbatim transcript.

Actual selector prompts/raw outputs, expanded/displayed answers, attempts and usage are preserved. The summary records retries, token totals and 35/40-second overruns; offline execution does not enforce native deadlines. Stop reason remains inferred by the unchanged adapter. Neither structural acceptance nor this test establishes learning benefit, professional competence or a need for weight training.

Production stays on v5; no prompt promotion or app behaviour change is made. See [protocol](../../docs/course/HISTORY_EVALUATION.md), run and lock JSON, actual prompt sidecars and old-answer diagnostic in this directory.

Independent failure interpretation: both versions' weather answer cites a truthful
current restriction but omits the requested overall-readiness uncertainty. Both
stand-history answers select a real E4 report for ST406 instead of the conversation
referent ST204. That is a wrong-flight response, not an invented fact or citation.
Citation/support failures in the score are relative to the expected flight. Neither
response was withheld by structural validation. The new rubric reveals these
semantic limitations while accepting correctly labelled, relevant history.
