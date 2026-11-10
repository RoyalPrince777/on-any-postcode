from datetime import UTC, datetime

from mission_control import sika_customer_payment_authority


def _receipt(**overrides):
    values = {
        "payment_id": "pay-1",
        "payer_account_id": "acct-1",
        "payee_reference": "payee-1",
        "amount": "10.00",
        "currency": "GBP",
        "jurisdiction": "United Kingdom",
        "authority_reference": "customer-auth:1",
        "authorised_at": "2026-10-02T18:00:00Z",
        "expires_at": "2026-10-02T20:00:00Z",
    }
    values.update(overrides)
    return sika_customer_payment_authority.build_receipt(**values)


def test_receipt_is_hash_bound_and_payment_specific():
    receipt = _receipt()
    check = sika_customer_payment_authority.verify_receipt(
        receipt,
        now=datetime(2026, 10, 2, 19, 0, tzinfo=UTC),
    )
    assert check["verified"] is True
    assert len(receipt["receipt_hash"]) == 64
    assert receipt["money_movement"] is False


def test_tampered_or_expired_receipt_fails():
    receipt = _receipt()
    receipt["amount"] = "11.00"
    assert sika_customer_payment_authority.verify_receipt(
        receipt,
        now=datetime(2026, 10, 2, 19, 0, tzinfo=UTC),
    )["verified"] is False

    expired = _receipt()
    assert sika_customer_payment_authority.verify_receipt(
        expired,
        now=datetime(2026, 10, 2, 21, 0, tzinfo=UTC),
    )["reason"] == "receipt_expired"


def test_schema_is_append_only_contract_surface():
    sql = "\n".join(sika_customer_payment_authority.SCHEMA_STATEMENTS)
    assert "oap_sika_customer_payment_authority" in sql
    assert "receipt_hash TEXT PRIMARY KEY" in sql
    assert "payment_id TEXT NOT NULL" in sql
