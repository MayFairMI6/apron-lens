"""Image preparation shared by hosted adapters.

Hosted adapters downscale to the same `image_max_side` the local adapter uses,
so every provider sees the same pixels. The result is re-encoded as PNG.
"""
import base64
import io


def prepare_png(image, max_side):
    """Return (base64 PNG string, width, height) no larger than max_side on either axis."""
    from PIL import Image
    picture = Image.open(io.BytesIO(image.data)).convert('RGB')
    picture.thumbnail((max_side, max_side))
    stream = io.BytesIO()
    picture.save(stream, format='PNG')
    return base64.standard_b64encode(stream.getvalue()).decode('ascii'), picture.width, picture.height
