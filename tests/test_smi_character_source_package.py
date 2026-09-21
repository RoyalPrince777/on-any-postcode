"""Real source-pixel extraction contracts, with SYNTHETIC fixtures only.

These fixtures do not assert that SMI's real seven segmentation masks exist.
"""
from __future__ import annotations

import hashlib
import json

import pytest
from PIL import Image

from oap.smi import character_source_package as source_pkg
from oap.smi.character_rig_assets import LAYERS, inspect_assets


def _inputs(tmp_path, monkeypatch):
    source = tmp_path / "original.jpg"
    img = Image.new("RGB", (48, 40), (23, 76, 141))
    img.putpixel((12, 9), (220, 45, 31))
    img.save(source, format="JPEG", quality=96)
    monkeypatch.setattr(
        source_pkg, "APPROVED_SOURCE_SHA256",
        hashlib.sha256(source.read_bytes()).hexdigest(),
    )
    masks = tmp_path / "private-masks"
    masks.mkdir()
    for i, layer in enumerate(LAYERS):
        mask = Image.new("L", (48, 40))
        for x in range(3 + i, 19 + i):
            for y in range(6 + i, 20 + i):
                mask.putpixel((x, y), 255)
        mask.save(masks / (layer + ".png"))
    outparent = tmp_path / "private-packages"
    outparent.mkdir(mode=0o700)
    return source, masks, outparent / "exact-character"


def test_source_pixel_extraction_and_read_only_asset_gate(tmp_path, monkeypatch):
    source, masks, target = _inputs(tmp_path, monkeypatch)
    result = source_pkg.build_source_package(source, masks, target)
    assert result["created"] is True
    assert result["layers"] == 7
    assert result["active"] is False
    assert result["motion_proven"] is False
    assert result["human_authority_approved"] is False
    manifest = json.loads((target / "manifest.json").read_text())
    assert manifest["active"] is False
    assert manifest["hidden_region_reconstruction"] is False
    assert list(manifest["layers"]) == list(LAYERS)
    assert target.stat().st_mode & 0o777 == 0o700
    with Image.open(source) as original, Image.open(target / "eyes.png") as eyes:
        eyes.load()
        assert eyes.mode == "RGBA"
        assert eyes.size == (16, 14)
        assert eyes.getpixel((0, 0))[:3] == original.getpixel((3, 6))
        assert eyes.getpixel((0, 0))[3] == 255
    assert all(
        (target / (name + ".png")).stat().st_mode & 0o777 == 0o600
        for name in LAYERS
    )
    # The old byte verifier still cannot turn these layers into a true rig.
    report = inspect_assets(manifest, target)
    assert report["reason"] == "source_identity_unproven"


def test_missing_or_wrong_mask_fails_with_no_output(tmp_path, monkeypatch):
    source, masks, target = _inputs(tmp_path, monkeypatch)
    (masks / "hands.png").unlink()
    with pytest.raises(source_pkg.SourcePackageError):
        source_pkg.build_source_package(source, masks, target)
    assert not target.exists()

    Image.new("L", (47, 40), 255).save(masks / "hands.png")
    with pytest.raises(
        source_pkg.SourcePackageError, match="mask_canvas_mismatch"
    ):
        source_pkg.build_source_package(source, masks, target)
    assert not target.exists()


def test_original_hash_not_swappable_in_production(tmp_path, monkeypatch):
    source, masks, target = _inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(source_pkg, "APPROVED_SOURCE_SHA256", "0" * 64)
    with pytest.raises(
        source_pkg.SourcePackageError, match="exact_source_hash_mismatch"
    ):
        source_pkg.build_source_package(source, masks, target)
    assert not target.exists()


def test_no_public_output_overwrite_or_mask_symlink(tmp_path, monkeypatch):
    source, masks, target = _inputs(tmp_path, monkeypatch)
    (masks / "eyes.png").unlink()
    (masks / "eyes.png").symlink_to(masks / "head.png")
    with pytest.raises(source_pkg.SourcePackageError):
        source_pkg.build_source_package(source, masks, target)
    assert not target.exists()
    (masks / "eyes.png").unlink()
    Image.new("L", (48, 40), 255).save(masks / "eyes.png")

    public_output = tmp_path / "static" / "package"
    public_output.parent.mkdir()
    with pytest.raises(
        source_pkg.SourcePackageError, match="public_asset_path_denied"
    ):
        source_pkg.build_source_package(source, masks, public_output)
    assert not public_output.exists()
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("existing-work")
    with pytest.raises(source_pkg.SourcePackageError):
        source_pkg.build_source_package(source, masks, target)
    assert sentinel.read_text() == "existing-work"


