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


SIMULATION_STAGES_21 = (
    {"stage": 1, "name": "Observe", "purpose": "Receive the situation without acting.", "light": "⚪"},
    {"stage": 2, "name": "Name", "purpose": "Name the system, route, product or problem.", "light": "⚪"},
    {"stage": 3, "name": "Classify", "purpose": "Place it under OAP Atlas, Movement Intelligence, OAP Direct, The Spot, The Link, War Room, SIKA or SMI Intelligence.", "light": "⚪"},
    {"stage": 4, "name": "Boundary", "purpose": "Check public/private, Founder-only, youth, privacy and compliance boundaries.", "light": "🛡️"},
    {"stage": 5, "name": "Risk", "purpose": "Detect money, dispatch, hidden tracking, fake-live, private leak or real-world risk.", "light": "🟠"},
    {"stage": 6, "name": "Lock", "purpose": "Keep restricted functions locked before any deeper simulation.", "light": "🔒"},
    {"stage": 7, "name": "Proof Need", "purpose": "List the exact proof required before green.", "light": "🟡"},
    {"stage": 8, "name": "Source", "purpose": "Check whether a named source, timestamp or receipt exists.", "light": "🟡"},
    {"stage": 9, "name": "Route/API", "purpose": "Check route or API existence, expected 200/302, JSON shape and safe fallback.", "light": "🛣️"},
    {"stage": 10, "name": "Data", "purpose": "Check whether place, business, event, open-now or live source data is real or seeded.", "light": "🗺️"},
    {"stage": 11, "name": "Simulation", "purpose": "Run the dry-run scenario and produce visible safe signals.", "light": "🧠"},
    {"stage": 12, "name": "Compare", "purpose": "Compare expected state against actual/known proof state.", "light": "📊"},
    {"stage": 13, "name": "Gap", "purpose": "Name missing files, routes, proof, data, logs or receipts.", "light": "🟠"},
    {"stage": 14, "name": "Green Gate", "purpose": "Score green/yellow/orange/red without fake green.", "light": "🟢"},
    {"stage": 15, "name": "Guardian", "purpose": "Confirm privacy, safety, youth and compliance guardrails.", "light": "🛡️"},
    {"stage": 16, "name": "HRM Receipt", "purpose": "Prepare the memory/audit receipt fields.", "light": "📚"},
    {"stage": 17, "name": "Founder Decision", "purpose": "Mark whether Founder approval is needed before any write/deploy/action.", "light": "👑"},
    {"stage": 18, "name": "Patch Plan", "purpose": "Recommend the smallest safe patch, with rollback path.", "light": "🛠️"},
    {"stage": 19, "name": "Deploy Proof", "purpose": "Require deploy ID, live status and fresh error scan before green.", "light": "🚀"},
    {"stage": 20, "name": "Learn", "purpose": "Feed safe outcome into HRM and Learning Intelligence without changing authority.", "light": "🧬"},
    {"stage": 21, "name": "Lock Result", "purpose": "Return final status, locks, blockers, next action and HRM memory.", "light": "✅"},
)


