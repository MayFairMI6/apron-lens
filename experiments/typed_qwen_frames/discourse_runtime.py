"""Explicit discourse-first variant; inherits the same one-request deadline path."""
from .two_pass_runtime import TwoPassFrameAdapter
from . import discourse_candidate


class DiscourseFrameAdapter(TwoPassFrameAdapter):
    candidate_api = discourse_candidate
