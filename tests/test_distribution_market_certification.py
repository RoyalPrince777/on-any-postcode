from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import certification, product_core_views, product_cores


def test_market_publish_guard_requires_certified_merchant(monkeypatch):
    monkeypatch.setattr(
        certification,
        "identity_status",
        lambda _identity_id: {"merchant": False},
    )
    with pytest.raises(PermissionError, match="certified_merchant_required"):
        product_core_views._require_certified_merchant(
            "00000000-0000-0000-0000-000000000258"
        )


def test_market_publish_guard_fails_closed_when_certification_store_unavailable(monkeypatch):
    def unavailable(_identity_id):
        raise certification.CertificationUnavailable("certification_read_unavailable")

    monkeypatch.setattr(certification, "identity_status", unavailable)
    with pytest.raises(RuntimeError, match="merchant_certification_unavailable"):
        product_core_views._require_certified_merchant(
            "00000000-0000-0000-0000-000000000258"
        )


def test_market_publish_routes_call_certified_merchant_guard():
    source = Path(product_core_views.__file__).read_text(encoding="utf-8")
    storefront = source.split("def create_storefront():", 1)[1].split(
        "def create_product():", 1
    )[0]
    product = source.split("def create_product():", 1)[1].split(
        "def create_order():", 1
    )[0]
    assert "_require_certified_merchant(_identity(sync=True))" in storefront
    assert "_require_certified_merchant(_identity(sync=True))" in product


def test_order_intent_requires_active_certified_merchant_in_sql():
    source = Path(product_cores.__file__).read_text(encoding="utf-8")
    section = source.split("def create_order_intent(", 1)[1].split(
        "def create_parcel_intent(", 1
    )[0]
    assert "JOIN oap_identities oi" in section
    assert "oi.status='ACTIVE'" in section
    assert "JOIN oap_identity_roles merchant" in section
    assert "merchant.role_id='certified_merchant'" in section
