from datetime import datetime, timezone

from mission_control import (
    sika_account_engine,
    sika_balance_engine,
    sika_customer_view,
)


def _account(status="OPEN"):
    return sika_account_engine.BankAccount(
        account_id="acct-1",
        owner_reference="11111111-1111-1111-1111-111111111111",
        legal_entity="ON ANY POSTCODE LTD",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-1",
        status=status,
    )


def test_customer_snapshot_is_owner_scoped_and_ledger_derived(monkeypatch):
    monkeypatch.setattr(
        sika_customer_view.sika_account_engine,
        "read_owner_accounts",
        lambda owner: [_account()],
    )
    monkeypatch.setattr(
        sika_customer_view.sika_balance_engine,
        "project",
        lambda account: sika_balance_engine.BalanceProjection(
            account_id=account.account_id,
            ledger_account_id=account.ledger_account_id,
            currency=account.currency,
            cleared=sika_balance_engine.Decimal("100.00"),
            pending=sika_balance_engine.Decimal("10.00"),
            reserved=sika_balance_engine.Decimal("20.00"),
            available=sika_balance_engine.Decimal("80.00"),
        ),
    )
    result = sika_customer_view.snapshot(
        "11111111-1111-1111-1111-111111111111"
    )
    assert result["owner_scoped"] is True
    assert result["balance_source"] == "canonical_ledger_and_holds"
    assert result["accounts"][0]["balance"]["available"] == "80.00"
    assert "owner_reference" not in result["accounts"][0]


class _Result:
    def fetchall(self):
        now = datetime(2026, 10, 4, 6, 0, tzinfo=timezone.utc)
        return [
            (
                "pay-1",
                "acct-1",
                "merchant-1",
                sika_balance_engine.Decimal("12.50"),
                "GBP",
                "United Kingdom",
                "AUTHORISED",
                None,
                now,
                now,
            )
        ]


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        assert "payer_account_id = ANY" in sql
        return _Result()


def test_customer_activity_reads_only_owned_account_ids(monkeypatch):
    monkeypatch.setattr(
        sika_customer_view.sika_account_engine,
        "read_owner_accounts",
        lambda owner: [_account()],
    )
    monkeypatch.setattr(
        sika_customer_view.postgres_db,
        "connect",
        lambda readonly=True: _Connection(),
    )
    result = sika_customer_view.activity(
        "11111111-1111-1111-1111-111111111111"
    )
    assert result["owner_scoped"] is True
    assert result["source"] == "canonical_payment_intents"
    assert result["items"][0]["payer_account_id"] == "acct-1"
    assert result["items"][0]["status"] == "AUTHORISED"


def test_customer_view_status_is_private_read_only_truth():
    status = sika_customer_view.status()
    assert status["owner_scoped"] is True
    assert status["verified_identity_reference_required"] is True
    assert status["read_only"] is True
    assert status["money_movement"] is False
