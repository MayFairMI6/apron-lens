# Answer methods: who should do the reasoning?

A self-contained comparison of five ways to answer a typed question about one
aircraft at a replay moment. It asks where a small local vision-language model
helps: reasoning over the reports itself, writing the logic, or only interpreting
the question while deterministic rules answer it.

| Method | Model's role | What decides the answer |
|---|---|---|
| `direct` | reads every received report and picks the facts | the model |
| `pal` | writes Python over the reports (PAL, Gao et al. 2022, arXiv 2211.10435) | the model's code, run in a sandbox |
| `generated` | writes a one-line query such as `current(baggage_status)` | a strict grammar, then `backend.evidence` |
| `choice` | picks a query type (A/B/C) and a topic letter by next-token scores | `backend.evidence` |
| `keyword` | none: keyword rules map the question to a query | `backend.evidence` |

Every method is scored on the **final answer**: the fact ids and unknown
properties it returns, against what `backend.evidence` returns for the labelled
query. Parsing methods are also scored on the query itself.

**Status: evaluation-only research record.** Nothing here changes the app, the
training backend, `backend/` sources (the frozen-source integrity check still
passes) or the shared backbone. Milestone placement is for the ledger reviewer;
see the dated entry in `docs/course/CLAUDE_TAKEOVER.md`.

## Data

| Folder | Questions | Replay moment |
|---|---|---|
| `data/apron/` | 36 dev, 36 test | frozen M1 replay, flight A2 at 20 s |
| `data/tower/` | 24 dev, 24 test | `tower1.json`, EZY123 at 50 s |

`tower1.json` is an original fictional tower replay: two departures with similar
call signs (EZY123, EZY132), an amended taxi clearance, a readback transcript that
arrived late, a readback from the wrong aircraft, and a take-off clearance whose
display update arrived late. Its five clearance fields are registered in
`backend.evidence.FIELDS` for the running process only (`scenarios.py`).

Each test set was hash-frozen (`manifest.json`) and committed before any parser
existed. Questions and labels were written by the AI assistant that wrote the
parsers, without independent human review. The keyword rules were written from
the dev questions. The choice thresholds were set on 32 apron dev questions only
(`outputs/answer-methods-v1/dev-tuning.json`).

## Run

Needs a model environment (`requirements-qwen.lock.txt`) and downloaded weights.

```sh
python -m experiments.answer_methods.evaluate --dataset apron --split test \
    --model qwen2.5-vl-3b --device cpu --dtype float16 --attn eager \
    --output work/answer-methods/apron-3b
python -m experiments.answer_methods.report work/answer-methods/apron-3b ...
```

`--methods` runs a subset; `--resume` continues an interrupted run. No run is
overwritten, gold labels are read only after every method has answered, and each
run records its model revision, device, number type, attention and source hashes.

## Safety of the PAL condition

Model-written code is parsed first and rejected if it imports, touches dunder
names or calls `open`, `eval`, `getattr` and similar. It then runs in a separate
isolated Python process with CPU, memory and file limits, plain built-ins only,
and an audit hook that aborts on file, network or process access. This suits a
disposable evaluation container; no service runs model-written code.

## Results

See `outputs/answer-methods-v1/REPORT.md`.
