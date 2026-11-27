from __future__ import annotations

import uuid

import pytest

from mission_control import ptt_guest


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, *_args):
        return False


class _Connection:
    def __init__(self, *, creator_id=None):
        self.creator_id = creator_id
        self.commits = 0
        self.executed = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        compact = " ".join(sql.split())
        if compact.startswith("SELECT 1 FROM users WHERE username="):
            return _Rows(None)
        if compact.startswith("SELECT id FROM users WHERE username="):
            return _Rows((self.creator_id,)) if self.creator_id else _Rows(None)
        return _Rows(None)

    def commit(self):
        self.commits += 1


class _Rows:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


def test_create_invite_is_short_lived_eight_digit_guest(monkeypatch):
    connection = _Connection()
    monkeypatch.setattr(ptt_guest.postgres_db, "connect", lambda *a, **k: _Context(connection))
    monkeypatch.setattr(ptt_guest.secrets, "randbelow", lambda _limit: 12345678)

    invite = ptt_guest.create_invite()

    uuid.UUID(invite["identity_id"])
    assert invite["code"] == "12345678"
    assert invite["expires_at"]
    assert connection.commits == 1
    joined = "\n".join(sql for sql, _params in connection.executed)
    assert "INSERT INTO users" in joined
    assert "oap-ptt-guest-" not in joined  # value is parameterised, never interpolated into SQL


def test_join_invite_creates_expiring_purpose_link(monkeypatch):
    creator = str(uuid.uuid4())
    joiner = str(uuid.uuid4())
    connection = _Connection(creator_id=creator)
    monkeypatch.setattr(ptt_guest.postgres_db, "connect", lambda *a, **k: _Context(connection))
    monkeypatch.setattr(ptt_guest, "ensure_session_guest", lambda value=None: joiner)
    monkeypatch.setattr(ptt_guest, "_active_pair_from_relations", lambda _identity: None)

    observed = {}

    def request_link(requester, recipient, **kwargs):
        observed.update(requester=requester, recipient=recipient, kwargs=kwargs)
        return str(uuid.uuid4())

    monkeypatch.setattr(ptt_guest.link_relationships, "request_link", request_link)
    monkeypatch.setattr(ptt_guest.link_relationships, "respond", lambda recipient, relationship, decision: True)

    paired = ptt_guest.join_invite("12345678", joiner)

    assert paired["active"] is True
    assert paired["identity_id"] == joiner
    assert paired["peer_id"] == creator
    assert observed["requester"] == creator
    assert observed["recipient"] == joiner
    assert observed["kwargs"]["link_kind"] == "purpose"
    assert observed["kwargs"]["purpose_text"] == ptt_guest.PAIR_PURPOSE
    assert observed["kwargs"]["expires_at"] is not None


def test_join_invite_rejects_unknown_code(monkeypatch):
    connection = _Connection(creator_id=None)
    monkeypatch.setattr(ptt_guest.postgres_db, "connect", lambda *a, **k: _Context(connection))
    monkeypatch.setattr(ptt_guest, "ensure_session_guest", lambda value=None: str(uuid.uuid4()))

    with pytest.raises(ValueError, match="pair_code_expired_or_unknown"):
        ptt_guest.join_invite("12345678")


