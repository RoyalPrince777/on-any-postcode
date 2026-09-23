"""Draft-only global shipment leg contract extending OAP Post Core.

No database, carrier, dispatch, customs, tracking, payment or external I/O.
The authoritative parcel remains oap_post_office_parcels; plans never change it.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from uuid import UUID

_MODES = frozenset({"ROAD", "RAIL", "SEA", "AIR", "WALK", "CYCLE"})
_COUNTRY = re.compile(r"^[A-Z]{2}$")
_ALLOWED_FIELDS = frozenset({"sequence", "mode", "origin_country", "destination_country"})
_BLOCKED = frozenset({
    "carrier_id", "vehicle_id", "booking_id", "dispatch", "payment",
    "customs_cleared", "handoff", "tracking", "operator_certified",
    "delivered", "approved", "executed", "external_reference",
})


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _country(value: object, name: str) -> str:
    if not isinstance(value, str) or not _COUNTRY.fullmatch(value):
        raise ValueError(f"invalid_{name}")
    return value


def draft_global_shipment(
    *, parcel_id: object, owner_identity_id: object, legs: object
) -> dict[str, object]:
    """Validate a bounded plan; never imply the parcel or a carrier was verified.

    Caller must separately enforce owner access before exposing or persisting
    the plan. No read of OAP Post Core is attempted by this pure function.
    """
    parcel = _uuid(parcel_id, "parcel_id")
    owner = _uuid(owner_identity_id, "owner_identity_id")
    if isinstance(legs, (str, bytes)) or not isinstance(legs, Sequence):
        raise ValueError("invalid_legs")
    if not 1 <= len(legs) <= 16:
        raise ValueError("invalid_leg_count")
    clean: list[dict[str, object]] = []
    for index, raw in enumerate(legs, start=1):
        if not isinstance(raw, Mapping):
            raise ValueError("invalid_leg")
        if set(raw) & _BLOCKED or set(raw) != _ALLOWED_FIELDS:
            raise ValueError("unsupported_leg_fields")
        sequence = raw["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence != index:
            raise ValueError("invalid_leg_sequence")
        mode = raw["mode"]
        if not isinstance(mode, str) or mode not in _MODES:
            raise ValueError("invalid_transport_mode")
        origin = _country(raw["origin_country"], "origin_country")
        destination = _country(raw["destination_country"], "destination_country")
        if clean and clean[-1]["destination_country"] != origin:
            raise ValueError("disconnected_shipment_legs")
        clean.append({
            "sequence": index,
            "mode": mode,
            "origin_country": origin,
            "destination_country": destination,
            "state": "DRAFT",
        })
    return {
        "parcel_id": parcel,
        "owner_identity_id": owner,
        "state": "DRAFT",
        "legs": clean,
        "cross_border": any(
            leg["origin_country"] != leg["destination_country"] for leg in clean
        ),
        "parcel_ownership_verified": False,
        "carrier_eligibility_verified": False,
        "customs_ready": False,
        "capacity_verified": False,
        "external_action_performed": False,
        "carrier_handoff_performed": False,
        "dispatch_performed": False,
        "payment_performed": False,
        "tracking_enabled": False,
        "persisted": False,
        "human_authority_final": True,
    }
