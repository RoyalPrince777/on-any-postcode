"""Founder-only SMI Deep-Dive Simulation Protocol.

The deep dive starts from SMI, not from the War Room. SMI selects the smallest
sufficient depth (3 / 7 / 21) and escalates only when evidence, risk, conflict
or Founder intent requires it. This module is read-only: it does not execute,
approve, deploy, dispatch, track, spend, or write production records.
"""
from __future__ import annotations

from typing import Any

CANONICAL_FLOW: tuple[str, ...] = (
    "User / Human Authority",
    "SMI Protocol",
    "Depth Selection",
    "Evidence + Context",
    "HRM / JOOG Memory",
    "Specialist Intelligence",
    "Registered Agent Challenge",
    "War Room when triggered/requested",
    "Guardian + Judgement",
    "Human Authority Final",
)

DEPTH_MODES: tuple[dict[str, object], ...] = (
    {
        "id": "auto",
        "label": "◎ AUTO",
        "depth": "adaptive",
        "use_for": "SMI chooses the smallest sufficient depth and escalates 3 → 7 → 21 when justified",
    },
    {
        "id": "instant_3",
        "label": "⚡ INSTANT 3",
        "depth": 3,
        "use_for": "simple, low-risk, obvious tasks",
    },
    {
        "id": "medium_7",
        "label": "🧠 MEDIUM 7",
        "depth": 7,
        "use_for": "analytical checks, structure, normal review, moderate uncertainty",
    },
    {
        "id": "high_21",
        "label": "👑 HIGH 21",
        "depth": 21,
        "use_for": "deep multi-system, consequential, safety, money, dispatch, authority, or conflicting evidence",
    },
)

ROUTE_FIELDS: tuple[str, ...] = (
    "Intelligence World(s)",
    "system(s)",
    "brain regions",
    "relevant evidence",
    "HRM / JOOG memory",
    "Matrix relationships",
    "NEXUS dependencies",
    "Guardian boundaries",
)

SIMULATION_MODEL: tuple[str, ...] = (
    "Known facts",
    "Unknowns",
    "Assumptions",
    "Dependencies",
    "Possible outcomes",
    "Failure paths",
    "Recovery paths",
)

WAR_ROOM_TRIGGERS: tuple[str, ...] = (
    "Founder requests War Room",
    "significant risk exists",
    "evidence conflicts",
    "consequences are high",
    "multiple systems disagree",
    "recovery is uncertain",
    "SMI escalates from 7 to 21",
)

FOUNDER_DECISIONS: tuple[str, ...] = (
    "APPROVE",
    "APPROVE WITH CONDITIONS",
    "CONTINUE WAR ROOM",
    "HOLD",
    "REJECT / STOP",
)

WAR_ROOM_BUTTONS: tuple[dict[str, str], ...] = (
    {"button": "▶", "name": "RUN WAR ROOM", "does": "Start the governed review at the selected depth."},
    {"button": "⏹", "name": "STOP", "does": "Stop the current bounded simulation/review run."},
    {"button": "↻", "name": "CHALLENGE AGAIN", "does": "Run another registered-agent challenge against the recommendation."},
    {"button": "⚖", "name": "COMPARE", "does": "Compare viable alternatives, evidence, risk and reversibility."},
    {"button": "👑", "name": "HIGH 21", "does": "Escalate SMI to the full 3x7 review cycle."},
    {"button": "👥", "name": "AGENTS", "does": "Show or choose registered specialists selected for this case."},
    {"button": "🎯", "name": "AUTO SELECT", "does": "SMI selects the strongest relevant registered agents for the current issue."},
    {"button": "🔎", "name": "EVIDENCE", "does": "Show sources, freshness, confidence and gaps; no private chain-of-thought."},
    {"button": "⚔️", "name": "RED TEAM", "does": "Attack the current recommendation and assumptions."},
    {"button": "🔗", "name": "DEPENDENCIES", "does": "Show upstream/downstream systems and cascade risk."},
    {"button": "💥", "name": "FAILURE TEST", "does": "Run the worst credible failure scenario."},
    {"button": "🛡", "name": "GUARDIAN", "does": "Check privacy, authority, safety and policy boundaries."},
    {"button": "⚖", "name": "JUDGEMENT", "does": "Show the governed gate decision without granting execution authority."},
    {"button": "💾", "name": "HRM / JOOG", "does": "Check memory, provenance, lessons, receipts and missing records."},
    {"button": "↩", "name": "ROLLBACK", "does": "Show or test the reversible recovery path where applicable."},
    {"button": "🟢", "name": "STRONGEST LINK", "does": "Show the strongest proven part."},
    {"button": "🟡", "name": "WEAKEST LINK", "does": "Show the limiting evidence, uncertainty or risk."},
    {"button": "📋", "name": "MINORITY REPORT", "does": "Preserve serious dissent even when most agents agree."},
    {"button": "➡️", "name": "NEXT GATE", "does": "Show the smallest evidence-backed action that moves the case forward."},
    {"button": "✓", "name": "APPROVE", "does": "Human Authority approval for the specifically bounded proposed action only."},
    {"button": "⚙", "name": "EXECUTE", "does": "Remain locked until production gates, authority, rollback and verification requirements pass."},
)