SIMULATION_ACTIONS = (
    {
        "id": "public_route_sweep",
        "label": "Public route sweep",
        "signal": "🛣️",
        "default_stage": 9,
        "can_do": "Preview-check public routes for 200/302 targets and naming alignment.",
        "simulation_output": "route list, expected status, missing route warning, next patch recommendation",
        "locked": "Does not change routes without Founder-approved code patch.",
    },
    {
        "id": "private_fail_closed_check",
        "label": "Private fail-closed check",
        "signal": "🔒",
        "default_stage": 4,
        "can_do": "Confirm private War Room/SMI routes should reject anonymous access.",
        "simulation_output": "private route list, expected anonymous result, Founder-only requirement",
        "locked": "Does not bypass auth or reveal private state.",
    },
    {
        "id": "public_private_leak_scan",
        "label": "Public/private leak scan",
        "signal": "🛡️",
        "default_stage": 15,
        "can_do": "Scan public-facing labels for private words, debug language and fake-live wording.",
        "simulation_output": "leak term, file/section hint, severity, safe replacement wording",
        "locked": "Does not publish private logs or secrets.",
    },
    {
        "id": "green_gate_simulation",
        "label": "Green Gate simulation",
        "signal": "🟢",
        "default_stage": 14,
        "can_do": "Score whether a function can be green, yellow, orange or red from proof fields.",
        "simulation_output": "status light, proof seen, proof missing, reason not green",
        "locked": "Cannot mark whole product green without proof-runner pass.",
    },
    {
        "id": "map_place_simulation",
        "label": "Map/place simulation",
        "signal": "🗺️",
        "default_stage": 10,
        "can_do": "Preview On Any Place results for places, spots, categories and source timestamps.",
        "simulation_output": "area, points, source timestamp, missing tiles/data/geometry",
        "locked": "Does not claim every shop, road or alley is live.",
    },
    {
        "id": "movement_route_simulation",
        "label": "Movement route simulation",
        "signal": "🚶",
        "default_stage": 11,
        "can_do": "Preview On Any Route distance/ETA proof and request state.",
        "simulation_output": "proof_id, from/to, ETA, route state, next gate",
        "locked": "No turn-by-turn, no dispatch, no hidden tracking without proof/consent.",
    },
    {
        "id": "direct_supply_simulation",
        "label": "Direct supply simulation",
        "signal": "🏪",
        "default_stage": 8,
        "can_do": "Preview OAP Direct listings, supplier proof needs, quote/hold/reservation gates.",
        "simulation_output": "supplier proof state, listing proof, receipt needed, blocked confirmation",
        "locked": "No confirmed booking, no supplier claim, no payment capture without receipt.",
    },
    {
        "id": "ride_drop_simulation",
        "label": "Ride/Drop simulation",
        "signal": "🚘",
        "default_stage": 6,
        "can_do": "Preview On Any Ride and On Any Drop request flow and licence/dispatch gates.",
        "simulation_output": "request preview, licence proof needed, dispatch locked, payment locked",
        "locked": "No driver/courier assignment and no operator claim without licence proof.",
    },
    {
        "id": "live_pattern_simulation",
        "label": "Live Pattern simulation",
        "signal": "📡",
        "default_stage": 7,
        "can_do": "Preview traffic-style, event, crowd and open-now signals as proof-gated patterns.",
        "simulation_output": "signal level, source need, timestamp need, stale/fake-live warning",
        "locked": "No true live claim without timestamped source proof.",
    },
    {
        "id": "hrm_receipt_simulation",
        "label": "HRM receipt simulation",
        "signal": "📚",
        "default_stage": 16,
        "can_do": "Preview the memory receipt SMI should write after checks and deployments.",
        "simulation_output": "check_id, status, proof, missing piece, lock, blocker, deploy id, Founder decision",
        "locked": "Does not rewrite history or self-approve decisions.",
    },
    {
        "id": "smi_learning_readiness_simulation",
        "label": "SMI learning readiness simulation",
        "signal": "🧬",
        "default_stage": 20,
        "can_do": "Check whether SMI memory, coherence, evidence and Learning Intelligence loops are ready for the next governed A-level.",
        "simulation_output": "coherence score, missing memory/proof loops, autonomy lock state and next evidence gate",
        "locked": "Does not self-promote A5, A6 or A7 and never grants autonomous authority.",
    },
)

# Quiet compatibility for old private URLs/commands. Never expose this as the
# canonical maturity model; A1-A7 is the only current SMI operating-level ladder.
ACTION_ALIASES = {"aci_readiness_simulation": "smi_learning_readiness_simulation"}


def _stage(number: int) -> dict[str, object]:
    bounded = max(1, min(21, int(number or 1)))
    return next(item for item in SIMULATION_STAGES_21 if item["stage"] == bounded)


