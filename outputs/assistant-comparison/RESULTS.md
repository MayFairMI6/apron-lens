# Current assistant: bounded comparison results

18 authored turns in three dependent conversations, evaluated in three configurations (54 responses). Seed 17, Qwen3.5-9B, text only. This is a development comparison, not a held-out benchmark, professional safety assessment, visual-reasoning test or learner-outcome study.

| Configuration | Complete supported answers | Validator accepted | Median seconds | Model calls |
|---|---:|---:|---:|---:|
| lexical_history | 18/18 | 18/18 | 5.886 | 18 |
| selector_no_history | 14/18 | 17/18 | 6.361 | 18 |
| selector_history | 17/18 | 18/18 | 6.64 | 18 |

| Configuration | Vehicle obstruction | Occupied stand | Baggage delay |
|---|---:|---:|---:|
| lexical_history | 6/6 | 6/6 | 6/6 |
| selector_no_history | 5/6 | 4/6 | 5/6 |
| selector_history | 5/6 | 6/6 | 6/6 |

All configurations share the same evidence selector, expansion and validator. The lexical arm restricts the eligible reports to six ranked facts; history means existing validated reference memory, not a verbatim chat transcript. The no-history arm starts a fresh session each turn. No aircraft is selected, making conversation-dependent reference resolution observable.

Claim values are copied from selected evidence by the existing adapter. The important measured differences are flight identity, report selection, completeness and appropriate unknowns. An accepted response can still fail the answer key. A clarification can be appropriate for an arm deprived of history while still failing the full conversation task; it is not an empty-answer defect. Unknown-only answers have no citation requirement.

The summary JSON includes token totals, retries, identity/coverage/uncertainty failures and responses exceeding the native 35-second/driver 40-second thresholds. The offline runner does not enforce those deadlines. Fixed execution order makes latency descriptive, not a controlled speed comparison.

Failures (including withheld output):

- **selector_no_history / surface_conflict / turn 5**: Does that establish its overall departure readiness?
  Score: {"accepted": true, "citationValid": null, "claimsSupported": true, "complete": true, "emptyAnswer": true, "errors": [], "identityCorrect": false, "passed": false, "staleClaims": false, "unknownsCorrect": false}
  Display: {"resultStatus": "clarify", "validatorVersion": "conversation-validator-v2", "answer": "Clarification needed.", "claims": [], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}
- **selector_no_history / late_arrival / turn 3**: Has its stand been confirmed available now?
  Score: {"accepted": true, "citationValid": false, "claimsSupported": false, "complete": false, "emptyAnswer": false, "errors": [], "identityCorrect": false, "passed": false, "staleClaims": false, "unknownsCorrect": true}
  Display: {"resultStatus": "answer", "validatorVersion": "conversation-validator-v2", "answer": "Authored movement condition: reposition to Stand C — current. Event 50 s; received 52 s. [L011]", "claims": [{"fact_id": "L011:movement_condition", "value": "reposition to Stand C", "status": "current", "evidence_ids": ["L011"]}], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}
- **selector_no_history / late_arrival / turn 5**: Does that establish its overall departure readiness?
  Score: {"accepted": true, "citationValid": null, "claimsSupported": true, "complete": true, "emptyAnswer": true, "errors": [], "identityCorrect": false, "passed": false, "staleClaims": false, "unknownsCorrect": false}
  Display: {"resultStatus": "clarify", "validatorVersion": "conversation-validator-v2", "answer": "Clarification needed.", "claims": [], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}
- **selector_no_history / late_baggage / turn 5**: Do these updates establish its overall departure readiness?
  Score: {"accepted": false, "citationValid": null, "claimsSupported": true, "complete": true, "emptyAnswer": false, "errors": ["schema"], "identityCorrect": false, "passed": false, "staleClaims": false, "unknownsCorrect": true}
  Display: {"resultStatus": "withheld", "validatorVersion": "conversation-validator-v2", "answer": "The model proposal failed support or completeness checks. No model claims were displayed; review the report history.", "claims": [], "interpretation": null}
- **selector_history / surface_conflict / turn 5**: Does that establish its overall departure readiness?
  Score: {"accepted": true, "citationValid": true, "claimsSupported": true, "complete": true, "emptyAnswer": false, "errors": [], "identityCorrect": true, "passed": false, "staleClaims": false, "unknownsCorrect": false}
  Display: {"resultStatus": "answer", "validatorVersion": "conversation-validator-v2", "answer": "Authored movement condition: exercise ground hold released — current. Event 100 s; received 104 s. [L011]", "claims": [{"fact_id": "L011:movement_condition", "value": "exercise ground hold released", "status": "current", "evidence_ids": ["L011"]}], "unknowns": [], "observations": [], "interpretation": null, "validation": "Claims match receipt-eligible typed facts and their sources; changed facts are covered. The referent choice and the interpretation are not verified."}

No prompts or answer keys were revised in response to these results. A graph database was not introduced: this comparison does not establish a graph-specific retrieval need. Retain these results, including ties or losses; do not claim state-of-the-art performance.

See [protocol](../../docs/course/ASSISTANT_COMPARISON.md), run JSON, actual selector prompt/response sidecar and source manifest in this directory. Historical frozen research is unchanged.