REGISTERED_AGENT_CHOICES: dict[str, tuple[str, ...]] = {
    "matrix": ("Neo", "Trinity", "Morpheus", "Oracle", "Architect", "Smith", "Analyst"),
    "governance": ("Akan", "Chancellor", "Judge", "Guardian", "Mediator", "Registrar", "Steward"),
    "civilisation": ("Atlas", "Chronos", "Sentinel", "Mirror", "Horizon", "Pulse", "Forge"),
    "jungle": ("Akela", "Mowgli", "Baloo", "Bagheera", "Shere Khan"),
    "specialists": ("Nirmata", "Falcon", "Owl", "Octopus", "Wolf", "Raven", "Fox"),
}

AGENT_BUTTONS: dict[str, object] = {
    "recommended": ("Neo", "Nirmata", "Guardian"),
    "families": REGISTERED_AGENT_CHOICES,
    "auto_select": "AUTO SELECT RELEVANT REGISTERED AGENTS",
    "rule": "Only registered OAP agents participate; selection grants no authority and dissent remains visible.",
}

WAR_ROOM_TOP_BAR: dict[str, object] = {
    "title": "OAP WAR ROOM",
    "signal": "🟡 REVIEW",
    "smi_mode": "AUTO",
    "depth": "3 / 7 / 21 adaptive",
    "round": 1,
    "agents": "selected per case",
    "evidence": "calculated per case",
    "confidence": "calculated per case",
    "guardian": "🛡 PASSED / BLOCKED / UNKNOWN",
    "hrm": "💾 ACTIVE / MISSING / UNKNOWN",
    "controls": ("RUN", "STOP", "CHALLENGE", "COMPARE", "AGENTS", "EVIDENCE", "ROLLBACK", "NEXT GATE"),
}

SIGNAL_RULES: dict[str, str] = {
    "🟢 PROVEN": "runtime or evidence proof exists for the exact stated capability/state",
    "🟢 SIMULATION PASSED": "the bounded analytical/simulation protocol passed; this is not production proof",
    "🟢 PRODUCTION PROVEN": "real execution completed and post-execution verification proved the intended production state",
    "🟡 REVIEW": "unresolved, building, awaiting evidence or Human Authority review",
    "🔴 BLOCKED": "failed, unsafe, conflicting or blocked by a required gate",
    "🔒 LOCKED": "intentionally unavailable until evidence, authority, compliance, provider, rollback or safety requirements pass",
    "⚪ UNKNOWN": "no sufficient evidence; unknown must stay unknown",
    "👑 HUMAN AUTHORITY": "Founder final for consequential real-world action",
}

SAFE_PROGRESS_STAGES: tuple[str, ...] = (
    "Understanding",
    "Evidence",
    "Memory",
    "Agents",
    "Challenge",
    "Guardian",
    "Judgement",
    "Solution",
)

