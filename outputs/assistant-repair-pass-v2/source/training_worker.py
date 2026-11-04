"""Killable inference ownership for the live training service only.

Prompts/validators stay in the original adapter. A failed request is never retried
implicitly: replacement warmup prepares a subsequent user request.
"""
import json
import multiprocessing as mp
import threading
import subprocess
import sys
import os
import time
from pathlib import Path
from modelaccess.contract import Result, FinishReason, Usage
from dataclasses import asdict
from backend.training_result import checked_training_result


def _serve(connection, factory, settings):
    try:
        adapter = factory()
        adapter.load()
        warmup = adapter.warmup(settings)
        connection.send(('ready', warmup))
        while True:
            operation, request = connection.recv()
            connection.send(('result', getattr(adapter, operation)(request)))
    except (EOFError, BrokenPipeError):
        pass
    except BaseException as exc:
        try: connection.send(('failure', type(exc).__name__))
        except (EOFError, BrokenPipeError, OSError): pass
    finally:
        connection.close()


class _ProcessOwner:
    """Independent interpreter: child resource tracking is not shared with service."""
    def __init__(self, connection):
        self.connection = connection
        self.process = None
    @property
    def pid(self): return None if self.process is None else self.process.pid
    @property
    def exitcode(self): return None if self.process is None else self.process.poll()
    def start(self):
        if os.name != 'posix': raise RuntimeError('Isolated training worker requires POSIX')
        self.process = subprocess.Popen(
            [sys.executable, '-m', 'backend.training_worker', str(self.connection.fileno())],
            pass_fds=(self.connection.fileno(),), stdin=subprocess.DEVNULL,
            cwd=Path(__file__).resolve().parents[1],
            env=dict(os.environ, PYTHONPATH=os.pathsep.join(str(p) for p in sys.path if p)))
    def is_alive(self): return self.process is not None and self.process.poll() is None
    def terminate(self): self.process.terminate()
    def kill(self): self.process.kill()
    def join(self, timeout=None):
        try: self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired: pass
    def close(self):
        if self.is_alive(): raise RuntimeError('Cannot close live worker')


