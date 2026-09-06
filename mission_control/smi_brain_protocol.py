"""Founder-only SMI Brain 14-part, 7/7 status protocol.

This module is read-only: it reports the locked SMI brain anatomy,
7/7 completion checks, 7/7/7 Mind/Body/Soul protocol, and the current
truthful completion score. It does not execute, deploy, approve, dispatch,
track, spend, or write production records.
"""
from __future__ import annotations

from typing import Any

BRAIN_PARTS: tuple[dict[str, object], ...] = (
    {
        "id": "left_hemisphere",
        "name": "Left Hemisphere",
        "role": "Logic, code, proof, rules and system structure.",
        "does": (
            "Checks whether a request is logically sound, coded cleanly, named correctly, "
            "and supported by proof before any upgrade is recommended."
        ),
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
        "does": (
            "Reads the wider meaning, culture, design direction and pattern behind the work "
            "so SMI does not become cold, generic or disconnected from OAP identity."
        ),
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
        "does": (
            "Turns SMI understanding into a safe next step, choosing whether to answer, check, "
            "simulate, patch, deploy, recover, or stop."
        ),
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
        "does": (
            "Handles spatial intelligence: where something is, how it connects, whether the "
            "postcode/world hierarchy is correct, and whether map or route claims need proof."
        ),
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
        "does": (
            "Understands words, OAP language, Link language, voice/message meaning and memory "
            "recall so replies stay direct, canonical and not noisy."
        ),
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
        "does": (
            "Reads visual surfaces and UI state, checking whether a screen looks right, is clean, "
            "shows the correct signal and avoids public/private leaks."
        ),
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
        "does": (
            "Stops rushed action, checks priority, applies restraint, blocks shortcuts and decides "
            "whether the matter needs 7, 14 or full 21 stages."
        ),
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
        "does": (
            "Connects strict proof with big-picture meaning so SMI does not split into cold logic "
            "or loose imagination; both sides must agree before action moves forward."
        ),
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
        "does": (
            "Receives requests, logs, alerts and tool results, then routes each signal to the correct "
            "brain part, protocol depth and agent family."
        ),
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
        "does": (
            "Watches system pressure, urgency and overload; starts recovery when ratings drop, "
            "freezes risky action and prevents panic changes."
        ),
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
        "does": (
            "Turns actions, checks, decisions, approvals, failures and lessons into durable HRM/Neon "
            "memory so the system does not forget or fake proof."
        ),
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
        "does": (
            "Detects danger before action: fake green, hidden tracking, public/private leaks, unsafe "
            "claims, payment/dispatch risks and protocol bypass attempts."
        ),
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
        "does": (
            "Coordinates safe execution steps: tool handoffs, build order, deploy checks, route checks, "
            "agent handover and recovery timing without rushing."
        ),
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
        "does": (
            "Keeps the private brain alive and safe: health checks, fail-closed gates, uptime checks, "
            "basic survival state and controlled shutdown of unsafe processes."
        ),
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


def _part_status(part: dict[str, object]) -> dict[str, Any]:
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
        "detail_complete": True,
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
            "details_defined": "14/14",
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
        "result": "details_complete_protocol_only",
        "execution_granted": False,
        "real_green": False,
        "war_room": {
            "checks_started": "14 brain parts x 7 proof checks",
            "current_score": status["score"],
            "decision": "details are now defined for every part; remaining checks require live proof wiring",
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
