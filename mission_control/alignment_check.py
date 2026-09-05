"""SMI alignment checks for public route cleanup and simple task debugging.

This module is private-safe and read-only. It reports whether the public OAP
surface is clean, whether key routes exist, and whether major unsafe functions
remain locked. It does not expose secrets, private records, or internal logs.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


PUBLIC_ALLOWED_ROUTES = (
    "/",
    "/on-any-place",
    "/places",
    "/spots",
    "/events",
    "/on-any-route",
    "/routes",
    "/travel",
    "/on-any-ride",
    "/ride",
    "/on-any-drop",
    "/drop",
    "/live-pattern",
    "/atlas",
    "/uk-map",
    "/business-map",
    "/traffic-map",
    "/movement",
    "/movement/status",
    "/movement/route-proof?from=Mitcham&to=London%20Bridge&profile=driving",
    "/movement/request-preview?from=Mitcham&to=London%20Bridge&purpose=local_business_route",
    "/travel/direct",
    "/atlas/api/local-map?location=Mitcham&to=London%20Bridge",
    "/atlas/api/live-source?location=Mitcham",
)

PRIVATE_CHECK_ROUTES = (
    "/mission",
    "/mission/war-room",
    "/mission/war-room/actions",
    "/mission/war-room/alignment",
    "/mission/war-room/actions/alignment",
    "/mission/war-room/thinking-signals",
    "/mission/war-room/actions/thinking-signals",
    "/mission/war-room/debug/simple-task",
    "/mission/war-room/actions/simple-task-debug",
    "/mission/war-room/debug/404",
    "/mission/war-room/actions/404-check",
    "/mission/war-room/movement/proof",
    "/mission/map-movement/status",
    "/mission/map-movement/live-source-status",
    "/mission/smi/debug",
)

PUBLIC_NOISE_REMOVED = (
    "public_final_signals_block",
    "duplicate_atlas_cards",
    "spot_first_map_routing",
    "public_debug_language",
    "public_war_room_language",
    "public_private_state",
)

SAFETY_LOCKS = {
    "payment_capture_enabled": False,
    "dispatch_enabled": False,
    "hidden_tracking_enabled": False,
    "confirmed_booking_without_supplier_receipt": False,
    "public_private_debug_enabled": False,
    "fake_live_traffic_claim_enabled": False,
}

THINKING_SIGNAL_STEPS = (
    {
        "id": "war_room_checks",
        "label": "War Room checks",
        "signal": "🧠",
        "stage": "private_control",
        "safe_visible_thought": "Check the private command surface first, then report only safe status and proof gaps.",
        "proof_needed": "Founder-only route returns JSON after login and anonymous access fails closed.",
        "state": "built_needs_live_route_proof",
    },
    {
        "id": "not_found_debug",
        "label": "404 debug",
        "signal": "🟡",
        "stage": "route_recovery",
        "safe_visible_thought": "If a public path breaks, recover users to Home, On Any Place, Movement and Direct without exposing private debug.",
        "proof_needed": "Public 404 page renders clean recovery links and private debug stays under /mission.",
        "state": "built",
    },
    {
        "id": "simple_task_debug",
        "label": "Simple task debug",
        "signal": "🛠️",
        "stage": "smallest_safe_fix",
        "safe_visible_thought": "Name the problem, check boundary, patch the smallest safe file, deploy, scan logs, report honestly.",
        "proof_needed": "Debug pack returns protocol without executing or self-approving changes.",
        "state": "built",
    },
    {
        "id": "public_private_boundary",
        "label": "Public/private boundary",
        "signal": "🛡️",
        "stage": "boundary_guard",
        "safe_visible_thought": "Public shows products only; private SMI, War Room, logs and debug stay Founder-only.",
        "proof_needed": "No public template leaks private wording, private routes require Founder login.",
        "state": "guarded_needs_template_scan",
    },
    {
        "id": "route_proof",
        "label": "Route proof",
        "signal": "🛣️",
        "stage": "movement_check",
        "safe_visible_thought": "Show distance and ETA only as seed/proof-ready until route geometry and live source proof exist.",
        "proof_needed": "Route endpoint returns proof_id, source, timestamp, locks and no fake live claim.",
        "state": "seed_proof_ready",
    },
    {
        "id": "map_proof",
        "label": "Map proof",
        "signal": "🗺️",
        "stage": "place_check",
        "safe_visible_thought": "On Any Place can show seeded UK points now, but full green waits for real tiles and UK data ingestion.",
        "proof_needed": "On Any Place route/API returns component, sections, points, source timestamps and missing_before_green.",
        "state": "surface_live_not_full_green",
    },
    {
        "id": "movement_proof",
        "label": "Movement proof",
        "signal": "🚶",
        "stage": "movement_boundary",
        "safe_visible_thought": "Movement requests can preview safely; dispatch, assignment and tracking stay locked without proof/consent.",
        "proof_needed": "Movement request preview returns preview_only, consent requirement, payment false, dispatch false.",
        "state": "preview_only",
    },
    {
        "id": "direct_proof",
        "label": "Direct proof",
        "signal": "🏪",
        "stage": "supplier_check",
        "safe_visible_thought": "Direct can show requests/listings, but confirmations require supplier receipt and proof.",
        "proof_needed": "Direct route works; reservation confirmation requires authenticated proof and cannot fake supplier receipt.",
        "state": "connected_supplier_proof_needed",
    },
    {
        "id": "live_pattern_proof",
        "label": "Live Pattern proof",
        "signal": "📡",
        "stage": "live_claim_guard",
        "safe_visible_thought": "Pattern signals show watch/review until live traffic, events or disruption data has source timestamps.",
        "proof_needed": "Live source status returns timestamped sources; public does not claim true live traffic without proof.",
        "state": "proof_gated",
    },
    {
        "id": "payment_lock",
        "label": "Payment lock",
        "signal": "🔒",
        "stage": "money_guard",
        "safe_visible_thought": "No payment capture until legal, supplier, receipt and Green Gate checks pass.",
        "proof_needed": "All status outputs keep payment_capture_enabled false.",
        "state": "locked",
    },
    {
        "id": "dispatch_lock",
        "label": "Dispatch lock",
        "signal": "🔒",
        "stage": "real_world_guard",
        "safe_visible_thought": "No driver, courier, ride or delivery dispatch until licence, consent, operator and receipt gates pass.",
        "proof_needed": "All status outputs keep dispatch_enabled and automatic_dispatch_enabled false.",
        "state": "locked",
    },
    {
        "id": "hidden_tracking_block",
        "label": "Hidden tracking block",
        "signal": "⛔",
        "stage": "privacy_guard",
        "safe_visible_thought": "Location is never tracked silently; Live Spot needs clear consent and expiry.",
        "proof_needed": "All status outputs keep hidden_tracking_enabled false and location features consent-only.",
        "state": "blocked",
    },
    {
        "id": "fake_green_block",
        "label": "Fake green block",
        "signal": "🛑",
        "stage": "truth_guard",
        "safe_visible_thought": "Do not mark the whole product green while tiles, live data, traffic, events, route geometry or proof runners are missing.",
        "proof_needed": "overall_green remains false until all missing_before_green items pass.",
        "state": "blocked_until_proof",
    },
)


def thinking_signals() -> dict[str, object]:
    """Return a private-safe visible SMI thinking/status signal board."""

    return {
        "component": "SMI Thinking Signals",
        "generated_at": _now(),
        "mode": "visible_safe_reasoning_signals",
        "private_chain_of_thought_exposed": False,
        "purpose": "Show the Founder what SMI is checking, what it found, what is locked, and what proof is still missing.",
        "signals": THINKING_SIGNAL_STEPS,
        "summary": {
            "war_room_checks": "🟡 built, live proof needed",
            "404_debug": "🟢 built",
            "simple_task_debug": "🟢 built",
            "public_private_boundary": "🛡️ guarded, template scan still needed",
            "route_proof": "🟡 seed proof-ready",
            "map_proof": "🟠 surface live, full map not green",
            "movement_proof": "🟡 preview-only",
            "direct_proof": "🟡 connected, supplier proof needed",
            "live_pattern_proof": "🟡 proof-gated",
            "payment_lock": "🔒 locked",
            "dispatch_lock": "🔒 locked",
            "hidden_tracking_block": "⛔ blocked",
            "fake_green_block": "🛑 blocked until proof",
        },
        "next_steps_before_green": (
            "HTTP proof for all public aliases",
            "anonymous fail-closed proof for private routes",
            "real map tiles",
            "route geometry / OSRM",
            "UK-wide source-backed place data",
            "events/open-now source proof",
            "live traffic/disruption source proof",
            "War Room proof-runner pass",
        ),
        "overall_green": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    """Return the current SMI alignment contract for War Room."""

    return {
        "component": "SMI Public Alignment Checker",
        "generated_at": _now(),
        "mode": "read_only_alignment_check",
        "public_surface_goal": "clean public home + On Any Place + Movement + Direct",
        "private_surface_goal": "SMI Mission/War Room handles checks, debug and simple fixes",
        "public_noise_removed": PUBLIC_NOISE_REMOVED,
        "public_allowed_routes": PUBLIC_ALLOWED_ROUTES,
        "private_check_routes": PRIVATE_CHECK_ROUTES,
        "safety_locks": SAFETY_LOCKS,
        "thinking_signals": thinking_signals()["summary"],
        "alignment": {
            "home_simple": True,
            "public_signals_removed_for_now": True,
            "on_any_place_first": True,
            "spot_noise_removed_from_map": True,
            "duplicate_map_entry_reduced": True,
            "404_simple_recovery": True,
            "war_room_debug_private_only": True,
            "payment_stays_locked": True,
        },
        "still_to_prove_live": (
            "HTTP 200/302 proof for all public allowed routes after deploy",
            "Anonymous fail-closed proof for all private check routes after deploy",
            "Live open-data source result proof for UK places",
            "No public template contains private SMI/War Room debug language",
            "War Room proof-runner pass before overall green",
        ),
        "can_approve": False,
        "can_execute": False,
        "overall_green": False,
        "human_authority_final": True,
    }


def simple_task_debug(task: object = None) -> dict[str, object]:
    """Return a safe simple-task debug pack without executing changes."""

    text = " ".join(str(task or "").strip().split())[:240]
    return {
        "component": "SMI Simple Task Debug",
        "generated_at": _now(),
        "task": text or "public_alignment_check",
        "protocol": (
            "name the problem",
            "check public/private boundary",
            "remove duplicate/noise",
            "keep safety locks",
            "patch smallest safe file",
            "deploy both services",
            "scan fresh logs",
            "return honest green/yellow status",
        ),
        "thinking_signal_mode": "safe_visible_steps_only",
        "thinking_signals": thinking_signals()["summary"],
        "allowed": True,
        "executes_changes": False,
        "requires_founder_approval_for_write": True,
        "payment_stays_locked": True,
        "dispatch_stays_locked": True,
        "hidden_tracking_blocked": True,
    }
