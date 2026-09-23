"""Isolated byte-lineage fixtures; none is the approved SMI image or mouth."""
from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image

from oap.smi import character_decoded_source_proof as proof


def test_exact_hashed_jpeg_decodes_to_supplied_rgba(monkeypatch):
    image = Image.new("RGB", (3, 2), (70, 90, 110))
    encoded = BytesIO()
    image.save(encoded, format="JPEG")
    data = encoded.getvalue()
    rgba = Image.open(BytesIO(data)).convert("RGBA").tobytes()
    monkeypatch.setattr(proof, "APPROVED_SOURCE_SHA256", hashlib.sha256(data).hexdigest())
    assert proof.matches_approved_decoded_rgba(data, rgba, 3, 2)
    assert not proof.matches_approved_decoded_rgba(data, rgba[:-1] + bytes([0]), 3, 2)
    assert not proof.matches_approved_decoded_rgba(data, rgba, 2, 3)
    assert not proof.matches_approved_decoded_rgba(data + b"tampered", rgba, 3, 2)
    assert not proof.matches_approved_decoded_rgba(data, rgba, True, 2)
    assert not proof.matches_approved_decoded_rgba(data, rgba, 3, 0)
    assert not proof.matches_approved_decoded_rgba(data, rgba, 8193, 2)


def test_wrong_source_and_non_jpeg_fail_closed(monkeypatch):
    image = Image.new("RGB", (2, 2), (5, 7, 9))
    png = BytesIO()
    image.save(png, format="PNG")
    png_bytes = png.getvalue()
    rgba = image.convert("RGBA").tobytes()
    monkeypatch.setattr(
        proof, "APPROVED_SOURCE_SHA256", hashlib.sha256(png_bytes).hexdigest()
    )
    assert not proof.matches_approved_decoded_rgba(png_bytes, rgba, 2, 2)
    assert not proof.matches_approved_decoded_rgba(None, rgba, 2, 2)
    assert not proof.matches_approved_decoded_rgba(png_bytes, None, 2, 2)
    assert not proof.matches_approved_decoded_rgba(b"not an image", rgba, 2, 2)


def test_pinned_source_is_not_satisfied_by_fixture():
    image = Image.new("RGB", (1, 1), (1, 2, 3))
    encoded = BytesIO()
    image.save(encoded, format="JPEG")
    assert not proof.matches_approved_decoded_rgba(
        encoded.getvalue(), image.convert("RGBA").tobytes(), 1, 1
    )
