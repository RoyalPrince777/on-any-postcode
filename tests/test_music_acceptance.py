from uuid import uuid4

import pytest

from mission_control import music_acceptance


def test_acceptance_schema_covers_all_final_gates_and_is_owner_scoped():
    sql = "\n".join(music_acceptance.SCHEMA_STATEMENTS)
    for kind in ("GOLDEN_TRACK", "PLAYER", "RADIO", "LIVE", "RECOVERY", "DISTRIBUTION"):
        assert kind in sql
    assert "owner_identity_id UUID NOT NULL REFERENCES users(id)" in sql
    assert "REFERENCES oap_music_releases(release_id)" in sql


def test_completion_gate_requires_all_acceptance_kinds_but_never_public_execution():
    rows = [{"acceptance_kind": kind} for kind in music_acceptance.ACCEPTANCE_KINDS]
    result = music_acceptance.software_completion_gate(rows)
    assert result["acceptance_receipt_coverage_complete"] is True
    assert result["missing_acceptance_kinds"] == []
    assert result["public_playback_enabled"] is False
    assert result["external_distribution_enabled"] is False
    assert result["rights_verified_by_software"] is False


def test_acceptance_receipt_hashes_actual_bytes_and_rejects_foreign_release(monkeypatch):
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
            raise AssertionError("must not commit foreign release")

    monkeypatch.setattr(music_acceptance.postgres_db, "connect", lambda **_kwargs: Connection())
    with pytest.raises(PermissionError, match="acceptance_release_not_owned"):
        music_acceptance.MusicAcceptanceStore().append(
            owner_identity_id=owner,
            release_id=release,
            acceptance_kind="PLAYER",
            evidence_bytes=b"real acceptance evidence",
            evidence_reference="device-run-1",
            human_approval_reference="founder-final-1",
        )
