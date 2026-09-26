from __future__ import annotations

import contextlib
import uuid
from datetime import UTC, datetime

import pytest

from mission_control import arena_profile_store


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

    monkeypatch.setattr(arena_profile_store.postgres_db, "connect", fake_connect)


def test_profile_reads_only_canonical_active_user(monkeypatch):
    identity = str(uuid.uuid4())
    now = datetime.now(UTC)
    connection = _Connection([
        _Result(one=(identity, "Player One", 4, 2, 1, 1, 7, now)),
    ])
    _patch_connection(monkeypatch, connection)

    result = arena_profile_store.profile(identity)

    assert result["identity_id"] == identity
    assert result["display_name"] == "Player One"
    assert result["matches_played"] == 4
    assert result["points"] == 7
    assert "JOIN users u ON u.id=p.identity_id" in connection.calls[0][0]
    assert "u.status='active'" in connection.calls[0][0]


def test_ranking_is_server_ordered_and_bounded(monkeypatch):
    a = str(uuid.uuid4())
    b = str(uuid.uuid4())
    connection = _Connection([
        _Result(many=[
            (a, "Alpha", 3, 3, 0, 0, 9),
            (b, "Beta", 3, 2, 1, 0, 6),
        ]),
    ])
    _patch_connection(monkeypatch, connection)

    result = arena_profile_store.ranking(limit=999)

    assert [item["rank"] for item in result] == [1, 2]
    assert [item["identity_id"] for item in result] == [a, b]
    assert connection.calls[0][1] == (100,)
    assert "ORDER BY p.points DESC,p.wins DESC" in connection.calls[0][0]


def test_completed_match_is_owner_bound_idempotent_and_updates_profiles(monkeypatch):
    a = str(uuid.uuid4())
    b = str(uuid.uuid4())
    match = str(uuid.uuid4())
    receipt = "a" * 64
    connection = _Connection([
        _Result(many=[(a,), (b,)]),
        _Result(one=None),
        _Result(),
        _Result(),
        _Result(),
    ])
    _patch_connection(monkeypatch, connection)

    result = arena_profile_store.record_completed_match(
        match_id=match,
        player_a_id=a,
        player_b_id=b,
        player_a_score=7,
        player_b_score=5,
        receipt_hash=receipt,
    )

    assert result == {
        "match_id": match,
        "duplicate": False,
        "player_a_outcome": "WIN",
        "player_b_outcome": "LOSS",
    }
    assert connection.commits == 1
    assert any("INSERT INTO oap_arena_matches" in call[0] for call in connection.calls)
    assert sum("INSERT INTO oap_arena_player_profiles" in call[0] for call in connection.calls) == 2


def test_completed_match_exact_replay_is_idempotent(monkeypatch):
    a = str(uuid.uuid4())
    b = str(uuid.uuid4())
    match = str(uuid.uuid4())
    receipt = "b" * 64
    connection = _Connection([
        _Result(many=[(a,), (b,)]),
        _Result(one=(a, b, 4, 4, receipt)),
    ])
    _patch_connection(monkeypatch, connection)

    result = arena_profile_store.record_completed_match(
        match_id=match,
        player_a_id=a,
        player_b_id=b,
        player_a_score=4,
        player_b_score=4,
        receipt_hash=receipt,
    )

    assert result == {"match_id": match, "duplicate": True}
    assert connection.commits == 1


def test_completed_match_conflicting_replay_fails_closed(monkeypatch):
    a = str(uuid.uuid4())
    b = str(uuid.uuid4())
    match = str(uuid.uuid4())
    receipt = "c" * 64
    connection = _Connection([
        _Result(many=[(a,), (b,)]),
        _Result(one=(a, b, 7, 1, receipt)),
    ])
    _patch_connection(monkeypatch, connection)

    with pytest.raises(ValueError, match="arena_match_idempotency_conflict"):
        arena_profile_store.record_completed_match(
            match_id=match,
            player_a_id=a,
            player_b_id=b,
            player_a_score=7,
            player_b_score=2,
            receipt_hash=receipt,
        )


def test_invalid_identity_score_receipt_and_self_match_fail_closed():
    a = str(uuid.uuid4())
    b = str(uuid.uuid4())
    match = str(uuid.uuid4())

    with pytest.raises(ValueError, match="arena_identity_invalid"):
        arena_profile_store.profile("not-a-uuid")
    with pytest.raises(ValueError, match="arena_match_distinct_players_required"):
        arena_profile_store.record_completed_match(
            match_id=match,
            player_a_id=a,
            player_b_id=a,
            player_a_score=1,
            player_b_score=0,
            receipt_hash="d" * 64,
        )
    with pytest.raises(ValueError, match="arena_score_invalid"):
        arena_profile_store.record_completed_match(
            match_id=match,
            player_a_id=a,
            player_b_id=b,
            player_a_score=8,
            player_b_score=0,
            receipt_hash="d" * 64,
        )
    with pytest.raises(ValueError, match="arena_receipt_hash_invalid"):
        arena_profile_store.record_completed_match(
            match_id=match,
            player_a_id=a,
            player_b_id=b,
            player_a_score=1,
            player_b_score=0,
            receipt_hash="not-a-receipt",
        )


def test_status_keeps_money_and_deployment_locked():
    assert arena_profile_store.status() == {
        "canonical_users_identity": True,
        "durable_profiles": True,
        "durable_match_history": True,
        "rankings": True,
        "explicit_migration_required": True,
        "payments": False,
        "prizes": False,
        "deployed": False,
    }
