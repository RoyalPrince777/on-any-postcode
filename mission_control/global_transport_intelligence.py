"""Fail-closed OAP Global Transport intelligence, never an operating carrier.

Extends the existing draft_global_shipment contract without replacing OAP Post
Core parcels, Movement matching, Supply reservations or SIKA. These functions
have no database, network, dispatch, tracking, payment or customs side effects.
All third-party, physical and financial actions remain unavailable.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from uuid import UUID

from .global_shipment import draft_global_shipment

_COUNTRY = re.compile(r"^[A-Z]{2}$")
_MODES = frozenset({"ROAD", "RAIL", "SEA", "AIR", "WALK", "CYCLE"})
_CAPABILITIES = frozenset({"CARGO", "PASSENGER", "COURIER", "WAREHOUSE"})
_ALLOWED_OPERATOR = frozenset({
    "operator_id", "country", "modes", "capabilities",
    "certification_state", "insurance_state", "capacity_state",
})
_ALLOWED_EVENT = frozenset({
    "sequence", "leg_sequence", "kind", "evidence_ref", "occurred_at",
})
_EVENTS = frozenset({
    "COLLECTION_REPORTED", "HUB_RECEIPT_REPORTED", "TRANSFER_REPORTED",
    "DELIVERY_REPORTED", "RETURN_REPORTED", "LOSS_REPORTED",
    "DAMAGE_REPORTED", "EXCEPTION_REPORTED",
})
_BLOCKED_EVENT = frozenset({"CUSTOMS_CLEARED", "PAYMENT_CAPTURED", "DISPATCHED"})
_ALLOWED_READINESS = frozenset({
    "document_review", "jurisdiction_review", "operator_review",
    "restricted_goods_review", "recipient_review",
})
_REVIEW_STATES = frozenset({"REQUIRED", "PENDING", "REJECTED", "REVIEWED"})
_EVIDENCE = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _country(value: object) -> str:
    if not isinstance(value, str) or not _COUNTRY.fullmatch(value):
        raise ValueError("invalid_country")
    return value


def _timestamp(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("invalid_event_timestamp")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_event_timestamp") from exc
    if stamp.tzinfo is None:
        raise ValueError("invalid_event_timestamp")
    return stamp.astimezone(UTC).isoformat()


def assess_operator(*, record: object, mode: str, country: str) -> dict[str, object]:
    """Advisory evidence review. An operator can never be certified by input."""
    if not isinstance(record, Mapping):
        raise TypeError("invalid_operator")
    if set(record) != _ALLOWED_OPERATOR:
        raise ValueError("unsupported_operator_fields")
    operator = _uuid(record["operator_id"], "operator_id")
    target_country = _country(country)
    record_country = _country(record["country"])
    if mode not in _MODES:
        raise ValueError("invalid_transport_mode")
    modes = record["modes"]
    capabilities = record["capabilities"]
    if (
        not isinstance(modes, (list, tuple))
        or not modes or len(modes) > len(_MODES)
        or any(not isinstance(item, str) or item not in _MODES for item in modes)
        or len(modes) != len(set(modes))
    ):
        raise ValueError("invalid_operator_modes")
    if (
        not isinstance(capabilities, (list, tuple))
        or not capabilities or len(capabilities) > len(_CAPABILITIES)
        or any(not isinstance(item, str) or item not in _CAPABILITIES for item in capabilities)
        or len(capabilities) != len(set(capabilities))
    ):
        raise ValueError("invalid_operator_capabilities")
    if record["certification_state"] not in _REVIEW_STATES:
        raise ValueError("invalid_certification_state")
    if record["insurance_state"] not in _REVIEW_STATES:
        raise ValueError("invalid_insurance_state")
    if record["capacity_state"] not in _REVIEW_STATES:
        raise ValueError("invalid_capacity_state")
    in_scope = (
        record_country == target_country and mode in modes and "CARGO" in capabilities
    )
    return {
        "operator_id": operator,
        "in_declared_scope": in_scope,
        "review_required": True,
        "certified_for_assignment": False,
        "capacity_verified": False,
        "dispatch_allowed": False,
        "physical_asset_owned_by_oap": False,
    }


def assess_cross_border(*, plan: object, reviews: object) -> dict[str, object]:
    """Review-only documents; REVIEWED does not mean legally customs-cleared."""
    if not isinstance(plan, Mapping) or plan.get("state") != "DRAFT":
        raise ValueError("draft_shipment_required")
    legs = plan.get("legs")
    if not isinstance(legs, list) or not legs:
        raise ValueError("draft_legs_required")
    if not isinstance(reviews, Mapping) or set(reviews) != _ALLOWED_READINESS:
        raise ValueError("invalid_review_fields")
    if any(value not in _REVIEW_STATES for value in reviews.values()):
        raise ValueError("invalid_review_state")
    border = any(
        isinstance(leg, Mapping) and leg.get("origin_country") != leg.get("destination_country")
        for leg in legs
    )
    return {
        "cross_border": border,
        "review_complete": all(value == "REVIEWED" for value in reviews.values()),
        "customs_cleared": False,
        "import_export_authorised": False,
        "carrier_handoff_allowed": False,
        "payment_allowed": False,
    }


def review_custody(*, plan: object, events: object) -> dict[str, object]:
    """Bounded evidence ledger projection, NOT a proof-of-delivery writer."""
    if not isinstance(plan, Mapping) or plan.get("state") != "DRAFT":
        raise ValueError("draft_shipment_required")
    legs = plan.get("legs")
    if not isinstance(legs, list) or not 1 <= len(legs) <= 16:
        raise ValueError("draft_legs_required")
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise TypeError("invalid_events")
    if len(events) > 64:
        raise ValueError("too_many_events")
    reviewed = []
    previous_time = ""
    for index, event in enumerate(events, start=1):
        if not isinstance(event, Mapping):
            raise TypeError("invalid_event")
        if set(event) != _ALLOWED_EVENT:
            raise ValueError("unsupported_event_fields")
        kind = event["kind"]
        if kind in _BLOCKED_EVENT or kind not in _EVENTS:
            raise ValueError("unsupported_event_kind")
        if type(event["sequence"]) is not int or event["sequence"] != index:
            raise ValueError("invalid_event_sequence")
        number = event["leg_sequence"]
        if type(number) is not int or not 1 <= number <= len(legs):
            raise ValueError("invalid_event_leg")
        evidence = event["evidence_ref"]
        if not isinstance(evidence, str) or not _EVIDENCE.fullmatch(evidence):
            raise ValueError("invalid_evidence_ref")
        observed = _timestamp(event["occurred_at"])
        if previous_time and observed < previous_time:
            raise ValueError("out_of_order_event_time")
        previous_time = observed
        reviewed.append({
            "sequence": index, "leg_sequence": number,
            "kind": kind, "evidence_ref": evidence, "occurred_at": observed,
            "verified": False,
        })
    return {
        "parcel_id": _uuid(plan.get("parcel_id"), "parcel_id"),
        "reviewed_events": reviewed,
        "evidence_count": len(reviewed),
        "custody_verified": False,
        "delivered": False,
        "claim_settled": False,
        "carrier_handoff_performed": False,
        "external_action_performed": False,
        "persisted": False,
    }


def assess_global_transport(
    *, parcel_id: object, owner_identity_id: object, legs: object,
    operator: object, reviews: object, events: object,
) -> dict[str, object]:
    """Combine three independent draft reviews without promoting proof."""
    plan = draft_global_shipment(
        parcel_id=parcel_id, owner_identity_id=owner_identity_id, legs=legs
    )
    first = plan["legs"][0]
    operator_review = assess_operator(
        record=operator, mode=first["mode"], country=first["origin_country"]
    )
    customs_review = assess_cross_border(plan=plan, reviews=reviews)
    custody_review = review_custody(plan=plan, events=events)
    return {
        "shipment": plan,
        "operator_review": operator_review,
        "cross_border_review": customs_review,
        "custody_review": custody_review,
        "execution_authorised": False,
        "first_party_intelligence": True,
        "post_core_authoritative": True,
    }
