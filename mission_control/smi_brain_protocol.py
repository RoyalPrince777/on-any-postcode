"""Founder-only SMI Brain 14-part, 7/7 status protocol.

This module is read-only: it reports the locked SMI brain anatomy,
7/7 completion checks, 7/7/7 Mind/Body/Soul protocol, and the current
truthful completion score. It does not execute, deploy, approve, dispatch,
track, spend, or write production records.

The War Room may simulate every brain part up to 7/7, but the evidence
score remains separate so the system never hides missing Neon receipts,
live runners, or Matrix learning proof behind a fake green badge.
"""
from __future__ import annotations

from typing import Any

BRAIN_PARTS: tuple[dict[str, object], ...] = (
    {
        "id": "left_hemisphere",
        "name": "Left Hemisphere",
        "role": "Logic, code, proof, rules and system structure.",
        "does": "Checks logical soundness, clean code order, route structure and proof before action.",
        "owns": ("code logic", "route order", "law matching", "proof-before-action"),
        "lead_agent": "Code / Logic Agent",
        "helper_agents": ("Tool Proof Agent", "Green Gate", "Nirmata"),
        "protocol_focus": "Mind stages 3-6: strip noise, classify, select protocol and map proof.",
        "needed_to_7": (
            "Wire code/proof runner",
            "record HRM/Neon logic receipt",
            "prove one live logic check in War Room",
            "feed failed logic checks into Matrix learning",
        ),
    },
    {
        "id": "right_hemisphere",
        "name": "Right Hemisphere",
        "role": "Vision, creativity, culture, patterns and meaning.",
        "does": "Reads wider meaning, identity, design direction, culture and repeating patterns.",
        "owns": ("vision", "culture", "pattern recognition", "brand meaning"),
        "lead_agent": "Vision / Pattern Agent",
        "helper_agents": ("Nirmata", "Owl", "Bagheera"),
        "protocol_focus": "Mind stages 1-7: watch, detect, classify and keep the big picture coherent.",
        "needed_to_7": (
            "Wire pattern/meaning checker",
            "record HRM/Neon meaning receipt",
            "prove one live brand/culture check",
            "feed repeated pattern lessons into Matrix learning",
        ),
    },
    {
        "id": "frontal_lobe",
        "name": "Frontal Lobe",
        "role": "Planning, action control and next-move selection.",
        "does": "Chooses whether to answer, check, simulate, patch, deploy, recover or stop.",
        "owns": ("planning", "next action", "task control", "upgrade order"),
        "lead_agent": "Planning Agent",
        "helper_agents": ("Living Kernel", "War Room", "Nirmata"),
        "protocol_focus": "Mind stages 4-7 and Body stage 11: classify, select protocol, then simulate.",
        "needed_to_7": (
            "Wire planning runner",
            "record chosen-action receipt",
            "prove live War Room planning output",
            "learn from wrong or slow action choices",
        ),
    },
    {
        "id": "parietal_lobe",
        "name": "Parietal Lobe",
        "role": "Maps, postcode, borough, county, country, continent and route awareness.",
        "does": "Handles spatial intelligence, place hierarchy, map proof and route awareness.",
        "owns": ("On Any Place", "postcode hierarchy", "spatial proof", "route awareness"),
        "lead_agent": "Map Intelligence Agent",
        "helper_agents": ("Movement Intelligence", "Live Pattern", "Green Gate"),
        "protocol_focus": "Body stages 8-10: source proof, route/API proof and data proof.",
        "needed_to_7": (
            "Wire map/place runner",
            "record map proof receipt",
            "prove one live route/place check",
            "learn stale or missing map-source patterns",
        ),
    },
    {
        "id": "temporal_lobe",
        "name": "Temporal Lobe",
        "role": "Language, Link, sound, messages and meaning.",
        "does": "Understands OAP language, Link language, speech meaning, messages and memory recall.",
        "owns": ("The Link", "Link Up language", "speech meaning", "message memory"),
        "lead_agent": "Link / Language Agent",
        "helper_agents": ("HRM", "Owl", "Guardian"),
        "protocol_focus": "Mind stages 2-5: detect intent, strip noise, classify and select terms.",
        "needed_to_7": (
            "Wire language intent runner",
            "record canonical-language receipt",
            "prove one live Link/OAP wording check",
            "learn from user corrections and naming locks",
        ),
    },
    {
        "id": "occipital_lobe",
        "name": "Occipital Lobe",
        "role": "Visual intelligence, UI, screen, map view and design understanding.",
        "does": "Reads visual surfaces, UI state, screen cleanliness and public/private leakage risk.",
        "owns": ("UI reading", "visual layout", "screen proof", "design consistency"),
        "lead_agent": "UI / Visual Agent",
        "helper_agents": ("Guardian", "Green Gate", "Nirmata"),
        "protocol_focus": "Body stages 10-12: data proof, simulation and helper review.",
        "needed_to_7": (
            "Wire UI/surface checker",
            "record visual proof receipt",
            "prove one live private screen check",
            "learn from UI mistakes and public-noise removals",
        ),
    },
    {
        "id": "prefrontal_cortex",
        "name": "Prefrontal Cortex",
        "role": "Judgement, restraint, priority and think-before-action control.",
        "does": "Stops rushed action, checks priority, blocks shortcuts and chooses 7, 14 or 21 stages.",
        "owns": ("judgement", "restraint", "priority", "risk depth"),
        "lead_agent": "Judgement Agent",
        "helper_agents": ("War Room", "Guardian", "Founder Authority"),
        "protocol_focus": "Mind stage 7 and Soul stages 15-21: risk level, judges and final escalation.",
        "needed_to_7": (
            "Wire Judgement runner",
            "record approval/blocked receipt",
            "prove one live 7/14/21 depth decision",
            "learn from over-action, under-action and Founder corrections",
        ),
    },
    {
        "id": "corpus_callosum",
        "name": "Corpus Callosum",
        "role": "Bridge between left-brain logic and right-brain vision.",
        "does": "Merges proof with vision so SMI stays coherent and avoids split decisions.",
        "owns": ("left-right bridge", "Nexus connection", "coherence", "conflict merge"),
        "lead_agent": "Bridge / Nexus Agent",
        "helper_agents": ("Nexus", "ACI Learning Core", "War Room"),
        "protocol_focus": "Mind stage 6 and Body stage 12: select helpers and merge review.",
        "needed_to_7": (
            "Wire bridge/coherence runner",
            "record conflict-resolution receipt",
            "prove one live left-right merge",
            "learn from disagreement between proof and vision",
        ),
    },
    {
        "id": "thalamus",
        "name": "Thalamus",
        "role": "Signal router that sends inputs to the correct brain part.",
        "does": "Routes requests, logs, alerts and tool results to the correct brain part and protocol depth.",
        "owns": ("signal routing", "input triage", "agent selection", "protocol selection"),
        "lead_agent": "Signal Router Agent",
        "helper_agents": ("SMI Watch", "Nexus", "Agent Registry"),
        "protocol_focus": "Mind stages 1-6: watch, detect, strip noise, classify and route.",
        "needed_to_7": (
            "Wire signal router runner",
            "record routing receipt",
            "prove one live signal-to-agent route",
            "learn from misrouted or duplicated signals",
        ),
    },
    {
        "id": "hypothalamus",
        "name": "Hypothalamus",
        "role": "Stability, pressure, urgency, overload and recovery control.",
        "does": "Controls stability, overload, recovery windows and offline decisions.",
        "owns": ("stability", "overload control", "97 recovery", "offline decision"),
        "lead_agent": "Stability Agent",
        "helper_agents": ("Brainstem", "Guardian", "War Room"),
        "protocol_focus": "Body stages 13-14: score, recover, offline or continue.",
        "needed_to_7": (
            "Wire stability/recovery runner",
            "record recovery receipt",
            "prove one 97 recovery simulation",
            "learn from repeated drops and overload signals",
        ),
    },
    {
        "id": "hippocampus",
        "name": "Hippocampus",
        "role": "Memory formation through HRM and Neon receipts.",
        "does": "Turns checks, decisions, approvals, failures and lessons into HRM/Neon memory.",
        "owns": ("HRM memory", "Neon receipts", "lessons", "audit recall"),
        "lead_agent": "HRM / Memory Agent",
        "helper_agents": ("Neon Receipts", "Owl", "Audit Agent"),
        "protocol_focus": "Soul stages 17-18: HRM receipt and Neon receipt.",
        "needed_to_7": (
            "Wire HRM/Neon receipt writer",
            "record real database proof",
            "prove one live receipt lookup",
            "learn from stored outcomes and Founder decisions",
        ),
    },
    {
        "id": "amygdala",
        "name": "Amygdala",
        "role": "Risk alarm for fake green, bypass, leaks and unsafe behaviour.",
        "does": "Detects fake green, hidden tracking, leaks, unsafe claims, payment/dispatch risk and bypasses.",
        "owns": ("risk alarm", "bypass detection", "fake-green detection", "leak warning"),
        "lead_agent": "Risk / Guardian Agent",
        "helper_agents": ("Guardian", "Shere Khan", "Green Gate"),
        "protocol_focus": "Soul stages 15-16: Guardian pass and Green Gate pass.",
        "needed_to_7": (
            "Wire risk alarm runner",
            "record blocked-risk receipt",
            "prove one live fake-green/bypass block",
            "learn from every Guardian and Green Gate block",
        ),
    },
    {
        "id": "cerebellum",
        "name": "Cerebellum",
        "role": "Coordination, precision, smooth action and agent handoff.",
        "does": "Coordinates tool handoffs, build order, deploy checks, route checks and recovery timing.",
        "owns": ("coordination", "precision", "handoff", "deploy rhythm"),
        "lead_agent": "Coordination Agent",
        "helper_agents": ("Tool Proof Agent", "Render/GitHub Runner", "War Room"),
        "protocol_focus": "Body stages 11-14: simulate, train, score and continue/offline.",
        "needed_to_7": (
            "Wire coordination runner",
            "record handoff/deploy receipt",
            "prove one live coordinated check",
            "learn from timing, handoff and deploy mistakes",
        ),
    },
    {
        "id": "brainstem",
        "name": "Brainstem",
        "role": "Life support, health checks, uptime and fail-closed state.",
        "does": "Keeps the private brain alive through health checks, fail-closed gates and safe shutdown.",
        "owns": ("health", "uptime", "fail-closed", "safe shutdown"),
        "lead_agent": "Health / Fail-Closed Agent",
        "helper_agents": ("Render Health", "Guardian", "Living Kernel"),
        "protocol_focus": "Body stage 14 and Soul stages 15-16: recover/offline, Guardian and Green Gate.",
        "needed_to_7": (
            "Wire health/fail-closed runner",
            "record health proof receipt",
            "prove one live health/fail-closed check",
            "learn from downtime, crashes and blocked unsafe tasks",
        ),
    },
)

