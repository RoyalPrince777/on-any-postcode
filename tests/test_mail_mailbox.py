from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from mission_control import mail_mailbox


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((" ".join(str(query).split()), params))
        return _Result(self.rows)


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def _ready(monkeypatch):
    monkeypatch.setattr(
        mail_mailbox.mail_migration,
        "schema_status",
        lambda: {"schema_ready": True, "error": None},
    )


def test_mailbox_status_is_read_only_and_truthful(monkeypatch):
    _ready(monkeypatch)
    state = mail_mailbox.status()

    assert state["ready"] is True
    assert state["read_only"] is True
    assert state["owner_scoped"] is True
    assert state["inbound_transport_built"] is False
    assert state["delivery_claimed"] is False
    assert set(state["folders"]) == {"inbox", "sent", "draft", "review"}


def test_mailbox_list_is_owner_and_folder_scoped(monkeypatch):
    _ready(monkeypatch)
    owner = str(uuid.uuid4())
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    connection = _Connection(
        [(item_id, "inbox", "Hello", "Body", "sender@example.com", now, now)]
    )
    monkeypatch.setattr(
        mail_mailbox.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    items = mail_mailbox.list_folder(owner, "inbox", limit=500)

    assert items[0]["id"] == item_id
    assert items[0]["folder"] == "inbox"
    query, params = connection.calls[0]
    assert "WHERE owner_id=%s AND folder=%s" in query
    assert params == (owner, "inbox", 100)


def test_mailbox_rejects_invalid_folder_before_database(monkeypatch):
    _ready(monkeypatch)
    monkeypatch.setattr(
        mail_mailbox.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("invalid folder must not touch database"),
    )

    with pytest.raises(ValueError, match="invalid_mail_folder"):
        mail_mailbox.list_folder(uuid.uuid4(), "spam")


def test_mailbox_fails_closed_when_schema_not_ready(monkeypatch):
    monkeypatch.setattr(
        mail_mailbox.mail_migration,
        "schema_status",
        lambda: {"schema_ready": False, "error": "mail_migration_pending"},
    )

    with pytest.raises(mail_mailbox.MailboxUnavailable):
        mail_mailbox.list_folder(uuid.uuid4(), "inbox")


def test_mailbox_search_is_owner_scoped(monkeypatch):
    _ready(monkeypatch)
    owner = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    connection = _Connection(
        [(str(uuid.uuid4()), "sent", "Subject", "Body", "person@example.com", now, now)]
    )
    monkeypatch.setattr(
        mail_mailbox.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    items = mail_mailbox.search(owner, "person")

    assert len(items) == 1
    query, params = connection.calls[0]
    assert "WHERE owner_id=%s" in query
    assert params[0] == owner
    assert params[-1] == 50