FOUNDER_RESULT_FIELDS: tuple[str, ...] = (
    "PROOF",
    "RISK",
    "STRONGEST LINK",
    "WEAKEST LINK",
    "AGENTS",
    "OPTIONS",
    "RECOMMENDATION",
    "NEXT GATE",
    "AUTHORITY",
)

COMMAND_LANGUAGE: tuple[str, ...] = (
    "SMI auto — choose the right depth.",
    "SMI 3 — instant review.",
    "SMI 7 — medium review.",
    "SMI 21 — deep dive this.",
    "War Room.",
    "Auto-select my agents.",
    "Red team it.",
    "Failure test.",
    "Show strongest link.",
    "Show weakest link.",
    "Show dissent.",
    "Run rollback test.",
    "Next gate.",
)

FINAL_LAW: tuple[str, ...] = (
    "Evidence before green.",
    "Configured is not ready.",
    "UI presence is not readiness.",
    "Simulation passed is not production proven.",
    "Unknown stays unknown.",
    "Forecast is not fact.",
    "Dissent survives.",
    "Approve is not execute.",
    "Human Authority final.",
)


def status() -> dict[str, Any]:
    """Return the locked SMI-first deep-dive simulation protocol."""

    return {
        "name": "SMI Deep-Dive Simulation Protocol",
        "status": "ready",
        "mode": "read_only_founder_review",
        "starts_from": "SMI, not War Room",
        "canonical_flow": CANONICAL_FLOW,
        "depth_modes": DEPTH_MODES,
        "safe_progress_stages": SAFE_PROGRESS_STAGES,
        "founder_result_fields": FOUNDER_RESULT_FIELDS,
        "steps": {
            "1_request": "Founder gives SMI the mission, question, problem or scenario.",
            "2_mode": DEPTH_MODES,
            "3_route": ROUTE_FIELDS,
            "4_memory": "Retrieve relevant HRM / JOOG evidence and prior receipts.",
            "5_agents": AGENT_BUTTONS,
            "6_simulation": SIMULATION_MODEL,
            "7_war_room_trigger": WAR_ROOM_TRIGGERS,
            "8_guardian_judgement": "Preserve blockers, dissent, reversibility and authority boundaries.",
            "9_human_authority": FOUNDER_DECISIONS,
        },
        "war_room_buttons": WAR_ROOM_BUTTONS,
        "agent_buttons": AGENT_BUTTONS,
        "top_bar": WAR_ROOM_TOP_BAR,
        "signal_rules": SIGNAL_RULES,
        "command_language": COMMAND_LANGUAGE,
        "final_law": FINAL_LAW,
        "locks": {
            "only_registered_oap_agents": True,
            "agent_authority_gain": False,
            "simulation_is_real_world_proof": False,
            "simulation_pass_is_production_proof": False,
            "approve_equals_execute": False,
            "show_thinking_is_telemetry_only": True,
            "private_chain_of_thought_hidden": True,
            "guardian_required": True,
            "green_gate_required": True,
            "hrm_required": True,
            "rollback_required_for_consequential_execution": True,
            "post_execution_verification_required": True,
            "founder_authority_final": True,
            "no_fake_green": True,
        },
    }


def simulate(command: str | None = None, agent: str | None = None) -> dict[str, Any]:
    """Return a bounded SMI-first simulation frame for a command."""

    selected_command = (command or "current mission").strip()
    selected_agent = (agent or "auto_select_registered_agents").strip()
    protocol = status()
    return {
        "case": selected_command,
        "selected_agent": selected_agent,
        "smi_first": True,
        "war_room_open": "when triggered/requested",
        "depth_default": "auto: 3 / 7 / 21",
        "signal": "🟡 REVIEW",
        "result": "bounded_simulation_frame_ready",
        "execution_granted": False,
        "real_world_proof_claimed": False,
        "frame": SIMULATION_MODEL,
        "progress": SAFE_PROGRESS_STAGES,
        "founder_result_fields": FOUNDER_RESULT_FIELDS,
        "next_gate": "Show evidence, select relevant registered agents, challenge alternatives, test failure/recovery, then Human Authority decides.",
        "protocol": protocol,
    }
