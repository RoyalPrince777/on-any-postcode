"""Offline registration checks for exact-pixel SMI layer masks.

Registration proves that required landmarks fall inside their named masks. It
does not prove that the masks follow real anatomy or that motion is authentic.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .character_rig_assets import LAYERS, inspect_assets
from .character_rig_geometry import ANCHORS, inspect_geometry
from .character_rig_lineage import inspect_lineage

MAX_COVERAGE = {
    "eyes": 0.03,
    "head": 0.45,
    "breathing": 0.30,
    "mouth_visemes": 0.03,
    "face": 0.15,
    "hands": 0.15,
    "upper_body": 0.55,
}


def _result(reason: str, layers: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "version": "0.1",
        "active": False,
        "emits_frames": False,
        "mask_registration_proven": False,
        "anatomy_proven": False,
        "identity_proven": False,
        "motion_proven": False,
        "speech_sync_proven": False,
        "human_authority_approved": False,
        "private": True,
        "layers": layers or {name: "not_inspected" for name in LAYERS},
        "reason": reason,
    }


def inspect_registration(
    manifest: object,
    private_root: Path | str,
    approved_source: Path | str,
    geometry_bundle: object,
) -> dict[str, Any]:
    """Check bounded mask-to-landmark registration; never enable the rig."""
    lineage = inspect_lineage(manifest, private_root, approved_source)
    if not lineage.get("pixel_lineage_proven"):
        return _result("exact_pixel_lineage_unproven")

    assets = inspect_assets(manifest, private_root)
    geometry = inspect_geometry(geometry_bundle, assets)
    if geometry.get("reason") != "schema_only_requires_independent_visual_motion_and_audio_proof":
        return _result("geometry_schema_unproven")

    root = Path(private_root)
    records = manifest["layers"]
    geometry_layers = geometry_bundle["layers"]
    verdicts: dict[str, str] = {}
    try:
        for name in LAYERS:
            with Image.open(root / records[name]["file"]) as raw:
                alpha = raw.convert("RGBA").getchannel("A")
                width, height = alpha.size
                visible = alpha.histogram()[255]
                if visible / (width * height) > MAX_COVERAGE[name]:
                    verdicts[name] = "mask_coverage_too_large"
                    continue
                landmarks = geometry_layers[name]["landmarks"]
                missing = False
                for anchor in ANCHORS[name]:
                    normalized_x, normalized_y = landmarks[anchor]
                    x = min(width - 1, max(0, round(normalized_x * (width - 1))))
                    y = min(height - 1, max(0, round(normalized_y * (height - 1))))
                    if alpha.getpixel((x, y)) != 255:
                        missing = True
                        break
                verdicts[name] = (
                    "required_anchor_outside_named_mask"
                    if missing
                    else "anchors_registered_not_anatomy_proof"
                )
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        return _result("registration_image_decode_failed")

    if not all(
        value == "anchors_registered_not_anatomy_proof"
        for value in verdicts.values()
    ):
        return _result("mask_registration_incomplete", verdicts)

    outcome = _result("registered_masks_require_human_anatomy_review", verdicts)
    outcome["mask_registration_proven"] = True
    return outcome
