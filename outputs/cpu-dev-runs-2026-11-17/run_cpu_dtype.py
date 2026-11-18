"""Wrapper used for these runs: sets the CPU number type (CPU_DTYPE, default bfloat16) so 3-4B models fit in 15 GB.

It patches an engine internal on purpose, for this one-off record only; it is not project code.
Usage from the repository root: CPU_DTYPE=float16 python outputs/dev_runs/2026-11-17-cpu/run_cpu_dtype.py --suite dev --model qwen3-vl-4b --output work/x
"""
import atexit
import resource
import runpy
import sys
import time

started = time.perf_counter()
atexit.register(lambda: print(f'PEAK_RSS_GB {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.1f} '
                              f'WALL_S {time.perf_counter() - started:.0f}', flush=True))

ROOT = str(__import__('pathlib').Path(__file__).resolve().parents[3])
sys.path.insert(0, ROOT)
import backend.engine as engine

original = engine.pick_dtype
import os
CPU_DTYPE = os.environ.get('CPU_DTYPE', 'bfloat16')
engine.pick_dtype = lambda torch, device, mps_dtype='float16': getattr(torch, CPU_DTYPE) if device == 'cpu' else original(torch, device, mps_dtype)
sys.argv = [f'{ROOT}/scripts/run_model_check.py', *sys.argv[1:]]
runpy.run_path(sys.argv[0], run_name='__main__')
