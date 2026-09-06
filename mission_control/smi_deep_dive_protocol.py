"""Founder-only SMI Deep-Dive Simulation Protocol.

The deep dive starts from SMI, not from the War Room. War Room is triggered
only when requested, when risk/conflict is significant, or when SMI escalates
from 7 to 21. This module is read-only: it does not execute, approve, deploy,
dispatch, track, spend, or write production records.
"""
from __future__ import annotations

from typing import Any

CANONICAL_FLOW: tuple[str, ...] = (
    "User / Human Authority",
    "SMI Protocol",
    "Depth Selection",
    "Evidence + Context",
    "Specialist Intelligence",
    "Optional Founder-selected Agent",
    "War Room when triggered/requested",
    "Judgement",
    "Human Authority Final",
)

DEPTH_MODES: tuple[dict[str, object], ...] = (
    {"id": "instant_3", "label": "⚡ INSTANT 3", "depth": 3, "use_for": "simple, low-risk, obvious tasks"},
    {"id": "medium_7", "label": "🧠 MEDIUM 7", "depth": 7, "use_for": "analytical checks, structure, normal review"},
    {"id": "high_21", "label": "🟣 HIGH 21", "depth": 21, "use_for": "deep multi-system, consequential, public/private, safety, money, dispatch, authority, or conflicting evidence"},
)

ROUTE_FIELDS: tuple[str, ...] = (
    "Intelligence World(s)",
    "system(s)",
    "brain regions",
    "relevant evidence",
    "HRM memory",
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
    {"button": "🟢", "name": "RUN WAR ROOM", "does": "Start the full seven-judge review."},
    {"button": "🟣", "name": "DEEP DIVE 21", "does": "Escalate SMI to the full 3x7 cycle."},
    {"button": "👥", "name": "BRING IN AGENT", "does": "Choose a registered specialist."},
    {"button": "🎯", "name": "AUTO SELECT 7", "does": "SMI selects the strongest seven registered agents for the current issue."},
    {"button": "🔎", "name": "SHOW EVIDENCE", "does": "Show sources, freshness, confidence and gaps; no private chain-of-thought."},
    {"button": "🧠", "name": "SHOW THINKING", "does": "Show telemetry only: Mode, Stage, Evidence, Agents, Tools, Confidence, Guardian, HRM."},
    {"button": "⚔️", "name": "RED TEAM", "does": "Attack the current recommendation and assumptions."},
    {"button": "📊", "name": "SWOT x7", "does": "Run full SWOT across all seven judges."},
    {"button": "🔗", "name": "DEPENDENCIES", "does": "Show upstream/downstream systems and cascade risk."},
    {"button": "💥", "name": "FAILURE TEST", "does": "Run worst credible failure scenario."},
    {"button": "🛡", "name": "GUARDIAN CHECK", "does": "Check privacy, authority, safety and policy boundary."},
    {"button": "💾", "name": "HRM CHECK", "does": "Check memory quality, provenance, lessons and missing records."},
    {"button": "🔄", "name": "RECOVERY TEST", "does": "Isolation -> fallback -> recovery -> integrity -> reconciliation -> resume."},
    {"button": "⭐", "name": "SCORE 7x", "does": "Run the seven-star evidence score."},
    {"button": "🟢", "name": "STRONGEST LINK", "does": "Show strongest proven part."},
    {"button": "🟡", "name": "WEAKEST LINK", "does": "Show limiting evidence or risk."},
    {"button": "🗣", "name": "JUDGE SPEECHES", "does": "Show each judge's mandatory short speech."},
    {"button": "📋", "name": "MINORITY REPORT", "does": "Preserve serious dissent even if the vote is 6-1."},
    {"button": "➡️", "name": "NEXT GATE", "does": "Show the smallest action that moves the case forward."},
)

AGENT_BUTTONS: dict[str, object] = {
    "recommended": ("Neo", "Seraph", "Nirmata"),
    "matrix": ("Morpheus", "Trinity", "Oracle", "Architect", "Keymaker"),
    "life": ("Akela", "Shere Khan", "Owl"),
    "specialists": ("Falcon", "Spider", "Octopus", "Gyata"),
    "auto_select": "AUTO SELECT BEST AGENT",
    "rule": "Only registered OAP agents participate; the agent joins review and gains no authority.",
}

