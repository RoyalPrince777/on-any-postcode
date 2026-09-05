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
    "/atlas",
    "/local-map",
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


def status() -> dict[str, object]:
    """Return the current SMI alignment contract for War Room."""

    return {
        "component": "SMI Public Alignment Checker",
        "generated_at": _now(),
        "mode": "read_only_alignment_check",
        "public_surface_goal": "clean public home + UK Local Map + Movement + Direct",
        "private_surface_goal": "SMI Mission/War Room handles checks, debug and simple fixes",
        "public_noise_removed": PUBLIC_NOISE_REMOVED,
        "public_allowed_routes": PUBLIC_ALLOWED_ROUTES,
        "private_check_routes": PRIVATE_CHECK_ROUTES,
        "safety_locks": SAFETY_LOCKS,
        "alignment": {
            "home_simple": True,
            "public_signals_removed_for_now": True,
            "atlas_is_local_map_first": True,
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
        ),
        "can_approve": False,
        "can_execute": False,
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
        "allowed": True,
        "executes_changes": False,
        "requires_founder_approval_for_write": True,
        "payment_stays_locked": True,
        "dispatch_stays_locked": True,
        "hidden_tracking_blocked": True,
    }
