"""Proof of private rig asset byte checks; never proof of live animation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image

from oap.smi.character_rig_assets import (
    APPROVED_SOURCE_SHA256,
    LAYERS,
    inspect_assets,
)


def _asset(root: Path, name: str, mode: str = "RGBA") -> dict[str, str]:
    path = root / (name + ".png")
    Image.new(mode, (16, 16), (60, 140, 220, 120) if mode == "RGBA" else (60, 140, 220)).save(path)
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _manifest(root: Path) -> dict[str, object]:
    return {
        "version": "0.1",
        "approved_source_sha256": APPROVED_SOURCE_SHA256,
        "layers": {name: _asset(root, name) for name in LAYERS},
        "founder_approved": True,
        "rig_enabled": True,
        "motion_proven": True,
    }


def test_missing_asset_or_manifest_is_fail_closed(tmp_path):
    assert inspect_assets(None, tmp_path)["active"] is False
    assert inspect_assets(None, tmp_path)["reason"] == "missing_or_invalid_manifest"
    result = inspect_assets(_manifest(tmp_path), tmp_path / "not-present")
    assert result["reason"] == "private_asset_root_unavailable"
    assert result["motion_proven"] is False


def test_all_seven_valid_bytes_still_cannot_certify_motion(tmp_path):
    result = inspect_assets(_manifest(tmp_path), tmp_path)
    assert result["reason"] == "bytes_verified_only_requires_independent_rig_proofs"
    assert list(result["layers"]) == list(LAYERS)
    assert set(result["layers"].values()) == {"bytes_valid_not_rig_proof"}
    assert result["active"] is False
    assert result["frames"] is False
    assert result["motion_proven"] is False
    assert result["human_authority_approved"] is False


def test_wrong_source_missing_layer_and_claimed_flags_are_not_proof(tmp_path):
    manifest = _manifest(tmp_path)
    manifest["approved_source_sha256"] = "0" * 64
    assert inspect_assets(manifest, tmp_path)["reason"] == "source_identity_unproven"
    manifest["approved_source_sha256"] = APPROVED_SOURCE_SHA256
    manifest["layers"].pop("hands")
    assert inspect_assets(manifest, tmp_path)["reason"] == "seven_layer_contract_incomplete"


def test_filename_digest_symlink_nonalpha_and_truncated_png_rejected(tmp_path):
    manifest = _manifest(tmp_path)
    records = manifest["layers"]

    records["eyes"]["file"] = "../eyes.png"
    assert inspect_assets(manifest, tmp_path)["layers"]["eyes"] == "invalid_private_filename"
    records["eyes"] = _asset(tmp_path, "eyes")

    path = tmp_path / "eyes.png"
    path.write_bytes(path.read_bytes() + b"modified")
    assert inspect_assets(manifest, tmp_path)["layers"]["eyes"] == "digest_mismatch"
    records["eyes"] = _asset(tmp_path, "eyes")

    path.unlink()
    path.symlink_to(tmp_path / "head.png")
    assert inspect_assets(manifest, tmp_path)["layers"]["eyes"] == "missing_private_asset"
    path.unlink()
    records["eyes"] = _asset(tmp_path, "eyes", mode="RGB")
    assert inspect_assets(manifest, tmp_path)["layers"]["eyes"] == "invalid_alpha_png"

    records["eyes"] = _asset(tmp_path, "eyes")
    path.write_bytes(path.read_bytes()[:-10])
    records["eyes"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert inspect_assets(manifest, tmp_path)["layers"]["eyes"] == "invalid_png"


def test_no_runtime_activation_or_private_asset_path_disclosure(tmp_path):
    report = inspect_assets(_manifest(tmp_path), tmp_path)
    assert str(tmp_path) not in str(report)
    assert all("private" not in str(value) or value is True for value in report["layers"].values())
    assert report["active"] is False
