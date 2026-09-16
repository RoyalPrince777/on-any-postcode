"""Founder-only SMI Deep-Dive Simulation Protocol.

SMI owns one adaptive reasoning mode. War Room 7x is not another model or depth:
it repeats the complete governed research/review loop through seven distinct
verification purposes, preserving evidence, dissent and truth boundaries.
This module is read-only and grants no execution authority.
"""
from __future__ import annotations

from typing import Any

CANONICAL_FLOW: tuple[str, ...] = (
    "User / Human Authority", "SMI Protocol", "Evidence + Context",
    "HRM / JOOG Memory", "Specialist Intelligence", "Registered Agent Challenge",
    "War Room when triggered/requested", "Guardian + Judgement", "Human Authority Final",
)

PROTOCOL_LOOP: tuple[str, ...] = (
    "Observe", "Classify", "Verify", "Fix / Plan", "Retest", "Record", "Learn",
)

SEVEN_X_PASSES: tuple[dict[str, str], ...] = (
    {"pass": "1/7", "name": "Discovery", "purpose": "Gather the strongest relevant evidence, context, memory and unknowns."},
    {"pass": "2/7", "name": "Verification", "purpose": "Check provenance, freshness, contradictions and unsupported claims."},
    {"pass": "3/7", "name": "Alternatives", "purpose": "Search credible alternatives and preserve meaningful dissent."},
    {"pass": "4/7", "name": "Adversarial", "purpose": "Attack assumptions, false Green, bypasses and fragile conclusions."},
    {"pass": "5/7", "name": "Systems", "purpose": "Trace dependencies, integration effects and cascade risk."},
    {"pass": "6/7", "name": "Consequence", "purpose": "Stress failure, recovery, reversibility, safety and authority boundaries."},
    {"pass": "7/7", "name": "Synthesis", "purpose": "Re-evaluate all evidence, votes, dissent and gates into one clear judgement."},
)

SEVEN_STAR_GATE: tuple[str, ...] = (
    "Truth", "Function", "Security", "Stability", "Integration", "Compliance", "Learning",
)

WAR_ROOM_BUTTONS: tuple[dict[str, str], ...] = (
    {"button": "▶", "name": "RUN", "does": "Run the standard governed SMI War Room review."},
    {"button": "🔬", "name": "RESEARCH", "does": "Gather or refresh evidence, provenance, freshness, confidence and gaps."},
    {"button": "⚔️", "name": "CHALLENGE", "does": "Attack the current conclusion and preserve serious dissent."},
    {"button": "7×", "name": "7X DEEP DIVE", "does": "Repeat the complete protocol through Discovery, Verification, Alternatives, Adversarial, Systems, Consequence and Synthesis."},
    {"button": "⏹", "name": "STOP", "does": "Stop the current bounded simulation/review run."},
    {"button": "⚖", "name": "COMPARE", "does": "Compare viable alternatives, evidence, risk and reversibility."},
    {"button": "👥", "name": "AGENTS", "does": "Show registered specialists selected for this case."},
    {"button": "🔎", "name": "EVIDENCE", "does": "Show sources, freshness, confidence and gaps; no private chain-of-thought."},
    {"button": "🕶", "name": "SMITH ATTACK", "does": "Attack stale evidence, duplicate routes, bypasses and false confidence."},
    {"button": "💥", "name": "FAILURE TEST", "does": "Run the worst credible bounded failure scenario."},
    {"button": "🛡", "name": "GUARDIAN", "does": "Check privacy, authority, safety and governance boundaries."},
    {"button": "⚖", "name": "JUDGEMENT", "does": "Show the governed recommendation without granting execution authority."},
    {"button": "💾", "name": "HRM / JOOG", "does": "Check memory, provenance, lessons, receipts and missing records."},
    {"button": "↩", "name": "ROLLBACK", "does": "Show or test the reversible recovery path where applicable."},
    {"button": "➡️", "name": "NEXT GATE", "does": "Show the smallest evidence-backed action that moves the case forward."},
)

SIGNAL_RULES: dict[str, str] = {
    "🟢 PROVEN": "current evidence proves the exact stated capability or state",
    "🟣 LEARNING": "research, simulation or intelligence only; not production proof",
    "🟡 REVIEW": "unresolved, incomplete, stale or awaiting evidence/Human Authority",
    "🔴 BLOCKED": "failed, unsafe, conflicting or blocked by a required gate",
    "🔒 LOCKED": "intentionally unavailable until required proof and authority exist",
    "⚪ UNKNOWN": "insufficient evidence; unknown stays unknown",
    "👑 HUMAN AUTHORITY": "Founder final for consequential real-world action",
}

FOUNDER_RESULT_FIELDS: tuple[str, ...] = (
    "MISSION", "EVIDENCE", "AGREED", "DISAGREED", "UNRESOLVED", "VOTES",
    "STRONGEST ARGUMENT", "STRONGEST COUNTERARGUMENT", "RISK", "7-STAR",
    "GUARDIAN", "END REVIEW", "SMI JUDGEMENT", "NEXT GATE", "AUTHORITY", "RECEIPT",
)

FINAL_LAW: tuple[str, ...] = (
    "One SMI; no duplicate intelligence engine.",
    "Evidence before Green.", "Configured is not ready.", "UI presence is not readiness.",
    "Simulation passed is not production proven.", "Unknown stays unknown.",
    "Dissent survives.", "Votes inform judgement; votes do not grant authority.",
    "Approve is not execute.", "Human Authority final.",
)


def status() -> dict[str, Any]:
    return {
        "name": "SMI War Room Research Intelligence Protocol",
        "status": "ready",
        "mode": "read_only_founder_review",
        "starts_from": "SMI",
        "canonical_flow": CANONICAL_FLOW,
        "protocol_loop": PROTOCOL_LOOP,
        "seven_x": {
            "is_depth_mode": False,
            "passes": SEVEN_X_PASSES,
            "rule": "Each pass receives the accumulated evidence and dissent from earlier passes; it is not seven copies of the same answer.",
        },
        "seven_star_gate": SEVEN_STAR_GATE,
        "war_room_buttons": WAR_ROOM_BUTTONS,
        "founder_result_fields": FOUNDER_RESULT_FIELDS,
        "signal_rules": SIGNAL_RULES,
        "final_law": FINAL_LAW,
        "locks": {
            "read_only": True,
            "production_write": False,
            "deploy": False,
            "auth_change": False,
            "permission_change": False,
            "publishing_authority": False,
            "payment_authority": False,
            "human_authority_final": True,
        },
    }
