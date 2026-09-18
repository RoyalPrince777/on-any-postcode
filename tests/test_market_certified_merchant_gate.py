from __future__ import annotations

from pathlib import Path

import app as app_module
from mission_control import certification, product_store, public_store


def test_market_listing_requires_certified_merchant(client, csrf, monkeypatch):
    created = False

    monkeypatch.setattr(
        certification,
        "identity_status",
        lambda _identity_id: {"merchant": False},
    )

    def fake_create_product(*_args, **_kwargs):
        nonlocal created
        created = True
        return "product-1"

    monkeypatch.setattr(product_store, "create_product", fake_create_product)

    response = client.post(
        "/market/listings",
        data={
            "csrf_token": csrf["csrf_token"],
            "name": "OAP Tee",
            "description": "Test listing",
            "price": "10.00",
        },
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "certified_merchant_required"
    assert created is False


def test_market_listing_fails_closed_when_certification_store_is_unavailable(
    client, csrf, monkeypatch
):
    def unavailable(_identity_id):
        raise certification.CertificationUnavailable(
            "certification_read_unavailable"
        )

    monkeypatch.setattr(certification, "identity_status", unavailable)

    response = client.post(
        "/market/listings",
        data={
            "csrf_token": csrf["csrf_token"],
            "name": "OAP Tee",
            "description": "Test listing",
            "price": "10.00",
        },
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )

    assert response.status_code == 503
    assert (
        response.get_json()["error"]["code"]
        == "merchant_certification_unavailable"
    )


def test_certified_merchant_can_reach_existing_market_listing_store(
    client, csrf, monkeypatch
):
    observed = {}

    monkeypatch.setattr(
        certification,
        "identity_status",
        lambda _identity_id: {"merchant": True},
    )
    monkeypatch.setattr(
        public_store,
        "ensure_authenticated_user",
        lambda *args, **kwargs: None,
    )

    def fake_create_product(seller_id, **kwargs):
        observed["seller_id"] = seller_id
        observed.update(kwargs)
        return "product-1"

    monkeypatch.setattr(product_store, "create_product", fake_create_product)

    response = client.post(
        "/market/listings",
        data={
            "csrf_token": csrf["csrf_token"],
            "name": "OAP Tee",
            "description": "Test listing",
            "price": "10.00",
        },
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/the-spot/market")
    assert observed == {
        "seller_id": "11111111-1111-4111-8111-111111111111",
        "name": "OAP Tee",
        "description": "Test listing",
        "price": "10.00",
    }


def test_market_ui_and_truth_board_keep_checkout_locked():
    root = Path(app_module.app.root_path)
    template = (
        root / "mission_control" / "templates" / "spot_capability.html"
    ).read_text(encoding="utf-8")
    products_source = (
        root / "mission_control" / "products.py"
    ).read_text(encoding="utf-8")

    assert "Certified Merchant required" in template
    assert "merchant_certified" in template
    assert "regulated payment capture remain separately locked" in template
    assert "Certified Merchant publishing gate connected" in products_source
    assert "Checkout still requires a compliant regulated payment route" in products_source
