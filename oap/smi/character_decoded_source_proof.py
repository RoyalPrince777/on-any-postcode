"""Offline proof that supplied RGBA matches bytes decoded from the exact SMI JPEG.

Only byte/pixel lineage. Never approves anatomy, speech, motion or a live rig.
No network, filesystem writes, retained media, or third-party telemetry.
"""
from __future__ import annotations

import hashlib
import hmac
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from .character_rig_assets import APPROVED_SOURCE_SHA256

MAX_SOURCE_BYTES = 32_000_000
MAX_PIXELS = 16_000_000


def matches_approved_decoded_rgba(
    jpeg_bytes: object, rgba: object, width: object, height: object
) -> bool:
    """Decode *the hashed bytes* independently, compare every RGBA byte."""
    if (
        not isinstance(jpeg_bytes, bytes)
        or not 0 < len(jpeg_bytes) <= MAX_SOURCE_BYTES
        or not isinstance(rgba, bytes)
        or type(width) is not int
        or type(height) is not int
        or not 0 < width <= 8192
        or not 0 < height <= 8192
        or width * height > MAX_PIXELS
        or len(rgba) != width * height * 4
        or not hmac.compare_digest(
            hashlib.sha256(jpeg_bytes).hexdigest(), APPROVED_SOURCE_SHA256
        )
    ):
        return False
    try:
        with Image.open(BytesIO(jpeg_bytes)) as original:
            if (
                original.format != "JPEG"
                or original.size != (width, height)
                or getattr(original, "n_frames", 1) != 1
                or original.getexif().get(274, 1) != 1
            ):
                return False
            independently_decoded = original.convert("RGBA").tobytes()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        return False
    return hmac.compare_digest(independently_decoded, rgba)
