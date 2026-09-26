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


def test_wallet_reference_ledger_is_owner_scoped_and_non_executable():
    client = app.test_client()
    created = client.post("/api/sika/ledger/reference", json={
        "owner_id": "owner-a",
        "kind": "credit_reference",
        "amount_sika": "12.50",
        "memo": "software reference only",
    })
    assert created.status_code == 201
    assert created.get_json()["money_moved"] is False
    wallet_a = client.get("/api/sika/wallet?owner_id=owner-a").get_json()
    wallet_b = client.get("/api/sika/wallet?owner_id=owner-b").get_json()
    assert wallet_a["balance_reference"] == "12.50"
    assert wallet_b["balance_reference"] == "0.00"
    assert wallet_a["executable"] is False


def test_treasury_rate_snapshot_can_feed_quote_without_external_provider():
    client = app.test_client()
    saved = client.post("/api/sika/treasury/rates", json={
        "currency": "EUR",
        "gbp_per_unit": "0.85",
        "source": "founder-approved-test-snapshot",
    })
    assert saved.status_code == 201
    response = client.post("/api/sika/quote", json={
        "amount_sika": "85",
        "currency": "EUR",
    })
    assert response.status_code == 200
    body = response.get_json()
    assert body["local_amount"] == "100.00"
    assert body["executable"] is False


def test_treasury_rate_requires_source_and_positive_value():
    client = app.test_client()
    assert client.post("/api/sika/treasury/rates", json={
        "currency": "USD",
        "gbp_per_unit": "0",
        "source": "test",
    }).status_code == 400
    assert client.post("/api/sika/treasury/rates", json={
        "currency": "USD",
        "gbp_per_unit": "0.75",
        "source": "",
    }).status_code == 400
