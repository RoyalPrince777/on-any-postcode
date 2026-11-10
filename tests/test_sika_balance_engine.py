from mission_control import sika_account_engine, sika_balance_engine


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self):
        self._rows = [
            ("125.00", "25.00"),
            ("30.00",),
            ("30.00",),
        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        return _Result(self._rows.pop(0))


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


def test_balance_projection_is_ledger_derived_and_hold_aware(monkeypatch):
    monkeypatch.setattr(
        sika_balance_engine.postgres_db,
        "connect",
        lambda readonly=True: _Connection(),
    )
    result = sika_balance_engine.project(_account())
    assert result.cleared == sika_balance_engine.Decimal("100.00")
    assert result.pending == sika_balance_engine.Decimal("30.00")
    assert result.reserved == sika_balance_engine.Decimal("30.00")
    assert result.available == sika_balance_engine.Decimal("70.00")


def test_balance_engine_status_refuses_display_balance_truth():
    status = sika_balance_engine.status()
    assert status["ledger_derived"] is True
    assert status["display_balance_stored"] is False
    assert status["active_holds_reduce_available"] is True
    assert status["money_movement"] is False
