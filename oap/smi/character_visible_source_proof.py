"""Offline, fail-closed visible-pixel lineage from the exact original JPEG.

A true result is *only* integrity of selected visible pixels. It cannot prove
reviewed mouth anatomy, hidden regions, audio alignment or live readiness.
"""
from __future__ import annotations

from .character_decoded_source_proof import matches_approved_decoded_rgba

MAX_PIXELS = 16_000_000


def matches_approved_visible_geometry(
    jpeg_bytes: object,
    source_rgba: object,
    mask_rgba: object,
    geometry_rgba: object,
    width: object,
    height: object,
) -> bool:
    """Bind decoded original -> binary source mask -> visible source pixels."""
    if (
        type(width) is not int
        or type(height) is not int
        or width <= 0
        or height <= 0
        or width * height > MAX_PIXELS
    ):
        return False
    expected = width * height * 4
    if (
        not isinstance(source_rgba, bytes)
        or not isinstance(mask_rgba, bytes)
        or not isinstance(geometry_rgba, bytes)
        or len(mask_rgba) != expected
        or len(geometry_rgba) != expected
        or not matches_approved_decoded_rgba(
            jpeg_bytes, source_rgba, width, height
        )
    ):
        return False
    selected = 0
    for offset in range(0, expected, 4):
        mask = mask_rgba[offset:offset + 4]
        pixel = geometry_rgba[offset:offset + 4]
        if mask[3] and mask[:3] != b"\\xff\\xff\\xff":
            return False
        if mask[3] >= 128:
            selected += 1
            if pixel[3] != 255 or pixel[:3] != source_rgba[offset:offset + 3]:
                return False
        elif pixel[3] != 0:
            return False
    return selected > 0
