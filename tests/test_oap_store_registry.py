"""OAP Store package registry verification tests."""
import base64
import hashlib

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from mission_control import oap_store_registry as registry


def _signed_manifest(artifact: bytes):
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    unsigned = registry.ReleaseManifest(
        app_id="oap.world",
        version="1.0.0",
        channel="stable",
        artifact_sha256=hashlib.sha256(artifact).hexdigest(),
        artifact_size=len(artifact),
        publisher="ON ANY POSTCODE LTD",
        signature_b64="",
        min_os="android-10",
    )
    signature = key.sign(registry._canonical_message(unsigned))
    manifest = registry.ReleaseManifest(
        **{**unsigned.__dict__, "signature_b64": base64.b64encode(signature).decode()}
    )
    return manifest, base64.b64encode(public).decode()


def test_signed_package_verifies_hash_size_and_publisher():
    artifact = b"oap-native-package-proof"
    manifest, public_key = _signed_manifest(artifact)
    result = registry.verify_package(
        manifest, artifact, publisher_public_key_b64=public_key
    )
    assert result["install_gate_passed"] is True
    assert result["signature_verified"] is True
    assert result["hash_verified"] is True
    assert result["physical_device_certified"] is False


def test_tampered_package_fails_closed():
    artifact = b"oap-native-package-proof"
    manifest, public_key = _signed_manifest(artifact)
    with pytest.raises(registry.PackageVerificationError):
        registry.verify_package(
            manifest, artifact + b"-tampered", publisher_public_key_b64=public_key
        )


def test_native_registry_stays_locked_without_registered_artifact():
    state = registry.native_install_status()
    assert state["registry_ready"] is True
    assert state["signature_verification_ready"] is True
    assert state["update_contract_ready"] is True
    assert state["rollback_contract_ready"] is True
    assert state["signed_native_package_registered"] is False
    assert state["native_install_enabled"] is False


def test_trusted_install_denies_missing_publisher_root():
    artifact = b"release-bytes"
    manifest, public_key = _signed_manifest(artifact)
    with pytest.raises(registry.PackageVerificationError, match="trusted_publisher_key_missing"):
        registry.verify_trusted_package(manifest, artifact, trusted_publisher_keys={})
    with pytest.raises(registry.PackageVerificationError, match="trusted_publisher_key_missing"):
        registry.verify_trusted_package(manifest, artifact, trusted_publisher_keys={"oap.sika": public_key})


def test_trusted_install_rejects_valid_signature_from_other_publisher():
    artifact = b"release-bytes"
    manifest, untrusted_key = _signed_manifest(artifact)
    _, trusted_key = _signed_manifest(artifact)
    assert untrusted_key != trusted_key
    with pytest.raises(registry.PackageVerificationError, match="publisher_signature_invalid"):
        registry.verify_trusted_package(
            manifest, artifact, trusted_publisher_keys={"oap.world": trusted_key}
        )


def test_trusted_install_accepts_matching_configured_publisher():
    artifact = b"release-bytes"
    manifest, key = _signed_manifest(artifact)
    result = registry.verify_trusted_package(
        manifest, artifact, trusted_publisher_keys={"oap.world": key}
    )
    assert result["signature_verified"] is True
    assert result["physical_device_certified"] is False