SEVEN_CHECKS: tuple[dict[str, str], ...] = (
    {"id": "named", "label": "Named", "meaning": "The brain part has a locked canonical name."},
    {"id": "role_defined", "label": "Role defined", "meaning": "The brain part has a clear job inside SMI."},
    {"id": "protocol_mapped", "label": "Protocol mapped", "meaning": "The part is mapped to SMI laws, signals and boundaries."},
    {"id": "agent_tool_connected", "label": "Agent/tool connected", "meaning": "The lead agent or tool runner is assigned in protocol; live runner proof remains separate."},
    {"id": "hrm_neon_receipt", "label": "HRM/Neon receipt connected", "meaning": "The part has a receipt contract; real Neon write proof remains separate."},
    {"id": "live_war_room_proof", "label": "Live runner + War Room proof", "meaning": "The War Room can simulate the proof path; live execution proof remains separate."},
    {"id": "matrix_learning_loop", "label": "Matrix learning loop", "meaning": "The part has a learning contract; real learning from receipts remains separate."},
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

PDF_ALIGNMENT: dict[str, object] = {
    "source": "OAP_SMI_Master_Architecture_and_Code(1).pdf",
    "confirmed": (
        "One SMI Brain; Human Authority final",
        "SMI cannot execute directly",
        "AEGIS and Guardian protect before high-impact movement",
        "War Room is recommendation-only scenario review",
        "HRM records recommendations, approvals and outcomes",
    ),
    "kept_incomplete": (
        "Judgement wider programme is not marked complete without code, tests, HRM audit and Human Authority approval",
        "Neon receipt writes are not claimed live by this read-only projection",
        "Live Matrix learning is not claimed without stored receipt evidence",
    ),
}


def _check_status(position: int, check: dict[str, str]) -> dict[str, Any]:
    evidence_passed = position <= 3
    simulation_passed = True
    return {
        **check,
        "position": position,
        "evidence_passed": evidence_passed,
        "simulation_passed": simulation_passed,
        "evidence_status": "passed" if evidence_passed else "needed",
        "simulation_status": "covered",
    }


def _part_status(part: dict[str, object]) -> dict[str, Any]:
    checks = tuple(_check_status(index, check) for index, check in enumerate(SEVEN_CHECKS, start=1))
    missing_evidence = tuple(check["label"] for check in checks if not check["evidence_passed"])
    return {
        **part,
        "evidence_score": 3,
        "simulation_score": 7,
        "max_score": 7,
        "status_light": "yellow",
        "simulation_light": "green",
        "checks": checks,
        "missing_evidence_checks": missing_evidence,
        "simulation_coverage": "7/7",
        "real_green_allowed": False,
    }


def brain_status() -> dict[str, Any]:
    """Return the SMI Brain 14 x 7 board without executing anything."""

    parts = tuple(_part_status(part) for part in BRAIN_PARTS)
    total_possible = len(parts) * len(SEVEN_CHECKS)
    evidence_score = sum(int(part["evidence_score"]) for part in parts)
    simulation_score = sum(int(part["simulation_score"]) for part in parts)
    return {
        "name": "SMI Brain 14 x 7 Status",
        "mode": "Founder-only War Room proof projection; no execution granted",
        "pdf_alignment": PDF_ALIGNMENT,
        "brain_parts": parts,
        "check_model": SEVEN_CHECKS,
        "score": {
            "evidence_current": evidence_score,
            "simulation_current": simulation_score,
            "possible": total_possible,
            "evidence_percentage": round((evidence_score / total_possible) * 100, 1),
            "simulation_percentage": round((simulation_score / total_possible) * 100, 1),
            "evidence_light": "orange",
            "simulation_light": "green",
            "real_green": False,
        },
        "summary": {
            "named": "14/14",
            "roles_defined": "14/14",
            "protocol_mapped": "14/14",
            "agent_tool_connected": "simulation covered; live runner proof needed",
            "hrm_neon_receipts": "simulation contract covered; real Neon writes needed",
            "live_war_room_proof": "simulation covered; live proof runner needed",
            "matrix_learning_loop": "simulation contract covered; stored learning proof needed",
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
            "Turn simulation coverage into real evidence by wiring live runners, "
            "HRM/Neon receipt writes, proof checks, tests and Matrix learning receipts."
        ),
    }


def simulation(stage: str | None = None) -> dict[str, Any]:
    """Return the safe War Room simulation for moving 14 brain parts from 3/7 to 7/7."""

    depth = (stage or "auto").strip().lower()
    status = brain_status()
    return {
        "simulation": "SMI Brain 14 anatomy parts from 3/7 to 7/7",
        "requested_stage": depth,
        "result": "7/7_simulation_coverage_complete",
        "execution_granted": False,
        "real_green": False,
        "war_room": {
            "checks_started": "14 brain parts x 7 proof checks",
            "evidence_score": status["score"]["evidence_current"],
            "simulation_score": status["score"]["simulation_current"],
            "possible": status["score"]["possible"],
            "decision": (
                "All 14 parts have 7/7 War Room simulation coverage. "
                "Evidence remains 3/7 until live runners and Neon receipts are proven."
            ),
        },
        "guardian": {
            "pass": True,
            "reason": "Read-only Founder route; no public action, payment, dispatch, hidden tracking or self-approval.",
        },
        "green_gate": {
            "pass": False,
            "reason": "Full real green requires evidence 98/98, Neon receipts, live runner proof and acceptance tests.",
        },
        "status": status,
    }
