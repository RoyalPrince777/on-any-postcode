"""Tests for the Founder-only durable Inbox persistence boundary."""
import uuid

import pytest

from mission_control import mail_inbound_store
from mission_control.mail_inbound_envelope import validate_founder_delivery

RAW = b"From: sender@example.net\r\nSubject: Hello\r\n\r\nHello"


class Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, fail=False):
        self.fail = fail
        self.seen = set()
        self.commits = 0
        self.rollbacks = 0

    def execute(self, query, params):
        if self.fail:
            raise RuntimeError("database unavailable")
        key = params[0]
        inserted = key not in self.seen
        self.seen.add(key)
        return Result((key,) if inserted else None)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, *args):
        return False


def delivery():
    return validate_founder_delivery(
        envelope_recipient="founder@example.org",
        founder_address="founder@example.org",
        founder_owner_id=str(uuid.uuid4()),
        raw_message=RAW,
    )


def test_commit_and_idempotent_retry(monkeypatch):
    db = Connection()
    monkeypatch.setattr(mail_inbound_store.mail_migration, "schema_status", lambda: {"schema_ready": True})
    monkeypatch.setattr(mail_inbound_store.postgres_db, "connect", lambda: Context(db))
    item = delivery()
    first = mail_inbound_store.persist_founder_inbox(item, delivery_key="smtp-delivery-1")
    second = mail_inbound_store.persist_founder_inbox(item, delivery_key="smtp-delivery-1")
    assert first.item_id == second.item_id
    assert first.inserted is True
    assert second.inserted is False
    assert db.commits == 2


def test_database_failure_rolls_back(monkeypatch):
    db = Connection(fail=True)
    monkeypatch.setattr(mail_inbound_store.mail_migration, "schema_status", lambda: {"schema_ready": True})
    monkeypatch.setattr(mail_inbound_store.postgres_db, "connect", lambda: Context(db))
    with pytest.raises(mail_inbound_store.InboundStoreUnavailable):
        mail_inbound_store.persist_founder_inbox(delivery(), delivery_key="smtp-delivery-2")
    assert db.rollbacks == 1
    assert db.commits == 0


def test_schema_gate_blocks_write(monkeypatch):
    monkeypatch.setattr(mail_inbound_store.mail_migration, "schema_status", lambda: {"schema_ready": False})
    monkeypatch.setattr(mail_inbound_store.postgres_db, "connect", lambda: pytest.fail("must not connect"))
    with pytest.raises(mail_inbound_store.InboundStoreUnavailable):
        mail_inbound_store.persist_founder_inbox(delivery(), delivery_key="smtp-delivery-3")


@pytest.mark.parametrize("key", ["", "contains space", "contains\nnewline", "x" * 257])
def test_bad_delivery_key_rejected(key):
    with pytest.raises(ValueError, match="invalid_inbound_delivery_key"):
        mail_inbound_store._delivery_id(delivery(), key)
