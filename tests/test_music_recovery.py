from uuid import uuid4

import pytest

from mission_control import music_recovery


def test_recovery_schema_is_owner_scoped_and_music_bound():
    sql = "\n".join(music_recovery.SCHEMA_STATEMENTS)
    assert "oap_music_recovery_manifests" in sql
    assert "owner_identity_id UUID NOT NULL REFERENCES users(id)" in sql
    assert "REFERENCES oap_music_releases(release_id)" in sql
    assert "manifest_sha256" in sql


def test_manifest_digest_is_deterministic_and_tamper_detected():
    payload = {"release": "one", "receipts": [{"a": 1}, {"b": 2}]}
    digest = music_recovery.manifest_digest(payload)
    assert music_recovery.verify_manifest(payload, digest)["verified"] is True
    tampered = {"release": "one", "receipts": [{"a": 1}, {"b": 3}]}
    result = music_recovery.verify_manifest(tampered, digest)
    assert result["verified"] is False
    assert result["playback_enabled"] is False


def test_capture_refuses_cross_owner_release(monkeypatch):
    owner, release = str(uuid4()), str(uuid4())

    class Result:
        def fetchone(self):
            return None

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, _sql, _params=()):
            return Result()
        def commit(self):
            raise AssertionError("must not commit")

    monkeypatch.setattr(music_recovery.postgres_db, "connect", lambda **_kwargs: Connection())
    with pytest.raises(PermissionError, match="recovery_release_not_owned"):
        music_recovery.MusicRecoveryStore().capture(
            owner_identity_id=owner,
            release_id=release,
            payload={"release_id": release},
        )
