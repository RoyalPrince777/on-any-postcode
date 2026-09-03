from __future__ import annotations

import uuid

import pytest

from mission_control import link_signalling_guard


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((" ".join(str(query).split()), params))
        return _Result(self.row)


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def _ready(monkeypatch):
    monkeypatch.setattr(
        link_signalling_guard.link_call_audit,
        "status",
        lambda: {"ready": True},
    )


def test_read_guard_requires_exact_active_participant_session(monkeypatch):
    _ready(monkeypatch)
    connection = _Connection(None)
    monkeypatch.setattr(
        link_signalling_guard.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    with pytest.raises(ValueError, match="active_call_session_required"):
        link_signalling_guard.validate_read(uuid.uuid4(), uuid.uuid4())

    query, params = connection.calls[0]
    assert "state IN ('ringing','active')" in query
    assert "expires_at>CURRENT_TIMESTAMP" in query
    assert "initiator_id=%s OR recipient_id=%s" in query
    assert params[1] == params[2]


def test_read_guard_block_stops_before_relationship_lookup(monkeypatch):
    _ready(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    connection = _Connection((peer, identity))
    monkeypatch.setattr(
        link_signalling_guard.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )
    monkeypatch.setattr(
        link_signalling_guard.linkup_safety,
        "blocked_between",
        lambda _first, _second: True,
    )
    monkeypatch.setattr(
        link_signalling_guard.link_relationships,
        "accepted_between",
        lambda *_args: pytest.fail("blocked read must not query accepted Link"),
    )

    with pytest.raises(ValueError, match="link_blocked"):
        link_signalling_guard.validate_read(identity, uuid.uuid4())


def test_read_guard_revoked_link_stops_before_signalling_read(monkeypatch):
    _ready(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    connection = _Connection((identity, peer))
    monkeypatch.setattr(
        link_signalling_guard.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )
    monkeypatch.setattr(
        link_signalling_guard.linkup_safety,
        "blocked_between",
        lambda _first, _second: False,
    )
    monkeypatch.setattr(
        link_signalling_guard.link_relationships,
        "accepted_between",
        lambda _first, _second: False,
    )

    with pytest.raises(ValueError, match="accepted_link_required"):
        link_signalling_guard.validate_read(identity, uuid.uuid4())


def test_read_guard_returns_only_peer_id_after_all_current_checks(monkeypatch):
    _ready(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    connection = _Connection((peer, identity))
    monkeypatch.setattr(
        link_signalling_guard.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )
    monkeypatch.setattr(
        link_signalling_guard.linkup_safety,
        "blocked_between",
        lambda _first, _second: False,
    )
    monkeypatch.setattr(
        link_signalling_guard.link_relationships,
        "accepted_between",
        lambda _first, _second: True,
    )

    assert link_signalling_guard.validate_read(identity, uuid.uuid4()) == peer


def test_read_guard_fails_closed_when_call_audit_not_ready(monkeypatch):
    monkeypatch.setattr(
        link_signalling_guard.link_call_audit,
        "status",
        lambda: {"ready": False},
    )
    monkeypatch.setattr(
        link_signalling_guard.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not be reached when audit is red"),
    )

    with pytest.raises(
        link_signalling_guard.LinkSignallingGuardUnavailable,
        match="link_call_audit_unavailable",
    ):
        link_signalling_guard.validate_read(uuid.uuid4(), uuid.uuid4())
