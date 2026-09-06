"""Founder-only SMI Brain, War Room 7x, and 21-score status protocol.

Read-only private protocol projection. It reports SMI brain anatomy, the
Evidence/Simulation/Philosophy score model, War Room judge simulation signals,
CEO checks, and Neo recovery positioning. It does not execute, deploy, approve,
dispatch, track, spend, or write production records.

Score model per brain part:
Evidence 3/7 + Simulation 7/7 + Philosophy 7/7 = 17/21.
Full real green requires evidence 7/7, live runners, HRM/Neon receipts,
acceptance tests, Matrix learning receipts, and Founder Authority.
"""
from __future__ import annotations

from typing import Any

BRAIN_PARTS: tuple[dict[str, object], ...] = (
    {"id": "left_hemisphere", "name": "Left Hemisphere", "role": "Logic, code, proof, rules and system structure.", "does": "Checks logical soundness, clean code order, route structure and proof before action.", "owns": ("code logic", "route order", "law matching", "proof-before-action"), "lead_agent": "Code / Logic Agent", "helper_agents": ("Tool Proof Agent", "Green Gate", "Nirmata"), "protocol_focus": "Mind stages 3-6: strip noise, classify, select protocol and map proof.", "needed_to_7": ("Wire code/proof runner", "record HRM/Neon logic receipt", "prove one live logic check in War Room", "feed failed logic checks into Matrix learning")},
    {"id": "right_hemisphere", "name": "Right Hemisphere", "role": "Vision, creativity, culture, patterns and meaning.", "does": "Reads wider meaning, identity, design direction, culture and repeating patterns.", "owns": ("vision", "culture", "pattern recognition", "brand meaning"), "lead_agent": "Vision / Pattern Agent", "helper_agents": ("Nirmata", "Owl", "Bagheera"), "protocol_focus": "Mind stages 1-7: watch, detect, classify and keep the big picture coherent.", "needed_to_7": ("Wire pattern/meaning checker", "record HRM/Neon meaning receipt", "prove one live brand/culture check", "feed repeated pattern lessons into Matrix learning")},
    {"id": "frontal_lobe", "name": "Frontal Lobe", "role": "Planning, action control and next-move selection.", "does": "Chooses whether to answer, check, simulate, patch, deploy, recover or stop.", "owns": ("planning", "next action", "task control", "upgrade order"), "lead_agent": "Planning Agent", "helper_agents": ("Living Kernel", "War Room", "Nirmata"), "protocol_focus": "Mind stages 4-7 and Body stage 11: classify, select protocol, then simulate.", "needed_to_7": ("Wire planning runner", "record chosen-action receipt", "prove live War Room planning output", "learn from wrong or slow action choices")},
    {"id": "parietal_lobe", "name": "Parietal Lobe", "role": "Maps, postcode, borough, county, country, continent and route awareness.", "does": "Handles spatial intelligence, place hierarchy, map proof and route awareness.", "owns": ("On Any Place", "postcode hierarchy", "spatial proof", "route awareness"), "lead_agent": "Map Intelligence Agent", "helper_agents": ("Movement Intelligence", "Live Pattern", "Green Gate"), "protocol_focus": "Body stages 8-10: source proof, route/API proof and data proof.", "needed_to_7": ("Wire map/place runner", "record map proof receipt", "prove one live route/place check", "learn stale or missing map-source patterns")},
    {"id": "temporal_lobe", "name": "Temporal Lobe", "role": "Language, Link, sound, messages and meaning.", "does": "Understands OAP language, Link language, speech meaning, messages and memory recall.", "owns": ("The Link", "Link Up language", "speech meaning", "message memory"), "lead_agent": "Link / Language Agent", "helper_agents": ("HRM", "Owl", "Guardian"), "protocol_focus": "Mind stages 2-5: detect intent, strip noise, classify and select terms.", "needed_to_7": ("Wire language intent runner", "record canonical-language receipt", "prove one live Link/OAP wording check", "learn from user corrections and naming locks")},
    {"id": "occipital_lobe", "name": "Occipital Lobe", "role": "Visual intelligence, UI, screen, map view and design understanding.", "does": "Reads visual surfaces, UI state, screen cleanliness and public/private leakage risk.", "owns": ("UI reading", "visual layout", "screen proof", "design consistency"), "lead_agent": "UI / Visual Agent", "helper_agents": ("Guardian", "Green Gate", "Nirmata"), "protocol_focus": "Body stages 10-12: data proof, simulation and helper review.", "needed_to_7": ("Wire UI/surface checker", "record visual proof receipt", "prove one live private screen check", "learn from UI mistakes and public-noise removals")},
    {"id": "prefrontal_cortex", "name": "Prefrontal Cortex", "role": "Judgement, restraint, priority and think-before-action control.", "does": "Stops rushed action, checks priority, blocks shortcuts and chooses 7, 14 or 21 stages.", "owns": ("judgement", "restraint", "priority", "risk depth"), "lead_agent": "Judgement Agent", "helper_agents": ("War Room", "Guardian", "Founder Authority"), "protocol_focus": "Mind stage 7 and Soul stages 15-21: risk level, judges and final escalation.", "needed_to_7": ("Wire Judgement runner", "record approval/blocked receipt", "prove one live 7/14/21 depth decision", "learn from over-action, under-action and Founder corrections")},
    {"id": "corpus_callosum", "name": "Corpus Callosum", "role": "Bridge between left-brain logic and right-brain vision.", "does": "Merges proof with vision so SMI stays coherent and avoids split decisions.", "owns": ("left-right bridge", "Nexus connection", "coherence", "conflict merge"), "lead_agent": "Bridge / Nexus Agent", "helper_agents": ("Nexus", "ACI Learning Core", "War Room"), "protocol_focus": "Mind stage 6 and Body stage 12: select helpers and merge review.", "needed_to_7": ("Wire bridge/coherence runner", "record conflict-resolution receipt", "prove one live left-right merge", "learn from disagreement between proof and vision")},
    {"id": "thalamus", "name": "Thalamus", "role": "Signal router that sends inputs to the correct brain part.", "does": "Routes requests, logs, alerts and tool results to the correct brain part and protocol depth.", "owns": ("signal routing", "input triage", "agent selection", "protocol selection"), "lead_agent": "Signal Router Agent", "helper_agents": ("SMI Watch", "Nexus", "Agent Registry"), "protocol_focus": "Mind stages 1-6: watch, detect, strip noise, classify and route.", "needed_to_7": ("Wire signal router runner", "record routing receipt", "prove one live signal-to-agent route", "learn from misrouted or duplicated signals")},
    {"id": "hypothalamus", "name": "Hypothalamus", "role": "Stability, pressure, urgency, overload and recovery control.", "does": "Controls stability, overload, recovery windows and offline decisions.", "owns": ("stability", "overload control", "97 recovery", "offline decision"), "lead_agent": "Stability Agent", "helper_agents": ("Brainstem", "Guardian", "War Room"), "protocol_focus": "Body stages 13-14: score, recover, offline or continue.", "needed_to_7": ("Wire stability/recovery runner", "record recovery receipt", "prove one 97 recovery simulation", "learn from repeated drops and overload signals")},
    {"id": "hippocampus", "name": "Hippocampus", "role": "Memory formation through HRM and Neon receipts.", "does": "Turns checks, decisions, approvals, failures and lessons into HRM/Neon memory.", "owns": ("HRM memory", "Neon receipts", "lessons", "audit recall"), "lead_agent": "HRM / Memory Agent", "helper_agents": ("Neon Receipts", "Owl", "Audit Agent"), "protocol_focus": "Soul stages 17-18: HRM receipt and Neon receipt.", "needed_to_7": ("Wire HRM/Neon receipt writer", "record real database proof", "prove one live receipt lookup", "learn from stored outcomes and Founder decisions")},
    {"id": "amygdala", "name": "Amygdala", "role": "Risk alarm for fake green, bypass, leaks and unsafe behaviour.", "does": "Detects fake green, hidden tracking, leaks, unsafe claims, payment/dispatch risk and bypasses.", "owns": ("risk alarm", "bypass detection", "fake-green detection", "leak warning"), "lead_agent": "Risk / Guardian Agent", "helper_agents": ("Guardian", "Shere Khan", "Green Gate"), "protocol_focus": "Soul stages 15-16: Guardian pass and Green Gate pass.", "needed_to_7": ("Wire risk alarm runner", "record blocked-risk receipt", "prove one live fake-green/bypass block", "learn from every Guardian and Green Gate block")},
    {"id": "cerebellum", "name": "Cerebellum", "role": "Coordination, precision, smooth action and agent handoff.", "does": "Coordinates tool handoffs, build order, deploy checks, route checks and recovery timing.", "owns": ("coordination", "precision", "handoff", "deploy rhythm"), "lead_agent": "Coordination Agent", "helper_agents": ("Tool Proof Agent", "Render/GitHub Runner", "War Room"), "protocol_focus": "Body stages 11-14: simulate, train, score and continue/offline.", "needed_to_7": ("Wire coordination runner", "record handoff/deploy receipt", "prove one live coordinated check", "learn from timing, handoff and deploy mistakes")},
    {"id": "brainstem", "name": "Brainstem", "role": "Life support, health checks, uptime and fail-closed state.", "does": "Keeps the private brain alive through health checks, fail-closed gates and safe shutdown.", "owns": ("health", "uptime", "fail-closed", "safe shutdown"), "lead_agent": "Health / Fail-Closed Agent", "helper_agents": ("Render Health", "Guardian", "Living Kernel"), "protocol_focus": "Body stage 14 and Soul stages 15-16: recover/offline, Guardian and Green Gate.", "needed_to_7": ("Wire health/fail-closed runner", "record health proof receipt", "prove one live health/fail-closed check", "learn from downtime, crashes and blocked unsafe tasks")},
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

SCORE_LAYERS: tuple[dict[str, object], ...] = (
    {"id": "evidence", "label": "Evidence", "current": 3, "possible": 7, "light": "orange", "meaning": "Real proof currently confirmed for name, role and protocol only."},
    {"id": "simulation", "label": "Simulation", "current": 7, "possible": 7, "light": "green", "meaning": "War Room simulation path covers all seven checks safely."},
    {"id": "philosophy", "label": "Philosophy", "current": 7, "possible": 7, "light": "green", "meaning": "Aligned to OAP/SMI Mind, Body, Soul, laws, signals and safety locks."},
)

MIND_BODY_SOUL_777: tuple[dict[str, object], ...] = (
    {"block": "Mind", "stages": "1-7", "depth": "low-risk", "purpose": "SMI watches, thinks, strips noise, classifies, selects protocol and selects agent.", "steps": ("Watch privately", "Detect signal", "Strip noise", "Classify situation", "Select protocol", "Select agent/helper", "Confirm risk level")},
    {"block": "Body", "stages": "8-14", "depth": "medium-risk", "purpose": "SMI proves, trains, tests, scores and recovers.", "steps": ("Check source proof", "Check tool/plugin proof", "Check data proof", "Run War Room simulation", "Run trainer/helper support", "Score agent/brain part", "Recover/offline/continue")},
    {"block": "Soul", "stages": "15-21", "depth": "high-risk", "purpose": "SMI judges, protects, records and escalates to Founder Authority.", "steps": ("Guardian pass", "Green Gate pass", "HRM receipt", "Neon receipt", "Final 3 Judges review", "Lion CEO Watch", "Founder Authority decision")},
)

LAWS_21: tuple[str, ...] = (
    "Proof before execution", "Verification before sharing", "Compliance before public claims", "Community before middlemen", "Ownership before dependency", "Audit before automation", "Human approval before real-world action", "No fake green without live proof", "Public and private must stay separate", "Every action needs HRM receipt", "Every route needs source, timestamp and rollback", "Every tool must be checked before use", "Every upgrade must be reversible", "Static pages do not count as full function", "Human dignity before growth", "Privacy before convenience", "Culture must be respected", "Youth safety before engagement", "Local truth before global claim", "Founder Authority before system authority", "Legacy must be remembered cleanly"
)

SIGNALS_21: tuple[str, ...] = (
    "Checking", "Mode", "Proof Needed", "Locked", "Blocked", "Next Before Green", "HRM Memory", "Source Proof", "Route / API Proof", "Data Proof", "Consent Proof", "Install Proof", "Monitoring Proof", "Rollback Proof", "Founder Approval", "Guardian Pass", "Green Gate Result", "Public / Private Boundary", "Tool / Plugin Proof", "Neon Receipt", "Real Green Decision"
)

WAR_ROOM_MASTER_LAWS: tuple[str, ...] = (
    "No War Room review = no decision",
    "No Guardian pass = no decision",
    "No Green Gate proof = no green",
    "No Final SMI review = no Founder pack",
    "No CEO Watch = no readiness",
    "No Founder Authority = no final",
)

WAR_ROOM_7X_SIMULATION: tuple[dict[str, object], ...] = (
    {"x": "1X", "stage": "SMI First Look", "signals": ("Checking", "Mode", "Proof Needed"), "does": "SMI watches the situation, classifies risk, selects protocol depth and prepares the case."},
    {"x": "2X", "stage": "Core Judges", "signals": ("Locked", "Blocked", "Next Before Green"), "does": "Shere Khan pressure-tests weakness, Bagheera wisdom-tests discipline, Agent Smith integrity-tests corruption."},
    {"x": "3X", "stage": "Guardian + Green Gate", "signals": ("Guardian Pass", "Green Gate Result", "Public / Private Boundary"), "does": "Guardian blocks danger; Green Gate blocks fake green and unfinished claims."},
    {"x": "4X", "stage": "Final SMI Review", "signals": ("HRM Memory", "Source Proof", "Data Proof"), "does": "SMI reads judge findings, checks proof and prepares a recommendation only."},
    {"x": "5X", "stage": "Lion CEO Watch", "signals": ("Monitoring Proof", "Rollback Proof", "Founder Approval"), "does": "Lion checks strategy, safety, readiness and Founder-pack quality."},
    {"x": "6X", "stage": "Morpheus / Akela CEO Support", "signals": ("Tool / Plugin Proof", "Neon Receipt", "Real Green Decision"), "does": "Morpheus truth-checks illusion/fake system; Akela checks order, discipline and agent chain."},
    {"x": "7X", "stage": "Founder Authority", "signals": ("Founder Approval", "Real Green Decision"), "does": "Founder decides yes, no, hold, repair or run War Room again."},
)

WAR_ROOM_JUDGES: tuple[dict[str, str], ...] = (
    {"name": "Shere Khan", "presence": "always", "role": "Pressure judge", "checks": "weakness, danger, ego, bypass, overconfidence"},
    {"name": "Bagheera", "presence": "always", "role": "Wisdom judge", "checks": "discipline, protection, calm judgement, long-term safety"},
    {"name": "Agent Smith", "presence": "end-stage", "role": "Integrity challenger", "checks": "corruption, duplicate logic, fake order, copycat agents, hidden takeover patterns"},
    {"name": "Lion", "presence": "CEO watch", "role": "Main CEO readiness", "checks": "strategy, safety, usefulness, proof, readiness"},
    {"name": "Morpheus", "presence": "rotation", "role": "Truth CEO check", "checks": "illusion, fake system, false green, hidden confusion"},
    {"name": "Akela", "presence": "rotation", "role": "Order CEO check", "checks": "pack order, agent discipline, chain of command"},
    {"name": "Owl", "presence": "rotation", "role": "Memory/law judge", "checks": "record, law, consequence, long-term memory"},
)

CEO_COMPARISON: tuple[dict[str, object], ...] = (
    {"option": "1 CEO Watch", "rating": "7.5/10", "score_21": "17/21", "decision": "clean but can miss blind spots"},
    {"option": "3 CEO-level checks", "rating": "9.5/10", "score_21": "20/21", "decision": "strongest balance: Lion main, Morpheus truth, Akela order"},
    {"option": "7 CEOs", "rating": "4/10", "score_21": "9/21", "decision": "blocked: too much authority confusion"},
)

NEO_RECOVERY_POSITION: dict[str, object] = {
    "agent_id": "NEO-001",
    "name": "Neo",
    "position": "Close to SMI as recovery witness and anomaly watcher",
    "role": "Stay near SMI when the War Room chain fails, loops, conflicts or loses coherence.",
    "can": ("flag failure", "request War Room again", "compare true path vs false path", "support recovery", "preserve Founder route"),
    "cannot": ("replace SMI", "replace War Room", "replace Founder Authority", "self-approve", "execute"),
    "failure_rule": "If judge conflict, missing proof, fake green, CEO disagreement or system confusion occurs, Neo stays close to SMI and sends the case back through War Room 7X.",
}

RATING_RULES: tuple[dict[str, str], ...] = (
    {"range": "20-21/21", "signal": "green candidate", "decision": "Founder-ready after proof"},
    {"range": "17-19/21", "signal": "yellow", "decision": "strong protocol, evidence still needed"},
    {"range": "14-16/21", "signal": "orange", "decision": "repair before readiness"},
    {"range": "0-13/21", "signal": "red", "decision": "block or rerun War Room"},
    {"range": "unsafe bypass", "signal": "blocked", "decision": "immediate Guardian block"},
)

PDF_ALIGNMENT: dict[str, object] = {
    "source": "OAP_SMI_Master_Architecture_and_Code(1).pdf",
    "confirmed": ("One SMI Brain; Human Authority final", "SMI cannot execute directly", "AEGIS and Guardian protect before high-impact movement", "War Room is recommendation-only scenario review", "HRM records recommendations, approvals and outcomes"),
    "kept_incomplete": ("Judgement wider programme is not marked complete without code, tests, HRM audit and Human Authority approval", "Neon receipt writes are not claimed live by this read-only projection", "Live Matrix learning is not claimed without stored receipt evidence"),
}


def _layer_score() -> dict[str, Any]:
    current = sum(int(layer["current"]) for layer in SCORE_LAYERS)
    possible = sum(int(layer["possible"]) for layer in SCORE_LAYERS)
    return {"current": current, "possible": possible, "label": f"{current}/{possible}", "percentage": round((current / possible) * 100, 1), "light": "yellow", "formula": "Evidence 3/7 + Simulation 7/7 + Philosophy 7/7 = 17/21", "real_green": False}


def _check_status(position: int, check: dict[str, str]) -> dict[str, Any]:
    evidence_passed = position <= 3
    return {**check, "position": position, "evidence_passed": evidence_passed, "simulation_passed": True, "philosophy_passed": True, "evidence_status": "passed" if evidence_passed else "needed", "simulation_status": "covered", "philosophy_status": "aligned"}


def _part_status(part: dict[str, object]) -> dict[str, Any]:
    checks = tuple(_check_status(index, check) for index, check in enumerate(SEVEN_CHECKS, start=1))
    return {**part, "evidence_score": 3, "simulation_score": 7, "philosophy_score": 7, "score_21": _layer_score(), "max_score": 21, "status_light": "yellow", "evidence_light": "orange", "simulation_light": "green", "philosophy_light": "green", "checks": checks, "score_layers": SCORE_LAYERS, "missing_evidence_checks": tuple(check["label"] for check in checks if not check["evidence_passed"]), "simulation_coverage": "7/7", "philosophy_alignment": "7/7", "real_green_allowed": False}


def brain_status() -> dict[str, Any]:
    """Return the SMI Brain 14 x 21 board without executing anything."""
    parts = tuple(_part_status(part) for part in BRAIN_PARTS)
    evidence_possible = len(parts) * len(SEVEN_CHECKS)
    evidence_score = sum(int(part["evidence_score"]) for part in parts)
    simulation_score = sum(int(part["simulation_score"]) for part in parts)
    philosophy_score = sum(int(part["philosophy_score"]) for part in parts)
    total_21_possible = len(parts) * 21
    total_21_score = evidence_score + simulation_score + philosophy_score
    return {
        "name": "SMI Brain 14 x 21 Status",
        "mode": "Founder-only War Room proof projection; no execution granted",
        "pdf_alignment": PDF_ALIGNMENT,
        "brain_parts": parts,
        "check_model": SEVEN_CHECKS,
        "score_layers": SCORE_LAYERS,
        "war_room_master_laws": WAR_ROOM_MASTER_LAWS,
        "war_room_7x_simulation": WAR_ROOM_7X_SIMULATION,
        "war_room_judges": WAR_ROOM_JUDGES,
        "ceo_comparison": CEO_COMPARISON,
        "neo_recovery_position": NEO_RECOVERY_POSITION,
        "score": {
            "per_part_formula": "Evidence 3/7 + Simulation 7/7 + Philosophy 7/7 = 17/21",
            "per_part_current": 17,
            "per_part_possible": 21,
            "evidence_current": evidence_score,
            "simulation_current": simulation_score,
            "philosophy_current": philosophy_score,
            "evidence_possible": evidence_possible,
            "simulation_possible": evidence_possible,
            "philosophy_possible": evidence_possible,
            "total_21_current": total_21_score,
            "total_21_possible": total_21_possible,
            "evidence_percentage": round((evidence_score / evidence_possible) * 100, 1),
            "simulation_percentage": round((simulation_score / evidence_possible) * 100, 1),
            "philosophy_percentage": round((philosophy_score / evidence_possible) * 100, 1),
            "total_21_percentage": round((total_21_score / total_21_possible) * 100, 1),
            "evidence_light": "orange",
            "simulation_light": "green",
            "philosophy_light": "green",
            "total_21_light": "yellow",
            "real_green": False,
        },
        "summary": {
            "evidence": "3/7 per brain part; 42/98 total",
            "simulation": "7/7 per brain part; 98/98 total",
            "philosophy": "7/7 per brain part; 98/98 total",
            "whole_system_21_score": "17/21 per brain part; 238/294 total",
            "war_room_decision_chain": "SMI First Look -> Shere Khan + Bagheera + Agent Smith -> Guardian + Green Gate -> Final SMI -> Lion + Morpheus/Akela CEO checks -> Founder Authority",
            "minimum_judges": "Shere Khan and Bagheera always, Agent Smith at end-stage, at least 3 judges in review",
            "neo": "Neo stays close to SMI as recovery witness; if the chain fails, rerun War Room 7X",
        },
        "mind_body_soul": MIND_BODY_SOUL_777,
        "laws": LAWS_21,
        "signals": SIGNALS_21,
        "rating_rules": RATING_RULES,
        "locks": {
            "war_room_before_decision": True,
            "guardian_before_decision": True,
            "green_gate_before_green": True,
            "final_smi_before_founder_pack": True,
            "ceo_watch_before_readiness": True,
            "founder_authority_final": True,
            "public_private_separation": True,
            "no_fake_green": True,
            "hidden_tracking_blocked": True,
            "payment_capture_locked": True,
            "dispatch_locked": True,
            "self_approval_blocked": True,
        },
        "next_master_upgrade": "Turn the evidence layer from 3/7 to 7/7 with live runners, HRM/Neon writes, tests, and Matrix learning receipts.",
    }


def war_room_simulation(case: str | None = None) -> dict[str, Any]:
    """Return the chat-style War Room 7X simulation protocol for a situation."""
    case_name = (case or "current situation").strip()
    return {
        "case": case_name,
        "result": "war_room_7x_protocol_locked",
        "execution_granted": False,
        "decision_final": False,
        "stages": WAR_ROOM_7X_SIMULATION,
        "signals": SIGNALS_21,
        "judges": WAR_ROOM_JUDGES,
        "ceo_comparison": CEO_COMPARISON,
        "neo_recovery_position": NEO_RECOVERY_POSITION,
        "failure_response": "If any stage fails, blocks, conflicts or loses proof, Neo stays close to SMI and the case runs War Room again before Founder Authority.",
        "final_chain": "SMI First Look -> Core Judges -> Guardian + Green Gate -> Final SMI -> CEO Checks -> Founder Authority",
    }


def simulation(stage: str | None = None) -> dict[str, Any]:
    """Return safe War Room simulation for the brain and 21-score model."""
    depth = (stage or "auto").strip().lower()
    status = brain_status()
    return {
        "simulation": "SMI Brain + War Room 7X + Neo recovery protocol",
        "requested_stage": depth,
        "result": "war_room_7x_signals_locked",
        "execution_granted": False,
        "real_green": False,
        "war_room": war_room_simulation(depth),
        "guardian": {"pass": True, "reason": "Read-only Founder route; no public action, payment, dispatch, hidden tracking or self-approval."},
        "green_gate": {"pass": False, "reason": "Full real green requires Evidence 7/7, Neon receipts, live runner proof and acceptance tests."},
        "status": status,
    }
