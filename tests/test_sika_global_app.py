from decimal import Decimal

import pytest

from mission_control import sika_global
from sika_global_app import app


def test_anchor_is_one_sika_to_one_gbp():
    quote = sika_global.quote_from_sika("25", "GBP", gbp_per_unit={})
    assert quote.local_amount == Decimal("25.00")
    assert quote.executable is False


def test_arbitrary_three_letter_currency_works_with_treasury_rate():
    quote = sika_global.quote_from_sika("10", "XYZ", gbp_per_unit={"XYZ": "0.50"})
    assert quote.local_amount == Decimal("20.00")


def test_missing_rate_fails_closed():
    with pytest.raises(sika_global.CurrencyError, match="treasury_rate_unavailable"):
        sika_global.quote_from_sika("1", "USD", gbp_per_unit={})


def test_regulated_actions_are_blocked():
    client = app.test_client()
    for path in ("/api/sika/pay", "/api/sika/card", "/api/sika/cash-out"):
        response = client.post(path)
        assert response.status_code == 423
        assert response.get_json()["money_moved"] is False


def test_app_surface_and_quote_endpoint():
    client = app.test_client()
    assert client.get("/sika").status_code == 200
    response = client.post("/api/sika/quote", json={
        "amount_sika": "100",
        "currency": "USD",
        "gbp_per_unit": {"USD": "0.80"},
    })
    assert response.status_code == 200
    assert response.get_json()["local_amount"] == "125.00"
