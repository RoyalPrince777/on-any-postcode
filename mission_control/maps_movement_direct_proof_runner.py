"""Read-only proof runner plan for Maps + Movement + Direct.

This module is intentionally safe by default. It defines what must be proven before
Maps, Movement or Direct can move from built/guarded to operationally certified.
It does not dispatch people, charge money, confirm reservations, scrape suppliers,
write production approvals, expose private media, or unlock A5.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

PROOF_RUNNER_VERSION = 3

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
        "name": "Route Matrix",
        "area": "maps_movement_direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Live 200/302/401/403 results for every public and private route.",
    },
    {
        "id": "private_guard",
        "name": "Private Guard",
        "area": "guardian",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Anonymous users must never see Founder supply, movement workspace, Direct Intelligence, private media, receipts or admin state.",
    },
    {
        "id": "map_source_health",
        "name": "Map Source Health",
        "area": "map",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Map data source, timestamp, stale-data label and no-fake-live-route boundary.",
    },
    {
        "id": "movement_schema",
        "name": "Movement Schema",
        "area": "movement",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Schema readiness for request, match, consent, tracking and Link Up binding records.",
    },
    {
        "id": "direct_supply",
        "name": "Direct Supply",
        "area": "direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Founder-certified supplier, terms record, active listing and first-party supply boundary.",
    },
    {
        "id": "pictures_lifecycle",
        "name": "Pictures + Lifecycle",
        "area": "direct",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Certified photos, safe quote/hold/request path, supplier confirmation receipt and no public confirmation claim without proof.",
    },
    {
        "id": "hrm_green_gate",
        "name": "HRM + Green Gate",
        "area": "memory_green_gate",
        "state": "building",
        "signal": "yellow",
        "proof_needed": "Consequential Direct/Movement decisions create HRM receipts and Green Gate reads live proof outputs.",
    },
)

PROOF_LANES: tuple[dict[str, object], ...] = (
    {
        "id": "route_matrix",
        "name": "Route Matrix",
        "lane": "routes",
        "state": "awaiting_live_evidence",
        "signal": "yellow",
        "safe_action": "Collect status codes for public and private routes without mutating state.",
        "green_when": "Public routes return expected public responses and private routes fail closed for anonymous users.",
    },
    {
        "id": "private_guard",
        "name": "Private Guard",
        "lane": "guardian",
        "state": "awaiting_fail_closed_evidence",
        "signal": "yellow",
        "safe_action": "Check Founder-only surfaces for fail-closed responses.",
        "green_when": "Anonymous access cannot read Direct Intelligence, movement workspace, supply controls, private receipts or media.",
    },
    {
        "id": "map_source_health",
        "name": "Map Source Health",
        "lane": "map",
        "state": "awaiting_source_evidence",
        "signal": "yellow",
        "safe_action": "Read map/source status, timestamp and stale-data label only.",
        "green_when": "Source, timestamp, stale-data boundary and no-fake-live-route rule are present.",
    },
    {
        "id": "movement_schema",
        "name": "Movement Schema",
        "lane": "movement",
        "state": "awaiting_schema_evidence",
        "signal": "yellow",
        "safe_action": "Read movement schema status without running migrations or creating bookings.",
        "green_when": "Request, match, consent, tracking and Link Up binding stores are proven ready.",
    },
    {
        "id": "direct_supply",
        "name": "Direct Supply",
        "lane": "direct",
        "state": "awaiting_supply_evidence",
        "signal": "yellow",
        "safe_action": "Read supplier, listing and inventory readiness without importing third-party inventory.",
        "green_when": "A Founder-certified supplier, active listing, terms record and timestamped availability exist.",
    },
    {
        "id": "pictures_lifecycle",
        "name": "Pictures + Lifecycle",
        "lane": "direct",
        "state": "awaiting_lifecycle_evidence",
        "signal": "yellow",
        "safe_action": "Read photo, quote, hold, request and supplier-confirmation proof without confirming reservations.",
        "green_when": "Certified photos, safe quote/hold, reservation request and authorised supplier confirmation receipt are proven.",
    },
    {
        "id": "hrm_green_gate",
        "name": "HRM + Green Gate",
        "lane": "memory_green_gate",
        "state": "awaiting_receipt_evidence",
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
    lane_green = sum(1 for lane in PROOF_LANES if lane["signal"] == "green")
    return {
        "total_steps": len(PROOF_STEPS),
        "certified": certified,
        "building": building,
        "hard_blocks": len(HARD_BLOCKS),
        "proof_lanes": len(PROOF_LANES),
        "proof_lanes_green": lane_green,
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
        "mode": "read_only_proof_lanes",
        "state": "building" if building else "certified",
        "signal": "yellow" if building else "green",
        "no_fake_green": True,
        "human_authority_final": True,
        "proof_lane_model": "quiet_read_only_lanes",
        "compatibility_routes_kept_quiet": True,
        "can_execute": False,
        "can_approve": False,
        "payment_capture_enabled": False,
        "dispatch_enabled": False,
        "confirmed_reservation_claim_enabled": False,
        "private_media_leak_allowed": False,
        "safe_public_routes": SAFE_PUBLIC_ROUTES,
        "founder_private_routes": FOUNDER_PRIVATE_ROUTES,
        "proof_lanes": PROOF_LANES,
        "proof_steps": PROOF_STEPS,
        "hard_blocks": HARD_BLOCKS,
        "summary": summary,
        "next_gate": "Attach live probes to the proof lanes, then certify only the checks with real evidence.",
    }
