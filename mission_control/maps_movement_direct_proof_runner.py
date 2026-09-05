"""Read-only proof runner plan for Maps + Movement + Direct.

This module is intentionally safe by default. It defines what must be proven before
Maps, Movement or Direct can move from built/guarded to operationally certified.
It does not dispatch people, charge money, confirm reservations, scrape suppliers,
write production approvals, expose private media, or unlock A5.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

PROOF_RUNNER_VERSION = 2

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

PARALLEL_TASKS: tuple[dict[str, object], ...] = (
    {
        "id": "task_01_route_matrix",
        "name": "Route Matrix",
        "lane": "routes",
        "covers": ("route_matrix",),
        "state": "queued_for_live_probe",
        "signal": "yellow",
        "safe_action": "Collect status codes for public and private routes without mutating state.",
        "green_when": "All public routes return 200/302 as expected and private routes fail closed for anonymous users.",
    },
    {
        "id": "task_02_private_guard",
        "name": "Private Guard",
        "lane": "guardian",
        "covers": ("private_fail_closed",),
        "state": "queued_for_live_probe",
        "signal": "yellow",
        "safe_action": "Check Founder-only surfaces for fail-closed responses.",
        "green_when": "Anonymous access cannot read Direct Intelligence, movement workspace, supply controls, private receipts or media.",
    },
    {
        "id": "task_03_map_source",
        "name": "Map Source Health",
        "lane": "map",
        "covers": ("map_source_health",),
        "state": "queued_for_source_probe",
        "signal": "yellow",
        "safe_action": "Read map/source status, timestamp and stale-data label only.",
        "green_when": "Source, timestamp, stale-data boundary and no-fake-live-route rule are present.",
    },
    {
        "id": "task_04_movement_schema",
        "name": "Movement Schema",
        "lane": "movement",
        "covers": ("movement_schema",),
        "state": "queued_for_schema_probe",
        "signal": "yellow",
        "safe_action": "Read movement schema status without running migrations or creating bookings.",
        "green_when": "Request, match, consent, tracking and Link Up binding stores are proven ready.",
    },
    {
        "id": "task_05_direct_supply",
        "name": "Direct Supply",
        "lane": "direct",
        "covers": ("direct_supplier", "direct_inventory"),
        "state": "queued_for_supply_probe",
        "signal": "yellow",
        "safe_action": "Read supplier, listing and inventory readiness without importing third-party inventory.",
        "green_when": "A Founder-certified supplier, active listing, terms record and timestamped availability exist.",
    },
    {
        "id": "task_06_pictures_lifecycle",
        "name": "Pictures + Lifecycle",
        "lane": "direct",
        "covers": ("direct_listing_photos", "quote_hold_reservation", "supplier_confirmation"),
        "state": "queued_for_lifecycle_probe",
        "signal": "yellow",
        "safe_action": "Read photo, quote, hold, request and supplier-confirmation proof without confirming reservations.",
        "green_when": "Certified photos, safe quote/hold, reservation request and authorised supplier confirmation receipt are proven.",
    },
    {
        "id": "task_07_hrm_green_gate",
        "name": "HRM + Green Gate",
        "lane": "memory_green_gate",
        "covers": ("hrm_receipts", "green_gate_live"),
        "state": "queued_for_receipt_probe",
        "signal": "yellow",
        "safe_action": "Read HRM receipt readiness and Green Gate aggregation without writing approvals.",
        "green_when": "Consequential actions have HRM receipts and Green Gate reads live evidence rather than fixed labels.",
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


def _summary() -> dict[str, int]:
    building = sum(1 for step in PROOF_STEPS if step["state"] == "building")
    certified = sum(1 for step in PROOF_STEPS if step["state"] == "certified")
    task_green = sum(1 for task in PARALLEL_TASKS if task["signal"] == "green")
    return {
        "total_steps": len(PROOF_STEPS),
        "certified": certified,
        "building": building,
        "hard_blocks": len(HARD_BLOCKS),
        "parallel_tasks": len(PARALLEL_TASKS),
        "parallel_tasks_green": task_green,
        "score_percent": round((certified / len(PROOF_STEPS)) * 100) if PROOF_STEPS else 0,
    }


def status() -> dict[str, Any]:
    """Return the current safe proof-runner projection."""
    summary = _summary()
    building = summary["building"]
    return {
        "component": "Maps + Movement + Direct Proof Runner",
        "version": PROOF_RUNNER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_plan",
        "state": "building" if building else "certified",
        "signal": "yellow" if building else "green",
        "no_fake_green": True,
        "human_authority_final": True,
        "parallel_execution_model": "seven_safe_read_only_lanes",
        "can_execute": False,
        "can_approve": False,
        "payment_capture_enabled": False,
        "dispatch_enabled": False,
        "confirmed_reservation_claim_enabled": False,
        "private_media_leak_allowed": False,
        "safe_public_routes": SAFE_PUBLIC_ROUTES,
        "founder_private_routes": FOUNDER_PRIVATE_ROUTES,
        "parallel_tasks": PARALLEL_TASKS,
        "proof_steps": PROOF_STEPS,
        "hard_blocks": HARD_BLOCKS,
        "summary": summary,
        "next_gate": "Attach live probes to the seven lanes, then certify only the checks with real evidence.",
    }
