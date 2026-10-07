from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import founder_private_commerce


def _product(**overrides):
    product = {
        "product_id": "11111111-1111-1111-1111-111111111111",
        "private_owner_view": True,
        "supplier_state": "READY",
        "design_state": "READY",
        "supplier_label": "Prodigi",
        "supplier_product_ref": "prodigi-sku-1",
        "supplier_variant_ref": "variant-a",
        "artwork_reference": "oap://artwork/1",
        "garment_type": "t-shirt",
        "placements": ["front"],
        "colors": ["Black", "Gold"],
        "sizes": ["M", "L"],
        "public_listing_active": False,
    }
    product.update(overrides)
    return product


def test_private_plan_does_not_require_public_listing():
    plan = founder_private_commerce.private_fulfilment_plan(
        product=_product(),
        quantity=2,
        color="Black",
        size="M",
        destination_country="GB",
    )

    assert plan["scope"] == "founder_private"
    assert plan["provider_id"] == "prodigi"
    assert plan["private_plan_ready"] is True
    assert plan["public_listing_required"] is False
    assert plan["public_merchant_access"] is False
    assert plan["provider_payload_mapping_ready"] is False
    assert plan["provider_execution_allowed"] is False
    assert plan["external_order_created"] is False


def test_private_plan_rejects_unready_supplier():
    with pytest.raises(
        founder_private_commerce.FounderPrivateCommerceError,
        match="private_supplier_not_ready",
    ):
        founder_private_commerce.private_fulfilment_plan(
            product=_product(supplier_state="DRAFT"),
            quantity=1,
            color="Black",
            size="M",
            destination_country="GB",
        )


def test_private_plan_rejects_unknown_variant_choice():
    with pytest.raises(
        founder_private_commerce.FounderPrivateCommerceError,
        match="private_size_not_available",
    ):
        founder_private_commerce.private_fulfilment_plan(
            product=_product(),
            quantity=1,
            color="Black",
            size="XXXL",
            destination_country="GB",
        )


def test_tapstitch_private_execution_plan_stays_fail_closed():
    with pytest.raises(
        founder_private_commerce.FounderPrivateCommerceError,
        match="tapstitch_direct_api_contract_unproven",
    ):
        founder_private_commerce.private_fulfilment_plan(
            product=_product(supplier_label="Tapstitch"),
            quantity=1,
            color="Black",
            size="M",
            destination_country="GB",
        )


def test_reconciliation_normalizes_without_automatic_consequence():
    result = founder_private_commerce.reconcile_provider_state(
        provider_id="printful",
        provider_state="failed",
    )

    assert result["canonical_state"] == "RECOVERY_REQUIRED"
    assert result["recovery_required"] is True
    assert result["automatic_public_effect"] is False
    assert result["automatic_refund_performed"] is False
    assert result["automatic_reprint_performed"] is False


def test_unknown_provider_state_requires_review():
    result = founder_private_commerce.reconcile_provider_state(
        provider_id="prodigi",
        provider_state="mystery-state",
    )

    assert result["canonical_state"] == "REVIEW_REQUIRED"
    assert result["recovery_required"] is True


def test_private_analytics_excludes_customer_and_secret_data():
    result = founder_private_commerce.private_catalogue_analytics([
        _product(),
        _product(
            product_id="22222222-2222-2222-2222-222222222222",
            supplier_state="DRAFT",
            public_listing_active=True,
        ),
    ])

    assert result["product_count"] == 2
    assert result["private_ready_count"] == 1
    assert result["public_active_count"] == 1
    assert result["private_only_count"] == 1
    assert result["customer_data_included"] is False
    assert result["provider_secrets_included"] is False
    assert result["external_execution_performed"] is False


def test_status_keeps_public_and_external_execution_closed():
    status = founder_private_commerce.status()

    assert status["founder_private_only"] is True
    assert status["canonical_order_mapping"] is True
    assert status["private_supplier_routing"] is True
    assert status["public_merchant_access"] is False
    assert status["public_seller_launch"] is False
    assert status["external_execution_enabled_here"] is False


def test_private_routes_are_founder_only():
    source = (
        Path(founder_private_commerce.__file__).parent / "product_core_views.py"
    ).read_text(encoding="utf-8")

    for route in (
        '/market/pod/private/status',
        '/market/pod/private/analytics',
        '/market/pod/private/plan',
        '/market/pod/private/reconcile',
    ):
        marker = f'@bp.'
        position = source.index(route)
        decorator_window = source[max(0, position - 220):position + 220]
        assert marker in decorator_window
        assert "founder_only=True" in decorator_window
