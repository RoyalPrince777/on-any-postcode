"""Cash service-point intents cannot be mistaken for real cash transactions."""
import pytest

from mission_control import sika_cash_service_point as cash


def _assess(**changes):
    args = {
        "intent_id": "cash-001",
        "service_point_id": "point-001",
        "operator_id": "staff-001",
        "customer_reference": "customer-001",
        "amount": "10.00",
        "currency": "GBP",
        "direction": "CASH_IN",
        "staff_authorised": True,
        "site_verified": True,
        "regulated_cash_authority_proven": True,
    }
    return cash.assess_intent(**{**args, **changes})


@pytest.mark.parametrize("direction", ["CASH_IN", "CASH_OUT"])
def test_approved_intent_remains_non_executing(direction):
    result = _assess(direction=direction)
    assert result["intent_validated"] is True
    assert result["direction"] == direction
    assert result["amount"] == "10.00"
    for flag in ("cash_execution_enabled", "cash_received", "cash_dispensed",
                 "ledger_posted", "funds_moved", "receipt_issued"):
        assert result[flag] is False


@pytest.mark.parametrize("bad", ["0", "-1", "0.001", "1.005", "NaN", "Infinity", "1e100", ""])
def test_unsafe_amount_rejected(bad):
    with pytest.raises(cash.CashServicePointError, match="cash_amount_invalid"):
        _assess(amount=bad)


@pytest.mark.parametrize("changes,error", [
    ({"staff_authorised": False}, "cash_staff_authority_missing"),
    ({"site_verified": False}, "cash_site_unverified"),
    ({"regulated_cash_authority_proven": False}, "cash_regulatory_authority_missing"),
    ({"direction": "TRANSFER"}, "cash_direction_invalid"),
    ({"currency": "USD"}, "cash_currency_unsupported"),
    ({"service_point_id": ""}, "service_point_id_required"),
])
def test_absent_authority_or_invalid_request_denied(changes, error):
    with pytest.raises(cash.CashServicePointError, match=error):
        _assess(**changes)


def test_status_stays_off_even_with_validation_available():
    status = cash.status()
    assert status["cash_intent_validation_available"] is True
    for field in ("cash_in_enabled", "cash_out_enabled", "ledger_posting_enabled",
                  "service_point_registration_enabled"):
        assert status[field] is False
