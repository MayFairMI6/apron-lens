# Typed evidence reasoning: reproducible pilot

Qwen2.5-VL-3B-Instruct was tested on 36 questions from 12 original fictional scenario families. The final protocol ran 144 model requests: 96 development and 48 held-out. Four composition families (12 questions) were held out from model-driven prompt changes. All scenarios and labels were authored by the same developer, so this is an author-known synthetic pilot, not an independently curated benchmark.

## What changed

Qwen selects atomic facts with values, temporal statuses, and citations. The validator checks every field against the selected flight’s received evidence and checks query coverage. Only accepted selections are rendered, using deterministic templates. The original merged-claim citation bug is therefore blocked within this typed schema. This is constrained, source-linked rendering—not a general free-text entailment verifier.

The state engine distinguishes receipt time from event time, applies validity intervals and explicit supersession, preserves old plans as history, and treats unresolved conflicting values as unknown. A delayed older update does not overwrite a received newer replacement. Expiring a replacement does not revive an explicitly superseded plan.

## Held-out results

| Condition | Raw exact answers | Valid schema | Accepted by guard | Accepted but incorrect | Median seconds |
|---|---:|---:|---:|---:|---:|
| unfiltered_history_text | 3/12 | 5/12 | 3/12 | 0 | 2.731 |
| scoped_history_text | 5/12 | 9/12 | 5/12 | 0 | 2.618 |
| state_aware_text | 6/12 | 10/12 | 6/12 | 0 | 2.675 |
| state_aware_image | 6/12 | 10/12 | 6/12 | 0 | 3.744 |
| deterministic state engine | 12/12 | n/a | n/a | n/a | not benchmarked |

Raw exactness requires the complete correct set of claim IDs, values, statuses, citations, and unknown properties. Failures and malformed JSON remain in the denominator. Accepted coverage is reported separately so rejection cannot be mistaken for model competence. The guard uses the deterministic query contract; a high accepted-answer precision is a property of that contract, not an independent model-accuracy improvement.

| Condition | Supported citations / emitted claims | Correct abstention sets on unknown questions | Wrong-identity claims | Unavailable-ID or wrong-status claims | Mean input / output tokens |
|---|---:|---:|---:|---:|---:|
| unfiltered_history_text | 6/6 | 0/3 | 0 | 0 | 745.2 / 39 |
| scoped_history_text | 10/10 | 0/3 | 0 | 1 | 679.4 / 39.2 |
| state_aware_text | 12/12 | 0/3 | 0 | 3 | 689.6 / 41.5 |
| state_aware_image | 11/11 | 0/3 | 0 | 2 | 1075.6 / 40.1 |

Citation support here means exact source/value support for the typed atom; temporal status is scored separately. Malformed responses have zero emitted scored claims but still fail answer accuracy; do not interpret citation precision alone as end-to-end quality.

## Interpretation

The deterministic baseline answers all supported questions correctly. These tasks therefore do not establish that an LLM is necessary or superior. The meaningful research direction is measuring when context selection, temporal constraints, and controlled abstention improve a model, then extending evaluation to genuinely visual or open-ended tasks that the state engine cannot answer alone.

The paired state-aware versus unfiltered text difference is 25.0 percentage points. An exploratory family-bootstrap interval is [0.0, 50.0] points; four held-out families are insufficient for a strong generalization claim.

The image condition uses the same non-diagnostic schematic at all checkpoints as a negative control. It is intentionally not evidence for service status or plan validity. Its result does not demonstrate visual reasoning, motion prediction, longitudinal memory, or AR usefulness. Context lengths differ across retrieval conditions; token counts are reported, but this is not a matched-input-budget study.

## Development history and reproducibility

The initial format-only development pilot was stopped after recurrent schema errors. Its raw outputs and frozen protocol remain in initial-format-pilot/. The final prompt adds a concrete output example; a lossless parser normalization unwraps a single extra claim object. No missing value, status, or citation is invented. No prompt or engine changes were made after the final protocol freeze, and no held-out model outputs were used to tune it.

Protocol: protocol.json. Dataset and per-file hashes: ../../data/reasoning_v1/manifest.json. Raw prompts, outputs, tokens, timing, and errors: dev-runs.jsonl and heldout-runs.jsonl. Per-question scores: per-query.csv. Full errors: error-catalog.json.

Reproduce with scripts/evaluate_reasoning.py using a new output/version for changed code. --resume runs only missing requests under the identical protocol hash. Run scripts/report_reasoning.py to regenerate this report. Model revision and deterministic decoding are fixed in the protocol.

## Before a research-grade performance claim

Obtain independent domain review of facts, event semantics, and gold answers; expand the number of independent families; preregister the next version before testing; compare matched evidence budgets; add multi-frame, visually necessary questions with geometry withheld from model input; measure calibrated abstention and robust source attribution; and evaluate the actual Android UI with users. No airport safety, training-effectiveness, or accident-reduction claim follows from this pilot.

## Literature grounding

The separation of answer correctness from citation quality follows the evaluation concerns in [Gao et al., EMNLP 2023, ALCE](https://aclanthology.org/2023.emnlp-main.398/). Atomic fact assessment is motivated by [Min et al., EMNLP 2023, FActScore](https://aclanthology.org/2023.emnlp-main.741/). This project does not reproduce either benchmark or claim equivalent metrics: it verifies a much narrower typed scenario schema without an NLI judge.
