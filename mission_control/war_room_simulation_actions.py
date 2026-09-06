"""Founder-only War Room simulation actions for SMI.

The actions in this module are dry-run previews. They help the Founder see what
SMI can check, simulate and recommend without executing money movement,
dispatch, hidden tracking, public claims or self-approved changes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


SIMULATION_ACTIONS = (
    {
        "id": "public_route_sweep",
        "label": "Public route sweep",
        "signal": "🛣️",
        "can_do": "Preview-check public routes for 200/302 targets and naming alignment.",
        "simulation_output": "route list, expected status, missing route warning, next patch recommendation",
        "locked": "Does not change routes without Founder-approved code patch.",
    },
    {
        "id": "private_fail_closed_check",
        "label": "Private fail-closed check",
        "signal": "🔒",
        "can_do": "Confirm private War Room/SMI routes should reject anonymous access.",
        "simulation_output": "private route list, expected anonymous result, Founder-only requirement",
        "locked": "Does not bypass auth or reveal private state.",
    },
    {
        "id": "public_private_leak_scan",
        "label": "Public/private leak scan",
        "signal": "🛡️",
        "can_do": "Scan public-facing labels for private words, debug language and fake-live wording.",
        "simulation_output": "leak term, file/section hint, severity, safe replacement wording",
        "locked": "Does not publish private logs or secrets.",
    },
    {
        "id": "green_gate_simulation",
        "label": "Green Gate simulation",
        "signal": "🟢",
        "can_do": "Score whether a function can be green, yellow, orange or red from proof fields.",
        "simulation_output": "status light, proof seen, proof missing, reason not green",
        "locked": "Cannot mark whole product green without proof-runner pass.",
    },
    {
        "id": "map_place_simulation",
        "label": "Map/place simulation",
        "signal": "🗺️",
        "can_do": "Preview On Any Place results for places, spots, categories and source timestamps.",
        "simulation_output": "area, points, source timestamp, missing tiles/data/geometry",
        "locked": "Does not claim every shop, road or alley is live.",
    },
    {
        "id": "movement_route_simulation",
        "label": "Movement route simulation",
        "signal": "🚶",
        "can_do": "Preview On Any Route distance/ETA proof and request state.",
        "simulation_output": "proof_id, from/to, ETA, route state, next gate",
        "locked": "No turn-by-turn, no dispatch, no hidden tracking without proof/consent.",
    },
    {
        "id": "direct_supply_simulation",
        "label": "Direct supply simulation",
        "signal": "🏪",
        "can_do": "Preview OAP Direct listings, supplier proof needs, quote/hold/reservation gates.",
        "simulation_output": "supplier proof state, listing proof, receipt needed, blocked confirmation",
        "locked": "No confirmed booking, no supplier claim, no payment capture without receipt.",
    },
    {
        "id": "ride_drop_simulation",
        "label": "Ride/Drop simulation",
        "signal": "🚘",
        "can_do": "Preview On Any Ride and On Any Drop request flow and licence/dispatch gates.",
        "simulation_output": "request preview, licence proof needed, dispatch locked, payment locked",
        "locked": "No driver/courier assignment and no operator claim without licence proof.",
    },
    {
        "id": "live_pattern_simulation",
        "label": "Live Pattern simulation",
        "signal": "📡",
        "can_do": "Preview traffic-style, event, crowd and open-now signals as proof-gated patterns.",
        "simulation_output": "signal level, source need, timestamp need, stale/fake-live warning",
        "locked": "No true live claim without timestamped source proof.",
    },
    {
        "id": "hrm_receipt_simulation",
        "label": "HRM receipt simulation",
        "signal": "📚",
        "can_do": "Preview the memory receipt SMI should write after checks and deployments.",
        "simulation_output": "check_id, status, proof, missing piece, lock, blocker, deploy id, Founder decision",
        "locked": "Does not rewrite history or self-approve decisions.",
    },
    {
        "id": "aci_readiness_simulation",
        "label": "ACI readiness simulation",
        "signal": "🧬",
        "can_do": "Check whether SMI is ready to move toward Adaptive Coherent Intelligence.",
        "simulation_output": "coherence score, missing memory/proof loops, autonomy lock state",
        "locked": "Does not claim AGI, ASI or autonomous authority.",
    },
)


def list_actions() -> dict[str, object]:
    """Return the safe War Room simulation action catalogue."""

    return {
        "component": "War Room Simulation Actions",
        "generated_at": _now(),
        "mode": "dry_run_preview_only",
        "action_count": len(SIMULATION_ACTIONS),
        "actions": SIMULATION_ACTIONS,
        "global_locks": {
            "payment_capture_enabled": False,
            "dispatch_enabled": False,
            "hidden_tracking_enabled": False,
            "self_approval_enabled": False,
            "agi_or_asi_claim_enabled": False,
        },
        "human_authority_final": True,
        "overall_green": False,
    }


def simulate(action_id: object = None, target: object = None) -> dict[str, object]:
    """Return a deterministic dry-run report for one action."""

    clean_action = str(action_id or "green_gate_simulation").strip().lower().replace(" ", "_")
    clean_target = " ".join(str(target or "On Any Place").strip().split())[:160]
    action = next((item for item in SIMULATION_ACTIONS if item["id"] == clean_action), SIMULATION_ACTIONS[3])
    generated_at = _now()
    receipt_id = sha256(f"{action['id']}|{clean_target}|{generated_at[:16]}".encode()).hexdigest()[:16]
    return {
        "component": "War Room Simulation Run",
        "generated_at": generated_at,
        "receipt_id": receipt_id,
        "mode": "simulation_only_no_execution",
        "action": action,
        "target": clean_target,
        "visible_signals": {
            "checking": action["label"],
            "stage": "simulation_preview",
            "proof_needed": action["simulation_output"],
            "locked": action["locked"],
            "blocked": "payment, dispatch, hidden tracking, fake green, private leak and self-approval remain blocked",
            "next_before_green": "Run live proof runner, confirm route/API responses, scan logs, then record HRM receipt.",
            "hrm_memory": "Store receipt_id, action_id, target, status light, proof seen/missing, blocker and Founder decision.",
        },
        "result": {
            "status_light": "🟡",
            "safe_to_execute": False,
            "can_recommend_patch": True,
            "can_change_public_claim": False,
            "can_unlock_payment": False,
            "can_dispatch": False,
            "can_track_hidden_location": False,
            "overall_green": False,
        },
        "human_authority_final": True,
    }
