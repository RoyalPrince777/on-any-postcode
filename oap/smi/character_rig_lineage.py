"""Offline proof that private rig layers contain only approved source pixels.

This module validates pixel lineage, not anatomy, identity quality, motion,
speech synchronisation, or Human Authority approval. It never renders or
publishes the private layers and it cannot activate the client rig.
"""
from __future__ import annotations

import hashlib
import hmac
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .character_rig_assets import (
    APPROVED_SOURCE_SHA256,
    LAYERS,
    inspect_assets,
)


def _closed(reason: str, layers: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "version": "0.1",
        "active": False,
        "emits_frames": False,
        "pixel_lineage_proven": False,
        "anatomy_proven": False,
        "identity_proven": False,
        "motion_proven": False,
        "speech_sync_proven": False,
        "human_authority_approved": False,
        "private": True,
        "layers": layers or {name: "not_inspected" for name in LAYERS},
        "reason": reason,
    }


def inspect_lineage(
    manifest: object,
    private_root: Path | str,
    approved_source: Path | str,
) -> dict[str, Any]:
    """Verify exact-pixel ancestry while keeping every activation claim false."""
    asset_report = inspect_assets(manifest, private_root)
    if asset_report.get("reason") != "bytes_verified_only_requires_independent_rig_proofs":
        return _closed("private_asset_bytes_unproven")

    source_path = Path(approved_source)
    if source_path.is_symlink() or not source_path.is_file():
        return _closed("approved_source_unavailable")
    source_bytes = source_path.read_bytes()
    if not hmac.compare_digest(
        hashlib.sha256(source_bytes).hexdigest(), APPROVED_SOURCE_SHA256
    ):
        return _closed("approved_source_digest_mismatch")

    try:
        with Image.open(source_path) as raw_source:
            raw_source.verify()
        with Image.open(source_path) as raw_source:
            source = raw_source.convert("RGB")
            source_size = source.size
            source_pixels = source.load()

            records = manifest["layers"]  # guarded by inspect_assets
            root = Path(private_root)
            results: dict[str, str] = {}
            for name in LAYERS:
                with Image.open(root / records[name]["file"]) as raw_layer:
                    layer = raw_layer.convert("RGBA")
                    if layer.size != source_size:
                        results[name] = "source_dimensions_mismatch"
                        continue
                    pixels = layer.load()
                    visible = 0
                    transparent = 0
                    verdict = "exact_source_pixels_not_anatomy_proof"
                    for y in range(source_size[1]):
                        for x in range(source_size[0]):
                            red, green, blue, alpha = pixels[x, y]
                            if alpha == 0:
                                transparent += 1
                            elif alpha == 255:
                                visible += 1
                                if (red, green, blue) != source_pixels[x, y]:
                                    verdict = "altered_visible_pixel"
                                    break
                            else:
                                verdict = "non_binary_alpha"
                                break
                        if verdict != "exact_source_pixels_not_anatomy_proof":
                            break
                    if verdict == "exact_source_pixels_not_anatomy_proof" and (
                        visible == 0 or transparent == 0
                    ):
                        verdict = "empty_or_unmasked_layer"
                    results[name] = verdict
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        return _closed("lineage_image_decode_failed")

    if not all(
        value == "exact_source_pixels_not_anatomy_proof"
        for value in results.values()
    ):
        return _closed("pixel_lineage_incomplete", results)

    outcome = _closed("exact_pixels_require_anatomy_motion_audio_and_human_proof", results)
    outcome["pixel_lineage_proven"] = True
    return outcome
