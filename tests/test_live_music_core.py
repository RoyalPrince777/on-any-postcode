from uuid import uuid4

import pytest

from mission_control import entertainment_catalogue, live_music_core


def test_live_music_schema_binds_sessions_to_music_and_records():
    sql = "\n".join(live_music_core.SCHEMA_STATEMENTS)
    assert "oap_live_music_sessions" in sql
    assert "REFERENCES oap_music_releases(release_id)" in sql
    assert "REFERENCES oap_records_masters(master_id)" in sql
    assert "stopped BOOLEAN NOT NULL DEFAULT TRUE" in sql


def test_live_contract_reuses_universal_player_and_stays_fail_closed():
    result = live_music_core.live_contract()
    assert result["music_source"] == "OAP Music"
    assert result["player"]["owner"] == entertainment_catalogue.PLAYER_OWNER
    assert result["broadcast_enabled"] is False
    assert result["microphone_access_performed"] is False
    assert result["camera_access_performed"] is False


def test_player_handoff_requires_rights_and_non_stopped_runtime_but_never_broadcasts():
    blocked = live_music_core.player_handoff_plan(
        session={"session_id": str(uuid4()), "stopped": True},
        music_gate={"private_handoff_ready": True},
    )
    planned = live_music_core.player_handoff_plan(
        session={"session_id": str(uuid4()), "stopped": False},
        music_gate={"private_handoff_ready": True},
    )
    assert blocked["private_handoff_ready"] is False
    assert planned["private_handoff_ready"] is True
    assert planned["broadcast_enabled"] is False
    assert planned["media_delivery_performed"] is False


def test_create_session_rejects_release_not_owned(monkeypatch):
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

    monkeypatch.setattr(live_music_core.postgres_db, "connect", lambda **_kwargs: Connection())
    with pytest.raises(PermissionError, match="live_music_release_not_owned"):
        live_music_core.LiveMusicStore().create_session(
            owner_identity_id=owner,
            release_id=release,
            title="Live session",
        )


def test_stop_session_remains_fail_closed(monkeypatch):
    owner, session, release = str(uuid4()), str(uuid4()), str(uuid4())

    class Result:
        def __init__(self, row):
            self.row = row
        def fetchone(self):
            return self.row

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, _params=()):
            if "UPDATE oap_live_music_sessions" in sql:
                return Result((release,))
            return Result(None)
        def commit(self):
            return None

    monkeypatch.setattr(live_music_core.postgres_db, "connect", lambda **_kwargs: Connection())
    result = live_music_core.LiveMusicStore().stop_session(
        owner_identity_id=owner,
        session_id=session,
        reference="Founder STOP",
    )
    assert result["stopped"] is True
    assert result["broadcast_enabled"] is False
    assert result["player_handoff_allowed"] is False
