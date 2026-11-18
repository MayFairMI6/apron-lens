# Answering coordinator questions: five methods on frozen test sets

Every method answers the same typed questions about one aircraft at a fixed replay moment
(apron: flight A2 at 20 s; tower: EZY123 at 50 s, both aircraft's reports visible). The
correct answer is what the deterministic rules return for the labelled query. Test sets were
hash-frozen and committed before any parser existed; thresholds were set on dev only
(`dev-tuning.json`). Greedy decoding; run settings are listed below.

## Correct final answers

| Dataset | Model | Direct inference (model picks the facts) | PAL: model-written Python, sandboxed | Model-written query + code | Model choice + code | Keywords + code |
|---|---|---:|---:|---:|---:|---:|
| apron | qwen2.5-vl-3b | 9/36 | 3/36 (3 invalid) | 23/36 (13 invalid) | 27/36 | 31/36 (2 invalid) |
| apron | qwen3-vl-4b | 17/36 | 3/36 (6 invalid) | 35/36 (1 invalid) | 32/36 | 31/36 (2 invalid) |
| tower | qwen2.5-vl-3b | 8/24 | 1/24 (5 invalid) | 14/24 (7 invalid) | 20/24 | 19/24 (3 invalid) |
| tower | qwen3-vl-4b | 12/24 | 1/24 (3 invalid) | 20/24 | 20/24 | 19/24 (3 invalid) |

"Invalid" means output the method could not use: a query outside the grammar, JSON that did not
parse, or code rejected by the sandbox or failing at run time. Invalid outputs count as wrong.

## Query accuracy for the parsing methods

| Dataset | Model | Choice | Model-written | Keywords |
|---|---|---:|---:|---:|
| apron | qwen2.5-vl-3b | 25/36 | 17/36 | 30/36 |
| apron | qwen3-vl-4b | 30/36 | 32/36 | 30/36 |
| tower | qwen2.5-vl-3b | 20/24 | 10/24 | 18/24 |
| tower | qwen3-vl-4b | 20/24 | 20/24 | 18/24 |

## Median seconds per question (4-core CPU)

| Dataset | Model | Choice | Model-written | Direct | PAL |
|---|---|---:|---:|---:|---:|
| apron | qwen2.5-vl-3b | 4.3 | 5.1 | 12.3 | 29.5 |
| apron | qwen3-vl-4b | 5.1 | 6.1 | 15.5 | 70.2 |
| tower | qwen2.5-vl-3b | 4.1 | 5.7 | 21.6 | 37.0 |
| tower | qwen3-vl-4b | 4.8 | 6.8 | 28.0 | 160.1 |

## Run settings

| Dataset | Model | Revision | Device | Number type | Attention | Code commit | transformers |
|---|---|---|---|---|---|---|---|
| apron | qwen2.5-vl-3b | `6628554` | cpu | float16 | not recorded | `d7b67ac` | 4.57.6 |
| apron | qwen3-vl-4b | `ebb281e` | cpu | float16 | not recorded | `d7b67ac` | 4.57.6 |
| tower | qwen2.5-vl-3b | `6628554` | cpu | float16 | not recorded | `d7b67ac` | 4.57.6 |
| tower | qwen3-vl-4b | `ebb281e` | cpu | float16 | not recorded | `d7b67ac` | 4.57.6 |

Runs without a recorded attention setting came from the closed PR #74 code (commit `d7b67ac`),
where the same method code lived at `scripts/evaluate_query_parsing.py`, `backend/query_parser.py`,
`backend/direct_answer.py` and `backend/program_answer.py`. Against the modules here it differs only
in comments and import paths, and it used the same pinned model revisions and test files (identical
hashes). That engine loaded Qwen2.5-VL with eager attention and other models with the library
default (SDPA on CPU).

## Limits

- Questions and labels were written by the AI assistant that wrote the parsers, without
  independent human review; one scenario and one replay moment per dataset. Development-scale.
- The keyword rules were written from the dev questions; test wording differs on purpose. While
  testing this report script with a fake model, the tower test set was read once before the real
  runs, which showed the keyword baseline's tower score; the rules were already committed and
  were not changed afterwards.
- Direct inference and PAL see both aircraft's reports; parsing methods only produce a query
  and the rules handle identity, so the comparison is between whole designs, not prompts.
- The PAL sandbox suits a disposable evaluation container; the service never runs model code.

Raw outputs, option scores, model-written queries and code, and errors for every question are in
`runs/`. `runs/test-apron-qwen2.5-vl-3b`, `runs/test-apron-qwen3-vl-4b`, `runs/test-tower-qwen2.5-vl-3b`, `runs/test-tower-qwen3-vl-4b`.
