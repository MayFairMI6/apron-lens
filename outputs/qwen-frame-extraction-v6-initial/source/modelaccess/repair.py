"""One versioned JSON repair policy, applied identically to every provider.

Provider-specific repairs would make output validity a hidden fairness
variable. The only repair allowed is removing one surrounding Markdown code
fence. Raw validity is always reported separately from repaired validity.
"""
import json
import re

REPAIR_POLICY_VERSION = 'json-repair-v1'
_FENCE = re.compile(r'^```(?:json)?\s*\n?(.*?)\n?\s*```$', re.DOTALL)


def parse_json_output(text: str):
    """Return (value_or_None, raw_valid, repairs_applied, error)."""
    try:
        return json.loads(text), True, (), None
    except (json.JSONDecodeError, TypeError):
        pass
    stripped = (text or '').strip()
    match = _FENCE.match(stripped)
    if match:
        try:
            return json.loads(match.group(1)), False, ('strip_code_fence',), None
        except json.JSONDecodeError as exc:
            return None, False, ('strip_code_fence',), 'invalid_json:' + exc.msg
    return None, False, (), 'invalid_json'
