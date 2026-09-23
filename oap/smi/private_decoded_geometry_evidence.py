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
    original_jpg: bytes,
    mask_rgba: bytes,
    geometry_rgba: bytes,
    *,
    expected_mask_sha256: str | None = None,
    expected_geometry_sha256: str | None = None,
) -> dict[str, object]:
    """Return private evidence only; never inferred anatomy or active rig status."""
    result: dict[str, object] = {
        "source_pixels_proven": False,
        "receipt": None,
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
    # A decoded source match must refer to the exact mask and geometry
    # payloads named by the offline review manifest. Caller-supplied hashes
    # are integrity checks, not independent Human Authority approval.
    for payload, expected in (
        (mask_rgba, expected_mask_sha256),
        (geometry_rgba, expected_geometry_sha256),
    ):
        if (
            not isinstance(expected, str)
            or len(expected) != 64
            or any(ch not in "0123456789abcdef" for ch in expected)
            or not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), expected)
        ):
            result["reason"] = "mask_or_geometry_digest_mismatch"
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
    # Private cross-runtime identity receipt: SHA references only, no pixels,
    # approval token, paths, spoken text or permission to activate a rig.
    result["receipt"] = {
        "version": "source-pixel-lineage-v1",
        "source_sha256": APPROVED_SOURCE_SHA256,
        "mask_sha256": expected_mask_sha256,
        "geometry_sha256": expected_geometry_sha256,
        "width": width,
        "height": height,
        "anatomy_proven": False,
        "speech_sync_proven": False,
        "human_authority_approved": False,
    }
    result["source_pixels_proven"] = True
    result["reason"] = "decoded_source_pixels_only_not_anatomy_proof"
    return result
