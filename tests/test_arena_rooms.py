from __future__ import annotations

import contextlib
import json
import uuid

import pytest

from mission_control import arena_rooms, connect4


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
    initial = connect4.new_game("Alpha", "Bravo")
    connection = _Connection([
        _Result(one=(1,)),
        _Result(one=("ABC234", "connect4", "ACTIVE", 2, 3, json.dumps(initial))),
        _Result(many=[(p1, "Alpha", 1), (p2, "Bravo", 2)]),
    ])
    _patch_connection(monkeypatch, connection)

    result = arena_rooms.room_state(room_id=room_id, reconnect_token="t" * 40)

    assert result["your_seat"] == 1
    assert result["revision"] == 3
    assert result["game_state"]["current_player_id"] == "p1"
    assert "checkpoint" not in result["game_state"]
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
        "revision_conflict_guard": True,
        "connect4_server_actions": True,
        "dot_server_actions": True,
        "arbitrary_client_game_state_writes": False,
        "chat": False,
        "payments": False,
        "explicit_migration_required": True,
        "deployed": False,
    }


def test_connect4_room_action_commits_server_engine_move(monkeypatch):
    room_id = str(uuid.uuid4())
    connection = _Connection([
        _Result(one=("connect4", "ACTIVE", 2, 0, {})),
        _Result(one=(1,)),
        _Result(one=None),
        _Result(many=[(1, "Alpha"), (2, "Bravo")]),
        _Result(),
        _Result(),
    ])
    _patch_connection(monkeypatch, connection)
    result = arena_rooms.connect4_action(
        room_id=room_id, reconnect_token="x" * 40,
        expected_revision=0, request_id="c4-shared-move-0001",
        action="drop", column=3,
    )
    assert result["revision"] == 1
    assert result["status"] == "ACTIVE"
    assert result["game_state"]["board"][5][3] == 1
    assert result["game_state"]["current_player_id"] == "p2"
    assert connection.commits == 1
    state_update = next(call for call in connection.calls if "UPDATE oap_arena_rooms" in call[0])
    written = json.loads(state_update[1][0])
    assert written["checkpoint"]
    assert written["board"][5][3] == 1
    assert next(call for call in connection.calls if "INSERT INTO oap_arena_room_updates" in call[0])[1][-1]


def test_connect4_room_replay_conflict_fails_closed(monkeypatch):
    room_id = str(uuid.uuid4())
    connection = _Connection([
        _Result(one=("connect4", "ACTIVE", 2, 1, {})),
        _Result(one=(1,)),
        _Result(one=(1, "0" * 64)),
    ])
    _patch_connection(monkeypatch, connection)
    with pytest.raises(ValueError, match="arena_room_idempotency_conflict"):
        arena_rooms.connect4_action(
            room_id=room_id, reconnect_token="x" * 40,
            expected_revision=0, request_id="c4-shared-move-0001",
            action="drop", column=4,
        )
    assert not any("UPDATE oap_arena_rooms" in call[0] for call in connection.calls)


def test_connect4_room_rejects_wrong_seat_and_stale_revision(monkeypatch):
    room_id = str(uuid.uuid4())
    first = connect4.new_game("Alpha", "Bravo")
    connection = _Connection([
        _Result(one=("connect4", "ACTIVE", 2, 0, first)),
        _Result(one=(2,)),
        _Result(one=None),
        _Result(many=[(1, "Alpha"), (2, "Bravo")]),
    ])
    _patch_connection(monkeypatch, connection)
    with pytest.raises(ValueError, match="arena_room_not_your_turn"):
        arena_rooms.connect4_action(
            room_id=room_id, reconnect_token="y" * 40,
            expected_revision=0, request_id="c4-wrong-seat-0001",
            action="drop", column=3,
        )
    assert connection.commits == 0


def test_room_join_rejects_duplicate_name_before_connect4_game_start(monkeypatch):
    room_id = str(uuid.uuid4())
    connection = _Connection([
        _Result(one=(room_id, "connect4", "WAITING", 2)),
        _Result(many=[(1, "Alpha")]),
    ])
    _patch_connection(monkeypatch, connection)
    with pytest.raises(ValueError, match="arena_room_player_name_taken"):
        arena_rooms.join_room(room_code="ABC234", display_name=" alpha ")
    assert connection.commits == 0
    assert not any("INSERT INTO oap_arena_room_players" in sql for sql, _ in connection.calls)


def test_room_join_distinct_name_opens_two_player_game(monkeypatch):
    room_id = str(uuid.uuid4())
    connection = _Connection([
        _Result(one=(room_id, "connect4", "WAITING", 2)),
        _Result(many=[(1, "Alpha")]),
        _Result(),
        _Result(),
    ])
    _patch_connection(monkeypatch, connection)
    result = arena_rooms.join_room(room_code="ABC234", display_name="Bravo")
    assert result["seat"] == 2
    assert result["game_key"] == "connect4"
    assert connection.commits == 1
    assert any("SET status='ACTIVE'" in sql for sql, _ in connection.calls)
