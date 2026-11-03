# Reliability results

Ordinary v8 is adopted with the narrowed reference guard and startup warmup.
Typed candidates are rejected; the original typed reviewer and 60-second server
budget are restored exactly. Model weights, scenes, learner UI and video are unchanged.

| Check | Result |
|---|---|
| regression-v8 | 24/24; 25 calls; maximum 14.016s |
| fresh-v5 | 24/24; 24 calls; maximum 7.693s |
| fresh-v8 | 24/24; 24 calls; maximum 8.052s |
| Rejected indexed typed candidate | 15/18; 20 attempts; maximum 79.491s |

The old study remains 22/24 for both v5 and v6. The 24/24 v8 regression result
is a new development measurement, not a replacement. The 24 new probes are
paraphrases with renamed flight IDs in the same four families; both v5 and v8
pass, so this is not evidence of new-probe superiority. One genuine retry
corrected the wrong-flight stand answer in 14.016 seconds.

The typed candidate produced three accepted semantic failures: false occupancy,
a partial answer treated as an implied readiness claim, and an unsupported extra
claim. Valid quotations and source IDs did not make these judgments correct.
No further tuning was used to erase them. Recovery-only and indexed trials,
including interrupted trials and all invalid attempts, remain preserved.

The indexed trial used 0 passage-ID selections; observed gains cannot be attributed to ID expansion. Exact valid literal quotations were accepted by the backwards-compatible transport.

The temporary 80-second investigation budget is not deployed. Some recovered
candidate reviews approached it closely; the rejected candidate therefore does
not establish a timeout-free learner flow. Startup warmup addresses preparation
before readiness, not arbitrary slow or indefinitely stuck inference.

All 27 older artifacts are hash-preserved. The exact executed v7/v8 adapters,
typed candidates and runners are archived. Final guard replay matches all 48 v8
turns; typed expansion replay matches every saved attempt. Supplemental provenance
and post-lock refinements are explicitly identified in the protocol document.

Local verification: 334 tests passed, frozen research integrity preserved all160
records, and the backbone boundary check passed. Native/service and independent
review receipts accompany this report; they are distinct from offline model runs.
