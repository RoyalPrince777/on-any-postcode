"""Offline, read-only asset evidence for the original SMI character.

This verifier is NOT a rig engine or a production Green Gate. It never declares
genuine movement, visemes, identity fidelity or Human Authority approval.
Do not put layer files in public static assets; pass an isolated private root.
"""
from __future__ import annotations

import hashlib
import hmac
from io import BytesIO
from pathlib import Path
from typing import Any, Final

from PIL import Image, UnidentifiedImageError

APPROVED_SOURCE_SHA256: Final = (
    "f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b"
)
LAYERS: Final = (
    "eyes",
    "head",
    "breathing",
    "mouth_visemes",
    "face",
    "hands",
    "upper_body",
)
PNG_SIGNATURE: Final = bytes.fromhex("89504e470d0a1a0a")
MAX_LAYER_BYTES: Final = 12 * 1024 * 1024
MAX_LAYER_DIMENSION: Final = 8192


def _layer_bytes(root: Path, record: object) -> str:
    """Check real, private PNG bytes without following symlinks or exposing them."""
    if not isinstance(record, dict):
        return "missing_layer_record"
    filename = record.get("file")
    digest = record.get("sha256")
    if (
        not isinstance(filename, str)
        or filename in {"", ".", ".."}
        or Path(filename).name != filename
        or filename != filename.strip()
        or any(char in filename for char in ("/", "\\", "\x00"))
        or not filename.endswith(".png")
    ):
        return "invalid_private_filename"
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
    ):
        return "invalid_digest"
    path = root / filename
    if path.is_symlink() or not path.is_file():
        return "missing_private_asset"
    size = path.stat().st_size
    if size < 67 or size > MAX_LAYER_BYTES:
        return "invalid_asset_size"
    data = path.read_bytes()
    if len(data) != size or not hmac.compare_digest(
        hashlib.sha256(data).hexdigest(), digest
    ):
        return "digest_mismatch"
    if data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        return "invalid_png"
    try:
        # Decode exactly the bytes that matched the digest, never a second
        # file read; reject truncated, animated and non-alpha PNGs.
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
            if (
                image.format != "PNG"
                or image.mode not in {"RGBA", "LA"}
                or getattr(image, "n_frames", 1) != 1
                or not (1 <= width <= MAX_LAYER_DIMENSION)
                or not (1 <= height <= MAX_LAYER_DIMENSION)
                or width * height > 16_000_000
            ):
                return "invalid_alpha_png"
            image.verify()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        return "invalid_png"
    return "bytes_valid_not_rig_proof"


def inspect_assets(
    manifest: object, private_root: Path | str
) -> dict[str, Any]:
    """Return only bounded evidence; no active or ready states, even with files."""
    outcome: dict[str, Any] = {
        "version": "0.1",
        "active": False,
        "frames": False,
        "motion_proven": False,
        "human_authority_approved": False,
        "private": True,
        "layers": {name: "not_inspected" for name in LAYERS},
    }
    if not isinstance(manifest, dict) or manifest.get("version") != "0.1":
        return {**outcome, "reason": "missing_or_invalid_manifest"}
    if manifest.get("approved_source_sha256") != APPROVED_SOURCE_SHA256:
        return {**outcome, "reason": "source_identity_unproven"}
    records = manifest.get("layers")
    if not isinstance(records, dict) or set(records) != set(LAYERS):
        return {**outcome, "reason": "seven_layer_contract_incomplete"}
    root = Path(private_root)
    if root.is_symlink() or not root.is_dir():
        return {**outcome, "reason": "private_asset_root_unavailable"}
    result = {name: _layer_bytes(root, records[name]) for name in LAYERS}
    outcome["layers"] = result
    outcome["reason"] = (
        "bytes_verified_only_requires_independent_rig_proofs"
        if all(value == "bytes_valid_not_rig_proof" for value in result.values())
        else "asset_bytes_incomplete"
    )
    return outcome
