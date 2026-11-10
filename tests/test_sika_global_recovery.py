from decimal import Decimal

import pytest

from mission_control import sika_global


def test_anchor_is_one_sika_to_one_gbp():
    quote = sika_global.quote_from_sika("25", "GBP", gbp_per_unit={})
    assert quote.local_amount == Decimal("25.00")
    assert quote.executable is False


def test_explicit_treasury_rate_produces_read_only_quote():
    quote = sika_global.quote_from_sika(
        "10",
        "XYZ",
        gbp_per_unit={"XYZ": "0.50"},
        rate_source="founder-approved-test-snapshot",
    )
    assert quote.local_amount == Decimal("20.00")
    assert quote.rate_source == "founder-approved-test-snapshot"
    assert quote.executable is False


def test_missing_rate_fails_closed():
    with pytest.raises(sika_global.CurrencyError, match="treasury_rate_unavailable"):
        sika_global.quote_from_sika("1", "USD", gbp_per_unit={})


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_amount_is_rejected(amount):
    with pytest.raises(sika_global.CurrencyError, match="amount_must_be_finite"):
        sika_global.quote_from_sika(amount, "GBP", gbp_per_unit={})


@pytest.mark.parametrize("rate", ["NaN", "Infinity", "-Infinity", "0", "-1"])
def test_invalid_treasury_rate_is_rejected(rate):
    message = (
        "treasury_rate_must_be_finite"
        if rate in {"NaN", "Infinity", "-Infinity"}
        else "treasury_rate_must_be_positive"
    )
    with pytest.raises(sika_global.CurrencyError, match=message):
        sika_global.quote_from_sika(
            "1",
            "USD",
            gbp_per_unit={"USD": rate},
            rate_source="test",
        )


def test_status_keeps_legal_provider_execution_separate_from_sika_core():
    status = sika_global.status()
    assert status["canonical_unit"] == "SIKA"
    assert status["anchor"]["target"] == "1 SIKA = 1 GBP"
    assert status["provider_adapter_required"] is True
    assert status["provider_authority_evidence_required"] is True
    assert status["settlement_receipt_required"] is True
    assert status["regulated_execution_enabled"] is False
    assert status["customer_funds_enabled"] is False
