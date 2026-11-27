"""Private still-layer compositor for identity review; NOT a motion renderer.

This refuses a package unless all seven actual source-derived layers pass
their file/byte checks and each visible RGB pixel matches the exact original.
It does not infer missing anatomy, replay motion or publish a public image.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

from .character_rig_assets import APPROVED_SOURCE_SHA256, LAYERS, inspect_assets
from .character_source_package import (
    MAX_SOURCE_BYTES,
    SourcePackageError,
    _image,
    _regular_bytes,
)


def render_still_layer_review(
    source_path: Path | str,
    package_root: Path | str,
    output_path: Path | str,
    *,
    layer_order: tuple[str, ...],
) -> dict[str, Any]:
    """Compose a private still for review from existing source-derived pixels.

    Explicit layer order is required because image files cannot prove
    occlusion/depth. No overwrite, animation, frame loop or identity claim.
    """
    root, output = Path(package_root), Path(output_path)
    if (
        root.is_symlink()
        or not root.is_dir()
        or output.is_symlink()
        or output.exists()
        or output.parent.is_symlink()
        or not output.parent.is_dir()
        or "static" in output.parts
        or not output.name.endswith(".png")
    ):
        raise SourcePackageError("unsafe_private_review_destination")
    if (
        not isinstance(layer_order, tuple)
        or len(layer_order) != len(LAYERS)
        or set(layer_order) != set(LAYERS)
    ):
        raise SourcePackageError("explicit_complete_layer_order_required")
    original_bytes = _regular_bytes(Path(source_path), limit=MAX_SOURCE_BYTES)
    if not hmac.compare_digest(
        hashlib.sha256(original_bytes).hexdigest(), APPROVED_SOURCE_SHA256
    ):
        raise SourcePackageError("exact_source_hash_mismatch")
    original = _image(original_bytes, mode="RGB")
    try:
        manifest = json.loads(
            _regular_bytes(root / "manifest.json", limit=200_000)
        )
    except (UnicodeError, ValueError, TypeError) as error:
        raise SourcePackageError("invalid_private_manifest") from error
    if (
        not isinstance(manifest, dict)
        or manifest.get("canvas_width") != original.width
        or manifest.get("canvas_height") != original.height
        or manifest.get("approved_source_sha256") != APPROVED_SOURCE_SHA256
    ):
        raise SourcePackageError("canvas_or_source_mismatch")
    byte_report = inspect_assets(manifest, root)
    if byte_report["reason"] != "bytes_verified_only_requires_independent_rig_proofs":
        raise SourcePackageError("private_layer_bytes_unproven")

    canvas = Image.new("RGBA", original.size, (0, 0, 0, 0))
    for name in layer_order:
        record = manifest["layers"][name]
        bbox = record.get("bbox_xyxy")
        if (
            not isinstance(bbox, list)
            or len(bbox) != 4
            or any(type(n) is not int for n in bbox)
        ):
            raise SourcePackageError("invalid_layer_registration")
        left, top, right, bottom = bbox
        if not (
            0 <= left < right <= original.width
            and 0 <= top < bottom <= original.height
        ):
            raise SourcePackageError("invalid_layer_registration")
        data = _regular_bytes(root / (name + ".png"), limit=MAX_SOURCE_BYTES)
        if not hmac.compare_digest(
            hashlib.sha256(data).hexdigest(), record["sha256"]
        ):
            raise SourcePackageError("layer_changed_after_verification")
        with Image.open(BytesIO(data)) as image:
            image.load()
            if image.mode != "RGBA" or image.size != (
                right - left, bottom - top
            ):
                raise SourcePackageError("layer_canvas_mismatch")
            layer = image.copy()
        source_crop = original.crop((left, top, right, bottom))
        difference = ImageChops.difference(
            source_crop, layer.convert("RGB")
        )
        if difference.getbbox() is not None:
            raise SourcePackageError("layer_pixel_identity_mismatch")
        canvas.alpha_composite(layer, (left, top))

    with BytesIO() as buffer:
        canvas.save(buffer, format="PNG", optimize=True)
        contents = buffer.getvalue()
    fd = os.open(
        output, os.O_CREAT | os.O_WRONLY | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    with os.fdopen(fd, "wb") as target:
        target.write(contents)
    return {
        "created": True,
        "kind": "private_still_layer_review_only",
        "source_sha256": APPROVED_SOURCE_SHA256,
        "layers": len(LAYERS),
        "emits_motion": False,
        "identity_approved": False,
        "human_authority_approved": False,
        "reason": "still_composite_requires_human_identity_and_occlusion_review",
    }
