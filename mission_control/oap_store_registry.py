"""Fail-closed first-party OAP Store native package verification.

This module verifies package bytes against a release manifest and an Ed25519
publisher signature. It does not create, upload, publish, or install packages.
"""
from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class PackageVerificationError(ValueError):
    """Package or release evidence failed verification."""


@dataclass(frozen=True)
class ReleaseManifest:
    app_id: str
    version: str
    channel: str
    artifact_sha256: str
    artifact_size: int
    publisher: str
    signature_b64: str
    min_os: str = ""
    rollback_of: str | None = None


def _canonical_message(manifest: ReleaseManifest) -> bytes:
    fields = (
        manifest.app_id,
        manifest.version,
        manifest.channel,
        manifest.artifact_sha256.lower(),
        str(manifest.artifact_size),
        manifest.publisher,
        manifest.min_os,
        manifest.rollback_of or "",
    )
    return "\n".join(fields).encode("utf-8")


def verify_package(
    manifest: ReleaseManifest,
    artifact: bytes,
    *,
    publisher_public_key_b64: str,
) -> dict[str, object]:
    """Verify hash, size and publisher signature; fail closed on any mismatch."""

    if manifest.publisher != "ON ANY POSTCODE LTD":
        raise PackageVerificationError("publisher_not_allowed")
    if manifest.channel not in {"stable", "beta", "recovery"}:
        raise PackageVerificationError("release_channel_invalid")
    if not manifest.app_id.startswith("oap."):
        raise PackageVerificationError("app_id_invalid")
    if manifest.artifact_size <= 0 or manifest.artifact_size != len(artifact):
        raise PackageVerificationError("artifact_size_mismatch")

    digest = hashlib.sha256(artifact).hexdigest()
    if digest != manifest.artifact_sha256.lower():
        raise PackageVerificationError("artifact_hash_mismatch")

    try:
        public_key_raw = base64.b64decode(publisher_public_key_b64, validate=True)
        signature = base64.b64decode(manifest.signature_b64, validate=True)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_raw)
        public_key.verify(signature, _canonical_message(manifest))
    except (ValueError, TypeError, InvalidSignature) as exc:
        raise PackageVerificationError("publisher_signature_invalid") from exc

    return {
        "app_id": manifest.app_id,
        "version": manifest.version,
        "channel": manifest.channel,
        "artifact_sha256": digest,
        "artifact_size": len(artifact),
        "publisher": manifest.publisher,
        "signature_verified": True,
        "hash_verified": True,
        "size_verified": True,
        "rollback_release": bool(manifest.rollback_of),
        "install_gate_passed": True,
        "physical_device_certified": False,
    }


def native_install_status() -> dict[str, object]:
    """Truthful status before a signed native package is registered."""

    return {
        "registry_ready": True,
        "hash_verification_ready": True,
        "signature_verification_ready": True,
        "supported_signature": "Ed25519",
        "signed_native_package_registered": False,
        "native_install_enabled": False,
        "update_contract_ready": True,
        "rollback_contract_ready": True,
        "physical_device_certified": False,
        "reason": "No verified signed native package has been registered.",
    }