class IsolatedTrainingAdapter:
    provider = 'local-backbone'

    def __init__(self, factory, served_model, *, audit_path, generation_timeout=55.,
                 startup_timeout=300., cleanup_timeout=2.):
        self.factory, self.served_model = factory, served_model
        self.audit_path = Path(audit_path)
        self.generation_timeout = generation_timeout
        self.startup_timeout, self.cleanup_timeout = startup_timeout, cleanup_timeout
        self._context = mp.get_context('spawn')
        self._lock = threading.Lock()
        self._closed = threading.Event()
        self._process = self._connection = self._settings = None
        self._recovery = None
        self._startup_transport = None
        self.status = 'starting'

    def _record(self, event, **values):
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open('a') as stream:
            stream.write(json.dumps(dict(event=event, recordedAt=time.time(), **values))+'\n')

    def _stop(self):
        process = self._process
        stopped = None
        if process is not None:
            pid = process.pid
            if process.is_alive():
                process.terminate(); process.join(self.cleanup_timeout)
            if process.is_alive():
                process.kill(); process.join(self.cleanup_timeout)
            if process.is_alive():
                self.status = 'failed'
                raise RuntimeError('Previous model worker has not stopped')
            if process.pid is not None: process.join()
            stopped = dict(pid=pid, exitcode=process.exitcode)
            process.close(); self._process = None
        if self._connection is not None:
            self._connection.close(); self._connection = None
        if self._startup_transport is not None:
            self._startup_transport.join(min(.25, self.cleanup_timeout))
            if self._startup_transport.is_alive():
                self.status = 'failed'
                raise RuntimeError('Startup transport has not stopped')
            self._startup_transport = None
        # Audit failure must never prevent releasing a stopped owner's resources.
        if stopped is not None:
            self._record('worker_stopped', **stopped)

    def _start(self):
        self._stop()  # A second owner is forbidden until the old process is gone.
        if self._closed.is_set(): raise RuntimeError('Service closed')
        self.status = 'starting'
        parent, child = self._context.Pipe()
        process = _ProcessOwner(child)
        self._connection, self._process = parent, process
        try: process.start()
        finally: child.close()
        self._record('worker_started', pid=process.pid)
        finished = threading.Event()
        startup = {}
        def initialize():
            try:
                parent.send((self.factory, self._settings))
                startup['reply'] = parent.recv()
            except Exception as exc:
                startup['error'] = exc
            finally: finished.set()
        self._startup_transport = threading.Thread(target=initialize, daemon=True)
        self._startup_transport.start()
        deadline = time.monotonic()+self.startup_timeout
        while not finished.wait(.05):
            if self._closed.is_set(): raise RuntimeError('Service closed')
            if time.monotonic() >= deadline: raise TimeoutError('Worker startup timed out')
            if not process.is_alive(): raise RuntimeError('Worker exited during startup')
        if 'error' in startup: raise startup['error']
        kind, value = startup['reply']
        if kind != 'ready': raise RuntimeError('Worker startup failed: '+str(value))
        if self._closed.is_set(): raise RuntimeError('Service closed')
        self.status = 'ready'
        self._record('worker_ready', pid=process.pid)
        return value

    def warmup(self, settings):
        with self._lock:
            self._settings = settings
            try: return self._start()
            except Exception:
                self.status = 'failed'; self._stop(); raise

    def _recover(self):
        with self._lock:
            if self._closed.is_set():
                self.status = 'closed'; return
            try: self._start()
            except Exception as exc:
                self.status = 'closed' if self._closed.is_set() else 'failed'
                try:
                    self._record('worker_recovery_failed', error=type(exc).__name__)
                except Exception:
                    pass  # The failed audit destination cannot report its own failure.
                try:
                    # Logging failure must not strand a replacement model owner.
                    self._stop()
                except Exception:
                    self.status = 'closed' if self._closed.is_set() else 'failed'

    def _failure(self, request, error, started):
        return Result(request.request_id, self.provider, request.settings.model, None, '',
                      FinishReason.ERROR, 'worker_failure', Usage(), time.monotonic()-started,
                      {}, (), error=error, metadata={'workerStatus': self.status, 'usageUnknown': True})

    def _call(self, operation, request):
        started = time.monotonic()
        if not self._lock.acquire(blocking=False):
            return self._failure(request, 'model_worker_unavailable', started)
        try:
            if self.status != 'ready' or self._closed.is_set():
                return self._failure(request, 'model_worker_unavailable', started)
            # A stopped worker can block send() before it reads a large image,
            # or recv() midway through a message. Bound the whole exchange.
            connection = self._connection
            finished = threading.Event()
            exchange = {}
            def communicate():
                try:
                    connection.send((operation, request))
                    exchange['reply'] = connection.recv()
                except Exception as exc:
                    exchange['error'] = exc
                finally:
                    finished.set()
            transport = threading.Thread(target=communicate, daemon=True)
            try:
                transport.start()
                if not finished.wait(self.generation_timeout):
                    raise TimeoutError('Model request deadline exceeded')
                if 'error' in exchange: raise exchange['error']
                kind, value = exchange['reply']
                if kind != 'result': raise RuntimeError('Model worker failed: '+str(value))
                value = checked_training_result(value, request)
                if value.finish_reason == FinishReason.ERROR:
                    self._record('worker_runtime_failure', requestId=request.request_id,
                                 modelResult=asdict(value))
                    raise RuntimeError('Model runtime reported failure')
                self._record('worker_request_complete', requestId=request.request_id,
                             elapsedSeconds=time.monotonic()-started, ok=value.ok)
                return value
            except Exception as exc:
                self.status = 'recovering'
                audit_failed = False
                try:
                    self._record('worker_request_failed', requestId=request.request_id,
                                 error=type(exc).__name__, elapsedSeconds=time.monotonic()-started,
                                 usageUnknown=True)
                except Exception:
                    audit_failed = True
                try: self._stop()
                except Exception:
                    self.status = 'failed'
                    if transport.ident is not None:
                        transport.join(min(.25, self.cleanup_timeout))
                    return self._failure(request, 'model_worker_cleanup_failed', started)
                if transport.ident is not None:
                    transport.join(min(.25, self.cleanup_timeout))
                if transport.is_alive():
                    self.status = 'failed'
                    return self._failure(request, 'model_transport_cleanup_failed', started)
                if audit_failed:
                    self.status = 'failed'
                    return self._failure(request, 'model_worker_audit_failed', started)
                if not self._closed.is_set():
                    self._recovery = threading.Thread(target=self._recover, daemon=True)
                    self._recovery.start()
                return self._failure(request, 'model_worker_'+type(exc).__name__, started)
        finally:
            self._lock.release()

    def generate(self, request): return self._call('generate', request)
    def review(self, request): return self._call('review', request)

    def close(self):
        self._closed.set()
        # Startup polls the closed flag; inference has its own hard deadline.
        with self._lock:
            self._stop(); self.status = 'closed'
        if self._recovery is not None: self._recovery.join(self.cleanup_timeout)


if __name__ == '__main__':
    from multiprocessing.connection import Connection
    channel = Connection(int(sys.argv[1]))
    try:
        factory, settings = channel.recv()
        _serve(channel, factory, settings)
    finally:
        channel.close()
