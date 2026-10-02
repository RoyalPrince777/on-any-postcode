from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import music_market_purchase


def test_schema_binds_music_market_order_entitlement_and_split_ledger():
    sql = "\n".join(music_market_purchase.SCHEMA_STATEMENTS)

    assert "oap_music_market_products" in sql
    assert "REFERENCES oap_music_releases(release_id)" in sql
    assert "REFERENCES products(id)" in sql
    assert "REFERENCES oap_music_evidence_receipts(receipt_id)" in sql
    assert "minimum_price_minor >= 100" in sql
    assert "oap_music_purchase_entitlements" in sql
    assert "REFERENCES oap_commerce_orders(order_id)" in sql
    assert "UNIQUE(buyer_identity_id,release_id)" in sql
    assert "oap_music_purchase_splits" in sql
    assert "PAYOUT_PROVIDER_REQUIRED" in sql


def test_split_plan_requires_exact_100_percent_and_allocation_is_exact():
    plan = music_market_purchase._split_plan(
        [
            {
                "beneficiary_identity_id": "11111111-1111-1111-1111-111111111111",
                "split_kind": "ARTIST",
                "basis_points": 8500,
            },
            {
                "beneficiary_identity_id": "22222222-2222-2222-2222-222222222222",
                "split_kind": "OAP",
                "basis_points": 1500,
            },
        ]
    )
    allocation = music_market_purchase._allocate(101, plan)

    assert sum(row["amount_minor"] for row in allocation) == 101
    assert allocation[0]["amount_minor"] == 85
    assert allocation[1]["amount_minor"] == 16

    with pytest.raises(
        ValueError, match="split_plan_must_total_10000_basis_points"
    ):
        music_market_purchase._split_plan(
            [
                {
                    "beneficiary_identity_id": "11111111-1111-1111-1111-111111111111",
                    "split_kind": "ARTIST",
                    "basis_points": 9000,
                }
            ]
        )


def test_purchase_spine_does_not_capture_or_pay_money():
    source = Path(music_market_purchase.__file__).read_text(encoding="utf-8")

    assert "payment_not_captured" in source
    assert '"payment_capture_performed_here": False' in source
    assert '"payout_performed": False' in source
    assert '"split_state": "PAYOUT_PROVIDER_REQUIRED"' in source


def test_music_market_routes_are_canonical_and_separate_from_supplier_gate():
    source = (
        Path(__file__).resolve().parents[1]
        / "mission_control"
        / "product_core_views.py"
    ).read_text(encoding="utf-8")

    assert '@bp.post("/market/music-products")' in source
    assert '@bp.post("/market/music-orders")' in source
    assert '@bp.post("/market/music-orders/<order_id>/finalize")' in source
    assert '@bp.get("/tune/library/purchases")' in source
    assert '@bp.get("/market/music-entitlements/<entitlement_id>/splits")' in source
    music_order = source.split('def create_music_market_order():', 1)[1].split(
        '@bp.post("/market/music-orders/<order_id>/finalize")', 1
    )[0]
    assert "market_supplier_network.STORE.order_intent_allowed" not in music_order
    assert "_store.create_order_intent(" in music_order
    assert "unit_price_override_minor=override" in music_order
    assert "quantity=1" in music_order


def test_pay_more_extension_never_allows_discount_below_listing_price():
    source = (
        Path(__file__).resolve().parents[1]
        / "mission_control"
        / "product_cores.py"
    ).read_text(encoding="utf-8")
    order = source.split("def create_order_intent(", 1)[1].split(
        "def create_post_office_request(", 1
    )[0]

    assert "unit_price_override_below_listing_price" in order
    assert "unit_price = base_unit_price" in order
    assert "subtotal = unit_price * qty" in order
