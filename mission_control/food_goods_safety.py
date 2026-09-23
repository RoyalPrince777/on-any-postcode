"""Draft-only food-and-goods safety review for existing OAP Post Core shipments.

This is a pure, first-party review adapter over the canonical global shipment
planner. It never verifies declarations, certifies food safety, or operates a
new catalogue, fulfilment, carrier, payment, booking or warehouse engine.
There is no database, HTTP, external integration, dispatch or persistence.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date

from .global_shipment import draft_global_shipment

_ITEM_FIELDS = frozenset({
    "category", "handling", "lot_reference", "expiry_date",
    "allergen_information_ref",
})
_FOOD_HANDLING = frozenset({"AMBIENT", "CHILLED", "FROZEN"})
_REFERENCE = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")


def _reference(value: object, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _REFERENCE.fullmatch(value):
        raise ValueError(f"invalid_{name}")
    return value


def _expiry(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("invalid_expiry_date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("invalid_expiry_date") from exc
    if parsed.isoformat() != value:
        raise ValueError("invalid_expiry_date")
    return value


def review_food_goods_distribution(
    *, parcel_id: object, owner_identity_id: object, legs: object, item: object
) -> dict[str, object]:
    """Prepare food/goods review without elevating declarations to evidence.

    Owner authentication and Post Core parcel verification remain responsibilities
    of the invoking authorised layer; this function never reads parcel records.
    """
    plan = draft_global_shipment(
        parcel_id=parcel_id, owner_identity_id=owner_identity_id, legs=legs
    )
    if not isinstance(item, Mapping):
        raise TypeError("invalid_item")
    if set(item) != _ITEM_FIELDS:
        raise ValueError("unsupported_item_fields")
    category, handling = item["category"], item["handling"]
    if type(category) is not str or category not in {"FOOD", "GOODS"}:
        raise ValueError("invalid_item_category")
    if type(handling) is not str or (
        handling not in _FOOD_HANDLING
        if category == "FOOD" else handling != "NOT_APPLICABLE"
    ):
        raise ValueError("invalid_item_handling")
    lot = _reference(item["lot_reference"], "lot_reference")
    expiry = _expiry(item["expiry_date"])
    allergens = _reference(
        item["allergen_information_ref"], "allergen_information_ref"
    )
    if category == "GOODS" and (expiry is not None or allergens is not None):
        raise ValueError("food_declarations_on_goods")

    missing = ()
    if category == "FOOD":
        missing = tuple(
            field for field, value in (
                ("lot_reference", lot),
                ("expiry_date", expiry),
                ("allergen_information_ref", allergens),
            ) if value is None
        )
    requirements = ["operator_and_restricted_goods_review"]
    if category == "FOOD":
        requirements.extend([
            "food_traceability_review", "allergen_information_review",
            "expiry_and_storage_review", "food_handling_review",
        ])
        if handling in {"CHILLED", "FROZEN"}:
            requirements.append("cold_chain_temperature_evidence")
    if plan["cross_border"]:
        requirements.append("jurisdiction_and_customs_review")
    return {
        "shipment": plan,
        "item_declaration": {
            "category": category,
            "handling": handling,
            "lot_reference": lot,
            "expiry_date": expiry,
            "allergen_information_ref": allergens,
            "source": "unverified_caller_declaration",
        },
        "missing_declarations": missing,
        "review_requirements": tuple(requirements),
        "state": "DRAFT_REVIEW_REQUIRED",
        "food_safety_verified": False,
        "lot_traceability_verified": False,
        "allergens_verified": False,
        "expiry_verified": False,
        "temperature_control_verified": False,
        "operator_verified": False,
        "customs_cleared": False,
        "inventory_reserved": False,
        "dispatch_allowed": False,
        "carrier_handoff_performed": False,
        "delivered": False,
        "payment_performed": False,
        "external_action_performed": False,
        "persisted": False,
        "human_authority_final": True,
    }
