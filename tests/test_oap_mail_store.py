"""Mail SQL ownership enforcement without a live database or message delivery."""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from mission_control import mail_store, postgres_db

OWNER = str(uuid.uuid4())
OTHER = str(uuid.uuid4())


class _Connection:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []
        self.committed = False

    def execute(self, sql, params):
        self.queries.append((sql, params))
        return self

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return (uuid.uuid4(),)

    def commit(self):
        self.committed = True


def _connect(connection):
    @contextmanager
    def connection_factory(*, readonly=False):
        connection.readonly = readonly
        yield connection
    return connection_factory


def test_mail_list_filters_owner_and_folder_at_sql_layer(monkeypatch):
    row = (uuid.uuid4(), "inbox", "Subject", "Body", "Member",
           datetime.now(timezone.utc))
    connection = _Connection([row])
    monkeypatch.setattr(postgres_db, "connect", _connect(connection))
    items = mail_store.list_items(OWNER, OWNER, "inbox")
    sql, params = connection.queries[0]
    assert "WHERE owner_id=%s AND folder=%s" in sql
    assert params == (OWNER, "inbox")
    assert connection.readonly is True
    assert items[0]["id"] == str(row[0])


def test_cross_owner_read_and_draft_fail_before_db(monkeypatch):
    def no_database(**_kwargs):
        raise AssertionError("database must never open")
    monkeypatch.setattr(postgres_db, "connect", no_database)
    with pytest.raises(PermissionError, match="mail_owner_required"):
        mail_store.list_items(OTHER, OWNER, "inbox")
    with pytest.raises(PermissionError, match="mail_owner_required"):
        mail_store.save_draft(OTHER, OWNER, subject="x", body="private")


def test_draft_is_owned_unsent_record(monkeypatch):
    connection = _Connection([])
    monkeypatch.setattr(postgres_db, "connect", _connect(connection))
    draft_id = mail_store.save_draft(OWNER, OWNER, subject="Subject",
                                      body="Unsent", correspondent="Member")
    uuid.UUID(draft_id)
    sql, params = connection.queries[0]
    assert "INSERT INTO oap_mail_items" in sql
    assert "'draft'" in sql
    assert params == (OWNER, "Subject", "Unsent", "Member")
    assert connection.committed is True


def test_missing_mail_table_fails_closed(monkeypatch):
    @contextmanager
    def broken(*, readonly=False):
        raise RuntimeError("secret database detail")
        yield
    monkeypatch.setattr(postgres_db, "connect", broken)
    with pytest.raises(mail_store.MailUnavailable, match="mail_store_unavailable"):
        mail_store.list_items(OWNER, OWNER, "inbox")



def test_smi_subject_query_selects_no_body_or_private_columns(monkeypatch):
    connection = _Connection([("<subject>", "member@example.test")])
    monkeypatch.setattr(postgres_db, "connect", _connect(connection))
    items = mail_store.list_subjects(OWNER, OWNER, "inbox")
    sql, params = connection.queries[0]
    selected_columns = sql.split("FROM oap_mail_items", 1)[0]
    assert selected_columns.strip() == "SELECT subject,correspondent"
    assert "WHERE owner_id=%s AND folder=%s" in sql
    assert "ORDER BY created_at DESC,id DESC LIMIT 50" in sql
    assert params == (OWNER, "inbox")
    assert connection.readonly is True
    assert connection.committed is False
    assert items == [{
        "subject": "<subject>",
        "correspondent": "member@example.test",
    }]


def test_smi_subject_query_denies_cross_owner_and_invalid_folder_before_db(
    monkeypatch,
):
    def no_database(**_kwargs):
        raise AssertionError("database must never open")
    monkeypatch.setattr(postgres_db, "connect", no_database)
    with pytest.raises(PermissionError, match="mail_owner_required"):
        mail_store.list_subjects(OTHER, OWNER, "inbox")
    with pytest.raises(ValueError, match="mail_folder_invalid"):
        mail_store.list_subjects(OWNER, OWNER, "../mail")


def test_smi_subject_query_redacts_database_failure(monkeypatch):
    @contextmanager
    def broken(*, readonly=False):
        raise RuntimeError("private-database-host")
        yield
    monkeypatch.setattr(postgres_db, "connect", broken)
    with pytest.raises(mail_store.MailUnavailable) as exc:
        mail_store.list_subjects(OWNER, OWNER, "inbox")
    assert "private-database-host" not in str(exc.value)
