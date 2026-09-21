"""Mask registration rejects wrong labels while remaining fail-closed."""
from __future__ import annotations

import hashlib
from copy import deepcopy

from PIL import Image

from oap.smi import (
    character_rig_assets,
    character_rig_geometry,
    character_rig_lineage,
    character_rig_registration,
)


def _evidence(tmp_path, monkeypatch):
    size = (100, 100)
    source = tmp_path / "approved.png"
    Image.new("RGB", size, (10, 20, 30)).save(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(character_rig_assets, "APPROVED_SOURCE_SHA256", digest)
    monkeypatch.setattr(character_rig_geometry, "APPROVED_SOURCE_SHA256", digest)
    monkeypatch.setattr(character_rig_lineage, "APPROVED_SOURCE_SHA256", digest)

    records = {}
    geometry_layers = {}
    source_pixel = (10, 20, 30, 255)
    for layer_index, name in enumerate(character_rig_assets.LAYERS):
        anchors = character_rig_geometry.ANCHORS[name]
        landmarks = {}
        layer = Image.new("RGBA", size, (0, 0, 0, 0))
        for anchor_index, anchor in enumerate(anchors):
            x = 5 + layer_index * 12 + anchor_index
            y = 5 + anchor_index
            landmarks[anchor] = [x / (size[0] - 1), y / (size[1] - 1)]
            layer.putpixel((x, y), source_pixel)
        path = tmp_path / f"{name}.png"
        layer.save(path)
        records[name] = {
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        frames = []
        for timecode in (0, 120):
            frame = {
                "t_ms": timecode,
                "delta": {anchor: [0.0, 0.0] for anchor in anchors},
            }
            if name == "mouth_visemes":
                frame.update(viseme="silence", audio_ms=timecode)
            frames.append(frame)
        geometry_layers[name] = {"landmarks": landmarks, "frames": frames}
    manifest = {
        "version": "0.1",
        "approved_source_sha256": digest,
        "layers": records,
    }
    geometry = {
        "version": "0.1",
        "approved_source_sha256": digest,
        "layers": geometry_layers,
    }
    return source, manifest, geometry


def _rehash(manifest, root, name):
    path = root / manifest["layers"][name]["file"]
    manifest["layers"][name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()


def test_registered_masks_prove_only_registration(tmp_path, monkeypatch):
    source, manifest, geometry = _evidence(tmp_path, monkeypatch)
    result = character_rig_registration.inspect_registration(
        manifest, tmp_path, source, geometry
    )
    assert result["mask_registration_proven"] is True, (
        result["reason"], result["layers"]
    )
    assert result["reason"] == "registered_masks_require_human_anatomy_review"
    assert set(result["layers"].values()) == {"anchors_registered_not_anatomy_proof"}
    assert all(
        result[key] is False
        for key in (
            "active", "emits_frames", "anatomy_proven", "identity_proven",
            "motion_proven", "speech_sync_proven", "human_authority_approved",
        )
    )


def test_anchor_outside_named_mask_fails_closed(tmp_path, monkeypatch):
    source, manifest, geometry = _evidence(tmp_path, monkeypatch)
    geometry = deepcopy(geometry)
    geometry["layers"]["eyes"]["landmarks"]["left_eye_center"] = [0.99, 0.99]
    result = character_rig_registration.inspect_registration(
        manifest, tmp_path, source, geometry
    )
    assert result["layers"]["eyes"] == "required_anchor_outside_named_mask"
    assert result["mask_registration_proven"] is False
    assert result["active"] is False


def test_excessive_mask_and_wrong_pixel_lineage_are_rejected(tmp_path, monkeypatch):
    source, manifest, geometry = _evidence(tmp_path, monkeypatch)
    eyes = tmp_path / "eyes.png"
    Image.new("RGBA", (100, 100), (10, 20, 30, 255)).save(eyes)
    _rehash(manifest, tmp_path, "eyes")
    result = character_rig_registration.inspect_registration(
        manifest, tmp_path, source, geometry
    )
    assert result["reason"] == "exact_pixel_lineage_unproven"

    source, manifest, geometry = _evidence(tmp_path, monkeypatch)
    image = Image.open(eyes).convert("RGBA")
    for y in range(20):
        for x in range(20):
            image.putpixel((x, y), (10, 20, 30, 255))
    image.save(eyes)
    _rehash(manifest, tmp_path, "eyes")
    result = character_rig_registration.inspect_registration(
        manifest, tmp_path, source, geometry
    )
    assert result["layers"]["eyes"] == "mask_coverage_too_large"


def test_forged_geometry_flags_and_private_paths_do_not_escape(tmp_path, monkeypatch):
    source, manifest, geometry = _evidence(tmp_path, monkeypatch)
    geometry.update(enable_rig=True, anatomy_proven=True, founder_approved=True)
    result = character_rig_registration.inspect_registration(
        manifest, tmp_path, source, geometry
    )
    assert result["active"] is False
    assert result["anatomy_proven"] is False
    assert result["human_authority_approved"] is False
    assert str(tmp_path) not in str(result)
