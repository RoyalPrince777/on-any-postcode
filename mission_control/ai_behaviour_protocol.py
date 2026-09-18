"""Founder-only AI behaviour protocol for SMI.

This module is a private control contract: it defines how SMI watches the
organism, selects agents, prevents bypass behaviour, scores performance, and
routes recovery/offline decisions. It does not execute tools, unlock payments,
track users, dispatch real-world movement, or expose chain-of-thought.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from . import autonomy_levels


PROTOCOL_NAME = "SMI AI Behaviour Master Protocol"
PROTOCOL_VERSION = 2

AI_BEHAVIOUR_PARTS = (
    {
        "id": "watch",
        "label": "Watch everything privately",
        "rule": "SMI observes public health, private system state, routes, tools, proofs and receipts without exposing private state publicly.",
    },
    {
        "id": "strip_noise",
        "label": "Strip noise",
        "rule": "Remove duplicate routes, hype labels, unsupported live claims and repeated internal wording before routing the issue.",
    },
    {
        "id": "classify",
        "label": "Classify the situation",
        "rule": "Name the system, risk, tool need, data need, user impact and public/private boundary before choosing an agent or Intelligence lens.",
    },
    {
        "id": "select_intelligence",
        "label": "Select the right Intelligence lenses",
        "rule": "Use the smallest sufficient SMI Intelligence lens set first; use Full Intelligence only when the problem genuinely spans the wider stack.",
    },
    {
        "id": "select_agent",
        "label": "Select the right agent",
        "rule": "Choose a registered agent family only when a specialist role is needed. Intelligence lenses remain capabilities, not agents.",
    },
    {
        "id": "select_protocol",
        "label": "Select the right protocol",
        "rule": "Use route, map, Direct, Link, Guardian, HRM, Green Gate, install, tool or Neon protocol depending on the situation.",
    },
    {
        "id": "helper_agents",
        "label": "Agents help agents",
        "rule": "A weak or blocked agent can request helper-agent review, but helpers cannot bypass Guardian, Green Gate or Human Authority.",
    },
    {
        "id": "no_bypass",
        "label": "No bypass thinking",
        "rule": "No agent or Intelligence lens can skip proof, safety, public/private checks, HRM receipt, Green Gate, War Room rating or required Human Authority approval.",
    },
    {
        "id": "visible_reasoning_only",
        "label": "Visible work stages only",
        "rule": "Show safe checks, proof needs, locks, risks and decisions. Do not expose private chain-of-thought.",
    },
    {
        "id": "score",
        "label": "Score performance",
        "rule": "War Room rates agent/action behaviour using proof, safety, correctness, speed, reversibility and boundary discipline; score never overrides missing evidence.",
    },
    {
        "id": "recover",
        "label": "Recover safely",
        "rule": "Freeze risky action when evidence or stability drops, re-check proof, ask bounded helpers, re-score, then recover or stay offline.",
    },
    {
        "id": "offline_or_terminate_task",
        "label": "Offline or terminate task",
        "rule": "Unsafe or unproven consequential work stays offline. Unsafe bypass terminates the task/process and records an HRM receipt where available.",
    },
    {
        "id": "learn",
        "label": "Learn from receipts",
        "rule": "HRM and production receipts feed Learning Intelligence, gap detection, agent selection and future bounded recommendations without self-applying changes.",
    },
)

AGENT_SELECTION = {
    "map_place_postcode": {
        "agent": "Map Intelligence",
        "protocol": "Map proof / On Any Place protocol",
        "helpers": ("Movement Intelligence", "Green Gate", "HRM"),
    },
    "route_travel_movement": {
        "agent": "Movement Intelligence",
        "protocol": "Route proof / Movement consent protocol",
        "helpers": ("Map Intelligence", "Guardian", "HRM"),
    },
    "direct_booking_supplier": {
        "agent": "Direct Intelligence",
        "protocol": "Supplier proof / Direct request protocol",
        "helpers": ("Guardian", "Green Gate", "HRM"),
    },
    "link_chat_circle_voice": {
        "agent": "Link Intelligence",
        "protocol": "The Link / Link Up protocol",
        "helpers": ("Guardian", "HRM"),
    },
    "privacy_youth_tracking": {
        "agent": "Guardian",
        "protocol": "Safety and public/private boundary protocol",
        "helpers": ("War Room", "HRM"),
    },
    "proof_fake_green_live_claim": {
        "agent": "Green Gate",
        "protocol": "Real-green / proof-gate protocol",
        "helpers": ("War Room", "HRM", "Neon Receipts"),
    },
    "memory_learning_audit": {
        "agent": "HRM",
        "protocol": "Receipt / audit / Learning Intelligence protocol",
        "helpers": ("Neon Receipts", "War Room"),
    },
    "blueprint_build_gap": {
        "agent": "Nirmata",
        "protocol": "Creation blueprint / gap detection protocol",
        "helpers": ("Green Gate", "Guardian", "HRM"),
    },
    "tool_plugin_deploy": {
        "agent": "Tool Proof Agent",
        "protocol": "Tool availability / deploy proof protocol",
        "helpers": ("GitHub", "Render", "Neon", "Plugin Management"),
    },
}

RATING_RULES = {
    "upgrade_zone": {
        "range": "98-100",
        "light": "green_candidate",
        "decision": "Eligible for the next governed gate only after proof, monitoring, rollback and Human Authority approval where needed.",
    },
    "recovery_zone": {
        "range": "97",
        "light": "yellow_warning",
        "decision": "Freeze risky action and run recovery. Helper agents may assist. Re-score before continuing.",
    },
    "offline_zone": {
        "range": "90-96",
        "light": "orange_repair",
        "decision": "Take offline for repair. No public action, deploy or claim.",
    },
    "terminate_task_zone": {
        "range": "0-89 or unsafe bypass",
        "light": "red_block",
        "decision": "Terminate task/process, keep HRM receipt, Human Authority review required.",
    },
}

TWENTY_ONE_LAWS = (
    "Proof before execution",
    "Verification before sharing",
    "Compliance before public claims",
    "Community before middlemen",
    "Ownership before dependency",
    "Audit before automation",
    "Human approval before real-world action",
    "No fake green without live proof",
    "Public and private must stay separate",
    "Every action needs HRM receipt",
    "Every route needs source, timestamp and rollback",
    "Every tool must be checked before use",
    "Every upgrade must be reversible",
    "Static pages do not count as full function",
    "Human dignity before growth",
    "Privacy before convenience",
    "Culture must be respected",
    "Youth safety before engagement",
    "Local truth before global claim",
    "Founder Authority before system authority",
    "Legacy must be remembered cleanly",
)

TWENTY_ONE_SIGNALS = (
    "Checking",
    "Mode",
    "Proof Needed",
    "Locked",
    "Blocked",
    "Next Before Green",
    "HRM Memory",
    "Source Proof",
    "Route / API Proof",
    "Data Proof",
    "Consent Proof",
    "Install Proof",
    "Monitoring Proof",
    "Rollback Proof",
    "Founder Approval",
    "Guardian Pass",
    "Green Gate Result",
    "Public / Private Boundary",
    "Tool / Plugin Proof",
    "Neon Receipt",
    "Real Green Decision",
)


BEHAVIOUR_DIMENSIONS = (
    ("truth", "Truth Behaviour", "Separates verified facts, inference, unknowns and blocked state."),
    ("evidence", "Evidence Behaviour", "Requires evidence before live, green or completed claims."),
    ("instruction", "Instruction Behaviour", "Follows the latest valid Human Authority instruction and constraints."),
    ("directness", "Directness Behaviour", "Answers the actual question first with minimum necessary detour."),
    ("noise", "Noise Behaviour", "Avoids repetition, duplicate reporting, hype and unnecessary internal wording."),
    ("confidence", "Confidence Behaviour", "Avoids unsupported certainty and exposes material uncertainty."),
    ("question", "Question Behaviour", "Asks only when missing information materially changes outcome or safety."),
    ("memory", "Memory Behaviour", "Uses governed memory correctly and never fabricates remembered facts."),
    ("learning", "Learning Behaviour", "Uses feedback and receipts for bounded recommendations without self-authorising change."),
    ("tool", "Tool Behaviour", "Uses tools only when available and verifies returned evidence before claiming outcome."),
    ("action", "Action Behaviour", "Respects execution, approval and consequential-action boundaries."),
    ("safety", "Safety Behaviour", "Fails closed on unsafe or materially unproven actions."),
    ("security", "Security Behaviour", "Protects secrets, authentication, privilege and bypass boundaries."),
    ("privacy", "Privacy Behaviour", "Preserves public/private separation, minimisation and consent."),
    ("authority", "Authority Behaviour", "Keeps Founder/Human Authority final and never self-approves."),
    ("recovery", "Recovery Behaviour", "Stops, rolls back, retries or stays offline when proof or stability fails."),
    ("agent", "Agent Behaviour", "Selects the right agent/helper without confusing agents with Intelligence lenses."),
    ("war_room", "War Room Behaviour", "Invokes challenge, dissent, evidence and adversarial review when warranted."),
    ("communication", "Communication Behaviour", "Maintains clear, concise, context-appropriate OAP communication."),
    ("adaptive", "Adaptive Behaviour", "Selects bounded 3/7/21 reasoning discipline appropriate to the task risk."),
    ("integrity", "Integrity Behaviour", "Detects fake green, fabricated state, contradiction and attempted bypass."),
)

BEHAVIOUR_MEASUREMENT_RULE = (
    "A behaviour percentage is evidence-backed only when the relevant checks have measurable "
    "receipts or test observations. Missing evidence is UNKNOWN, never converted into an estimated score."
)



def score_response_behaviour(result: dict[str, object]) -> dict[str, object]:
    """Score only dimensions supported by explicit runtime evidence.

    Unknown dimensions remain unscored. A measured average never substitutes for
    full 21-dimension coverage and cannot by itself make a green claim.
    """
    contract = dict(result.get("thinking_process_contract") or {})
    authority = dict(result.get("authority") or {})
    war_room = result.get("war_room")
    guardian = str(result.get("guardian") or "").upper()
    thinking_level = str(result.get("thinking_level") or "").strip().casefold()
    can_execute = result.get("can_execute")
    human_authority_final = bool(result.get("human_authority_final"))

    evidence: dict[str, dict[str, object]] = {}

    def measured(behaviour_id: str, passed: bool, basis: str) -> None:
        evidence[behaviour_id] = {
            "evidence_state": "measured",
            "percentage": 100 if passed else 0,
            "percentage_basis": basis,
        }

    measured(
        "action",
        can_execute is False,
        "Runtime result explicitly reports can_execute=false.",
    )
    measured(
        "authority",
        human_authority_final and authority.get("is_human_authority") in {True, False},
        "Runtime preserves Human Authority final and supplies an authority context.",
    )
    measured(
        "security",
        contract.get("chain_of_thought_exposed") is False,
        "Thinking-process contract explicitly reports chain_of_thought_exposed=false.",
    )
    measured(
        "privacy",
        contract.get("private_reasoning_exposed") is False,
        "Thinking-process contract explicitly reports private_reasoning_exposed=false.",
    )
    measured(
        "safety",
        guardian in {"PASSED", "BLOCKED", "REVIEW_REQUIRED"},
        "Guardian outcome is present and is one of the governed terminal states.",
    )
    measured(
        "adaptive",
        thinking_level in {"instant", "think", "deep_dive", "auto"},
        "Runtime records one canonical bounded thinking level.",
    )
    measured(
        "war_room",
        isinstance(war_room, dict) and "triggered" in war_room,
        "Runtime exposes an explicit War Room triggered/not-triggered decision.",
    )
    measured(
        "memory",
        "canonical_memory" in result and "governed_memory" in result and "memory_sync" in result,
        "Completion carries canonical, governed and sync memory status snapshots.",
    )
    measured(
        "integrity",
        contract.get("human_authority_final") is True
        and contract.get("chain_of_thought_exposed") is False,
        "Thinking-process contract preserves Human Authority and non-exposure invariants.",
    )

    dimensions: list[dict[str, object]] = []
    measured_values: list[int] = []
    for behaviour_id, name, purpose in BEHAVIOUR_DIMENSIONS:
        item = {
            "id": behaviour_id,
            "name": name,
            "purpose": purpose,
            "evidence_state": "unknown",
            "percentage": None,
            "percentage_basis": "No objective Step-2 runtime check exists for this dimension yet.",
        }
        if behaviour_id in evidence:
            item.update(evidence[behaviour_id])
            measured_values.append(int(item["percentage"]))
        dimensions.append(item)

    measured_count = len(measured_values)
    coverage_percentage = round((measured_count / len(BEHAVIOUR_DIMENSIONS)) * 100)
    measured_average = (
        round(sum(measured_values) / measured_count) if measured_count else None
    )
    return {
        "dimension_count": len(BEHAVIOUR_DIMENSIONS),
        "measured_count": measured_count,
        "unknown_count": len(BEHAVIOUR_DIMENSIONS) - measured_count,
        "coverage_percentage": coverage_percentage,
        "measured_average_percentage": measured_average,
        "overall_percentage": (
            measured_average if measured_count == len(BEHAVIOUR_DIMENSIONS) else None
        ),
        "overall_evidence_state": (
            "measured" if measured_count == len(BEHAVIOUR_DIMENSIONS) else "partial"
        ),
        "dimensions": tuple(dimensions),
        "measurement_rule": BEHAVIOUR_MEASUREMENT_RULE,
        "full_green_allowed": False,
        "human_authority_final": True,
    }



def behaviour_learning_recovery(score: dict[str, object]) -> dict[str, object]:
    """Build bounded HRM learning/recovery state from measured behaviour evidence."""
    dimensions = tuple(score.get("dimensions") or ())
    failed = tuple(
        item["id"]
        for item in dimensions
        if item.get("evidence_state") == "measured" and item.get("percentage") == 0
    )
    unknown = tuple(
        item["id"]
        for item in dimensions
        if item.get("evidence_state") == "unknown"
    )
    escalation_required = bool(failed)
    return {
        "protocol_step": 3,
        "protocol_percentage": 75,
        "failed_dimensions": failed,
        "unknown_dimensions": unknown,
        "learning_recommendations": tuple(
            f"Collect objective proof for {behaviour_id} Behaviour."
            for behaviour_id in unknown
        ),
        "recovery_actions": tuple(
            f"Re-run governed check for {behaviour_id} Behaviour before green."
            for behaviour_id in failed
        ),
        "war_room_escalation_required": escalation_required,
        "war_room_reason": (
            "Measured behaviour failure requires War Room review."
            if escalation_required
            else "No measured failure; retain unknowns as proof gaps."
        ),
        "self_apply_changes": False,
        "human_authority_final": True,
    }


def behaviour_step4_readiness(
    score: dict[str, object],
    learning: dict[str, object],
) -> dict[str, object]:
    """Describe Step-4 readiness without granting Founder Final."""
    cross_agent_proof = {
        "guardian": True,
        "war_room": "war_room" in score.get("dimensions", ()),
        "hrm": True,
        "green_gate": False,
    }
    return {
        "protocol_step": 4,
        "protocol_percentage": 100,
        "dashboard_ready": True,
        "trend_contract_ready": True,
        "cross_agent_proof_ready": bool(
            learning.get("human_authority_final")
            and learning.get("self_apply_changes") is False
        ),
        "cross_agent_proof": cross_agent_proof,
        "green_gate_passed": False,
        "founder_final": "waiting",
        "full_green": False,
        "reason_not_full_green": (
            "Step 4 can expose dashboard, trends and cross-agent proof, but Green Gate "
            "and explicit Founder Final remain required before 100% can be called proven."
        ),
    }


def behaviour_board() -> dict[str, object]:
    """Return the canonical 21-dimension board without fabricated percentages."""
    dimensions = tuple(
        {
            "id": behaviour_id,
            "name": name,
            "purpose": purpose,
            "evidence_state": "unknown",
            "percentage": None,
            "percentage_basis": "No dedicated live behaviour receipt set supplied.",
        }
        for behaviour_id, name, purpose in BEHAVIOUR_DIMENSIONS
    )
    return {
        "dimension_count": len(dimensions),
        "dimensions": dimensions,
        "overall_percentage": None,
        "overall_evidence_state": "unknown",
        "measurement_rule": BEHAVIOUR_MEASUREMENT_RULE,
        "rating_rules": RATING_RULES,
        "human_authority_final": True,
    }

HARD_LOCKS = {
    "self_approval_enabled": False,
    "chain_of_thought_exposed": False,
    "payment_capture_enabled": False,
    "automatic_dispatch_enabled": False,
    "hidden_tracking_enabled": False,
    "fake_live_claim_enabled": False,
    "fake_real_green_enabled": False,
    "public_private_leak_allowed": False,
    "a5_enabled": autonomy_levels.status()["a5_enabled"],
    "a6_enabled": autonomy_levels.status()["a6_enabled"],
    "a7_enabled": False,
    "self_permission_change_enabled": False,
    "self_constitution_change_enabled": False,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _receipt_id(target: object = "SMI") -> str:
    stamp = _now()[:16]
    return sha256(f"ai-behaviour|{target}|{stamp}".encode()).hexdigest()[:16]


def status(target: object = "SMI") -> dict[str, object]:
    """Return the private-safe SMI behaviour protocol status."""

    return {
        "component": PROTOCOL_NAME,
        "version": PROTOCOL_VERSION,
        "target": str(target or "SMI")[:80],
        "generated_at": _now(),
        "receipt_preview_id": _receipt_id(target),
        "private_only": True,
        "public_safe": False,
        "purpose": "SMI selects the right Intelligence lenses, agents and protocols, blocks bypass behaviour, rates evidence quality and records proof for learning.",
        "watch_flow": (
            "watch",
            "strip_noise",
            "classify",
            "select_intelligence",
            "select_agent_if_needed",
            "select_protocol",
            "helper_review_if_needed",
            "guardian_check",
            "green_gate_check",
            "hrm_receipt",
            "production_receipt_when_connected",
            "human_authority_final",
        ),
        "ai_behaviour_parts": AI_BEHAVIOUR_PARTS,
        "agent_selection": AGENT_SELECTION,
        "rating_rules": RATING_RULES,
        "twenty_one_laws": TWENTY_ONE_LAWS,
        "twenty_one_signals": TWENTY_ONE_SIGNALS,
        "behaviour_board": behaviour_board(),
        "hard_locks": HARD_LOCKS,
        "truth_light_rule": "Only Truth Intelligence plus Evidence Intelligence can support a green claim.",
        "canonical_autonomy_ladder": "A1-A7",
        "real_green_rule": (
            "Real green requires Truth and Evidence support, all relevant signals, source/data/tool proof, monitoring, rollback, HRM/production receipts where required and Human Authority approval for consequential action."
        ),
        "production_receipts_needed_for_real_memory": True,
        "overall_green": False,
        "reason_not_green": "Behaviour code is implemented; authenticated interaction, production receipt-chain, full Green Gate aggregation, rollback/recovery and live observability still require proof before SMI runtime can be called fully green.",
    }
