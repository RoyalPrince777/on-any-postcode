"""Read-only proof runner plan for Maps + Movement + Direct.

This module is intentionally safe by default. It defines what must be proven before
Maps, Movement or Direct can move from built/guarded to operationally certified.
It does not dispatch people, charge money, confirm reservations, scrape suppliers,
write production approvals, expose private media, or unlock A5.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

PROOF_RUNNER_VERSION = 1

SAFE_PUBLIC_ROUTES: tuple[str, ...] = (
    "/travel",
    "/travel/direct",
    "/travel/api/catalogue",
    "/travel/direct/api/offers",
    "/travel/direct/api/quote",
    "/travel/direct/photos/<photo_id>",
    "/movement",
    "/movement/status",
    "/the-spot/maps-weather-travel",
)

FOUNDER_PRIVATE_ROUTES: tuple[str, ...] = (
    "/mission/direct-intelligence",
    "/mission/movement-intelligence",
    "/mission/map-intelligence",
    "/mission/movement-direct-map",
    "/mission/movement-direct-map-pictures",
    "/mission/supply",
    "/mission/supply/status",
    "/mission/supply/suppliers/certify",
    "/mission/supply/listings",
    "/mission/supply/inventory",
    "/mission/supply/reservations/confirm",
    "/movement/workspace",
    "/movement/route",
    "/movement/bookings",
)

PROOF_STEPS: tuple[dict[str, str], ...] = (
    {
        "id": "route_matrix",
        "name": "Route matrix proof",
        "area": "maps_movement_direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Live 200/302/401/403 results for every public and private route.",
    },
    {
        "id": "private_fail_closed",
        "name": "Private fail-closed proof",
        "area": "guardian",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Anonymous users must never see Founder supply, movement workspace, direct intelligence, private media, receipts or admin state.",
    },
    {
        "id": "map_source_health",
        "name": "Map source-health proof",
        "area": "map",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Map data source, timestamp, stale-data label and no-fake-live-route boundary.",
    },
    {
        "id": "movement_schema",
        "name": "Movement schema proof",
        "area": "movement",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Schema readiness for request, match, consent, tracking and Link Up binding records.",
    },
    {
        "id": "direct_supplier",
        "name": "OAP Direct supplier proof",
        "area": "direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Founder-certified supplier, terms record and first-party supply boundary.",
    },
    {
        "id": "direct_listing_photos",
        "name": "Certified listing picture proof",
        "area": "direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Every active public listing has rights-confirmed cover photo/gallery or is labelled photo-pending.",
    },
    {
        "id": "direct_inventory",
        "name": "Availability proof",
        "area": "direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Inventory/availability source exists, is owned by OAP Direct/supplier record, and is timestamped.",
    },
    {
        "id": "quote_hold_reservation",
        "name": "Quote, hold and reservation request proof",
        "area": "direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Quote and hold are safe; reservation request never claims confirmation without supplier confirmation.",
    },
    {
        "id": "supplier_confirmation",
        "name": "Supplier confirmation proof",
        "area": "direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Authorised supplier confirmation receipt exists before any confirmed reservation claim.",
    },
    {
        "id": "hrm_receipts",
        "name": "HRM receipt proof",
        "area": "memory",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Consequential Direct/Movement decisions create durable, audited HRM receipts.",
    },
    {
        "id": "green_gate_live",
        "name": "Green Gate live automation",
        "area": "green_gate",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Green Gate reads live proof outputs and refuses fake green labels.",
    },
)

HARD_BLOCKS: tuple[dict[str, str], ...] = (
    {"id": "a5", "name": "A5 autonomy", "state": "locked", "signal": "red"},
    {"id": "dispatch", "name": "Real-world dispatch", "state": "locked", "signal": "red"},
    {"id": "payment_capture", "name": "Payment capture", "state": "locked", "signal": "red"},
    {"id": "confirmed_claim", "name": "Confirmed reservation claim without supplier proof", "state": "locked", "signal": "red"},
    {"id": "hidden_tracking", "name": "Hidden tracking", "state": "blocked", "signal": "red"},
    {"id": "private_media_leak", "name": "Private media leak", "state": "blocked", "signal": "red"},
    {"id": "external_marketplace_authority", "name": "External marketplace authority", "state": "blocked", "signal": "red"},
)


def status() -> dict[str, Any]:
    """Return the current safe proof-runner projection."""
    building = sum(1 for step in PROOF_STEPS if step["state"] == "building")
    certified = sum(1 for step in PROOF_STEPS if step["state"] == "certified")
    return {
        "component": "Maps + Movement + Direct Proof Runner",
        "version": PROOF_RUNNER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_plan",
        "state": "building" if building else "certified",
        "signal": "yellow" if building else "green",
        "no_fake_green": True,
        "human_authority_final": True,
        "can_execute": False,
        "can_approve": False,
        "payment_capture_enabled": False,
        "dispatch_enabled": False,
        "confirmed_reservation_claim_enabled": False,
        "private_media_leak_allowed": False,
        "safe_public_routes": SAFE_PUBLIC_ROUTES,
        "founder_private_routes": FOUNDER_PRIVATE_ROUTES,
        "proof_steps": PROOF_STEPS,
        "hard_blocks": HARD_BLOCKS,
        "summary": {
            "total_steps": len(PROOF_STEPS),
            "certified": certified,
            "building": building,
            "hard_blocks": len(HARD_BLOCKS),
            "score_percent": round((certified / len(PROOF_STEPS)) * 100) if PROOF_STEPS else 0,
        },
        "next_gate": "Wire live HTTP, schema, supplier, photo, inventory, HRM and Green Gate probes into this runner.",
    }
