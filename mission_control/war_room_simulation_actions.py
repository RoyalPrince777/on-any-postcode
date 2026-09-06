"""Founder-only War Room simulation actions for SMI.

These actions are dry-run previews. They let Human Authority start the SMI
3/7/21 review protocol, request a registered advisory agent, challenge a case,
inspect evidence, test failure/recovery and expose a safe next gate without
executing money movement, dispatch, hidden tracking, public claims, deployment
or self-approved changes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


SIMULATION_STAGES_21 = (
    {"stage": 1, "name": "Observe", "purpose": "Receive the situation without acting.", "light": "⚪"},
    {"stage": 2, "name": "Name", "purpose": "Name the system, route, product or problem.", "light": "⚪"},
    {"stage": 3, "name": "Classify", "purpose": "Place the case under the correct OAP system and Intelligence World.", "light": "⚪"},
    {"stage": 4, "name": "Boundary", "purpose": "Check public/private, Founder-only, youth, privacy and compliance boundaries.", "light": "🛡️"},
    {"stage": 5, "name": "Risk", "purpose": "Detect money, dispatch, hidden tracking, fake-live, private leak or real-world risk.", "light": "🟠"},
    {"stage": 6, "name": "Lock", "purpose": "Keep restricted functions locked before any deeper simulation.", "light": "🔒"},
    {"stage": 7, "name": "Proof Need", "purpose": "List the exact proof required before green.", "light": "🟡"},
    {"stage": 8, "name": "Source", "purpose": "Check whether a named source, timestamp or receipt exists.", "light": "🟡"},
    {"stage": 9, "name": "Route/API", "purpose": "Check route or API existence, expected status, JSON shape and safe fallback.", "light": "🛣️"},
    {"stage": 10, "name": "Data", "purpose": "Check whether place, business, event or live-source data is real or seeded.", "light": "🗺️"},
    {"stage": 11, "name": "Simulation", "purpose": "Run the dry-run scenario and produce visible safe signals.", "light": "🧠"},
    {"stage": 12, "name": "Compare", "purpose": "Compare expected state against actual or known proof state.", "light": "📊"},
    {"stage": 13, "name": "Gap", "purpose": "Name missing files, routes, proof, data, logs or receipts.", "light": "🟠"},
    {"stage": 14, "name": "Green Gate", "purpose": "Score green/yellow/orange/red without fake green.", "light": "🟢"},
    {"stage": 15, "name": "Guardian", "purpose": "Confirm privacy, safety, youth and compliance guardrails.", "light": "🛡️"},
    {"stage": 16, "name": "HRM Receipt", "purpose": "Prepare the memory/audit receipt fields.", "light": "📚"},
    {"stage": 17, "name": "Human Authority Decision", "purpose": "Mark whether Human Authority approval is required before any consequential action.", "light": "👑"},
    {"stage": 18, "name": "Patch Plan", "purpose": "Recommend the smallest safe patch with rollback path.", "light": "🛠️"},
    {"stage": 19, "name": "Deploy Proof", "purpose": "Require deploy ID, live status and fresh error scan before green.", "light": "🚀"},
    {"stage": 20, "name": "Learn", "purpose": "Feed the safe outcome into HRM readiness without changing authority.", "light": "🟣"},
    {"stage": 21, "name": "Lock Result", "purpose": "Return final status, locks, blockers, next action and memory requirement.", "light": "✅"},
)

REVIEW_LENSES_7 = (
    {"id": "proof", "name": "Proof", "signal": "🔎"},
    {"id": "protection", "name": "Protection", "signal": "🛡️"},
    {"id": "creation", "name": "Creation", "signal": "🏗️"},
    {"id": "identity", "name": "Identity", "signal": "🪪"},
    {"id": "decision", "name": "Decision", "signal": "⚖️"},
    {"id": "memory", "name": "Memory", "signal": "🧾"},
    {"id": "growth_recovery", "name": "Growth / Recovery", "signal": "🌱"},
)

REGISTERED_ADVISORY_ROSTER = (
    "Neo",
    "Morpheus",
    "Trinity",
    "Oracle",
    "Architect",
    "Keymaker",
    "Seraph",
    "Nirmata",
    "Akela",
    "Shere Khan",
    "Bagheera",
    "Owl",
    "Falcon",
    "Spider",
    "Octopus",
)

BASE_JUDGE_PANEL_7 = (
    "Shere Khan",
    "Bagheera",
    "Seraph",
    "Nirmata",
    "Morpheus",
    "Akela",
    "Owl",
)

SIMULATION_ACTIONS = (
    {"id": "run_war_room", "label": "Run War Room", "signal": "⚔️", "default_stage": 11, "depth": 7, "can_do": "Open the governed seven-judge review for the current case.", "simulation_output": "seven lenses, judge panel, evidence gaps, blockers and next gate", "locked": "Recommendation only; Human Authority remains final."},
    {"id": "deep_dive_21", "label": "Deep Dive 21", "signal": "🟣", "default_stage": 21, "depth": 21, "can_do": "Run the full three-pass deep-review frame: establish, challenge and consolidate.", "simulation_output": "21-stage status, seven lenses, dissent, recovery and next gate", "locked": "Deep review does not grant execution authority."},
    {"id": "agent_advisory", "label": "Bring In Agent", "signal": "👥", "default_stage": 6, "depth": 7, "can_do": "Add one registered OAP specialist to the advisory context.", "simulation_output": "requested agent, registry status, advisory role and authority boundary", "locked": "Agent remains advisory and cannot approve or execute."},
    {"id": "auto_select_7", "label": "Auto Select 7", "signal": "🎯", "default_stage": 6, "depth": 7, "can_do": "Select a registered seven-agent panel with one specialist seat adapted to the case.", "simulation_output": "seven registered judges and specialist-selection reason", "locked": "Selection changes review participation only, never authority."},
    {"id": "red_team", "label": "Red Team", "signal": "⚔️", "default_stage": 12, "depth": 21, "can_do": "Attack the current recommendation, assumptions and evidence gaps.", "simulation_output": "counter-case, failure hypotheses, evidence challenges and dissent", "locked": "Red team cannot bypass Guardian or create harmful execution authority."},
    {"id": "dependency_scan", "label": "Dependencies", "signal": "🔗", "default_stage": 12, "depth": 7, "can_do": "Review upstream/downstream dependencies and cascade paths.", "simulation_output": "dependency states, single points of failure and isolation options", "locked": "Does not mutate services or fail over production."},
    {"id": "failure_test", "label": "Failure Test", "signal": "💥", "default_stage": 13, "depth": 21, "can_do": "Run a bounded worst-credible failure and cascade simulation.", "simulation_output": "failure trigger, blast radius, fallback, stop condition and recovery order", "locked": "Simulation only; no destructive production test is launched."},
    {"id": "guardian_check", "label": "Guardian Check", "signal": "🛡️", "default_stage": 15, "depth": 7, "can_do": "Review privacy, safety, public/private and authority boundaries.", "simulation_output": "Guardian state, blocked conditions and required safeguards", "locked": "Guardian cannot self-approve a consequential action."},
    {"id": "hrm_check", "label": "HRM Check", "signal": "💾", "default_stage": 16, "depth": 7, "can_do": "Review memory quality, provenance, receipt requirements and missing history.", "simulation_output": "memory state, provenance gaps, receipt fields and freshness", "locked": "Does not rewrite history or create a fake production receipt."},
    {"id": "recovery_test", "label": "Recovery Test", "signal": "🔄", "default_stage": 20, "depth": 21, "can_do": "Simulate detection, isolation, fallback, integrity verification, reconciliation and resume.", "simulation_output": "recovery chain, RTO/RPO questions, integrity proof and resume gate", "locked": "Does not trigger production failover or restore."},
    {"id": "next_gate", "label": "Next Gate", "signal": "➡️", "default_stage": 18, "depth": 7, "can_do": "Return the smallest safe next proof or implementation gate.", "simulation_output": "highest-leverage next gate, required evidence and stop condition", "locked": "Recommendation only; no patch or deploy occurs."},
    {"id": "score_7x", "label": "Score 7×", "signal": "⭐", "default_stage": 14, "depth": 7, "can_do": "Project the seven canonical review lenses without converting confidence into proof.", "simulation_output": "seven-lens score placeholders tied to evidence state", "locked": "No 7★ without proof."},
    {"id": "strongest_link", "label": "Strongest Link", "signal": "🟢", "default_stage": 12, "depth": 7, "can_do": "Identify the strongest currently supported part of the case.", "simulation_output": "strongest supported link and supporting proof requirement", "locked": "Does not erase weaker or red findings."},
    {"id": "weakest_link", "label": "Weakest Link", "signal": "🟡", "default_stage": 13, "depth": 7, "can_do": "Identify the limiting evidence, dependency or recovery gap.", "simulation_output": "weakest link, blast radius, missing proof and fix", "locked": "Weakest finding may not be hidden."},
    {"id": "minority_report", "label": "Minority Report", "signal": "📋", "default_stage": 12, "depth": 21, "can_do": "Preserve serious dissent even if the majority recommendation differs.", "simulation_output": "dissent position, supporting evidence gap and condition for reconsideration", "locked": "Dissent remains advisory and visible."},
    {"id": "judge_speeches", "label": "Judge Speeches", "signal": "🗣️", "default_stage": 12, "depth": 7, "can_do": "Show public-safe judge role statements for the selected panel.", "simulation_output": "short role statement per judge; no hidden chain-of-thought", "locked": "Private reasoning and internal deliberation stay protected."},
    {"id": "public_route_sweep", "label": "Public route sweep", "signal": "🛣️", "default_stage": 9, "depth": 7, "can_do": "Preview-check public routes for 200/302 targets and naming alignment.", "simulation_output": "route list, expected status, missing route warning, next patch recommendation", "locked": "Does not change routes without Human Authority-approved code patch."},
    {"id": "private_fail_closed_check", "label": "Private fail-closed check", "signal": "🔒", "default_stage": 4, "depth": 7, "can_do": "Confirm private War Room/SMI routes should reject anonymous access.", "simulation_output": "private route list, expected anonymous result, Founder-only requirement", "locked": "Does not bypass auth or reveal private state."},
    {"id": "public_private_leak_scan", "label": "Public/private leak scan", "signal": "🛡️", "default_stage": 15, "depth": 7, "can_do": "Scan public-facing labels for private words, debug language and fake-live wording.", "simulation_output": "leak term, file/section hint, severity, safe replacement wording", "locked": "Does not publish private logs or secrets."},
    {"id": "green_gate_simulation", "label": "Green Gate simulation", "signal": "🟢", "default_stage": 14, "depth": 7, "can_do": "Score whether a function can be green, yellow, orange or red from proof fields.", "simulation_output": "status light, proof seen, proof missing, reason not green", "locked": "Cannot mark whole product green without proof-runner pass."},
    {"id": "map_place_simulation", "label": "Map/place simulation", "signal": "🗺️", "default_stage": 10, "depth": 7, "can_do": "Preview On Any Place results for places, spots, categories and source timestamps.", "simulation_output": "area, points, source timestamp, missing tiles/data/geometry", "locked": "Does not claim every shop, road or alley is live."},
    {"id": "movement_route_simulation", "label": "Movement route simulation", "signal": "🚶", "default_stage": 11, "depth": 7, "can_do": "Preview On Any Route distance/ETA proof and request state.", "simulation_output": "proof_id, from/to, ETA, route state, next gate", "locked": "No turn-by-turn, dispatch or hidden tracking without proof/consent."},
    {"id": "direct_supply_simulation", "label": "Direct supply simulation", "signal": "🏪", "default_stage": 8, "depth": 7, "can_do": "Preview OAP Direct listings, supplier proof needs, quote/hold/reservation gates.", "simulation_output": "supplier proof state, listing proof, receipt needed, blocked confirmation", "locked": "No confirmed booking, supplier claim or payment capture without receipt."},
    {"id": "ride_drop_simulation", "label": "Ride/Drop simulation", "signal": "🚘", "default_stage": 6, "depth": 7, "can_do": "Preview On Any Ride and On Any Drop request flow and licence/dispatch gates.", "simulation_output": "request preview, licence proof needed, dispatch locked, payment locked", "locked": "No driver/courier assignment and no operator claim without licence proof."},
    {"id": "live_pattern_simulation", "label": "Live Pattern simulation", "signal": "📡", "default_stage": 7, "depth": 7, "can_do": "Preview traffic-style, event, crowd and open-now signals as proof-gated patterns.", "simulation_output": "signal level, source need, timestamp need, stale/fake-live warning", "locked": "No true live claim without timestamped source proof."},
    {"id": "hrm_receipt_simulation", "label": "HRM receipt simulation", "signal": "📚", "default_stage": 16, "depth": 7, "can_do": "Preview the memory receipt SMI should write after checks and deployments.", "simulation_output": "check_id, status, proof, missing piece, lock, blocker, deploy id, Human Authority decision", "locked": "Does not rewrite history or self-approve decisions."},
    {"id": "aci_readiness_simulation", "label": "ACI readiness simulation", "signal": "🧬", "default_stage": 20, "depth": 21, "can_do": "Check whether SMI is ready to move toward Adaptive Coherent Intelligence.", "simulation_output": "coherence score, missing memory/proof loops, autonomy lock state", "locked": "Does not claim AGI, ASI or autonomous authority."},
)


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
    if any(word in text for word in ("aci", "adaptive", "coherent", "agi", "asi")):
        return _stage(20)
    if any(word in text for word in ("source", "timestamp", "supplier")):
        return _stage(8)
    return _stage(int(action.get("default_stage", 11)))


def _stage_window(stage_number: int) -> dict[str, object]:
    previous_stage = _stage(stage_number - 1) if stage_number > 1 else None
    current_stage = _stage(stage_number)
    next_stage = _stage(stage_number + 1) if stage_number < 21 else None
    return {"previous": previous_stage, "current": current_stage, "next": next_stage, "progress": f"{stage_number}/21"}


def _select_judges(target: str) -> tuple[str, ...]:
    text = target.casefold()
    panel = list(BASE_JUDGE_PANEL_7)
    if any(word in text for word in ("recovery", "failure", "restore", "coherence")):
        panel[-1] = "Neo"
    elif any(word in text for word in ("network", "dependency", "nexus", "cascade")):
        panel[-1] = "Spider"
    elif any(word in text for word in ("multi-system", "multiple systems", "coordination")):
        panel[-1] = "Octopus"
    elif any(word in text for word in ("evidence", "precision", "monitor", "proof")):
        panel[-1] = "Falcon"
    return tuple(panel)


def _requested_agent(target: str) -> dict[str, object] | None:
    clean = target.strip()
    if not clean:
        return None
    requested = clean.split("|", 1)[0].strip()
    match = next((name for name in REGISTERED_ADVISORY_ROSTER if name.casefold() == requested.casefold()), None)
    return {"requested": requested, "registered_for_control": match is not None, "canonical_name": match, "authority": "advisory_only"}


def list_actions() -> dict[str, object]:
    """Return the safe War Room simulation action catalogue."""
    return {
        "component": "War Room Simulation Actions",
        "generated_at": _now(),
        "mode": "dry_run_preview_only",
        "stage_count": 21,
        "stages": SIMULATION_STAGES_21,
        "review_lenses": REVIEW_LENSES_7,
        "registered_advisory_roster": REGISTERED_ADVISORY_ROSTER,
        "baseline_judge_panel": BASE_JUDGE_PANEL_7,
        "action_count": len(SIMULATION_ACTIONS),
        "actions": SIMULATION_ACTIONS,
        "global_locks": {"payment_capture_enabled": False, "dispatch_enabled": False, "hidden_tracking_enabled": False, "self_approval_enabled": False, "agi_or_asi_claim_enabled": False},
        "human_authority_final": True,
        "overall_green": False,
    }


def simulate(action_id: object = None, target: object = None, stage: object = None) -> dict[str, object]:
    """Return a deterministic, read-only War Room simulation report."""
    clean_action = str(action_id or "green_gate_simulation").strip().lower().replace(" ", "_")
    clean_target = " ".join(str(target or "Current OAP system").strip().split())[:160]
    action = next((item for item in SIMULATION_ACTIONS if item["id"] == clean_action), None)
    if action is None:
        action = next(item for item in SIMULATION_ACTIONS if item["id"] == "green_gate_simulation")
    if stage in (None, "", "auto"):
        stage_info = _stage_for(action, clean_target)
    else:
        try:
            stage_info = _stage(int(stage))
        except (TypeError, ValueError):
            stage_info = _stage_for(action, clean_target)
    generated_at = _now()
    receipt_id = sha256(f"{action['id']}|{clean_target}|{stage_info['stage']}|{generated_at[:16]}".encode()).hexdigest()[:16]
    judge_panel = _select_judges(clean_target)
    agent_request = _requested_agent(clean_target) if action["id"] == "agent_advisory" else None
    speeches = None
    if action["id"] == "judge_speeches":
        speeches = tuple({"judge": judge, "speech": f"{judge}: I will review the evidence, risk, objection and vote within Human Authority boundaries."} for judge in judge_panel)
    return {
        "component": "War Room Simulation Run",
        "generated_at": generated_at,
        "receipt_id": receipt_id,
        "mode": "simulation_only_no_execution",
        "depth": int(action.get("depth", 7)),
        "stage_system": "21_stage_situation_simulation",
        "stage": _stage_window(int(stage_info["stage"])),
        "action": action,
        "target": clean_target,
        "war_room_signal": "🟡",
        "learning_signal": "🟣" if int(action.get("depth", 7)) == 21 else None,
        "review_lenses": REVIEW_LENSES_7,
        "judge_panel": judge_panel,
        "judge_count": len(judge_panel),
        "agent_request": agent_request,
        "judge_speeches": speeches,
        "visible_signals": {
            "checking": action["label"],
            "stage": f"Stage {stage_info['stage']}/21 — {stage_info['name']}",
            "stage_purpose": stage_info["purpose"],
            "proof_needed": action["simulation_output"],
            "locked": action["locked"],
            "blocked": "payment, dispatch, hidden tracking, fake green, private leak and self-approval remain blocked",
            "next_before_green": "Compare evidence, expose gaps, run Guardian/Green Gate, preserve dissent, test recovery and return the smallest safe next gate.",
            "hrm_memory": "A real consequential action requires a governed HRM receipt; this simulation does not write one.",
        },
        "human_options": ("APPROVE", "APPROVE WITH CONDITIONS", "CONTINUE WAR ROOM", "HOLD", "REJECT / STOP"),
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
        "private_chain_of_thought_exposed": False,
        "human_authority_final": True,
    }
