"""Warehouse and transfer-readiness review extending OAP Post Core.

Warehouse inventory and physical custody remain owned by verified operators.
This module does not reserve space, activate a site, change parcel state or
attest real carrier handoff. No database, network, payment or dispatch I/O.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from .global_transport_recovery import _plan

_ALLOWED_HUB = frozenset({
    "hub_id", "country", "state", "capacity_units",
    "occupied_units", "operator_review_state",
})
_ALLOWED_TRANSFER = frozenset({
    "leg_sequence", "from_hub_id", "to_hub_id",
    "reported_receipt", "evidence_review_state",
})
_STATES = frozenset({"PLANNED", "REVIEW_REQUIRED", "SUSPENDED", "CLOSED"})
_REVIEWS = frozenset({"UNKNOWN", "REQUIRED", "PENDING", "REVIEWED", "REJECTED"})


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def review_warehouse(*, plan: object, hubs: object, transfers: object) -> dict[str, object]:
    """Review warehouse declarations; no custody or capacity attestation."""
    legs = _plan(plan)
    if isinstance(hubs, (str, bytes)) or not isinstance(hubs, Sequence):
        raise TypeError("invalid_hubs")
    if not 1 <= len(hubs) <= 32:
        raise ValueError("invalid_hub_count")
    known: dict[str, dict[str, object]] = {}
    hub_reviews: list[dict[str, object]] = []
    for hub in hubs:
        if not isinstance(hub, Mapping):
            raise TypeError("invalid_hub")
        if set(hub) != _ALLOWED_HUB:
            raise ValueError("unsupported_hub_fields")
        ident = _uuid(hub["hub_id"], "hub_id")
        if ident in known:
            raise ValueError("duplicate_hub")
        country = hub["country"]
        if (
            not isinstance(country, str) or len(country) != 2
            or not country.isascii() or not country.isalpha()
            or not country.isupper()
        ):
            raise ValueError("invalid_hub_country")
        capacity, occupied = hub["capacity_units"], hub["occupied_units"]
        if (
            type(capacity) is not int or type(occupied) is not int
            or not 0 <= occupied <= capacity <= 1000000
        ):
            raise ValueError("invalid_hub_capacity")
        if hub["state"] not in _STATES or hub["operator_review_state"] not in _REVIEWS:
            raise ValueError("invalid_hub_review")
        known[ident] = {"country": country, "state": hub["state"]}
        hub_reviews.append({
            "hub_id": ident,
            "declared_free_units": capacity - occupied,
            "physical_site_verified": False,
            "capacity_reserved": False,
            "operator_certified": False,
        })
    if isinstance(transfers, (str, bytes)) or not isinstance(transfers, Sequence):
        raise TypeError("invalid_transfers")
    if len(transfers) > 32:
        raise ValueError("too_many_transfers")
    transfer_reviews: list[dict[str, object]] = []
    for transfer in transfers:
        if not isinstance(transfer, Mapping):
            raise TypeError("invalid_transfer")
        if set(transfer) != _ALLOWED_TRANSFER:
            raise ValueError("unsupported_transfer_fields")
        number = transfer["leg_sequence"]
        if type(number) is not int or not 1 <= number <= len(legs):
            raise ValueError("invalid_transfer_leg")
        source = _uuid(transfer["from_hub_id"], "from_hub_id")
        destination = _uuid(transfer["to_hub_id"], "to_hub_id")
        if source == destination or source not in known or destination not in known:
            raise ValueError("invalid_transfer_hubs")
        if (
            known[source]["country"] != legs[number - 1]["origin_country"]
            or known[destination]["country"] != legs[number - 1]["destination_country"]
        ):
            raise ValueError("transfer_country_mismatch")
        if type(transfer["reported_receipt"]) is not bool:
            raise ValueError("invalid_reported_receipt")
        if transfer["evidence_review_state"] not in _REVIEWS:
            raise ValueError("invalid_transfer_review")
        transfer_reviews.append({
            "leg_sequence": number, "from_hub_id": source,
            "to_hub_id": destination,
            "custody_verified": False, "carrier_handoff_performed": False,
        })
    return {
        "hubs": hub_reviews, "transfers": transfer_reviews,
        "warehouse_capacity_verified": False,
        "inventory_reserved": False,
        "physical_sites_activated": False,
        "custody_verified": False,
        "external_action_performed": False,
        "persisted": False,
    }
