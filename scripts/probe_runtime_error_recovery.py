"""Real-model warmup/recovery with one injected provider error; no accuracy claim.

Run only after the service/other model owners have stopped. Uses a new output
folder and never changes frozen research records or retries the failed request.
"""
import hashlib
import json
import sys
import time
from dataclasses import asdict
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.training_adapter import TrainingAdapter
from backend.training_worker import IsolatedTrainingAdapter
from modelaccess.contract import FinishReason, Request, Result, Settings, Usage


from scripts.runtime_error_probe_adapter import RuntimeProbeAdapter

def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    sources = ['backend/training_worker.py', 'backend/training_result.py',
               'backend/training_adapter.py', 'scripts/probe_runtime_error_recovery.py',
               'scripts/runtime_error_probe_adapter.py']
    (out / 'lock.json').write_text(json.dumps({
        'sourceSHA256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                         for name in sources},
        'generationTimeoutSeconds': 55, 'startupTimeoutSeconds': 300,
        'scope': 'One injected runtime error between real inference calls. Not a naturally occurring model failure or semantic acceptance.'
    }, indent=2))
    factory = partial(RuntimeProbeAdapter, 'qwen3.5-9b', profile='apronlens-v2-mps',
                      prompt_audit_path=out / 'selector.jsonl')
    adapter = IsolatedTrainingAdapter(factory, factory().served_model,
                                      audit_path=out / 'worker.jsonl')
    settings = Settings(adapter.served_model, 64, image_max_side=672)
    rows = []
    def call(name):
        reply = adapter.review(Request(name, (('user', 'Reply with the word ready.'),), settings))
        row = dict(requestId=name, result=asdict(reply), status=adapter.status,
                   pid=None if adapter._process is None else adapter._process.pid)
        rows.append(row)
        with (out / 'records.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        return reply
    summary = {'accepted': False, 'scope': 'bounded runtime ownership probe'}
    try:
        adapter.warmup(settings)
        first = call('before-failure')
        if not first.ok:
            raise RuntimeError('Initial actual inference failed; retained without retry')
        old_pid = adapter._process.pid
        failed = call('injected-runtime-error')
        if failed.ok or failed.text:
            raise RuntimeError('Injected runtime error was delivered as an answer')
        deadline = time.monotonic() + 310
        while adapter.status in ('starting', 'recovering') and time.monotonic() < deadline:
            time.sleep(.2)
        if adapter.status != 'ready' or adapter._process.pid == old_pid:
            raise RuntimeError('Replacement owner did not become ready')
        last = call('after-recovery')
        if not last.ok:
            raise RuntimeError('Actual post-recovery inference failed; retained without retry')
        summary.update(accepted=True, oldPID=old_pid, newPID=adapter._process.pid)
    except Exception as exc:
        summary.update(errorType=type(exc).__name__, error=str(exc), status=adapter.status)
        raise
    finally:
        try:
            adapter.close()
        finally:
            summary['closedStatus'] = adapter.status
            summary['requestsRecorded'] = len(rows)
            (out / 'summary.json').write_text(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
