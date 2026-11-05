"""Pure generated-token transport protocol for the frozen reasoning ablation."""

THINK_START_ID = 248068
THINK_END_ID = 248069
MAX_GENERATED_TOKENS = 1000


class ProtocolError(ValueError):
    """Invalid completion; caller must retain raw output rather than recover it."""


def _token(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def split_generated(token_ids, thinking: bool, eos_ids, max_tokens=1000):
    """Return a declared suffix only; counts include delimiter and terminal EOS.

    finalTokenIds excludes EOS for decoding. finalTokenCount includes EOS;
    reasoningTokenCount includes the generated closing marker. Inputs are not
    mutated. No decoded-text processing or semantic validation occurs here.
    """
    if not isinstance(thinking, bool):
        raise ProtocolError('thinking must be boolean')
    if not _token(max_tokens) or not 1 <= max_tokens <= MAX_GENERATED_TOKENS:
        raise ProtocolError('invalid token cap; cannot exceed frozen 1000')
    if not isinstance(token_ids, (list, tuple)) or any(not _token(t) for t in token_ids):
        raise ProtocolError('generated token IDs must be nonnegative integers')
    if (not isinstance(eos_ids, (list, tuple, set, frozenset)) or not eos_ids
            or any(not _token(t) for t in eos_ids)):
        raise ProtocolError('EOS IDs must be a nonempty integer collection')
    eos = set(eos_ids)
    if eos.intersection({THINK_START_ID, THINK_END_ID}):
        raise ProtocolError('thought markers cannot be EOS IDs')
    ids = list(token_ids)
    if not ids or len(ids) > max_tokens:
        raise ProtocolError('empty or over-cap generated sequence')
    if ids[-1] not in eos:
        raise ProtocolError('missing observed terminal EOS')
    if any(t in eos for t in ids[:-1]):
        raise ProtocolError('EOS occurs before terminal position')
    if THINK_START_ID in ids:
        raise ProtocolError('generated opening thought marker is forbidden')
    closes = [i for i, token in enumerate(ids) if token == THINK_END_ID]
    if thinking:
        if len(closes) != 1:
            raise ProtocolError('ON requires exactly one generated thought close')
        reasoning_count = closes[0] + 1
    else:
        if closes:
            raise ProtocolError('OFF forbids generated thought markers')
        reasoning_count = 0
    final_ids = ids[reasoning_count:-1]
    if not final_ids:
        raise ProtocolError('empty final suffix before EOS')
    return dict(finalTokenIds=final_ids, reasoningTokenCount=reasoning_count,
                finalTokenCount=len(ids) - reasoning_count,
                totalGeneratedTokens=len(ids))
