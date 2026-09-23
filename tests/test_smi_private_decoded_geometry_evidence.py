"""Source-image lineage is not anatomical approval or live motion."""
from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image

from oap.smi import private_decoded_geometry_evidence as proof


def _fixture(monkeypatch):
    image = Image.new("RGB", (2, 2))
    image.putdata([(10, 20, 30), (40, 50, 60), (70, 80, 90), (100, 110, 120)])
    output = BytesIO()
    image.save(output, format="JPEG", quality=92)
    encoded = output.getvalue()
    monkeypatch.setattr(proof, "APPROVED_SOURCE_SHA256", hashlib.sha256(encoded).hexdigest())
    with Image.open(BytesIO(encoded)) as decoded:
        pixels = list(decoded.convert("RGB").getdata())
    mask = bytes([255, 255, 255, 255] + [0, 0, 0, 0] * 3)
    geometry = bytes([*pixels[0], 255] + [0, 0, 0, 0] * 3)
    return encoded, mask, geometry


def test_exact_decoded_jpeg_visible_pixels_are_only_lineage(monkeypatch):
    source, mask, geometry = _fixture(monkeypatch)
    report = proof.verify_decoded_visible_geometry(source, mask, geometry)
    assert report["source_pixels_proven"] is True
    assert report["reason"] == "decoded_source_pixels_only_not_anatomy_proof"
    assert all(report[key] is False for key in (
        "anatomy_proven", "speech_sync_proven", "active", "human_authority_approved"
    ))


def test_modified_jpeg_or_forged_source_pixels_fail_closed(monkeypatch):
    source, mask, geometry = _fixture(monkeypatch)
    assert proof.verify_decoded_visible_geometry(source + b"x", mask, geometry)[
        "reason"
    ] == "source_unverified"
    tampered = bytearray(geometry)
    tampered[0] ^= 1
    assert proof.verify_decoded_visible_geometry(source, mask, bytes(tampered))[
        "reason"
    ] == "visible_pixel_mismatch"
    assert proof.verify_decoded_visible_geometry(source, mask, geometry[:-4])[
        "reason"
    ] == "full_canvas_geometry_required"


def test_unreviewed_alpha_and_unmasked_pixels_fail_closed(monkeypatch):
    source, mask, geometry = _fixture(monkeypatch)
    coloured = bytearray(mask)
    coloured[0] = 1
    assert proof.verify_decoded_visible_geometry(source, bytes(coloured), geometry)[
        "reason"
    ] == "mask_not_white_alpha"
    extras = bytearray(geometry)
    extras[7] = 255
    assert proof.verify_decoded_visible_geometry(source, mask, bytes(extras))[
        "reason"
    ] == "unmasked_pixel_present"
    empty = bytes(len(mask))
    assert proof.verify_decoded_visible_geometry(source, empty, bytes(len(geometry)))[
        "reason"
    ] == "empty_mask"


def test_wrong_format_is_not_approved_original(monkeypatch):
    source, mask, geometry = _fixture(monkeypatch)
    png = BytesIO()
    Image.new("RGB", (2, 2)).save(png, format="PNG")
    monkeypatch.setattr(proof, "APPROVED_SOURCE_SHA256", hashlib.sha256(png.getvalue()).hexdigest())
    assert proof.verify_decoded_visible_geometry(png.getvalue(), mask, geometry)[
        "reason"
    ] == "source_format_or_size_invalid"
