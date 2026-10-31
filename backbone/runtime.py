"""Device, number type and attention implementation. Takes the torch module so it can be tested without torch.

An engine never chooses these itself (backbone 1.1.0). Each run names a runtime
profile from models.json, or passes all three values, and results record them:
MPS float16, CUDA float16, CUDA bfloat16 and CPU float32 can flip near-zero
label margins, so they are not interchangeable backends. A requested device
that is unavailable is an error; there is no fallback.

pick_device and pick_dtype remain as suggestions for interactive use only.
"""
DEVICES = ('mps', 'cuda', 'cpu')
DTYPES = ('float16', 'bfloat16', 'float32')
ATTENTION = ('eager', 'sdpa')


def pick_device(torch):
    """Suggestion only: NVIDIA GPU (e.g. GAIVI), then Apple Silicon, then CPU."""
    if torch.cuda.is_available():
        return 'cuda'
    return 'mps' if torch.backends.mps.is_available() else 'cpu'


def pick_dtype(torch, device, mps_dtype='float16'):
    """Suggestion only: bfloat16 on NVIDIA where supported (float16 can overflow); MPS keeps the configured type."""
    if device == 'cpu':
        return torch.float32
    if device == 'cuda':
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    return getattr(torch, mps_dtype)


def resolve_runtime(torch, device, dtype, attn_implementation):
    """Validate an explicit runtime and return (device, torch dtype, attention). Never substitutes."""
    if device not in DEVICES:
        raise ValueError(f'device must be one of {DEVICES}, not {device!r}')
    if dtype not in DTYPES:
        raise ValueError(f'dtype must be one of {DTYPES}, not {dtype!r}')
    if attn_implementation not in ATTENTION:
        raise ValueError(f'attn_implementation must be one of {ATTENTION}, not {attn_implementation!r}')
    available = {'cpu': True, 'mps': torch.backends.mps.is_available(), 'cuda': torch.cuda.is_available()}
    if not available[device]:
        raise RuntimeError(f'Requested device {device} is unavailable; no fallback is applied')
    if device == 'cuda' and dtype == 'bfloat16' and not torch.cuda.is_bf16_supported():
        raise RuntimeError('This GPU does not support bfloat16; choose another runtime profile explicitly')
    return device, getattr(torch, dtype), attn_implementation
