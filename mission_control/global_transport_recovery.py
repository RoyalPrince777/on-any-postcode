"""Review-only global transport capacity and exception contracts.

No booked capacity, inventory mutation, carrier award, refund, or physical action.
OAP Post Core remains authoritative for parcels and fulfilment.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from .global_shipment import draft_global_shipment

_MODES = frozenset({"ROAD", "RAIL", "SEA", "AIR", "WALK", "CYCLE"})
_EXCEPTION_TYPES = frozenset({
    "MISSED_COLLECTION", "DELAY", "CARRIER_UNAVAILABLE", "DAMAGED",
    "MISSING", "CUSTOMS_HOLD", "DELIVERY_FAILED", "RETURN_REQUESTED",
})
_STATES = frozenset({"UNKNOWN", "REPORTED", "REVIEW_REQUIRED", "REVIEWED"})
_CAPACITY_FIELDS = frozenset({
    "leg_sequence", "mode", "available_units", "reserved_units",
    "source_state", "operator_reviewed",
})
_EXCEPTION_FIELDS = frozenset({
    "leg_sequence", "kind", "evidence_state", "review_state",
})


def _plan(plan: object) -> list[Mapping[str, object]]:
    if not isinstance(plan, Mapping) or plan.get("state") != "DRAFT":
        raise ValueError("draft_shipment_required")
    # Revalidate the actual contract, not merely a caller-supplied DRAFT label.
    original_legs = plan.get("legs")
    if not isinstance(original_legs, list):
        raise ValueError("draft_legs_required")
    proposed: list[dict[str, object]] = []
    for leg in original_legs:
        if not isinstance(leg, Mapping):
            raise TypeError("invalid_leg")
        if set(leg) != {
            "sequence", "mode", "origin_country", "destination_country", "state"
        } or leg["state"] != "DRAFT":
            raise ValueError("invalid_draft_leg")
        proposed.append({
            "sequence": leg["sequence"], "mode": leg["mode"],
            "origin_country": leg["origin_country"],
            "destination_country": leg["destination_country"],
        })
    validated = draft_global_shipment(
        parcel_id=plan.get("parcel_id"),
        owner_identity_id=plan.get("owner_identity_id"),
        legs=proposed,
    )
    if plan.get("legs") != validated["legs"]:
        raise ValueError("invalid_draft_leg")
    return validated["legs"]


def review_capacity(*, plan: object, records: object) -> dict[str, object]:
    """Treat reported quantities as declarations; never reserve them."""
    legs = _plan(plan)
    if not isinstance(records, (list, tuple)):
        raise TypeError("invalid_capacity_records")
    if len(records) != len(legs):
        raise ValueError("missing_capacity_legs")
    reviewed: list[dict[str, object]] = []
    for index, (leg, raw) in enumerate(zip(legs, records, strict=True), start=1):
        if not isinstance(raw, Mapping):
            raise TypeError("invalid_capacity_record")
        if set(raw) != _CAPACITY_FIELDS:
            raise ValueError("unsupported_capacity_fields")
        if type(raw["leg_sequence"]) is not int or raw["leg_sequence"] != index:
            raise ValueError("invalid_leg_sequence")
        if raw["mode"] != leg["mode"] or raw["mode"] not in _MODES:
            raise ValueError("capacity_mode_mismatch")
        available = raw["available_units"]
        reserved = raw["reserved_units"]
        if (
            type(available) is not int or type(reserved) is not int
            or not 0 <= available <= 1000000 or not 0 <= reserved <= available
        ):
            raise ValueError("invalid_capacity_units")
        if raw["source_state"] not in _STATES or type(raw["operator_reviewed"]) is not bool:
            raise ValueError("invalid_capacity_review")
        reviewed.append({
            "leg_sequence": index,
            "declared_remaining_units": available - reserved,
            "source_reviewed": raw["source_state"] == "REVIEWED",
            "operator_reviewed": raw["operator_reviewed"],
            "capacity_verified": False,
            "capacity_reserved": False,
        })
    return {
        "legs": reviewed,
        "capacity_verified": False,
        "capacity_reserved": False,
        "carrier_assigned": False,
        "external_action_performed": False,
    }


def review_exceptions(*, plan: object, reports: object) -> dict[str, object]:
    """Classify bounded failure reports without changing parcel state or claims."""
    legs = _plan(plan)
    if isinstance(reports, (str, bytes)) or not isinstance(reports, Sequence):
        raise TypeError("invalid_exception_reports")
    if len(reports) > 32:
        raise ValueError("too_many_exception_reports")
    reviewed: list[dict[str, object]] = []
    for raw in reports:
        if not isinstance(raw, Mapping):
            raise TypeError("invalid_exception_report")
        if set(raw) != _EXCEPTION_FIELDS:
            raise ValueError("unsupported_exception_fields")
        number = raw["leg_sequence"]
        if type(number) is not int or not 1 <= number <= len(legs):
            raise ValueError("invalid_exception_leg")
        if raw["kind"] not in _EXCEPTION_TYPES:
            raise ValueError("invalid_exception_kind")
        if raw["evidence_state"] not in _STATES or raw["review_state"] not in _STATES:
            raise ValueError("invalid_exception_state")
        reviewed.append({
            "leg_sequence": number, "kind": raw["kind"],
            "review_required": True, "resolved": False,
        })
    return {
        "exceptions": reviewed,
        "recovery_execution_allowed": False,
        "refund_authorised": False,
        "claim_settled": False,
        "parcel_state_changed": False,
        "external_action_performed": False,
    }
