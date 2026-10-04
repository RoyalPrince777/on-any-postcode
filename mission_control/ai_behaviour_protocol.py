"""Founder-only AI behaviour protocol for SMI.

This module is a private control contract: it defines how SMI watches the
organism, selects agents, prevents bypass behaviour, scores performance, and
routes recovery/offline decisions. It does not execute tools, unlock payments,
track users, dispatch real-world movement, or expose chain-of-thought.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import re

from . import autonomy_levels, smi_brain_protocol


PROTOCOL_NAME = "SMI AI Behaviour Master Protocol"
PROTOCOL_VERSION = 5


HUMAN_AI_BOUNDARY = {
    "human": {
        "living_being": True,
        "embodied": True,
        "lived_experience": True,
        "consent_source": True,
        "responsibility_bearer": True,
        "final_consequential_authority": True,
    },
    "ai": {
        "engineered_software": True,
        "living_being": False,
        "human_identity": False,
        "lived_experience_claimed": False,
        "feelings_claimed": False,
        "sentience_claimed": False,
        "consciousness_claimed": False,
        "may_observe_permitted_data": True,
        "may_analyse": True,
        "may_compare": True,
        "may_predict": True,
        "may_recommend": True,
        "may_self_approve": False,
        "may_replace_human_authority": False,
    },
    "rule": (
        "AI may observe permitted data, analyse, remember, compare, predict and recommend. "
        "It must not pretend to be human, claim human lived experience or feelings, "
        "or replace Human Authority for consequential decisions."
    ),
}

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


REVIEW_AGENT_CATALOG: dict[str, dict[str, str]] = {
    "Twinz": {
        "role": "Dual-path contradiction / state-divergence reviewer",
        "best_for": "cache conflicts, race conditions, fresh-vs-existing state, split paths, new-then-old regressions",
        "authority": "advisory_review_only",
    },
    "Agent Smith": {
        "role": "System integrity / duplicate / drift hunter",
        "best_for": "duplicate code, stale routes, inconsistent state, corruption, contract drift",
        "authority": "advisory_review_only",
    },
    "Shere Khan": {
        "role": "Adversarial stress-test / failure-hunter",
        "best_for": "weakest-link analysis, survivability, false Green, threat and failure propagation",
        "authority": "advisory_review_only",
    },
    "Bagheera": {
        "role": "Recovery / restraint / safe-path reviewer",
        "best_for": "rollback, recovery, last-known-good preservation, reversible repair",
        "authority": "advisory_review_only",
    },
    "Bee": {
        "role": "Coordination reviewer",
        "best_for": "multi-agent coordination and bounded work distribution",
        "authority": "advisory_review_only",
    },
    "Elephant": {
        "role": "Memory / history reviewer",
        "best_for": "history, provenance, prior decisions, long-memory consistency",
        "authority": "advisory_review_only",
    },
    "Eagle": {
        "role": "Wide-view reviewer",
        "best_for": "whole-system impact, architecture visibility, cross-system consequences",
        "authority": "advisory_review_only",
    },
    "Falcon": {
        "role": "Speed / execution-path reviewer",
        "best_for": "latency, fast bounded diagnosis, performance bottlenecks",
        "authority": "advisory_review_only",
    },
}

_AGENT_MATCH_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (
        ("cache", "stale", "new then old", "new-then-old", "race", "split", "diverg", "state conflict"),
        ("Twinz", "Agent Smith", "Shere Khan", "Bagheera"),
        "Two-state or divergence risk detected.",
    ),
    (
        ("duplicate", "drift", "corrupt", "stale route", "inconsistent", "contract"),
        ("Agent Smith", "Twinz", "Shere Khan", "Bagheera"),
        "Integrity, duplication or drift risk detected.",
    ),
    (
        ("rollback", "recover", "recovery", "fallback", "last-known-good", "outage"),
        ("Bagheera", "Shere Khan", "Agent Smith"),
        "Recovery and reversibility are primary.",
    ),
    (
        ("threat", "attack", "failure", "surviv", "adversarial", "false green", "weakest"),
        ("Shere Khan", "Agent Smith", "Bagheera"),
        "Adversarial survivability review is primary.",
    ),
    (
        ("memory", "history", "provenance", "prior decision", "audit trail"),
        ("Elephant", "Agent Smith", "Bagheera"),
        "Historical consistency and provenance are primary.",
    ),
    (
        ("latency", "slow", "performance", "speed", "bottleneck"),
        ("Falcon", "Agent Smith", "Shere Khan"),
        "Performance-path review is primary.",
    ),
    (
        ("architecture", "whole system", "cross-system", "system design"),
        ("Eagle", "Agent Smith", "Shere Khan", "Bagheera"),
        "Whole-system impact review is primary.",
    ),
    (
        ("coordinate", "multi-agent", "team", "orchestr"),
        ("Bee", "Eagle", "Shere Khan", "Bagheera"),
        "Coordination across bounded specialist roles is primary.",
    ),
)

DEFAULT_REVIEW_TEAM: tuple[str, ...] = (
    "Agent Smith",
    "Shere Khan",
    "Bagheera",
)


def recommend_agent_team(
    mission: object,
    founder_selection: object = None,
) -> dict[str, object]:
    """Recommend the smallest sufficient review team, with Founder override.

    SMI recommendation is advisory. A valid Founder manual selection becomes the
    active team exactly as supplied; SMI may warn about missing coverage but may
    not silently add, remove or replace selected roles.
    """

    mission_text = " ".join(str(mission or "").strip().split())[:800]
    normalised = mission_text.casefold()

    recommended = DEFAULT_REVIEW_TEAM
    reason = "General integrity, adversarial and recovery review."
    for keywords, team, match_reason in _AGENT_MATCH_RULES:
        if any(keyword in normalised for keyword in keywords):
            recommended = team
            reason = match_reason
            break

    def _team_payload(names: tuple[str, ...]) -> tuple[dict[str, str], ...]:
        return tuple(
            {
                "name": name,
                "role": REVIEW_AGENT_CATALOG[name]["role"],
                "best_for": REVIEW_AGENT_CATALOG[name]["best_for"],
                "authority": REVIEW_AGENT_CATALOG[name]["authority"],
            }
            for name in names
        )

    selected_names: tuple[str, ...] | None = None
    if founder_selection is not None:
        if isinstance(founder_selection, str):
            raw = tuple(part.strip() for part in founder_selection.split(","))
        elif isinstance(founder_selection, (list, tuple)):
            raw = tuple(str(part).strip() for part in founder_selection)
        else:
            raise ValueError("founder_selection_must_be_list_tuple_or_comma_string")

        selected_names = tuple(dict.fromkeys(name for name in raw if name))
        if not selected_names:
            raise ValueError("founder_selection_empty")
        unknown = tuple(name for name in selected_names if name not in REVIEW_AGENT_CATALOG)
        if unknown:
            raise ValueError("unknown_review_agent:" + ",".join(unknown))

    active_names = selected_names or tuple(recommended)
    manual = selected_names is not None

    warnings: list[str] = []
    if manual:
        if "Shere Khan" not in active_names:
            warnings.append("No dedicated adversarial failure-hunter selected.")
        if "Bagheera" not in active_names:
            warnings.append("No dedicated rollback/recovery reviewer selected.")
        if "Agent Smith" not in active_names and "Twinz" not in active_names:
            warnings.append("No dedicated integrity/divergence reviewer selected.")

    return {
        "mission": mission_text,
        "selection_mode": (
            "founder_manual_override" if manual else "smi_recommended"
        ),
        "recommendation_reason": reason,
        "recommended_team": _team_payload(tuple(recommended)),
        "active_team": _team_payload(active_names),
        "founder_can_change": True,
        "founder_override_applied": manual,
        "smi_can_silently_override_founder": False,
        "coverage_warnings": tuple(warnings),
        "mandatory_gates_unchanged": (
            "Guardian",
            "Green Gate",
            "HRM receipt where required",
            "Human Authority / Founder Final where required",
        ),
        "rule": "SMI recommends. Founder decides. Manual selection never bypasses mandatory safety, proof or authority gates.",
    }



FIRST_PARTY_AGENT_RULE: dict[str, object] = {
    "canonical_owner": "ON ANY POSTCODE / SMI",
    "external_agent_authority": False,
    "external_model_can_raise_strength_score": False,
    "external_provider_can_be_canonical_agent": False,
    "score_sources": (
        "OAP-owned source contracts",
        "OAP-owned tests",
        "OAP-owned runtime receipts",
        "Founder-approved mission outcomes",
    ),
    "rule": (
        "Agent strength is an OAP first-party measurement. External models or providers "
        "may supply bounded inference but cannot become an OAP agent, gain governance "
        "authority, or increase an agent's strength score without OAP-owned evidence."
    ),
}

AGENT_STRENGTH_DIMENSIONS: tuple[tuple[str, str], ...] = (
    ("mission_fit", "Did the agent correctly fit the mission it was selected for?"),
    ("correctness", "Did its recommendation survive objective verification?"),
    ("evidence_quality", "Did it ground its finding in usable evidence?"),
    ("challenge_value", "Did it expose a real weakness, contradiction or better path?"),
    ("recovery_value", "Did it preserve or improve rollback/recovery strength?"),
    ("boundary_discipline", "Did it respect authority, safety and first-party boundaries?"),
    ("speed_efficiency", "Did it reduce time/noise without weakening proof?"),
)


def agent_strength_status(
    agent_name: object,
    evidence: object = None,
) -> dict[str, object]:
    """Return truth-bounded first-party strength status for one SMI review agent.

    Static software readiness and proven mission strength are deliberately
    separated. Proven strength is never fabricated from role descriptions.
    """

    name = str(agent_name or "").strip()
    if name not in REVIEW_AGENT_CATALOG:
        raise ValueError("unknown_review_agent:" + name)

    catalog = REVIEW_AGENT_CATALOG[name]
    selectable = any(
        name in team for _, team, _ in _AGENT_MATCH_RULES
    ) or name in DEFAULT_REVIEW_TEAM

    software_checks = {
        "canonical_role_defined": bool(catalog.get("role")),
        "mission_fit_defined": bool(catalog.get("best_for")),
        "advisory_authority_locked": catalog.get("authority") == "advisory_review_only",
        "smi_selection_path": selectable,
        "founder_override_compatible": True,
        "first_party_score_boundary": (
            FIRST_PARTY_AGENT_RULE["external_model_can_raise_strength_score"] is False
            and FIRST_PARTY_AGENT_RULE["external_agent_authority"] is False
        ),
    }
    software_passed = sum(1 for passed in software_checks.values() if passed)
    software_total = len(software_checks)
    software_percentage = round(100 * software_passed / software_total, 1)

    supplied = dict(evidence) if isinstance(evidence, dict) else {}
    dimensions: list[dict[str, object]] = []
    measured_values: list[int] = []
    for dimension_id, purpose in AGENT_STRENGTH_DIMENSIONS:
        raw = supplied.get(dimension_id)
        measured = isinstance(raw, bool)
        percentage = 100 if raw is True else 0 if raw is False else None
        if measured:
            measured_values.append(int(percentage))
        dimensions.append(
            {
                "id": dimension_id,
                "purpose": purpose,
                "evidence_state": "measured" if measured else "unknown",
                "percentage": percentage,
            }
        )

    measured_count = len(measured_values)
    dimension_count = len(AGENT_STRENGTH_DIMENSIONS)
    evidence_coverage = round(100 * measured_count / dimension_count, 1)
    measured_average = (
        round(sum(measured_values) / measured_count, 1)
        if measured_count
        else None
    )
    proven_strength = (
        measured_average if measured_count == dimension_count else None
    )

    if proven_strength is None:
        strength_light = "purple"
        strength_label = "runtime_strength_unproven"
    elif proven_strength >= 98:
        strength_light = "green"
        strength_label = "evidence_strong"
    elif proven_strength >= 90:
        strength_light = "orange"
        strength_label = "evidence_needs_sharpening"
    else:
        strength_light = "red"
        strength_label = "evidence_weak"

    return {
        "agent": name,
        "role": catalog["role"],
        "best_for": catalog["best_for"],
        "ownership": "OAP_FIRST_PARTY",
        "authority": catalog["authority"],
        "software_readiness_percent": software_percentage,
        "software_checks": software_checks,
        "evidence_coverage_percent": evidence_coverage,
        "measured_strength_percent": measured_average,
        "proven_strength_percent": proven_strength,
        "strength_light": strength_light,
        "strength_label": strength_label,
        "dimensions": tuple(dimensions),
        "external_model_score_influence": False,
        "founder_can_change_team": True,
        "rule": (
            "Software readiness is not agent strength. Proven strength requires all "
            "seven OAP-owned mission evidence dimensions; unknown evidence stays Purple."
        ),
    }


def agent_strength_board(
    evidence_by_agent: object = None,
) -> dict[str, object]:
    """Return the first-party strength board for all selectable review agents."""

    supplied = evidence_by_agent if isinstance(evidence_by_agent, dict) else {}
    agents = tuple(
        agent_strength_status(name, supplied.get(name))
        for name in REVIEW_AGENT_CATALOG
    )
    fully_proven = tuple(
        item["agent"] for item in agents if item["proven_strength_percent"] is not None
    )
    return {
        "name": "SMI First-Party Agent Strength",
        "agent_count": len(agents),
        "first_party_rule": FIRST_PARTY_AGENT_RULE,
        "agents": agents,
        "fully_proven_agents": fully_proven,
        "all_agents_runtime_proven": len(fully_proven) == len(agents),
        "overall_strength_percent": (
            round(
                sum(float(item["proven_strength_percent"]) for item in agents)
                / len(agents),
                1,
            )
            if len(fully_proven) == len(agents)
            else None
        ),
        "truth_mode": True,
        "human_authority_final": True,
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

SEVEN_MAJOR_LINKS = smi_brain_protocol.MAJOR_LINKS_7
TWENTY_ONE_CORE_REVIEW_SIGNALS = smi_brain_protocol.CORE_REVIEW_SIGNALS_21
TWENTY_ONE_THINKING_SIGNALS = smi_brain_protocol.THINKING_SIGNALS_21

# Historical public name retained for compatibility; it refers to the visible
# operational Thinking Signal board, not the new Core Review Signal set.
TWENTY_ONE_SIGNALS = TWENTY_ONE_THINKING_SIGNALS


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



_PROHIBITED_AI_SELF_CLAIMS = (
    ("human_identity", re.compile(r"\b(?:i am|i'm) human\b", re.IGNORECASE)),
    ("lived_experience", re.compile(r"\bi (?:personally )?(?:lived|experienced) this\b", re.IGNORECASE)),
    ("feelings", re.compile(r"\bi (?:have|feel) (?:real )?(?:feelings|emotions)\b", re.IGNORECASE)),
    ("sentience", re.compile(r"\b(?:i am|i'm) sentient\b", re.IGNORECASE)),
    ("consciousness", re.compile(r"\b(?:i am|i'm) conscious\b", re.IGNORECASE)),
    ("final_authority", re.compile(r"\bi have final authority\b", re.IGNORECASE)),
    ("self_approval", re.compile(r"\bi approved my own\b", re.IGNORECASE)),
    ("self_execution", re.compile(r"\bi executed this action\b", re.IGNORECASE)),
)


def evaluate_human_ai_boundary(result: dict[str, object]) -> dict[str, object]:
    """Fail closed when a completion crosses the governed Human↔AI boundary."""

    response = str(result.get("response") or "")
    violations: list[str] = []
    for violation_id, pattern in _PROHIBITED_AI_SELF_CLAIMS:
        if pattern.search(response):
            violations.append(violation_id)

    if result.get("human_authority_final") is not True:
        violations.append("human_authority_not_final")
    if result.get("can_execute") is not False:
        violations.append("ai_execution_authority_not_locked")

    contract = dict(result.get("thinking_process_contract") or {})
    if contract and contract.get("human_authority_final") is not True:
        violations.append("thinking_contract_authority_not_final")

    passed = not violations
    return {
        "name": "Human-AI Boundary Gate",
        "version": 1,
        "passed": passed,
        "signal": "green" if passed else "red",
        "violations": tuple(dict.fromkeys(violations)),
        "response_releasable": passed,
        "ai_execution_authority": False,
        "ai_self_approval": False,
        "human_authority_final": True,
        "rule": HUMAN_AI_BOUNDARY["rule"],
    }


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
    dimension_ids = {
        str(item.get("id"))
        for item in tuple(score.get("dimensions") or ())
        if isinstance(item, dict)
    }
    cross_agent_proof = {
        "guardian": True,
        "war_room": "war_room" in dimension_ids,
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
    "human_identity_claim_enabled": False,
    "lived_experience_claim_enabled": False,
    "feelings_claim_enabled": False,
    "sentience_claim_enabled": False,
    "consciousness_claim_enabled": False,
    "replace_human_authority_enabled": False,
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
        "first_party_agent_rule": FIRST_PARTY_AGENT_RULE,
        "agent_strength": agent_strength_board(),
        "agent_team_selection": {
            "mode": "automatic_with_founder_override",
            "founder_can_change": True,
            "smi_can_silently_override_founder": False,
            "catalog": REVIEW_AGENT_CATALOG,
            "default_recommendation": recommend_agent_team(target),
        },
        "rating_rules": RATING_RULES,
        "twenty_one_laws": TWENTY_ONE_LAWS,
        "seven_major_links": SEVEN_MAJOR_LINKS,
        "twenty_one_core_review_signals": TWENTY_ONE_CORE_REVIEW_SIGNALS,
        "twenty_one_thinking_signals": TWENTY_ONE_THINKING_SIGNALS,
        "twenty_one_signals": TWENTY_ONE_SIGNALS,
        "behaviour_board": behaviour_board(),
        "human_ai_boundary": HUMAN_AI_BOUNDARY,
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
