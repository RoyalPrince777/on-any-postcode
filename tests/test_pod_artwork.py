from __future__ import annotations

import pytest

from mission_control import pod_artwork


def test_pod_artwork_validates_signatures_and_limits():
    pod_artwork.validate_image(b"\x89PNG\r\n\x1a\n" + b"payload", "image/png")
    pod_artwork.validate_image(b"\xff\xd8\xff" + b"payload", "image/jpeg")
    pod_artwork.validate_image(b"RIFF" + b"1234" + b"WEBP" + b"payload", "image/webp")
    with pytest.raises(ValueError, match="pod_artwork_content_mismatch"):
        pod_artwork.validate_image(b"not a png", "image/png")
    with pytest.raises(ValueError, match="pod_artwork_type_invalid"):
        pod_artwork.validate_image(b"abc", "image/svg+xml")
    with pytest.raises(ValueError, match="pod_artwork_size_invalid"):
        pod_artwork.validate_image(b"x" * (pod_artwork.MAX_ARTWORK_BYTES + 1), "image/png")


def test_pod_artwork_schema_is_owner_scoped_and_installs_only_with_authority():
    assert "owner_identity_id UUID NOT NULL" in pod_artwork.SCHEMA
    assert "REFERENCES users(id)" in pod_artwork.SCHEMA
    assert "media BYTEA NOT NULL" in pod_artwork.SCHEMA
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        pod_artwork.init_schema()
    assert pod_artwork.init_schema(assume_yes=True, dry_run=True)["schema_ready"] is False


def test_private_pod_artwork_routes_deny_anonymous_access(anonymous_client):
    upload = anonymous_client.post("/mission/organs/market/pod/artwork")
    retrieval = anonymous_client.get(
        "/mission/organs/market/pod/artwork/00000000-0000-0000-0000-000000000001"
    )
    assert upload.status_code in (401, 403)
    assert retrieval.status_code in (401, 403)
