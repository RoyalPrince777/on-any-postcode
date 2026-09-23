"""Private offline source-decode evidence; never authorises SMI motion or lip-sync.

Decode the *same* JPEG bytes whose SHA-256 matches the approved source.
Compare a full-canvas raw RGBA geometry payload against those decoded pixels
under an explicit white-alpha mask. No supplied source-RGBA is trusted.
"""
from __future__ import annotations

import hashlib
import hmac
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from .character_rig_assets import APPROVED_SOURCE_SHA256

MAX_PIXELS = 16_000_000
MAX_SOURCE_BYTES = 32_000_000


def verify_decoded_visible_geometry(
    original_jpg: bytes, mask_rgba: bytes, geometry_rgba: bytes
) -> dict[str, object]:
    """Return private evidence only; never inferred anatomy or active rig status."""
    result: dict[str, object] = {
        "source_pixels_proven": False,
        "anatomy_proven": False,
        "speech_sync_proven": False,
        "active": False,
        "human_authority_approved": False,
        "reason": "source_unverified",
    }
    if (
        not isinstance(original_jpg, bytes)
        or not 0 < len(original_jpg) <= MAX_SOURCE_BYTES
        or not hmac.compare_digest(
            hashlib.sha256(original_jpg).hexdigest(), APPROVED_SOURCE_SHA256
        )
    ):
        return result
    try:
        with Image.open(BytesIO(original_jpg)) as raw:
            if raw.format != "JPEG" or raw.size[0] * raw.size[1] > MAX_PIXELS:
                result["reason"] = "source_format_or_size_invalid"
                return result
            raw.verify()
        with Image.open(BytesIO(original_jpg)) as raw:
            if raw.format != "JPEG" or getattr(raw, "n_frames", 1) != 1:
                result["reason"] = "source_format_or_frames_invalid"
                return result
            original_rgb = raw.convert("RGB").tobytes()
            width, height = raw.size
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        result["reason"] = "source_decode_failed"
        return result
    length = width * height * 4
    if (
        not isinstance(mask_rgba, bytes)
        or not isinstance(geometry_rgba, bytes)
        or len(mask_rgba) != length
        or len(geometry_rgba) != length
    ):
        result["reason"] = "full_canvas_geometry_required"
        return result
    selected = 0
    for pixel in range(width * height):
        i, s = pixel * 4, pixel * 3
        alpha = mask_rgba[i + 3]
        if alpha and mask_rgba[i:i + 3] != b"\xff\xff\xff":
            result["reason"] = "mask_not_white_alpha"
            return result
        if alpha >= 128:
            selected += 1
            if geometry_rgba[i:i + 3] != original_rgb[s:s + 3] or geometry_rgba[i + 3] != 255:
                result["reason"] = "visible_pixel_mismatch"
                return result
        elif geometry_rgba[i + 3] != 0:
            result["reason"] = "unmasked_pixel_present"
            return result
    if not selected:
        result["reason"] = "empty_mask"
        return result
    result["source_pixels_proven"] = True
    result["reason"] = "decoded_source_pixels_only_not_anatomy_proof"
    return result