def test_stop_revokes_only_current_temporary_pair(monkeypatch):
    identity = str(uuid.uuid4())
    relationship = str(uuid.uuid4())
    monkeypatch.setattr(
        ptt_guest,
        "_active_pair_from_relations",
        lambda _identity: {
            "active": True,
            "relationship_id": relationship,
            "peer_id": str(uuid.uuid4()),
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    )
    observed = {}
    monkeypatch.setattr(
        ptt_guest.link_relationships,
        "revoke",
        lambda who, rel: observed.update(identity=who, relationship=rel) or True,
    )
    monkeypatch.setattr(
        ptt_guest,
        "_deactivate_guest",
        lambda who: observed.update(deactivated=who),
    )

    assert ptt_guest.stop(identity) is True
    assert observed == {
        "identity": identity,
        "relationship": relationship,
        "deactivated": identity,
    }


def test_join_invite_rejects_same_device_before_overwriting_creator(monkeypatch):
    creator = str(uuid.uuid4())
    connection = _Connection(creator_id=creator)
    monkeypatch.setattr(ptt_guest.postgres_db, "connect", lambda *a, **k: _Context(connection))
    touched = {"ensure": False}

    def ensure(value=None):
        touched["ensure"] = True
        return str(value)

    monkeypatch.setattr(ptt_guest, "ensure_session_guest", ensure)

    with pytest.raises(ValueError, match="cannot_pair_same_device"):
        ptt_guest.join_invite("12345678", creator)

    assert touched["ensure"] is False


def test_create_room_is_eight_digit_no_sign_in_host(monkeypatch):
    connection = _Connection()
    monkeypatch.setattr(ptt_guest.postgres_db, "connect", lambda *a, **k: _Context(connection))
    monkeypatch.setattr(ptt_guest.secrets, "randbelow", lambda _limit: 87654321)

    room = ptt_guest.create_room()

    uuid.UUID(room["identity_id"])
    assert room["owner_id"] == room["identity_id"]
    assert room["code"] == "87654321"
    assert room["expires_at"]
    inserts = [call for call in connection.executed if "INSERT INTO users" in call[0]]
    assert len(inserts) == 1
    assert inserts[0][1][2] == ptt_guest.ROOM_HOST_DISPLAY_NAME


def test_join_room_links_new_member_to_existing_room_members(monkeypatch):
    owner = str(uuid.uuid4())
    existing = str(uuid.uuid4())
    member = str(uuid.uuid4())
    monkeypatch.setattr(ptt_guest, "_room_owner_from_code", lambda code: owner)
    monkeypatch.setattr(ptt_guest, "ensure_session_guest", lambda value=None: member)
    monkeypatch.setattr(ptt_guest, "_room_members", lambda who: [existing] if who == owner else [])
    observed = []

    def request_link(requester, recipient, **kwargs):
        observed.append((requester, recipient, kwargs))
        return str(uuid.uuid4())

    monkeypatch.setattr(ptt_guest.link_relationships, "request_link", request_link)
    monkeypatch.setattr(ptt_guest.link_relationships, "respond", lambda *a, **k: True)
    monkeypatch.setattr(
        ptt_guest,
        "room_state",
        lambda identity, room_owner: {
            "active": True,
            "identity_id": identity,
            "owner_id": room_owner,
            "member_ids": [room_owner, existing, identity],
            "member_count": 3,
        },
    )

    room = ptt_guest.join_room("12345678", member)

    assert room["active"] is True
    assert room["member_count"] == 3
    assert {(a, b) for a, b, _kwargs in observed} == {
        (owner, member),
        (existing, member),
    }
    assert all(
        kwargs["purpose_text"] == ptt_guest._room_purpose(owner)
        for _a, _b, kwargs in observed
    )


def test_join_room_rejects_when_seven_devices_are_already_present(monkeypatch):
    owner = str(uuid.uuid4())
    member = str(uuid.uuid4())
    existing = [str(uuid.uuid4()) for _ in range(ptt_guest.ROOM_MAX_MEMBERS - 1)]
    monkeypatch.setattr(ptt_guest, "_room_owner_from_code", lambda code: owner)
    monkeypatch.setattr(ptt_guest, "ensure_session_guest", lambda value=None: member)
    monkeypatch.setattr(ptt_guest, "_room_members", lambda who: existing)

    with pytest.raises(ValueError, match="ptt_room_full"):
        ptt_guest.join_room("12345678", member)


def test_room_state_rejects_non_member(monkeypatch):
    owner = str(uuid.uuid4())
    member = str(uuid.uuid4())
    monkeypatch.setattr(ptt_guest, "_room_members", lambda who: [])

    state = ptt_guest.room_state(member, owner)

    assert state["active"] is False
    assert state["member_count"] == 0
