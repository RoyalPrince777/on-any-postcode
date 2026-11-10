"""Mode-aware OAP Journey Travel booking over the existing first-party Supply Core.

Reuses OAP Direct inventory/holds/reservations. Adds transport-mode validation
and evidence-gated ticket issuance without storing raw provider or licence
material. No duplicate inventory or reservation tables are created.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from . import (
    approval_service,
    postgres_db,
    transport_execution_evidence,
    travel_marketplace,
)

TRAVEL_MODES = frozenset({"bus", "rail", "flight", "ferry"})
_RECEIPT_HASH = re.compile(r"^[0-9a-f]{64}$")


def _mode(value: object) -> str:
    mode = str(value or "").strip().lower()
    if mode not in TRAVEL_MODES:
        raise ValueError("invalid_travel_mode")
    return mode


def _ticket_gate() -> dict[str, Any]:
    status = transport_execution_evidence.status()
    areas = status.get("areas") if isinstance(status.get("areas"), dict) else {}
    ticket = areas.get("ticket_issuance")
    if not isinstance(ticket, dict):
        ticket = {}
    return {
        "authorised": ticket.get("live_execution_authorised") is True,
        "verified": list(ticket.get("verified") or ()),
        "missing": list(
            ticket.get("missing")
            or transport_execution_evidence.EXECUTION_REQUIREMENTS["ticket_issuance"]
        ),
    }


def quote(payload: dict[str, Any]) -> dict[str, Any]:
    """Quote existing OAP Direct transport inventory for one travel mode."""

    mode = _mode(payload.get("mode"))
    result = travel_marketplace.quote_direct(payload)
    if str(result.get("category")) != "transport":
        raise ValueError("transport_listing_required")
    return {
        **result,
        "mode": mode,
        "journey_segment_type": mode,
        "reservation_confirmed": False,
        "ticket_issued": False,
    }


def hold(payload: dict[str, Any], *, buyer_identity_id: str) -> dict[str, Any]:
    """Create a capacity-backed hold for one transport segment."""

    mode = _mode(payload.get("mode"))
    result = travel_marketplace.create_buyer_hold(
        payload,
        buyer_identity_id=buyer_identity_id,
    )
    return {
        **result,
        "mode": mode,
        "journey_segment_type": mode,
        "reservation_confirmed": False,
        "ticket_issued": False,
    }


def reserve(payload: dict[str, Any], *, buyer_identity_id: str) -> dict[str, Any]:
    """Convert a hold into a human-confirmed pending travel reservation."""

    mode = _mode(payload.get("mode"))
    result = travel_marketplace.create_buyer_reservation(
        payload,
        buyer_identity_id=buyer_identity_id,
    )
    return {
        **result,
        "mode": mode,
        "journey_segment_type": mode,
        "ticket_issued": False,
    }


def confirm(
    payload: dict[str, Any],
    *,
    owner_identity_id: str,
) -> dict[str, Any]:
    """Confirm a supplier-owned travel reservation; ticket issuance remains separate."""

    mode = _mode(payload.get("mode"))
    result = travel_marketplace.confirm_supplier_reservation(
        payload,
        owner_identity_id=owner_identity_id,
    )
    return {
        **result,
        "mode": mode,
        "journey_segment_type": mode,
        "ticket_issued": str(result.get("pass_state")) == "ISSUED",
    }


def issue_ticket(
    *,
    owner_identity_id: str,
    reservation_id: object,
    mode: object,
    issued_ticket_receipt_hash: object,
) -> dict[str, Any]:
    """Mark an OAP travel ticket issued only after the governed ticket gate is proven."""

    travel_mode = _mode(mode)
    digest = str(issued_ticket_receipt_hash or "").strip().lower()
    if not _RECEIPT_HASH.fullmatch(digest):
        raise ValueError("issued_ticket_receipt_hash_required")

    gate = _ticket_gate()
    if not gate["authorised"]:
        raise PermissionError("ticket_issuance_evidence_incomplete")

    with postgres_db.connect() as connection:
        row = connection.execute(
            """SELECT r.reservation_id,r.state,r.pass_state,l.category
               FROM oap_supply_reservations r
               JOIN oap_supply_listings l ON l.listing_id=r.listing_id
               JOIN oap_supply_suppliers s ON s.supplier_id=r.supplier_id
               WHERE r.reservation_id=%s AND s.owner_identity_id=%s
               FOR UPDATE""",
            (reservation_id, owner_identity_id),
        ).fetchone()
        if row is None:
            raise PermissionError("reservation_not_owned_by_supplier")
        if str(row[1]) != "CONFIRMED":
            raise ValueError("reservation_not_confirmed")
        if str(row[3]) != "transport":
            raise ValueError("transport_reservation_required")
        if str(row[2]) == "ISSUED":
            return {
                "reservation_id": str(row[0]),
                "mode": travel_mode,
                "pass_state": "ISSUED",
                "ticket_issued": True,
                "idempotent_replay": True,
                "raw_ticket_receipt_stored": False,
            }

        updated = connection.execute(
            """UPDATE oap_supply_reservations
               SET pass_state='ISSUED',updated_at=CURRENT_TIMESTAMP
               WHERE reservation_id=%s
               RETURNING updated_at""",
            (reservation_id,),
        ).fetchone()
        approval_service._write_audit(
            connection,
            actor_id=owner_identity_id,
            action="OAP_TRAVEL_TICKET_ISSUED",
            target=str(reservation_id),
            reason="Evidence-gated OAP travel ticket issuance recorded.",
            correlation_id=hashlib.sha256(
                f"{reservation_id}|{digest}|{travel_mode}".encode()
            ).hexdigest()[:32],
            metadata={
                "passed": True,
                "mode": travel_mode,
                "issued_ticket_receipt_hash": digest,
                "raw_ticket_receipt_stored": False,
                "licence_evidence_exposed": False,
                "human_authority_final": True,
            },
        )
        connection.commit()

    return {
        "reservation_id": str(reservation_id),
        "mode": travel_mode,
        "pass_state": "ISSUED",
        "ticket_issued": True,
        "updated_at": updated[0].isoformat(),
        "raw_ticket_receipt_stored": False,
        "licence_evidence_exposed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    gate = _ticket_gate()
    return {
        "component": "OAP Journey Travel Booking",
        "modes": sorted(TRAVEL_MODES),
        "quote_ready": True,
        "hold_ready": True,
        "reservation_ready": True,
        "supplier_confirmation_ready": True,
        "ticket_issuance_software_ready": True,
        "ticket_issuance_live_authorised": gate["authorised"],
        "ticket_issuance_verified": gate["verified"],
        "ticket_issuance_missing": gate["missing"],
        "reuses_oap_supply_core": True,
        "duplicate_inventory_store": False,
        "raw_licence_evidence_required_in_chat": False,
        "raw_licence_evidence_exposed": False,
        "human_authority_final": True,
    }
