# Model service

The Unity app asks a local Python service about the selected aircraft at the
current replay time. The service runs on a computer (Mac, Linux, or a GAIVI GPU
node); the phone is only the interface. No weights are packaged into the APK.
This is a fictional research prototype with no operational airport feed or
movement authority.

## What the model does

**The model interprets the question; code answers it.**

1. **Parse.** Qwen turns the typed question into a structured query: a query
   type (latest report, current value, or change history) and the topics it is
   about (stand, baggage, fuel, TOBT, route, movement, movement condition,
   checkpoint, overall readiness). It only scores fixed options (A/B/C, then
   Yes/No per topic), so it cannot return an invalid query. Method version:
   `query-parse-v1` (`backend/query_parser.py`).
2. **Answer.** Code reads the reports received by the replay time for that
   aircraft and flight, applies validity, replacement, expiry and conflict
   rules, and selects the facts. Every time comparison is done in code: the
   models misjudged receipt-time comparisons in development runs
   (`outputs/dev_runs/2026-11-17-cpu/`).
3. **Check and word.** Values, statuses, times and sources are copied from the
   reports into fixed sentence templates; the claim guard checks them. Overall
   readiness stays unknown unless a report establishes it; TOBT is an
   estimate, never a movement clearance.

A request that names `queryType` (and `properties`) skips the model. The scene
image the app sends is optional, hashed for the audit and never used for
inference. Response fields `parsedBy`, `queryType`, `properties` and
`modelRole` say what happened.

The earlier pipeline (`pairwise-predicates-v5`: Qwen Yes/No decisions on each
report, including receipt-time comparisons) remains in `backend/decisions.py`
for reproducing the frozen evaluation in `outputs/reasoning_v2/`.

## Install and start

Verified on an Apple Silicon Mac (MPS float16) and on a 4-core CPU container.

```sh
python3.12 -m venv .venv-qwen
.venv-qwen/bin/python -m pip install -r requirements-qwen.lock.txt
.venv-qwen/bin/python -m backend.download --model qwen2.5-vl-3b
bash scripts/start_qwen_server.sh
```

`python scripts/download_qwen.py` also fetches the evaluated model. Add
`--model qwen3-vl-4b` to the server (`python -m backend.server --model …`)
to use another model from `config/models.json`. On a CPU-only machine set
`APRONLENS_CPU_DTYPE=float16` so a 3–4B model fits in about 11 GB.

`scripts/verify_qwen.py` is a one-image installation check (it asks where a
red square is relative to a blue circle); it is not evidence of airport
reasoning.

## Connect the app

The first server start writes `work/qwen-server-token.txt`; keep it local.
The service listens on `http://127.0.0.1:8765`.

- **Unity editor:** open `DesktopReplay` and press Play; the editor reads the
  token automatically. Select an aircraft and time, then use **Why**.
- **Phone over USB:** `adb reverse tcp:8765 tcp:8765`, then in
  **More → Model connection** enter `http://127.0.0.1:8765` and the token.
- **Phone over trusted Wi-Fi:** start with `--host 0.0.0.0` and enter
  `http://<computer LAN address>:8765`. This development build uses HTTP, so use
  it only with this fictional scenario.

Changing aircraft or replay time hides an old answer. A failed connection keeps
the reports and rule check on screen; nothing is filled in for the model.

## Audit

`work/qwen-requests.jsonl` records each request: question, parsed query and
every scored option, evidence, answer, model revision, tokens, latency and image
hash. No image bytes or tokens are logged. Scores are not calibrated confidence.

## Evaluation records

| Record | What it shows |
|---|---|
| `outputs/query_parsing_v1/` | Question parsing: model vs keyword baseline on a hash-frozen test set |
| `outputs/dev_runs/2026-11-17-cpu/` | CPU development runs of the predicate pipeline; receipt-time comparison errors |
| `outputs/reasoning_v2/REPORT.md` | Frozen evaluation of the predicate pipeline (31/32 vs 32/32 rule baseline) |
| `outputs/reasoning_v1/REPORT.md` | First pilot |
| `outputs/milestone1/` | Unity integration and layout checks |

The model's upstream licence stays with the weights: Qwen2.5-VL-3B uses the Qwen
Research License (non-commercial research and evaluation); the candidates in
`config/models.json` list their own.
