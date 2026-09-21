"""Exact-pixel lineage is useful evidence, never a live-character claim."""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image

from oap.smi import character_rig_assets, character_rig_lineage


def _fixture(tmp_path: Path, monkeypatch):
    source = tmp_path / "approved.png"
    source_image = Image.new("RGB", (4, 4))
    source_image.putdata([(x * 30, y * 40, 90) for y in range(4) for x in range(4)])
    source_image.save(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(character_rig_assets, "APPROVED_SOURCE_SHA256", digest)
    monkeypatch.setattr(character_rig_lineage, "APPROVED_SOURCE_SHA256", digest)

    layers = {}
    source_rgba = source_image.convert("RGBA")
    for index, name in enumerate(character_rig_assets.LAYERS):
        layer = Image.new("RGBA", source_image.size, (0, 0, 0, 0))
        x = index % 4
        y = index // 4
        layer.putpixel((x, y), source_rgba.getpixel((x, y)))
        path = tmp_path / f"{name}.png"
        layer.save(path)
        layers[name] = {
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    manifest = {
        "version": "0.1",
        "approved_source_sha256": digest,
        "layers": layers,
        "enable_rig": True,
        "motion_proven": True,
        "founder_approved": True,
    }
    return source, manifest


def _rehash(manifest, root: Path, name: str):
    path = root / manifest["layers"][name]["file"]
    manifest["layers"][name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_pixels_prove_only_lineage(tmp_path, monkeypatch):
    source, manifest = _fixture(tmp_path, monkeypatch)
    result = character_rig_lineage.inspect_lineage(manifest, tmp_path, source)
    assert result["pixel_lineage_proven"] is True
    assert result["reason"] == "exact_pixels_require_anatomy_motion_audio_and_human_proof"
    assert set(result["layers"].values()) == {"exact_source_pixels_not_anatomy_proof"}
    assert all(
        result[key] is False
        for key in (
            "active", "emits_frames", "anatomy_proven", "identity_proven",
            "motion_proven", "speech_sync_proven", "human_authority_approved",
        )
    )


def test_altered_pixel_resized_empty_and_soft_alpha_fail_closed(tmp_path, monkeypatch):
    source, manifest = _fixture(tmp_path, monkeypatch)
    eyes = tmp_path / "eyes.png"

    image = Image.open(eyes).convert("RGBA")
    image.putpixel((0, 0), (255, 0, 0, 255))
    image.save(eyes)
    _rehash(manifest, tmp_path, "eyes")
    assert character_rig_lineage.inspect_lineage(manifest, tmp_path, source)["layers"]["eyes"] == "altered_visible_pixel"

    source, manifest = _fixture(tmp_path, monkeypatch)
    image = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    image.save(eyes)
    _rehash(manifest, tmp_path, "eyes")
    assert character_rig_lineage.inspect_lineage(manifest, tmp_path, source)["layers"]["eyes"] == "source_dimensions_mismatch"

    source, manifest = _fixture(tmp_path, monkeypatch)
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(eyes)
    _rehash(manifest, tmp_path, "eyes")
    assert character_rig_lineage.inspect_lineage(manifest, tmp_path, source)["layers"]["eyes"] == "empty_or_unmasked_layer"

    source, manifest = _fixture(tmp_path, monkeypatch)
    image = Image.open(eyes).convert("RGBA")
    image.putpixel((0, 0), (*image.getpixel((0, 0))[:3], 128))
    image.save(eyes)
    _rehash(manifest, tmp_path, "eyes")
    assert character_rig_lineage.inspect_lineage(manifest, tmp_path, source)["layers"]["eyes"] == "non_binary_alpha"


def test_wrong_source_digest_and_forged_asset_report_cannot_pass(tmp_path, monkeypatch):
    source, manifest = _fixture(tmp_path, monkeypatch)
    source.write_bytes(source.read_bytes() + b"changed")
    result = character_rig_lineage.inspect_lineage(manifest, tmp_path, source)
    assert result["reason"] == "approved_source_digest_mismatch"
    assert result["pixel_lineage_proven"] is False

    source, manifest = _fixture(tmp_path, monkeypatch)
    manifest["layers"]["hands"]["sha256"] = "0" * 64
    result = character_rig_lineage.inspect_lineage(manifest, tmp_path, source)
    assert result["reason"] == "private_asset_bytes_unproven"
    assert result["active"] is False


def test_private_paths_are_never_returned(tmp_path, monkeypatch):
    source, manifest = _fixture(tmp_path, monkeypatch)
    result = character_rig_lineage.inspect_lineage(manifest, tmp_path, source)
    assert str(tmp_path) not in str(result)
