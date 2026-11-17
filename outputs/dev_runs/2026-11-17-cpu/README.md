# CPU development runs, 2026-11-17

Development observations, not held-out evidence. The 24 development questions
(`data/reasoning_v1`, split `dev`) and the two M1 smoke questions were used
during method development. Nothing here changes the frozen V2 evaluation.

**Setup.** Cloud container: 4 CPU cores, 15 GB memory, no GPU. Python 3.12,
torch 2.14.1+cpu, transformers 4.57.6, backbone 1.0.0, branch commit 174e8f9.
`scripts/run_model_check.py` run unchanged through `run_cpu_dtype.py`, which
only sets the CPU number type. Each `summary.json` records model revision,
number type, device and source hashes; `results.jsonl` keeps every raw answer
and Yes/No decision with its margin.

| Run | Number type | Exact | Rule baseline | Wall time | Peak memory |
|---|---|---|---|---|---|
| `cpu-smoke-qwen2.5-vl-3b` | bfloat16 | 1/2 | 2/2 | 15 s | 6.8 GB |
| `cpu-fp16-smoke-qwen2.5-vl-3b` | float16 | 2/2 | 2/2 | 25 s | 8.2 GB |
| `cpu-fp16-dev-qwen2.5-vl-3b` | float16 | 23/24 | 24/24 | 148 s | 10.4 GB |
| `cpu-smoke-qwen3-vl-4b` | bfloat16 | 2/2 | 2/2 | 13 s | 8.6 GB |
| `cpu-fp16-dev-qwen3-vl-4b` | float16 | 23/24 | 24/24 | 168 s | 10.6 GB |

**Observations.**

- The bfloat16 3B smoke miss (M1-14) is a rounding tie: one receipt-time
  comparison scored a Yes−No margin of exactly 0.0 (counted as No). All its
  bfloat16 margins are multiples of 0.125. In float16 the same question passes.
- Both dev-suite misses are receipt-time comparisons, withheld by the guard:
  - Qwen2.5-VL-3B, D08-Q1: judged 15 s not later than 14 s; its comparison
    margins are 0.016–0.047, close to chance.
  - Qwen3-VL-4B, D04-Q3: judged 18 s later than 28 s (margin 0.6) while also
    judging 28 s later than 18 s (margin 8.3), the late-report case.
- Qwen3-VL-4B's margins are 10–20 times larger than the 3B model's, so it is
  robust to rounding, but not more accurate here.
- The deterministic baseline answers all of these comparisons correctly.

These runs do not reproduce the evaluated configuration (Apple MPS float16).
