from __future__ import annotations

import json
from pathlib import Path

import pytest

from mission_control import civilization_events


class _Result:
    def fetchone(self):
        return None


class _Connection:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return _Result()


def test_civilization_outbox_migration_is_non_executing_and_idempotent():
    sql = Path("migrations/0012_oap_civilization_events.sql").read_text()
    assert "oap_civilization_events" in sql
    assert "UNIQUE (source_organ,event_type,entity_id)" in sql
    assert "'PENDING','DISPATCHING','DISPATCHED','HELD'" in sql
    assert "authority" in sql.lower()
    assert "oap_runtime_jobs" not in sql


def test_match_finished_event_is_deterministic_and_carries_causality():
    connection = _Connection()
    room = "00000000-0000-0000-0000-000000000777"
    state = {
        "status": "completed",
        "result": "checkmate",
        "winner": "White",
        "checkpoint": "a" * 64,
    }
    first = civilization_events.append_match_finished(
        connection, room_id=room, request_id="request-0001",
        game_state=state, revision=42,
    )
    second = civilization_events.append_match_finished(
        connection, room_id=room, request_id="request-0001",
        game_state=state, revision=42,
    )
    assert first == second
    sql, params = connection.calls[0]
    assert "ON CONFLICT (source_organ,event_type,entity_id) DO NOTHING" in sql
    assert params[1] == "MATCH_FINISHED"
    assert params[4] == "request-0001"
    payload = json.loads(params[6])
    assert payload["room_id"] == room
    assert payload["revision"] == 42
    assert payload["result"] == "checkmate"
    assert payload["winner"] == "White"


def test_match_finished_refuses_nonterminal_state():
    with pytest.raises(ValueError, match="not_completed"):
        civilization_events.append_match_finished(
            _Connection(),
            room_id="00000000-0000-0000-0000-000000000777",
            request_id="request-0001",
            game_state={"status": "active"},
            revision=2,
        )
