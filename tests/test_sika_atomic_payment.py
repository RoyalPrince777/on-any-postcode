import pytest

from mission_control import (
    sika_account_engine,
    sika_atomic_payment,
)


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, *, credits="100.00", debits="0.00", holds="20.00"):
        self.credits = credits
        self.debits = debits
        self.holds = holds
        self.sql = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.sql.append(sql)
        if "FROM oap_sika_accounts" in sql:
            return _Result(
                (
                    "acct-1",
                    "OPEN",
                    "ledger-1",
                    "GBP",
                    "United Kingdom",
                )
            )
        if "FROM oap_sika_journal_lines" in sql:
            return _Result((self.credits, self.debits))
        if "FROM oap_sika_payment_holds" in sql:
            return _Result((self.holds,))
        return _Result()

    def commit(self):
        self.committed = True


def _account():
    return sika_account_engine.BankAccount(
        account_id="acct-1",
        owner_reference="owner-1",
        legal_entity="Europa Crown Bank",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-1",
        status="OPEN",
    )


def _create(monkeypatch, connection, amount="50.00"):
    monkeypatch.setattr(
        sika_atomic_payment.postgres_db,
        "connect",
        lambda: connection,
    )
    return sika_atomic_payment.create(
        payer_account=_account(),
        payment_id="pay-1",
        hold_id="hold-1",
        idempotency_key="idem-1",
        payee_reference="merchant-1",
        amount=amount,
        currency="GBP",
        jurisdiction="United Kingdom",
        authority_reference="customer-confirmation-1",
        authorised_at="2026-10-04T06:00:00Z",
        expires_at="2026-10-04T06:10:00Z",
    )


def test_atomic_payment_creates_intent_authority_and_hold_together(monkeypatch):
    connection = _Connection()
    result = _create(monkeypatch, connection)
    inserts = [sql for sql in connection.sql if sql.lstrip().startswith("INSERT")]
    assert len(inserts) == 3
    assert connection.committed is True
    assert result["atomic"] is True
    assert result["payment_status"] == "DRAFT"
    assert result["hold_status"] == "ACTIVE"
    assert result["money_movement"] is False


def test_atomic_payment_fails_closed_on_insufficient_available_balance(monkeypatch):
    connection = _Connection(credits="60.00", holds="20.00")
    with pytest.raises(
        sika_atomic_payment.AtomicPaymentError,
        match="insufficient_available_balance",
    ):
        _create(monkeypatch, connection, amount="50.00")
    assert connection.committed is False
    assert not any(
        sql.lstrip().startswith("INSERT")
        for sql in connection.sql
    )


def test_atomic_payment_status_keeps_external_execution_closed():
    status = sika_atomic_payment.status()
    assert status["single_database_transaction"] is True
    assert status["payer_account_row_lock"] is True
    assert status["partial_commit_allowed"] is False
    assert status["provider_calling"] is False
    assert status["money_movement"] is False
