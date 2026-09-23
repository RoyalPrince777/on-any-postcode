"""Synthetic fixtures only; no approved SMI anatomy or live motion."""
from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image

from oap.smi import character_decoded_source_proof as decoded
from oap.smi.character_visible_source_proof import matches_approved_visible_geometry


def test_decoded_source_mask_and_visible_pixels_must_agree(monkeypatch):
    original = Image.new("RGB", (2, 2))
    original.putdata([(20, 40, 60), (30, 50, 70), (40, 60, 80), (50, 70, 90)])
    jpg = BytesIO()
    original.save(jpg, format="JPEG")
    raw = jpg.getvalue()
    pixels = Image.open(BytesIO(raw)).convert("RGBA").tobytes()
    monkeypatch.setattr(decoded, "APPROVED_SOURCE_SHA256", hashlib.sha256(raw).hexdigest())
    mask = bytes([255, 255, 255, 255]) + bytes(12)
    geometry = pixels[:4] + bytes(12)
    args = (raw, pixels, mask, geometry, 2, 2)
    assert matches_approved_visible_geometry(*args)
    assert not matches_approved_visible_geometry(raw + b"changed", *args[1:])
    assert not matches_approved_visible_geometry(raw, pixels[:-1] + bytes([0]), mask, geometry, 2, 2)
    assert not matches_approved_visible_geometry(raw, pixels, bytes(16), geometry, 2, 2)
    assert not matches_approved_visible_geometry(
        raw, pixels, mask, bytes([255, 0, 0, 255]) + bytes(12), 2, 2
    )
    assert not matches_approved_visible_geometry(
        raw, pixels, mask, pixels[:4] + bytes(8) + bytes([5, 6, 7, 255]), 2, 2
    )
    assert not matches_approved_visible_geometry(
        raw, pixels, bytes([1, 255, 255, 255]) + bytes(12), geometry, 2, 2
    )
    assert not matches_approved_visible_geometry(raw, pixels, mask, geometry, 1, 4)
    assert not matches_approved_visible_geometry(raw, pixels, mask, geometry, True, 2)


def test_unapproved_original_and_missing_inputs_fail_closed():
    assert not matches_approved_visible_geometry(None, None, None, None, 1, 1)
    assert not matches_approved_visible_geometry(b"fake", bytes(4), bytes(4), bytes(4), 1, 1)
