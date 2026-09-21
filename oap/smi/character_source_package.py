"""Build an exact-SMI-character PRIVATE editable layer package from real masks.

No automatic segmentation, invented anatomy, hidden-region hallucination, rig
activation, telemetry or public asset publishing. All seven Founder-reviewed
full-canvas grayscale masks are required before any output is written.

The source is the existing repository image, pinned by SHA-256. Synthetic test
fixtures never confer approval on real SMI layers.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import stat
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .character_rig_assets import (
    APPROVED_SOURCE_SHA256,
    LAYERS,
    MAX_LAYER_DIMENSION,
)

MAX_SOURCE_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 16_000_000


class SourcePackageError(ValueError):
    """No output package was created. Message contains no private path."""


def _regular_bytes(path: Path, *, limit: int) -> bytes:
    """Refuse links, special files and oversized files; read one safe handle."""
    if path.is_symlink() or not path.is_file():
        raise SourcePackageError("missing_or_unsafe_private_file")
    before = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= limit:
        raise SourcePackageError("invalid_file_size")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_size != before.st_size:
            raise SourcePackageError("unsafe_file_changed")
        with os.fdopen(fd, "rb", closefd=False) as source:
            data = source.read(limit + 1)
        if len(data) != opened.st_size:
            raise SourcePackageError("unsafe_file_changed")
        return data
    finally:
        os.close(fd)


def _image(data: bytes, *, mode: str) -> Image.Image:
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in {"JPEG", "PNG"} or image.mode != mode:
                raise SourcePackageError("invalid_image_format")
            width, height = image.size
            if (
                not 1 <= width <= MAX_LAYER_DIMENSION
                or not 1 <= height <= MAX_LAYER_DIMENSION
                or width * height > MAX_PIXELS
                or getattr(image, "n_frames", 1) != 1
            ):
                raise SourcePackageError("invalid_image_size")
            image.load()
            return image.copy()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        if isinstance(error, SourcePackageError):
            raise
        raise SourcePackageError("image_decode_failed") from error


def _mask_bytes(root: Path, layer: str) -> bytes:
    path = root / (layer + ".png")
    return _regular_bytes(path, limit=MAX_SOURCE_BYTES)


def build_source_package(
    source_path: Path | str,
    approved_mask_root: Path | str,
    private_output: Path | str,
) -> dict[str, Any]:
    """Produce seven true source-derived RGBA layers or fail with no package.

    The private output directory must not exist. Its parent must be an existing
    PRIVATE directory, not static/public. Masks are actual approved L-mode PNGs
    matching the entire image size; a file name or claimed hash is insufficient.
    The output never invents occluded body parts or fills missing artwork.
    """
    source = Path(source_path)
    masks = Path(approved_mask_root)
    output = Path(private_output)
    if masks.is_symlink() or not masks.is_dir() or output.exists() or output.is_symlink():
        raise SourcePackageError("private_inputs_or_output_unavailable")
    parent = output.parent
    if parent.is_symlink() or not parent.is_dir():
        raise SourcePackageError("private_output_parent_unavailable")
    if "static" in output.parts or "static" in masks.parts:
        raise SourcePackageError("public_asset_path_denied")
    if output.name in {"", ".", ".."}:
        raise SourcePackageError("invalid_output_name")
    src = _regular_bytes(source, limit=MAX_SOURCE_BYTES)
    if not hmac.compare_digest(hashlib.sha256(src).hexdigest(), APPROVED_SOURCE_SHA256):
        raise SourcePackageError("exact_source_hash_mismatch")
    source_image = _image(src, mode="RGB")
    size = source_image.size

    # Read, decode, validate and crop EVERY layer before creating any outputs.
    prepared: dict[str, tuple[bytes, list[int], str]] = {}
    for layer in LAYERS:
        mask_bytes = _mask_bytes(masks, layer)
        mask = _image(mask_bytes, mode="L")
        if mask.size != size:
            raise SourcePackageError("mask_canvas_mismatch")
        bbox = mask.getbbox()
        if bbox is None:
            raise SourcePackageError("empty_layer_mask")
        crop_mask = mask.crop(bbox)
        # Do not invent pixels: RGB values come ONLY from the exact source.
        rgba = source_image.crop(bbox).convert("RGBA")
        rgba.putalpha(crop_mask)
        # Coverage is nonempty and bounded; overlaps are legitimate for facial
        # and body layers, and must be adjudicated in a separate visual review.
        alpha_bbox = rgba.getchannel("A").getbbox()
        if alpha_bbox is None:
            raise SourcePackageError("empty_layer_mask")
        with BytesIO() as out:
            rgba.save(out, format="PNG", optimize=True)
            contents = out.getvalue()
        prepared[layer] = (contents, list(bbox), hashlib.sha256(mask_bytes).hexdigest())

    # Stage privately; never publish incomplete sets. Do not overwrite work.
    staging: Path | None = None
    try:
        staging = Path(tempfile.mkdtemp(prefix=".smi-character-", dir=parent))
        staging.chmod(0o700)
        records: dict[str, dict[str, Any]] = {}
        for layer, (contents, bbox, mask_digest) in prepared.items():
            filename = layer + ".png"
            fd = os.open(staging / filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as target:
                target.write(contents)
            records[layer] = {
                "file": filename,
                "sha256": hashlib.sha256(contents).hexdigest(),
                "bbox_xyxy": bbox,
                "source_mask_sha256": mask_digest,
                "asset_status": "source_derived_not_rig_approved",
            }
        manifest = {
            "version": "0.1",
            "approved_source_sha256": APPROVED_SOURCE_SHA256,
            "canvas_width": size[0],
            "canvas_height": size[1],
            "layers": records,
            "active": False,
            "geometry_proven": False,
            "motion_proven": False,
            "human_authority_approved": False,
            "hidden_region_reconstruction": False,
        }
        encoded = json.dumps(manifest, indent=2).encode("utf-8") + b"\n"
        fd = os.open(staging / "manifest.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as target:
            target.write(encoded)
        staging.rename(output)
        staging = None
        return {
            "created": True,
            "layers": len(records),
            "source_sha256": APPROVED_SOURCE_SHA256,
            "active": False,
            "motion_proven": False,
            "human_authority_approved": False,
            "reason": "source_derived_layers_require_visual_identity_approval",
        }
    finally:
        if staging is not None and staging.exists():
            for child in staging.iterdir():
                child.unlink()
            staging.rmdir()
