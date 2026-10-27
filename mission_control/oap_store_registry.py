"""Fail-closed first-party OAP Store native package verification.

This module verifies package bytes against a release manifest and an Ed25519
publisher signature. It does not create, upload, publish, or install packages.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
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



def verify_trusted_package(
    manifest: ReleaseManifest,
    artifact: bytes,
    *,
    trusted_publisher_keys: dict[str, str],
) -> dict[str, object]:
    """Verify only against independently configured app-specific OAP trust roots.

    The trusted mapping must come from the operator's protected release config,
    never from a submitted manifest or client request. No keys are provisioned
    by this module; an empty or missing trust root is a hard denial.
    """
    key = trusted_publisher_keys.get(manifest.app_id)
    if not isinstance(key, str) or not key:
        raise PackageVerificationError("trusted_publisher_key_missing")
    return verify_package(
        manifest, artifact, publisher_public_key_b64=key
    )




def load_operator_trust_roots() -> dict[str, str]:
    """Load app-specific public roots from server-only configuration.

    No manifest or browser-supplied key can establish publisher identity.
    Absent, malformed or empty configuration denies all releases.
    Private signing keys must never appear here.
    """
    raw = os.environ.get("OAP_STORE_TRUSTED_PUBLISHERS_JSON", "")
    if not raw.strip():
        raise PackageVerificationError("operator_trust_roots_missing")
    try:
        roots = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise PackageVerificationError("operator_trust_roots_invalid") from exc
    if (
        not isinstance(roots, dict)
        or not roots
        or any(
            not isinstance(app_id, str)
            or not app_id.startswith("oap.")
            or not isinstance(public_key, str)
            or not public_key.strip()
            for app_id, public_key in roots.items()
        )
    ):
        raise PackageVerificationError("operator_trust_roots_invalid")
    return roots


def assess_release_admission(
    manifest: ReleaseManifest,
    artifact: bytes,
    *,
    trusted_publisher_keys: dict[str, str],
    approved_app_ids: frozenset[str],
    founder_release_approved: bool,
    physical_device_certified: bool,
) -> dict[str, object]:
    """Fail closed unless every release admission prerequisite is proven.

    This is a pure assessment, not package registration or download activation.
    Trust roots and release approvals must be supplied by independently
    controlled server-side evidence, never submitted by a public client.
    """
    verified = verify_trusted_package(
        manifest, artifact, trusted_publisher_keys=trusted_publisher_keys
    )
    if manifest.app_id not in approved_app_ids:
        raise PackageVerificationError("release_app_not_approved")
    if founder_release_approved is not True:
        raise PackageVerificationError("founder_release_approval_missing")
    if physical_device_certified is not True:
        raise PackageVerificationError("physical_device_proof_missing")
    return {
        **verified,
        "physical_device_certified": True,
        "release_admission_passed": True,
        "native_install_enabled": False,
        "reason": "Admission assessment only; no artifact registered or download activated.",
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
