import hashlib

from oap_cloud.drive_manifest import verify_artifact_manifest


def test_drive_manifest_accepts_exact_payload():
    payload = b"founder-debug-apk-test"
    manifest = {"kind": "founder-debug-apk", "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest()}
    assert verify_artifact_manifest(manifest, payload)
    assert not verify_artifact_manifest(manifest, payload + b"tampered")


def test_drive_manifest_rejects_invalid_type_size_and_digest():
    payload = b"data"
    good = {"kind": "build-log", "size_bytes": 4,
            "sha256": hashlib.sha256(payload).hexdigest()}
    for bad in ({**good, "kind": "../secret"}, {**good, "size_bytes": True},
                {**good, "sha256": "not-a-hash"}):
        assert not verify_artifact_manifest(bad, payload)