WAR_ROOM_TOP_BAR: dict[str, object] = {
    "title": "OAP WAR ROOM",
    "signal": "🟡 OPEN",
    "smi_mode": "HIGH",
    "depth": 21,
    "round": 1,
    "judges": "7 / 7",
    "evidence": "calculated per case",
    "confidence": "calculated per case",
    "guardian": "🛡 PASSED / BLOCKED",
    "hrm": "💾 ACTIVE / MISSING",
    "controls": ("RUN", "RED TEAM", "AGENT +", "EVIDENCE", "RECOVERY", "NEXT GATE"),
}

SEVEN_LENS_SCORE: tuple[dict[str, str], ...] = (
    {"lens": "PROOF", "default_score": "⭐⭐⭐⭐⭐☆☆"},
    {"lens": "PROTECTION", "default_score": "⭐⭐⭐⭐⭐⭐☆"},
    {"lens": "CREATION", "default_score": "⭐⭐⭐⭐⭐☆☆"},
    {"lens": "IDENTITY", "default_score": "⭐⭐⭐⭐⭐⭐☆"},
    {"lens": "DECISION", "default_score": "⭐⭐⭐⭐⭐⭐☆"},
    {"lens": "MEMORY", "default_score": "⭐⭐⭐⭐☆☆☆"},
    {"lens": "RECOVERY", "default_score": "⭐⭐⭐⭐☆☆☆"},
)

SIGNAL_RULES: dict[str, str] = {
    "🟢": "proceed / healthy",
    "🟡": "War Room open / unresolved",
    "🔴": "stop / critical boundary",
    "🟣": "learning from evidence",
    "🔒": "full green locked until proof",
    "👑": "Founder final",
}

COMMAND_LANGUAGE: tuple[str, ...] = (
    "SMI 21 — deep dive this.",
    "Bring in Seraph.",
    "Auto-select my 7.",
    "War Room.",
    "Red team it.",
    "Failure test.",
    "Show weakest link.",
    "Run recovery.",
    "Replace judge 7.",
    "Next gate.",
    "🟡 = continue the current War Room.",
)

FINAL_LAW: tuple[str, ...] = (
    "Evidence before green.",
    "Unknown stays unknown.",
    "Forecast is not fact.",
    "Dissent survives.",
    "Human Authority final.",
)


def status() -> dict[str, Any]:
    """Return the locked SMI-first deep-dive simulation protocol."""

    return {
        "name": "SMI Deep-Dive Simulation Protocol",
        "status": "locked",
        "mode": "read_only_founder_review",
        "starts_from": "SMI, not War Room",
        "canonical_flow": CANONICAL_FLOW,
        "steps": {
            "1_request": "Founder gives SMI the mission, question, problem or scenario.",
            "2_mode": DEPTH_MODES,
            "3_route": ROUTE_FIELDS,
            "4_agents": AGENT_BUTTONS,
            "5_simulation": SIMULATION_MODEL,
            "6_war_room_trigger": WAR_ROOM_TRIGGERS,
            "7_judgement": "War Room outputs consensus, minority report, weakest link, strongest link and next gate.",
            "8_human_authority": FOUNDER_DECISIONS,
        },
        "war_room_buttons": WAR_ROOM_BUTTONS,
        "agent_buttons": AGENT_BUTTONS,
        "top_bar": WAR_ROOM_TOP_BAR,
        "seven_lens_score": SEVEN_LENS_SCORE,
        "signal_rules": SIGNAL_RULES,
        "command_language": COMMAND_LANGUAGE,
        "final_law": FINAL_LAW,
        "locks": {
            "only_registered_oap_agents": True,
            "agent_authority_gain": False,
            "simulation_is_real_world_proof": False,
            "show_thinking_is_telemetry_only": True,
            "private_chain_of_thought_hidden": True,
            "guardian_required": True,
            "green_gate_required": True,
            "hrm_required": True,
            "founder_authority_final": True,
            "no_fake_green": True,
        },
    }


def simulate(command: str | None = None, agent: str | None = None) -> dict[str, Any]:
    """Return a bounded SMI-first simulation frame for a command."""

    selected_command = (command or "current mission").strip()
    selected_agent = (agent or "auto_select_best_agent").strip()
    protocol = status()
    return {
        "case": selected_command,
        "selected_agent": selected_agent,
        "smi_first": True,
        "war_room_open": "when triggered/requested",
        "depth_default": "auto: 3 / 7 / 21",
        "result": "bounded_simulation_frame_ready",
        "execution_granted": False,
        "real_world_proof_claimed": False,
        "frame": SIMULATION_MODEL,
        "next_gate": "Show evidence, select agent, run red team, failure test, recovery test, or Founder final decision.",
        "protocol": protocol,
    }
