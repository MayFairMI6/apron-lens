# Remaining-fixes outcome

The reliability correction is accepted within the tested bounds. The experimental
typed-review replacement failed development and is not deployed. The wide scenery
audit established no geometry mismatch that warrants changing the renderer. The
finished 8:06.4 narrated presentation is unchanged and now replaces the older
Drive edit at the same file link.

| Area | Implemented and verified | Remaining limitation |
|---|---|---|
| Worker reliability (#62) | Independent interpreter per model owner; fresh connection after failure; deadline covers sending and receiving as well as inference; stopped worker with a large blocked send tested; three forced real-runtime recoveries with subsequent genuine responses. | Cold/replacement loading still takes time. Child cleanup warnings remain. Three cycles do not establish indefinite resource stability or recovery from all device faults. |
| Typed feedback (#60/#61) | Two isolated development revisions and exact learner-text references evaluated; failures retained and independently reviewed. | Candidate rejected: 2/6 exact delivered reviews, one false-credit review, three withheld. Production reviewer stays unchanged; semantic and generation limitations remain open. |
| Scenery (#59) | Astra reviewed saved wide native views and independently reconstructed 24 mapped water polygons, including holes, from the saved sources with zero symmetric difference. | Original reported viewpoint is unknown; no fresh current-build Region capture or full-video clearance. No demonstrated false-island geometry to patch. |
| Video and publication | Final narrated video unchanged; same Drive file ID, updated name and 49,176,272-byte size verified by readback. Original and silent local versions retained. | Drive's processed playback was not separately inspected; existing permissions preserved. |

## Reliability evidence

The live service now starts an independent POSIX interpreter rather than sharing
the parent's multiprocessing resource tracker. The old model owner must stop
before a replacement starts. Startup and the complete request exchange are bounded;
a blocked send of a large request can no longer precede the request timeout.
A failed request remains a failure and is never implicitly replayed or replaced by
a scripted answer. A later request can use the warmed replacement.

The intended request/cleanup allowance is 55 + 2 + 2 + 0.25 seconds, beneath the
existing 60-second server wait before scheduling overhead. It is not a universal
wall-clock guarantee. Startup has its own 300-second limit. This worker path
requires POSIX (the supported Mac/Linux setup); factories must be importable by
the child interpreter. The final import-path handoff fixes discovery-mode tests.

[Repeated real-model receipts](../repeated-worker-recovery-v1/) preserve three
forced hang/crash/hang cycles, recovery in 19.73, 23.89 and 21.11 seconds, and a
genuine Qwen3.5-9B reply after each. The probe uses a temporary 0.2-second deadline
for the deliberate fault, restores the normal 55-second deadline for real replies,
and records stop-before-start ownership. Recorded previous owner and descendant
PIDs were absent after each recovery. These are deliberately injected faults in a
loaded real model, not spontaneous device failures. The crash has exit code 7 even
though the shortened caller deadline reports TimeoutError.

Four child semaphore-cleanup warnings are retained in stderr. Parent RSS was
nonmonotonic; shared device allocation was not measured. Do not claim warning-free
or indefinitely leak-free execution. The exact tested worker source is preserved
as `../repeated-worker-recovery-v1/worker-source.py` and matches its locked hash.
The only subsequent worker change adds the parent's import search paths to the
child environment. The [final source snapshot](worker-source-final.py) has full
suite and independent source-review coverage, not another exact-final-source
real-model run.

[357 tests passed](../remaining-fixes-tests/airfield-fixes-tests-final.log), including
an actual stopped worker and blocked 2 MB request. The earlier full-suite failure
with seven child factory-import errors remains alongside the successful log.
Research-integrity and backbone-boundary checks have separate saved receipts.
[Independent review](../remaining-fixes-review.md) records coverage and limits.

## Typed-review experiment and stopping decision

[The plan](../../docs/course/REMAINING_FIXES_PLAN.md) separates learner coverage
from evidence support, and literal quotations from semantic correctness. It allows
two development revisions before deciding whether to freeze a candidate for a
fresh paired comparison. These six scenarios are exposed development material;
they are not independent held-out questions.

Revision 1 returned fenced JSON on all six cases; the strict parser withheld all
six. Revision 2 permits one complete JSON fence, strengthens the coverage wording,
and rejects inconsistent support mappings. Its complete actual results are:

| Cases | Delivered outcome |
|---|---|
| Waiting inbound versus occupied stand; completed fuel versus outstanding baggage | Two accepted exact reviews. |
| Fog answer omitting the requested hold/clearance status | Accepted false credit: omission was treated as implying the answer. |
| False stand-occupancy claim | Correct contradiction in raw text, but wrong output schema; withheld. |
| Correct core with an invented engine fire | Raw unsupported addition detected, but empty evidence list violates the contract; withheld. |
| Valid explicit uncertainty | Raw substantive statuses appropriate, but criterion cites a report outside its permitted set; withheld. |

Accepted yield is 3/6, exact delivered status match 2/6, and accepted fully correct
responses 2/3. Withholding is not a correct delivered review. This unpaired
six-case development result supports no improvement claim. Exact source text and
eligible report IDs did not prevent false credit. The candidate is not an atomic
entailment proof or a completed C02 claim checker.

Both [v1](../typed-claim-development-v1/) and [v2](../typed-claim-development-v2/)
retain raw prompts, outputs, lock files, model metadata and candidate snapshots.
The final [candidate](../../experiments/typed_claim_review/candidate.py) stays
isolated from production. The development gate failed; no fresh paired evaluation
set was consumed, no native adoption test was claimed, and no replacement reviewer
or weights were deployed. Further tuning is outside this completed bounded pass.
Original M2/M3 assignments remain separate.

## Scenery and video

The [Astra audit](scenery/wide-scenery-audit.md), [geometry receipt](scenery/wide-scenery-source-audit.json)
and copied native/frame samples preserve the new wide-view evidence. Twenty-four
is the full water-feature count, including Wraysbury; twenty-three was the earlier
addition count. Mapped western lake islands are not an airport-surrounding island.
No cosmetic removal of valid geography is justified. Issue #59 remains open with
its user-reported origin intact because the original camera/view is unidentified.

[Drive publication receipt](drive-publication.json) records the same-ID replacement
with the finished narrated presentation. This pass changes neither its visuals nor
spoken content. No voice recording is committed to the repository.

[Preservation audit](preservation.json) checks all pre-pass tracked output files
using Git-normalized hashes; existing results and the production typed reviewer
remain unchanged. Failure records are not new milestone tasks. Publication of a
bounded remedy does not mean every assistant limitation or course requirement is
resolved.

## Reproduction commands

From the repository root, using the existing compatible local runtimes:

```sh
.venv-qwen/bin/python -m unittest discover -s tests -v
.venv-qwen/bin/python scripts/check_research_integrity.py --current
.venv-qwen/bin/python -m backbone.check --project backend scripts tests modelaccess
.venv-candidates/bin/python scripts/check_repeated_worker_recovery.py work/recovery-new-run
.venv-candidates/bin/python scripts/develop_typed_claim_review.py work/claim-new-run experiments/typed_claim_review/development-v2.json
```

The last two commands require the existing pinned Qwen3.5-9B local weights and
write to new directories; they must not overwrite the saved receipts. They are
reproduction instructions, not a request to reopen the failed development cycle.
