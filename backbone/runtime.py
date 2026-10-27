"""Device and number-type choice. Takes the torch module so it can be tested without torch."""


def pick_device(torch):
    """NVIDIA GPU (e.g. GAIVI), then Apple Silicon, then CPU; a Mac keeps the evaluated MPS path."""
    if torch.cuda.is_available():
        return 'cuda'
    return 'mps' if torch.backends.mps.is_available() else 'cpu'


def pick_dtype(torch, device, mps_dtype='float16'):
    """bfloat16 on NVIDIA where supported (float16 can overflow); MPS keeps the configured type."""
    if device == 'cpu':
        return torch.float32
    if device == 'cuda':
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    return getattr(torch, mps_dtype)
