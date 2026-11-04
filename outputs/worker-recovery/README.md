# Bounded model-worker recovery

The live training entrypoint now loads its existing TrainingAdapter in a spawned
process. A request exceeding 55 seconds fails explicitly; the parent terminates
and joins its worker before starting a replacement. Terminate and kill each have
a two-second cleanup wait. This is an intended budget beneath the existing
60-second typed-server wait, not a universal exact wall-clock guarantee. The
native client's 90-second budget, prompts, rubric, weights and validators are
unchanged. The failed request is not replayed. Input remains available for the
learner to retry after replacement warmup. Health reports starting/failed rather
than ready during recovery. Shutdown closes the model process.

## Verification

Seven fake-engine tests use actual spawned processes: repeated hang/crash
recovery, failed initial and replacement startup, parallel request rejection,
shutdown during generation/queued recovery, and unpicklable-factory cleanup.
These test ownership and lifecycle behavior, not model accuracy.

The actual Qwen3.5-9B MPS service smoke loaded and warmed the pinned production
model, forced a 120-second sleep at the worker review boundary with a temporary
0.2-second fault-probe deadline, and recorded an explicit timeout. PID 3014 exited
before replacement PID 3067 started. The replacement reloaded and warmed in
18.22 seconds. Health was starting during recovery and ready afterward. The
normal 55-second deadline was restored before both actual model requests.

A typed fog response reached feedback with a supported verdict in 34.90 seconds;
its three quotations and evidence IDs refer to the actual learner response and
available reports. An ordinary question afterward returned a validator-accepted
answer. These are two compatibility examples, not a semantic benchmark. The
ordinary answer also included an unrequested readiness unknown; validation does
not certify the relevance of every statement. #60 remains unresolved.

The first smoke used the older .venv-qwen environment and failed startup with
ValueError; its logs are retained. The successful run used .venv-candidates.
Termination of the torch worker produced a Python resource-tracker warning about
two semaphore objects cleaned at interpreter shutdown. There is no claim of
indefinite repeated real-runtime recovery without resource accumulation. Repeated
recovery is tested with the lightweight engine; real-model recovery is one cycle.

The real smoke exercised the ASGI training application through TestClient, plus
an ordinary training turn, not a new native-phone recording. The two subsequent
cleanup-race corrections were covered by focused tests and independent code
review; this initial real smoke is not represented as an exact-source freeze of
those later corrections. Its original script is preserved as smoke-source.py.
The reusable script records source hashes and requires a new output directory.

No video or scenery was edited. The partial scenery review is recorded separately.
The accepted lifecycle remedy does not close #60/#61 or certify every aspect of
#62. Source/citation failures, semantic errors and general latency remain visible.

## Reproduction

From the repository root, run:

    .venv-qwen/bin/python -m unittest tests.test_training_worker -v
    AIRFIELD_RECOVERY_OUTPUT=work/recovery-new-run .venv-candidates/bin/python scripts/check_worker_recovery.py

Choose a new output directory each time. The second command loads the full local
model and deliberately terminates its isolated process once. It uses no remote
service and never changes the model weights or existing research results.
