# Training runtime failure repair

The bounded repair prevents a reported runtime error, malformed result or failed
serialization from leaving a poisoned worker advertised as ready. It does not
promise that model execution, stopping or semantic selection can never fail.
Original research outputs, the shared backbone/model-access implementation and
the narrated submission video remain outside this change.

The implementation keeps the existing 55-second worker request deadline,
60-second server and 90-second client budgets. A failed request receives an
explicit failure with unknown usage; it is never automatically replayed. A
replacement worker prepares only a subsequent user request. This runtime repair
does not change selector completeness rules; the separate history guard has its
own comparison and acceptance requirements.

The completion guard requires reported STOP, nonempty text, matching request and
accepted model identity. It now also rejects malformed typed fields and results
that cannot be serialized to finite JSON. Raw content, usage and reported stop
reason remain intact for well-formed rejected results. A reported runtime ERROR
is audited separately before retiring its worker. STOP is the engine's reported
reason; its length-based inference is not independent proof of actual EOS.

The worker catches ordinary exchange, validation and serialization exceptions.
It stops the old owner, closes its connection and joins bounded transport work
before preparing another owner. Resource release precedes the stopped-worker
audit so a broken audit destination cannot strand an otherwise stopped owner.
Audit failure leaves service unavailable. Recovery startup failure also cleans
up its replacement even when recording that failure fails. No second owner is
started while the previous owner remains live.

The implementation review found concrete holes in the earlier narrow exception
handler: non-string text or malformed finish reasons could escape validation,
non-JSON metadata could reach later server serialization, and audit exceptions
could interrupt cleanup before closing connections. Regression tests exercise
these cases using real spawned interpreters and fake inference. They also check
process-creation failure, unpicklable results, hangs, crashes, stopped-worker
large sends, concurrency rejection, startup failure, shutdown races, runtime
error replacement and unavailable recovery. All 17 targeted tests passed in
2.540 seconds with `.venv-qwen/bin/python -m unittest
 tests.test_training_completion tests.test_training_worker -v` (log:
`/tmp/airfield-runtime-repair-tests.log`). The same 17 tests also passed in 2.538 seconds with `.venv-candidates`.
The existing training-adapter regression suite passed separately in that runtime.
These are lifecycle/adapter tests, not actual model accuracy evidence.

The separate actual-model probe is `scripts/probe_runtime_error_recovery.py`,
with its importable test injector in `scripts/runtime_error_probe_adapter.py`.
It locks source hashes before execution, runs actual text/image warmup and an
actual response, injects one explicit runtime ERROR, then requires a different
warmed worker and another actual response. Every attempt is kept in a distinct
output directory. The first attempt at
`outputs/runtime-error-recovery-20261103` failed during factory unpickling before
any inference request (EOFError in the parent); its failed summary is retained.
The harness correction moved the injector out of `__main__` into an importable
module. The explicit second attempt uses `.venv-candidates/bin/python` and
`outputs/runtime-error-recovery-20261103-r2`. That run exited successfully:
PID 7256 stopped before replacement PID 7291 started; actual pre/post responses
both returned `ready\n`, reported STOP, and used four output tokens. The
injected failure returned empty error output in 0.509 seconds while its partial
text and provider error were retained in the worker audit. Both owners performed
text and image warmup. The image path answered `B.\n`, so warmup establishes
kernel execution, not response accuracy. Final status was closed. The stderr
log also contains Python's warning about one leaked semaphore at shutdown; this
probe does not establish zero resource leakage. Logs are copied into the r2
output directory beside lock, request records, warmup audit and summary.

Independent bounded code/receipt review found no blocking defect in this runtime
scope. The reviewer matched all three runtime source hashes to the r2 lock and
read the actual-model request/worker records: partial output and provider error
were audited before the old owner stopped, then a different warmed owner served
the subsequent request. The completion checks validate selected required field
types and finite JSON serialization, not every possible Result scalar schema.
The final [full-suite log](../../outputs/assistant-repair-pass-v2/tests.log)
records 395 passing tests in 77.860 seconds; [research integrity](../../outputs/assistant-repair-pass-v2/integrity.log)
passes with 160 preserved result records and [backbone boundaries](../../outputs/assistant-repair-pass-v2/backbone.log)
pass. The [preservation receipt](../../outputs/assistant-repair-pass-v2/preservation.json)
records 309 earlier output files unchanged, the unchanged production typed
reviewer and the fixed narrated-video hash. These checks support bounded runtime
acceptance together with the actual probe; they are not whole-assignment
acceptance. The separate history/typed candidates cannot inherit semantic
acceptance from this probe.

The probe's pre-history adapter is preserved as
`outputs/assistant-repair-pass-v2/source/runtime-probe-adapter.py`, matching the
probe's locked hash. The final adapter additionally contains the separately
evaluated history guard; the worker and result-checking sources remain the
probe versions. Do not describe the earlier real probe as an exact-final-adapter
run. The final CPU test suite overlapped the latter ordinary comparison arm;
ordinary timings therefore remain descriptive, not a controlled comparison.

The implementing agent also read back the actual-model summary, requests and
lifecycle records. This evidence neither establishes natural runtime-error
frequency nor indefinite resource stability, semantic correctness or a genuine
EOS signal. No historical failure is removed by a successful bounded probe.
