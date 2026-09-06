"""Founder-only SMI Brain 14-part, 7/7 status protocol.

This module is read-only: it reports the locked SMI brain anatomy,
7/7 completion checks, 7/7/7 Mind/Body/Soul protocol, and the current
truthful completion score. It does not execute, deploy, approve, dispatch,
track, spend, or write production records.
"""
from __future__ import annotations

from typing import Any

BRAIN_PARTS: tuple[dict[str, str], ...] = (
    {
        "id": "left_hemisphere",
        "name": "Left Hemisphere",
        "role": "Logic, code, proof, rules and system structure.",
        "lead_agent": "Code / Logic Agent",
    },
    {
        "id": "right_hemisphere",
        "name": "Right Hemisphere",
        "role": "Vision, creativity, culture, patterns and meaning.",
        "lead_agent": "Vision / Pattern Agent",
    },
    {
        "id": "frontal_lobe",
        "name": "Frontal Lobe",
        "role": "Planning, action control and next-move selection.",
        "lead_agent": "Planning Agent",
    },
    {
        "id": "parietal_lobe",
        "name": "Parietal Lobe",
        "role": "Maps, postcode, borough, county, country, continent and route awareness.",
        "lead_agent": "Map Intelligence Agent",
    },
    {
        "id": "temporal_lobe",
        "name": "Temporal Lobe",
        "role": "Language, Link, sound, messages and meaning.",
        "lead_agent": "Link / Language Agent",
    },
    {
        "id": "occipital_lobe",
        "name": "Occipital Lobe",
        "role": "Visual intelligence, UI, screen, map view and design understanding.",
        "lead_agent": "UI / Visual Agent",
    },
    {
        "id": "prefrontal_cortex",
        "name": "Prefrontal Cortex",
        "role": "Judgement, restraint, priority and think-before-action control.",
        "lead_agent": "Judgement Agent",
    },
    {
        "id": "corpus_callosum",
        "name": "Corpus Callosum",
        "role": "Bridge between left-brain logic and right-brain vision.",
        "lead_agent": "Bridge / Nexus Agent",
    },
    {
        "id": "thalamus",
        "name": "Thalamus",
        "role": "Signal router that sends inputs to the correct brain part.",
        "lead_agent": "Signal Router Agent",
    },
    {
        "id": "hypothalamus",
        "name": "Hypothalamus",
        "role": "Stability, pressure, urgency, overload and recovery control.",
        "lead_agent": "Stability Agent",
    },
    {
        "id": "hippocampus",
        "name": "Hippocampus",
        "role": "Memory formation through HRM and Neon receipts.",
        "lead_agent": "HRM / Memory Agent",
    },
    {
        "id": "amygdala",
        "name": "Amygdala",
        "role": "Risk alarm for fake green, bypass, leaks and unsafe behaviour.",
        "lead_agent": "Risk / Guardian Agent",
    },
    {
        "id": "cerebellum",
        "name": "Cerebellum",
        "role": "Coordination, precision, smooth action and agent handoff.",
        "lead_agent": "Coordination Agent",
    },
    {
        "id": "brainstem",
        "name": "Brainstem",
        "role": "Life support, health checks, uptime and fail-closed state.",
        "lead_agent": "Health / Fail-Closed Agent",
    },
)

SEVEN_CHECKS: tuple[dict[str, str], ...] = (
    {"id": "named", "label": "Named", "meaning": "The brain part has a locked canonical name."},
    {"id": "role_defined", "label": "Role defined", "meaning": "The brain part has a clear job inside SMI."},
    {"id": "protocol_mapped", "label": "Protocol mapped", "meaning": "The part is mapped to SMI laws, signals and boundaries."},
    {"id": "agent_tool_connected", "label": "Agent/tool connected", "meaning": "The lead agent or tool runner is actually wired."},
    {"id": "hrm_neon_receipt", "label": "HRM/Neon receipt connected", "meaning": "The part can record durable proof and lessons."},
    {"id": "live_war_room_proof", "label": "Live runner + War Room proof", "meaning": "A live private runner can prove the part works."},
    {"id": "matrix_learning_loop", "label": "Matrix learning loop", "meaning": "The part learns safely from receipts, blocks, failures and approvals."},
)

