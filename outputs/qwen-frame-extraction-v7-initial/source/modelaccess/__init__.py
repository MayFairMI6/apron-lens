"""Versioned model-access library shared by ApronLens and the GenAI project.

Each consuming project pins this library by commit SHA and upgrades it only by
an explicit change, so one update cannot silently alter both experiments.
"""
__version__ = '0.2.0'
