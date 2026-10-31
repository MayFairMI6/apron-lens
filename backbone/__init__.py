"""Shared, frozen vision-language backbone for ApronLens and the compaction project.

Projects use only the names in __all__. Prompts, data, labels, memory policies,
evidence rules and anything trained live in each project, never here.
See backbone/README.md for the boundary and python -m backbone.check for its enforcement.
"""
from pathlib import Path
from backbone.registry import PRIMARY_MODEL, check_transformers, expected_manifest, model_dir, model_entry, model_names
from backbone.runtime import pick_device, pick_dtype
from backbone.engine import VLMEngine, load_engine

__version__ = (Path(__file__).parent / 'VERSION').read_text().strip()
__all__ = ['PRIMARY_MODEL', 'VLMEngine', 'check_transformers', 'expected_manifest', 'load_engine',
           'model_dir', 'model_entry', 'model_names', 'pick_device', 'pick_dtype', '__version__']
