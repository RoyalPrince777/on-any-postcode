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


def test_release_admission_requires_independent_authority_and_device_proof():
    artifact = b"oap-approved-artifact"
    manifest, key = _signed_manifest(artifact)
    arguments = {
        "trusted_publisher_keys": {"oap.world": key},
        "approved_app_ids": frozenset({"oap.world"}),
        "founder_release_approved": True,
        "physical_device_certified": True,
    }
    for update, expected in (
        ({"approved_app_ids": frozenset()}, "release_app_not_approved"),
        ({"founder_release_approved": False}, "founder_release_approval_missing"),
        ({"physical_device_certified": False}, "physical_device_proof_missing"),
        ({"trusted_publisher_keys": {}}, "trusted_publisher_key_missing"),
    ):
        with pytest.raises(registry.PackageVerificationError, match=expected):
            registry.assess_release_admission(manifest, artifact, **{**arguments, **update})
    status = registry.assess_release_admission(manifest, artifact, **arguments)
    assert status["release_admission_passed"] is True
    assert status["native_install_enabled"] is False


def test_release_admission_rejects_tampered_artifact():
    artifact = b"oap-approved-artifact"
    manifest, key = _signed_manifest(artifact)
    with pytest.raises(registry.PackageVerificationError, match="artifact_size_mismatch"):
        registry.assess_release_admission(
            manifest, artifact + b"x",
            trusted_publisher_keys={"oap.world": key},
            approved_app_ids=frozenset({"oap.world"}),
            founder_release_approved=True,
            physical_device_certified=True,
        )


def test_operator_trust_roots_fail_closed(monkeypatch):
    monkeypatch.delenv("OAP_STORE_TRUSTED_PUBLISHERS_JSON", raising=False)
    with pytest.raises(registry.PackageVerificationError, match="operator_trust_roots_missing"):
        registry.load_operator_trust_roots()
    for invalid in ("{", "[]", "{}", '{"random": "key"}', '{"oap.world": ""}'):
        monkeypatch.setenv("OAP_STORE_TRUSTED_PUBLISHERS_JSON", invalid)
        with pytest.raises(registry.PackageVerificationError, match="operator_trust_roots_invalid"):
            registry.load_operator_trust_roots()


def test_operator_trust_roots_allow_only_configured_public_key(monkeypatch):
    artifact = b"private-oap-release"
    manifest, public_key = _signed_manifest(artifact)
    monkeypatch.setenv(
        "OAP_STORE_TRUSTED_PUBLISHERS_JSON",
        '{"oap.world": "' + public_key + '"}',
    )
    trust_roots = registry.load_operator_trust_roots()
    assert registry.verify_trusted_package(
        manifest, artifact, trusted_publisher_keys=trust_roots
    )["signature_verified"] is True
