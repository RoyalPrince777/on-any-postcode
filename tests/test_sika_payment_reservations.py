import pytest

from mission_control import sika_payment_reservations


def test_reservation_schema_is_durable_and_unique_per_payment():
    sql = "\n".join(sika_payment_reservations.SCHEMA_STATEMENTS)
    assert "payment_id TEXT NOT NULL UNIQUE" in sql
    assert "status IN ('ACTIVE','RELEASED','CONSUMED')" in sql
    assert "payer_account_id TEXT NOT NULL" in sql


def test_reservation_schema_init_requires_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        sika_payment_reservations.init_schema()


def test_reservation_model_tracks_active_state():
    hold = sika_payment_reservations.PaymentHold(
        hold_id="hold-1",
        payment_id="pay-1",
        payer_account_id="acct-1",
        amount=sika_payment_reservations.Decimal("12.00"),
        currency="GBP",
        status="ACTIVE",
    )
    assert hold.active is True
    assert hold.as_dict()["amount"] == "12.00"


def test_reservation_status_is_non_executing():
    status = sika_payment_reservations.status()
    assert status["persistent_holds"] is True
    assert status["payment_id_unique"] is True
    assert status["provider_calling"] is False
    assert status["money_movement"] is False