def _stage_for(action: dict[str, object], target: str) -> dict[str, object]:
    text = f"{action.get('id', '')} {target}".lower()
    if any(word in text for word in ("payment", "sika", "money", "card")):
        return _stage(6)
    if any(word in text for word in ("dispatch", "ride", "drop", "driver", "courier")):
        return _stage(6)
    if any(word in text for word in ("hidden", "tracking", "location", "live spot")):
        return _stage(15)
    if any(word in text for word in ("green", "all green", "approve")):
        return _stage(14)
    if any(word in text for word in ("404", "broken", "not found")):
        return _stage(9)
    if any(word in text for word in ("hrm", "receipt", "memory")):
        return _stage(16)
    if any(word in text for word in ("learning", "coherence", "a5", "a6", "a7", "aci", "adaptive", "coherent")):
        return _stage(20)
    if any(word in text for word in ("source", "timestamp", "supplier")):
        return _stage(8)
    return _stage(int(action.get("default_stage", 11)))


def _stage_window(stage_number: int) -> dict[str, object]:
    previous_stage = _stage(stage_number - 1) if stage_number > 1 else None
    current_stage = _stage(stage_number)
    next_stage = _stage(stage_number + 1) if stage_number < 21 else None
    return {
        "previous": previous_stage,
        "current": current_stage,
        "next": next_stage,
        "progress": f"{stage_number}/21",
    }


def list_actions() -> dict[str, object]:
    """Return the safe War Room simulation action catalogue."""

    return {
        "component": "War Room Simulation Actions",
        "generated_at": _now(),
        "mode": "dry_run_preview_only",
        "stage_count": 21,
        "stages": SIMULATION_STAGES_21,
        "action_count": len(SIMULATION_ACTIONS),
        "actions": SIMULATION_ACTIONS,
        "global_locks": {
            "payment_capture_enabled": False,
            "dispatch_enabled": False,
            "hidden_tracking_enabled": False,
            "self_approval_enabled": False,
            "a5_enabled": False,
            "a6_enabled": False,
            "a7_enabled": False,
            "self_permission_change_enabled": False,
            "self_constitution_change_enabled": False,
        },
        "canonical_autonomy_ladder": "A1-A7",
        "human_authority_final": True,
        "overall_green": False,
    }


def simulate(action_id: object = None, target: object = None, stage: object = None) -> dict[str, object]:
    """Return a deterministic dry-run report for one action."""

    clean_action = str(action_id or "green_gate_simulation").strip().lower().replace(" ", "_")
    clean_action = ACTION_ALIASES.get(clean_action, clean_action)
    clean_target = " ".join(str(target or "On Any Place").strip().split())[:160]
    action = next((item for item in SIMULATION_ACTIONS if item["id"] == clean_action), SIMULATION_ACTIONS[3])
    if stage in (None, "", "auto"):
        stage_info = _stage_for(action, clean_target)
    else:
        try:
            stage_info = _stage(int(stage))
        except (TypeError, ValueError):
            stage_info = _stage_for(action, clean_target)
    generated_at = _now()
    receipt_id = sha256(f"{action['id']}|{clean_target}|{stage_info['stage']}|{generated_at[:16]}".encode()).hexdigest()[:16]
    return {
        "component": "War Room Simulation Run",
        "generated_at": generated_at,
        "receipt_id": receipt_id,
        "mode": "simulation_only_no_execution",
        "stage_system": "21_stage_situation_simulation",
        "stage": _stage_window(int(stage_info["stage"])),
        "action": action,
        "target": clean_target,
        "visible_signals": {
            "checking": action["label"],
            "stage": f"Stage {stage_info['stage']}/21 — {stage_info['name']}",
            "stage_purpose": stage_info["purpose"],
            "proof_needed": action["simulation_output"],
            "locked": action["locked"],
            "blocked": "payment, dispatch, hidden tracking, fake green, private leak, self-approval and A5-A7 self-promotion remain blocked",
            "next_before_green": "Move through stages 12–21: compare, gap, Green Gate, Guardian, HRM receipt, Founder decision, patch plan, deploy proof, learn, lock result.",
            "hrm_memory": "Store receipt_id, action_id, target, stage, status light, proof seen/missing, blocker and Founder decision.",
        },
        "result": {
            "status_light": "🟡",
            "safe_to_execute": False,
            "can_recommend_patch": True,
            "can_change_public_claim": False,
            "can_unlock_payment": False,
            "can_dispatch": False,
            "can_track_hidden_location": False,
            "can_self_promote_autonomy": False,
            "overall_green": False,
        },
        "human_authority_final": True,
    }
