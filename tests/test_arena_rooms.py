from __future__ import annotations

import contextlib
import json
import uuid

import pytest

from mission_control import arena_rooms


class _Result:
    def __init__(self, *, one=None, many=None):
        self._one = one
        self._many = many or []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return list(self._many)


class _Connection:
    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.calls = []
        self.commits = 0

    def execute(self, sql, params=()):
        self.calls.append((" ".join(str(sql).split()), tuple(params)))
        if not self.scripted:
            return _Result()
        return self.scripted.pop(0)

    def commit(self):
        self.commits += 1


def _patch_connection(monkeypatch, connection):
    @contextlib.contextmanager
    def fake_connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(arena_rooms.postgres_db, "connect", fake_connect)


def test_room_state_requires_reconnect_token(monkeypatch):
    room_id = str(uuid.uuid4())
    connection = _Connection([_Result(one=None)])
    _patch_connection(monkeypatch, connection)

    with pytest.raises(ValueError, match="arena_room_access_denied"):
        arena_rooms.room_state(room_id=room_id, reconnect_token="x" * 40)


def test_room_state_returns_players_and_no_chat_or_payments(monkeypatch):
    room_id = str(uuid.uuid4())
    p1 = str(uuid.uuid4())
    p2 = str(uuid.uuid4())
    connection = _Connection([
        _Result(one=(1,)),
        _Result(one=("ABC234", "connect4", "ACTIVE", 2, 3, json.dumps({"turn": "p1"}))),
        _Result(many=[(p1, "Alpha", 1), (p2, "Bravo", 2)]),
    ])
    _patch_connection(monkeypatch, connection)

    result = arena_rooms.room_state(room_id=room_id, reconnect_token="t" * 40)

    assert result["revision"] == 3
    assert result["game_state"] == {"turn": "p1"}
    assert [p["seat"] for p in result["players"]] == [1, 2]
    assert result["chat"] is False
    assert result["payments"] is False


def test_room_state_client_write_fails_closed():
    with pytest.raises(ValueError, match="arena_room_server_game_adapter_required"):
        arena_rooms.update_game_state(
            room_id=str(uuid.uuid4()),
            reconnect_token="x" * 40,
            expected_revision=0,
            game_state={"winner": "me", "score": 999},
            request_id="forged-update-0001",
        )


def test_status_keeps_boundaries_explicit():
    assert arena_rooms.status() == {
        "durable_rooms": True,
        "invite_codes": True,
        "reconnect_tokens": True,
        "revision_conflict_guard": False,
        "arbitrary_client_game_state_writes": False,
        "chat": False,
        "payments": False,
        "explicit_migration_required": True,
        "deployed": False,
    }
