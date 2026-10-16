"""Negative and positive draft-only Food & Goods review contract tests."""
from uuid import uuid4

import pytest

from mission_control.food_goods_safety import review_food_goods_distribution


def _legs():
    return [
        {"sequence": 1, "mode": "ROAD",
         "origin_country": "GB", "destination_country": "GB"},
    ]


def _item(**changes):
    return {
        "category": "FOOD",
        "handling": "CHILLED",
        "lot_reference": "lot-000001",
        "expiry_date": "2026-09-30",
        "allergen_information_ref": "allergen-0001",
        **changes,
    }


def _review(*, item=None, legs=None):
    return review_food_goods_distribution(
        parcel_id=uuid4(), owner_identity_id=uuid4(),
        legs=_legs() if legs is None else legs,
        item=_item() if item is None else item,
    )


def test_complete_food_declarations_never_prove_safe_or_dispatched():
    result = _review()
    assert result["shipment"]["state"] == "DRAFT"
    assert result["state"] == "DRAFT_REVIEW_REQUIRED"
    assert result["missing_declarations"] == ()
    assert "cold_chain_temperature_evidence" in result["review_requirements"]
    assert result["item_declaration"]["source"] == "unverified_caller_declaration"
    for field in (
        "food_safety_verified", "lot_traceability_verified",
        "allergens_verified", "expiry_verified",
        "temperature_control_verified", "operator_verified",
        "customs_cleared", "inventory_reserved", "dispatch_allowed",
        "carrier_handoff_performed", "delivered",
        "payment_performed", "external_action_performed", "persisted",
    ):
        assert result[field] is False
    assert result["human_authority_final"] is True


def test_missing_food_declarations_remain_visible():
    result = _review(item=_item(
        lot_reference=None, expiry_date=None, allergen_information_ref=None
    ))
    assert result["missing_declarations"] == (
        "lot_reference", "expiry_date", "allergen_information_ref"
    )
    assert result["dispatch_allowed"] is False


def test_goods_do_not_inherit_food_certification_or_need_cold_chain():
    result = _review(item=_item(
        category="GOODS", handling="NOT_APPLICABLE",
        expiry_date=None, allergen_information_ref=None
    ))
    assert "cold_chain_temperature_evidence" not in result["review_requirements"]
    assert "food_traceability_review" not in result["review_requirements"]
    assert result["dispatch_allowed"] is False


def test_cross_border_adds_review_but_never_customs_permission():
    result = _review(legs=[
        {"sequence": 1, "mode": "SEA",
         "origin_country": "GB", "destination_country": "GH"}
    ])
    assert "jurisdiction_and_customs_review" in result["review_requirements"]
    assert result["shipment"]["cross_border"] is True
    assert result["customs_cleared"] is False


@pytest.mark.parametrize("change", [
    {"dispatch_allowed": True}, {"food_safety_verified": True},
    {"temperature_control_verified": True}, {"approved": True},
    {"carrier_handoff_performed": True}, {"source": "verified"},
    {"category": "MEDICINE"}, {"category": True},
    {"handling": "CERTIFIED"}, {"handling": True},
    {"expiry_date": "2026-02-30"}, {"expiry_date": "2026-9-30"},
    {"allergen_information_ref": "x"}, {"lot_reference": []},
])
def test_untrusted_authority_and_malformed_declarations_fail_closed(change):
    with pytest.raises((ValueError, TypeError)):
        _review(item=_item(**change))


def test_goods_cannot_carry_food_only_fields():
    with pytest.raises(ValueError, match="food_declarations_on_goods"):
        _review(item=_item(category="GOODS", handling="NOT_APPLICABLE"))


def test_existing_global_shipment_validation_still_owns_route_checks():
    with pytest.raises(ValueError, match="disconnected_shipment_legs"):
        _review(legs=[
            {"sequence": 1, "mode": "ROAD",
             "origin_country": "GB", "destination_country": "GB"},
            {"sequence": 2, "mode": "SEA",
             "origin_country": "GH", "destination_country": "GB"},
        ])