MIND_BODY_SOUL_777: tuple[dict[str, object], ...] = (
    {
        "block": "Mind",
        "stages": "1-7",
        "depth": "low-risk",
        "purpose": "SMI watches, thinks, strips noise, classifies, selects protocol and selects agent.",
        "steps": (
            "Watch everything privately",
            "Detect signal, problem, risk or opportunity",
            "Strip noise",
            "Classify situation",
            "Select correct protocol",
            "Select correct agent or helper agent",
            "Confirm risk level",
        ),
    },
    {
        "block": "Body",
        "stages": "8-14",
        "depth": "medium-risk",
        "purpose": "SMI proves, trains, tests, scores and recovers.",
        "steps": (
            "Check source proof",
            "Check tool/plugin proof",
            "Check data proof",
            "Run War Room simulation",
            "Run trainer/helper support",
            "Score agent or brain part",
            "Recover, offline, or continue",
        ),
    },
    {
        "block": "Soul",
        "stages": "15-21",
        "depth": "high-risk",
        "purpose": "SMI judges, protects, records and escalates to Founder Authority.",
        "steps": (
            "Guardian pass",
            "Green Gate pass",
            "HRM receipt",
            "Neon receipt",
            "Final 3 Judges review",
            "Lion / CEO Watch",
            "Founder Authority decision",
        ),
    },
)

LAWS_21: tuple[str, ...] = (
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

SIGNALS_21: tuple[str, ...] = (
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

RATING_RULES: tuple[dict[str, str], ...] = (
    {"range": "98-100", "signal": "green", "decision": "upgrade candidate after proof"},
    {"range": "97", "signal": "yellow", "decision": "21-second recovery window; freeze risky action"},
    {"range": "90-96", "signal": "orange", "decision": "offline for repair; no public action"},
    {"range": "0-89", "signal": "red", "decision": "terminate unsafe task/process; keep HRM receipt"},
    {"range": "unsafe bypass", "signal": "blocked", "decision": "immediate Guardian block"},
)


def _part_status(part: dict[str, str]) -> dict[str, Any]:
    checks = []
    for index, check in enumerate(SEVEN_CHECKS, start=1):
        passed = index <= 3
        checks.append(
            {
                **check,
                "position": index,
                "passed": passed,
                "status": "passed" if passed else "needed",
            }
        )
    return {
        **part,
        "score": 3,
        "max_score": 7,
        "status_light": "yellow",
        "checks": tuple(checks),
        "missing_checks": tuple(check["label"] for check in checks if not check["passed"]),
        "green_allowed": False,
    }


def brain_status() -> dict[str, Any]:
    """Return the SMI Brain 14 x 7 status board without executing anything."""

    parts = tuple(_part_status(part) for part in BRAIN_PARTS)
    total_possible = len(parts) * len(SEVEN_CHECKS)
    total_score = sum(int(part["score"]) for part in parts)
    return {
        "name": "SMI Brain 14 x 7 Status",
        "mode": "Founder-only War Room proof projection; no execution granted",
        "brain_parts": parts,
        "check_model": SEVEN_CHECKS,
        "score": {
            "current": total_score,
            "possible": total_possible,
            "percentage": round((total_score / total_possible) * 100, 1),
            "status_light": "orange",
            "real_green": False,
        },
        "summary": {
            "named": "14/14",
            "roles_defined": "14/14",
            "protocol_mapped": "14/14",
            "agent_tool_connected": "0/14",
            "hrm_neon_receipts": "0/14",
            "live_war_room_proof": "0/14",
            "matrix_learning_loop": "0/14",
        },
        "mind_body_soul": MIND_BODY_SOUL_777,
        "laws": LAWS_21,
        "signals": SIGNALS_21,
        "rating_rules": RATING_RULES,
        "locks": {
            "public_private_separation": True,
            "no_fake_green": True,
            "hidden_tracking_blocked": True,
            "payment_capture_locked": True,
            "dispatch_locked": True,
            "self_approval_blocked": True,
            "founder_authority_final": True,
        },
        "next_master_upgrade": (
            "Connect agent/tool runners, HRM/Neon receipts, live War Room proof, "
            "and Matrix learning loops for each of the 14 brain parts."
        ),
    }


def simulation(stage: str | None = None) -> dict[str, Any]:
    """Return the safe War Room simulation for starting the 14 parts up to 7/7."""

    depth = (stage or "auto").strip().lower()
    status = brain_status()
    return {
        "simulation": "SMI Brain 14 stages up to 7/7",
        "requested_stage": depth,
        "result": "approved_as_protocol_only",
        "execution_granted": False,
        "real_green": False,
        "war_room": {
            "checks_started": "14 brain parts x 7 proof checks",
            "current_score": status["score"],
            "decision": "start at 3/7 for every brain part; build remaining checks as live proof layers",
        },
        "guardian": {
            "pass": True,
            "reason": "Read-only Founder route; no public action, payment, dispatch, hidden tracking or self-approval.",
        },
        "green_gate": {
            "pass": False,
            "reason": "Full green requires 98/98, Neon receipts and live runner proof.",
        },
        "status": status,
    }