def test_different_grayscale_and_empty_masks_rejected(tmp_path, monkeypatch):
    source, masks, target = _inputs(tmp_path, monkeypatch)
    Image.new("RGB", (48, 40), (0, 0, 0)).save(masks / "eyes.png")
    with pytest.raises(
        source_pkg.SourcePackageError, match="invalid_image_format"
    ):
        source_pkg.build_source_package(source, masks, target)
    Image.new("L", (48, 40), 0).save(masks / "eyes.png")
    with pytest.raises(
        source_pkg.SourcePackageError, match="empty_layer_mask"
    ):
        source_pkg.build_source_package(source, masks, target)
    assert not target.exists()


def test_private_still_compositor_reuses_exact_source_pixels(tmp_path, monkeypatch):
    from oap.smi import character_layer_review, character_rig_assets

    source, masks, target = _inputs(tmp_path, monkeypatch)
    source_pkg.build_source_package(source, masks, target)
    approved = source_pkg.APPROVED_SOURCE_SHA256
    monkeypatch.setattr(character_rig_assets, "APPROVED_SOURCE_SHA256", approved)
    monkeypatch.setattr(character_layer_review, "APPROVED_SOURCE_SHA256", approved)
    review = tmp_path / "private-packages" / "review.png"
    result = character_layer_review.render_still_layer_review(
        source, target, review, layer_order=tuple(LAYERS)
    )
    assert result["created"] is True
    assert result["emits_motion"] is False
    assert result["identity_approved"] is False
    assert result["human_authority_approved"] is False
    assert review.stat().st_mode & 0o777 == 0o600
    with Image.open(review) as picture, Image.open(source) as original:
        assert picture.size == original.size
        assert picture.getpixel((3, 6))[:3] == original.getpixel((3, 6))
    with pytest.raises(source_pkg.SourcePackageError):
        character_layer_review.render_still_layer_review(
            source, target, review, layer_order=tuple(LAYERS)
        )


def test_private_still_compositor_blocks_forged_pixels_and_bbox(
    tmp_path, monkeypatch
):
    from oap.smi import character_layer_review, character_rig_assets

    source, masks, target = _inputs(tmp_path, monkeypatch)
    source_pkg.build_source_package(source, masks, target)
    approved = source_pkg.APPROVED_SOURCE_SHA256
    monkeypatch.setattr(character_rig_assets, "APPROVED_SOURCE_SHA256", approved)
    monkeypatch.setattr(character_layer_review, "APPROVED_SOURCE_SHA256", approved)
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    layer_path = target / "eyes.png"
    with Image.open(layer_path) as layer:
        copy = layer.copy()
    copy.putpixel((0, 0), (255, 255, 0, 255))
    copy.save(layer_path)
    manifest["layers"]["eyes"]["sha256"] = hashlib.sha256(
        layer_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(
        source_pkg.SourcePackageError, match="layer_pixel_identity_mismatch"
    ):
        character_layer_review.render_still_layer_review(
            source, target, tmp_path / "private-packages" / "review.png",
            layer_order=tuple(LAYERS),
        )
    assert not (tmp_path / "private-packages" / "review.png").exists()

    manifest["layers"]["eyes"]["bbox_xyxy"] = [0, 0, 100, 100]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(
        source_pkg.SourcePackageError, match="invalid_layer_registration"
    ):
        character_layer_review.render_still_layer_review(
            source, target, tmp_path / "private-packages" / "review.png",
            layer_order=tuple(LAYERS),
        )


def test_compositor_requires_explicit_complete_order(tmp_path, monkeypatch):
    from oap.smi import character_layer_review, character_rig_assets

    source, masks, target = _inputs(tmp_path, monkeypatch)
    source_pkg.build_source_package(source, masks, target)
    approved = source_pkg.APPROVED_SOURCE_SHA256
    monkeypatch.setattr(character_rig_assets, "APPROVED_SOURCE_SHA256", approved)
    monkeypatch.setattr(character_layer_review, "APPROVED_SOURCE_SHA256", approved)
    with pytest.raises(
        source_pkg.SourcePackageError,
        match="explicit_complete_layer_order_required",
    ):
        character_layer_review.render_still_layer_review(
            source, target, tmp_path / "private-packages" / "review.png",
            layer_order=("eyes",),
        )
