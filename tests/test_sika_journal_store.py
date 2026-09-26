import json
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from mission_control import sika_journal_store


class FakeConnection:
    def __init__(self):
        self.workspace = []
        self.audit = []

    def execute(self, sql, params=()):
        normalized = " ".join(sql.split())
        if normalized.startswith("SELECT pg_advisory_xact_lock"):
            return FakeRows([])
        if "FROM oap_workspace_records" in normalized:
            owner = params[0]
            rows = [
                (r["record_id"], r["title"], r["body"], r["created_at"])
                for r in self.workspace if r["owner_id"] == owner
            ]
            return FakeRows([(x[1], x[2], x[3]) for x in rows])
        if normalized.startswith("INSERT INTO oap_workspace_records"):
            owner, title, body = params
            record_id = str(uuid4())
            self.workspace.append({
                "record_id": record_id,
                "owner_id": owner,
                "title": title,
                "body": body,
                "created_at": datetime.now(UTC),
            })
            return FakeRows([(record_id,)])
        if "SELECT curr_hash FROM audit_events" in normalized:
            return FakeRows([(self.audit[-1]["curr_hash"],)] if self.audit else [])
        if normalized.startswith("INSERT INTO audit_events"):
            self.audit.append({"curr_hash": params[1], "metadata": params[-1]})
            return FakeRows([])
        raise AssertionError(normalized)

    def commit(self):
        return None


class FakeRows:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


@pytest.fixture
def fake_db(monkeypatch):
    connection = FakeConnection()

    @contextmanager
    def connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(sika_journal_store.postgres_db, "connect", connect)
    return connection


def test_balanced_reference_journal_is_owner_scoped_and_non_monetary(fake_db):
    owner = str(uuid4())
    other = str(uuid4())
    result = sika_journal_store.post_reference(
        owner,
        debit_account="wallet_reference",
        credit_account="treasury_reference",
        amount_sika="25",
        memo="test",
    )
    assert result["balanced"] is True
    assert result["money_moved"] is False
    assert sika_journal_store.statement(owner)["entry_count"] == 1
    assert sika_journal_store.statement(other)["entry_count"] == 0


def test_statement_reconciles_equal_debits_and_credits(fake_db):
    owner = str(uuid4())
    sika_journal_store.post_reference(
        owner,
        debit_account="wallet_reference",
        credit_account="treasury_reference",
        amount_sika="7.50",
    )
    statement = sika_journal_store.statement(owner)
    assert statement["total_debits_sika"] == "7.50"
    assert statement["total_credits_sika"] == "7.50"
    assert statement["difference_sika"] == "0.00"
    assert statement["reconciled"] is True
    assert statement["executable"] is False


def test_tampered_history_fails_closed(fake_db):
    owner = str(uuid4())
    sika_journal_store.post_reference(
        owner,
        debit_account="wallet_reference",
        credit_account="treasury_reference",
        amount_sika="1",
    )
    body = json.loads(fake_db.workspace[0]["body"])
    body["credit_sika"] = "2.00"
    fake_db.workspace[0]["body"] = json.dumps(body)
    with pytest.raises(
        sika_journal_store.SikaJournalUnavailable,
        match="journal_tampered_or_forked",
    ):
        sika_journal_store.history(owner)


def test_same_account_or_zero_amount_is_rejected(fake_db):
    owner = str(uuid4())
    with pytest.raises(ValueError):
        sika_journal_store.post_reference(
            owner,
            debit_account="same",
            credit_account="same",
            amount_sika="1",
        )
    with pytest.raises(ValueError):
        sika_journal_store.post_reference(
            owner,
            debit_account="a",
            credit_account="b",
            amount_sika="0",
        )
