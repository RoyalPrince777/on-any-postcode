"""Always-on, low-noise SMI intelligence routing for OAP requests.

This module does not call a model, mutate state, approve actions, or create audit
noise. It classifies each request into the minimum governed intelligence lenses
needed for that surface. Consequential actions escalate to War Room review while
Human Authority remains final.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from . import ai_behaviour

AUTO_VERSION = 6
AUTO_LIGHT = "purple"
BASE_LENSES = ("truth", "evidence", "alignment")
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

SEMANTIC_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("nirmata", "creation architect", "draft blueprint"), ("architecture", "dependency", "gap")),
    (("aei", "automatically executing intelligence"), ("security", "readiness", "risk")),
    (("gorilla", "containment", "safe rollback"), ("resilience", "security", "risk")),
    (("confusing", "hard to use", "usability", "navigation", "button", "layout", "mobile", "desktop"), ("ux", "behaviour")),
    (("slow", "latency", "performance", "speed", "bottleneck", "load"), ("performance", "architecture")),
    (("crash", "failure", "broken", "rollback", "recover", "recovery", "fallback"), ("resilience", "risk")),
    (("secure", "security", "auth", "permission", "secret", "attack", "abuse"), ("security", "risk")),
    (("privacy", "consent", "retention", "tracking", "sensitive"), ("privacy", "data")),
    (("database", "schema", "record", "ledger", "data", "provenance", "duplicate"), ("data", "architecture")),
    (("architecture", "ownership", "boundary", "interface", "route", "api"), ("architecture", "dependency")),
    (("ready", "readiness", "release", "green", "proof", "verify", "evidence"), ("readiness", "gap")),
    (("priority", "next", "roadmap", "sequence", "dependency"), ("priority", "dependency")),
    (("opportunity", "improve", "upgrade", "value", "growth"), ("opportunity", "impact")),
    (("competitor", "competitive", "compare", "alternative"), ("competitive", "decision")),
    (("trend", "latest", "change", "market shift"), ("trend", "impact")),
    (("swot",), ("swot",)),
    (("behaviour", "behavior", "repetition", "overconfident"), ("behaviour",)),
    (("scenario", "what if", "what-if"), ("scenario", "risk")),
)



MEMORY_LEARNING_TRIGGERS = (
    "memory and learning", "memory & learning", "learning from outcomes",
    "memory continuity", "hrm learning", "lessons learned",
)


def memory_learning_route(message: object) -> dict[str, object] | None:
    """Bounded specialist routing, not actual specialist execution or a vote."""
    source = str(message or "").casefold()
    if not any(trigger in source for trigger in MEMORY_LEARNING_TRIGGERS):
        return None
    checks = ai_behaviour.review_checks_for("7")
    return {
        "mission": "memory_and_learning",
        "lead": "Colonel Hathi",
        "lead_alias": "Hathi",
        "lead_passport": "JUNGLE-HATHI-001",
        "support": ("Hathi Jr", "Owl", "Oracle", "Fox"),
        "thinking_depth": 7,
        "selected_checks": checks["selected_checks"],
        "lenses": ("data", "learning", "behaviour", "impact", "verification"),
        "memory_owner": "HRM Core",
        "review_mode": "advisory_only",
        "checks_executed": False,
        "receipts_verified": False,
        "independent_votes_proven": False,
        "guardian_required": True,
        "green_gate_required": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


# Seven mission divisions share the existing SMI brain, lens registry and agent
# review roles. These are routing recommendations, never agent execution.
DYNAMIC_DIVISIONS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("truth", "Owl", ("Oracle", "Morpheus", "Spider"), ("truth", "evidence", "causality", "gap")),
    ("strategy", "Fox", ("Nirmata", "Lion", "Akela"), ("swot", "priority", "impact", "opportunity")),
    ("engineering", "Nirmata", ("Tank", "Dozer", "Neo"), ("architecture", "dependency", "resilience", "verification")),
    ("decision", "Morpheus", ("Oracle", "Akela", "Lion"), ("decision", "judgement", "readiness", "risk")),
    ("awareness", "Owl", ("Eagle", "Spider", "Fox"), ("trend", "data", "risk", "evidence")),
    ("recovery", "AEI", ("Gorilla", "Neo", "Tank", "Dozer"), ("resilience", "security", "readiness", "verification")),
    ("memory", "Colonel Hathi", ("Hathi Jr", "Oracle", "Owl"), ("data", "learning", "behaviour", "verification")),
)



MOUSE_FIT_TERMS = ("interactive world", "training scene", "simulation design",
                   "game mechanic", "ui edge case", "user interface edge case",
                   "training scenario", "virtual environment")


def recommend_matrix_mouse(mission: object) -> dict[str, object] | None:
    """Cross-family specialist suggestion; ownership and permissions never move."""
    from . import agents
    if not isinstance(mission, str) or len(mission) > 2000:
        return None
    text = mission.casefold()
    if not any(term in text for term in MOUSE_FIT_TERMS):
        return None
    profile = next((item for item in agents.MATRIX_ADVISORY_ALLIANCES
                    if item["id"] == "mouse_creative_simulation"), None)
    if profile is None or profile.get("members") != ("Mouse",) or profile.get("world_id") != "matrix":
        return None
    return {
        "agent": "Mouse",
        "commander": "Morpheus",
        "home_world": "matrix",
        "home_system": "Matrix System",
        "role": "Creative Simulation & Edge-Case Intelligence",
        "technical_allies": ("Neo", "Tank", "Dozer", "Nirmata"),
        "dynamic_recommendation_only": True,
        "family_transfer": False,
        "simulation_is_runtime_proof": False,
        "execution_granted": False,
        "approval_granted": False,
        "guardian_required": True,
        "green_gate_required": True,
        "human_authority_final": True,
    }



def auto_divisions_for_mission(mission: object) -> tuple[str, ...]:
    """Minimal deterministic advisory selection, never autonomous permission."""
    text = str(mission or "").strip().casefold()
    if not text or len(text) > 2000:
        raise ValueError("invalid_mission")
    selected = ["truth"]
    if any(word in text for word in ("repair", "fix", "build", "code", "ui", "ux", "api", "route", "test", "upgrade", "engineering")):
        selected.append("engineering")
    if any(word in text for word in ("security", "auth", "permission", "incident", "crash", "rollback", "recover", "failure")):
        selected.append("recovery")
    if any(word in text for word in ("memory", "recall", "history", "learning", "lesson")):
        selected.append("memory")
    if any(word in text for word in ("decide", "decision", "approval", "release", "founder", "governance")):
        selected.append("decision")
    if len(selected) == 1:
        selected.append("engineering")
    return tuple(selected[:3])


def route_divisions(divisions: object, *, thinking: object = "AUTO", mission: object = "") -> dict[str, object]:
    """Select several bounded specialist perspectives without creating agents."""
    from . import intelligence_lenses
    names = tuple(str(x).strip().lower() for x in divisions) if isinstance(divisions, (tuple, list)) else ()
    if names == ("auto",):
        names = auto_divisions_for_mission(mission)
    canonical = {row[0]: row for row in DYNAMIC_DIVISIONS}
    if not names or any(x not in canonical for x in names):
        raise ValueError("invalid_smi_divisions")
    distinct = tuple(dict.fromkeys(names))
    if len(distinct) > 7:
        raise ValueError("too_many_smi_divisions")
    choice = str(thinking or "AUTO").upper()
    if choice not in {"AUTO", "3", "7", "21"}:
        raise ValueError("invalid_smi_thinking")
    # Memory missions require the established seven-check Hathi review even
    # when selected alone; AUTO remains advisory and grants no execution.
    depth = (21 if "recovery" in distinct or len(distinct) >= 5 else
             7 if "memory" in distinct or len(distinct) >= 2 else 3) if choice == "AUTO" else int(choice)
    lenses: list[str] = []
    teams = []
    for name in distinct:
        _, lead, support, selected_lenses = canonical[name]
        _add(lenses, selected_lenses)
        teams.append({"division": name, "lead": lead, "support": support})
    if any(lens not in intelligence_lenses.FULL_LENS_IDS for lens in lenses):
        raise ValueError("unregistered_smi_lens")
    checks = ai_behaviour.review_checks_for(str(depth))
    return {
        "divisions": tuple(teams),
        "specialist_recommendation": recommend_matrix_mouse(mission),
        "thinking_mode": choice,
        "thinking_depth": depth,
        "selected_checks": checks["selected_checks"],
        "lenses": tuple(lenses),
        "selection_only": True,
        "agents_executed": False,
        "independent_votes_proven": False,
        "guardian_required": True,
        "green_gate_required": True,
        "hrm_proof_required": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def _add(target: list[str], values: Iterable[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _semantic_lenses(message: object) -> tuple[str, ...]:
    """Select only mission-relevant specialist lenses from safe message text.

    This is deterministic keyword routing, not private reasoning and not a model
    call. It can enrich surface routing without granting any authority.
    """
    text = str(message or "").casefold().strip()
    if not text:
        return ()
    selected: list[str] = []
    for triggers, lenses in SEMANTIC_RULES:
        if any(trigger in text for trigger in triggers):
            _add(selected, lenses)
    return tuple(selected)



def _adaptive_level(*, lenses: tuple[str, ...], semantic_lenses: tuple[str, ...], write_action: bool, consequential: bool) -> dict[str, object]:
    """Choose the minimum sufficient A1-A7 adaptive level.

    Levels increase capability/depth, never authority. The selector can stop at
    the current level when added intelligence would not materially improve the
    bounded task.
    """
    lens_count = len(lenses)
    semantic_count = len(semantic_lenses)

    if consequential and write_action and lens_count >= 9:
        level, reason = "A7", "consequential cross-system work needs adaptive governed coordination"
    elif consequential:
        level, reason = "A6", "consequential work needs anticipation, recovery and governance checks"
    elif semantic_count >= 5 or lens_count >= 9:
        level, reason = "A5", "multiple relevant intelligences need coordinated synthesis"
    elif semantic_count >= 3 or lens_count >= 7:
        level, reason = "A4", "task needs adaptive multi-lens analysis"
    elif semantic_count >= 1:
        level, reason = "A3", "mission meaning requires specialist routing"
    elif lens_count > len(BASE_LENSES):
        level, reason = "A2", "surface context adds bounded specialist understanding"
    else:
        level, reason = "A1", "base observation is sufficient"

    return {
        "level": level,
        "reason": reason,
        "stop": True,
        "stop_reason": "minimum sufficient intelligence selected; escalate only if new evidence, risk or mission complexity appears",
    }

def observe(method: object, path: object, endpoint: object = None, message: object = None) -> dict[str, object]:
    """Return deterministic SMI routing metadata for one request.

    The result is intentionally side-effect free. It is safe to run on every
    request and exists to keep SMI present without turning every click into an
    expensive provider call or noisy database event.
    """

    method_key = str(method or "GET").upper()
    path_key = "/" + str(path or "").lstrip("/").lower()
    endpoint_key = str(endpoint or "").lower()
    lenses: list[str] = list(BASE_LENSES)

    private_surface = path_key.startswith(("/mission", "/my-world", "/myworld", "/infrastructure"))
    write_action = method_key in WRITE_METHODS

    if private_surface:
        _add(lenses, ("security", "privacy"))
    if any(token in path_key for token in ("map", "atlas", "movement", "route", "travel", "booking", "direct")):
        _add(lenses, ("dependency", "architecture", "risk", "performance"))
    if any(token in path_key for token in ("link", "message", "voice", "call", "presence")):
        _add(lenses, ("privacy", "security", "behaviour"))
    if any(token in path_key for token in ("market", "sika", "payment", "wallet", "commerce")):
        _add(lenses, ("risk", "data", "privacy", "readiness"))
    if any(token in path_key for token in ("health", "status", "proof", "receipt", "audit")):
        _add(lenses, ("readiness", "resilience"))
    if any(token in path_key for token in ("war-room", "judgement", "approval")):
        _add(lenses, ("gap", "swot", "risk", "dependency", "readiness", "decision", "judgement"))
    if write_action:
        _add(lenses, ("risk", "security", "privacy", "readiness", "decision", "judgement"))

    semantic_lenses = _semantic_lenses(message)
    memory_route = memory_learning_route(message)
    _add(lenses, semantic_lenses)
    if memory_route:
        _add(lenses, memory_route["lenses"])

    consequential = write_action or any(
        token in path_key
        for token in (
            "judgement",
            "approval",
            "deploy",
            "migration",
            "dispatch",
            "payment",
            "wallet",
            "certify",
        )
    )

    adaptive = _adaptive_level(
        lenses=tuple(lenses),
        semantic_lenses=semantic_lenses,
        write_action=write_action,
        consequential=consequential,
    )

    return {
        "component": "SMI Automatic Intelligence",
        "version": AUTO_VERSION,
        "active": True,
        "light": AUTO_LIGHT,
        "mode": "automatic_low_noise",
        "method": method_key,
        "path": path_key,
        "endpoint": endpoint_key,
        "lenses": tuple(lenses),
        "semantic_lenses": semantic_lenses,
        "specialist_mission": memory_route,
        "selector": "surface+action+mission",
        "smi_intelligence": adaptive,
        "private_surface": private_surface,
        "write_action": write_action,
        "war_room_escalation": consequential,
        "provider_call_performed": False,
        "database_write_performed": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def public_status() -> dict[str, object]:
    """Return the stable architecture contract without request-specific data."""

    return {
        "component": "SMI Automatic Intelligence",
        "version": AUTO_VERSION,
        "active": True,
        "light": AUTO_LIGHT,
        "mode": "automatic_low_noise",
        "base_lenses": BASE_LENSES,
        "core_auto_review": CORE_AUTO_REVIEW,
        "captain_auto_protocol": "SMI_FIRST_CORE_REVIEW_THEN_SPECIALISTS",
        "selector": "surface+action+mission",
        "semantic_routing": True,
        "adaptive_levels": ("A1", "A2", "A3", "A4", "A5", "A6", "A7"),
        "minimum_sufficient_intelligence": True,
        "provider_call_per_request": False,
        "database_write_per_request": False,
        "consequential_actions_escalate": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


# Canonical named-review routing. These are evidence lenses inside SMI Auto,
# not separate brains, model providers or autonomous authorities.
REVIEW_ROLE_LENSES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Nirmata", ("nirmata",), "bounded repair architecture, dependencies and rollback design"),
    ("AEI", ("aei", "automatically executing intelligence"), "permitted execution readiness, auditability and failure limits"),
    ("Neo", ("neo",), "true path, execution coherence and recovery"),
    ("Shere Khan", ("shere khan", "claw test"), "adversarial stress-test, threat intelligence, failure-hunting, survivability authority and false-Green blocking; Claw Test is one pressure mode"),
    ("Bagheera", ("bagheera",), "protection, balance and reversible judgement"),
    ("Agent Smith", ("agent smith", "smith"), "duplication, corruption, bypass and false-green detection"),
    ("Morpheus", ("morpheus",), "mission clarity and alignment"),
    ("Trinity", ("trinity",), "integration and continuity"),
    ("Oracle", ("oracle",), "accuracy, uncertainty and adaptation"),
    ("Architect", ("architect",), "architecture, maintainability and dependency structure"),
    ("Keymaker", ("keymaker",), "access paths, routing and boundary integrity"),
    ("Seraph", ("seraph",), "security and alignment"),
    ("Owl", ("owl",), "evidence quality and wisdom"),
    ("Bee", ("bee",), "coordination and evidence gathering"),
    ("Elephant", ("elephant",), "memory, provenance and continuity"),
    ("Panther", ("panther",), "adaptation, gaps and security"),
    ("Eagle", ("eagle",), "whole-system view"),
    ("Falcon", ("falcon",), "speed and smallest bounded next gate"),
    ("Gorilla", ("gorilla",), "containment, pressure resistance, safe rollback and fail-closed recovery"),
    ("Octopus", ("octopus",), "systems integration, multi-route coordination and dependency reach"),
    ("Spider", ("spider",), "route mesh, connection integrity and hidden dependency detection"),
    ("Fox", ("fox",), "optimisation, loophole detection and edge-case efficiency"),
)

CORE_AUTO_REVIEW = (
    "Neo",
    "Shere Khan",
    "Bagheera",
)

DEFAULT_AUTO_REVIEW = (
    *CORE_AUTO_REVIEW,
    "Agent Smith",
    "Owl",
    "Guardian",
    "Green Gate",
)


def explicit_review_roles(message: object) -> tuple[str, ...]:
    """Resolve Founder-typed names to canonical SMI review lenses."""

    text = str(message or "").casefold()
    selected: list[str] = []
    for name, aliases, _ in REVIEW_ROLE_LENSES:
        if any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text) for alias in aliases):
            selected.append(name)
    return tuple(dict.fromkeys(selected))


def review_lens(name: str) -> str:
    for role_name, _, lens in REVIEW_ROLE_LENSES:
        if role_name == name:
            return lens
    return "governed evidence review"


def selected_review_roles(message: object, *, auto_mode: bool) -> tuple[str, ...]:
    explicit = explicit_review_roles(message)
    if auto_mode:
        selected: list[str] = list(DEFAULT_AUTO_REVIEW)
        _add(selected, explicit)
        # Couple bounded design, execution review and resilience whenever the
        # Founder invokes any member of this recovery triad. Review only:
        # no repair execution, approval or release authority is granted here.
        if any(role in explicit for role in ("Nirmata", "AEI", "Gorilla")):
            _add(selected, ("Nirmata", "AEI", "Gorilla"))
        return tuple(selected)
    return explicit


def build_evidence_vote_board(
    *,
    roles: tuple[str, ...],
    brain: dict[str, object],
    coherence: dict[str, object],
    judgement: dict[str, object],
    guardian_outcome: str,
) -> dict[str, object]:
    """Classify current evidence for active reviewers without simulated opinions."""

    if not roles:
        return {
            "automatic": False,
            "roles": (),
            "votes": (),
            "summary": {"PASS": 0, "FAIL": 0, "CONDITIONAL": 0},
            "authority_granted": False,
            "human_authority_final": True,
        }

    blocked = str(guardian_outcome).upper() == "BLOCKED"
    coherent = bool(coherence.get("passed"))
    constitution = bool(judgement.get("constitution_consistent"))
    provider_ready = bool(brain.get("passed"))
    high_impact = bool(brain.get("high_impact"))
    review_required = bool(
        not coherent
        or not constitution
        or high_impact
        or str(guardian_outcome).upper() == "REVIEW_REQUIRED"
    )
    if blocked:
        base_vote = "FAIL"
    elif provider_ready and coherent and constitution and not review_required:
        base_vote = "PASS"
    else:
        base_vote = "CONDITIONAL"

    votes: list[dict[str, object]] = []
    for reviewer in roles:
        vote = base_vote
        reason = "Current governed evidence supports the recommendation."
        if reviewer == "Shere Khan" and (high_impact or not coherent):
            vote = "FAIL" if blocked else "CONDITIONAL"
            reason = "Shere Khan holds Green until survivability, hidden-dependency, authority-misuse, failure-propagation, recovery and evidence quality are strong; the Claw Test is one pressure mode."
        elif reviewer in {"Guardian", "Green Gate"}:
            if blocked:
                vote = "FAIL"
                reason = "Protection/evidence gate is blocked."
            elif review_required:
                vote = "CONDITIONAL"
                reason = "Protection/evidence gate requires further proof."
        elif reviewer == "Agent Smith" and not constitution:
            vote = "FAIL" if blocked else "CONDITIONAL"
            reason = "Integrity review detected an unresolved governance/coherence condition."

        votes.append(
            {
                "reviewer": reviewer,
                "lens": review_lens(reviewer),
                "vote": vote,
                "reason": reason,
                "deterministic_evidence_review": True,
                "independent_personality_claimed": False,
            }
        )

    summary = {
        state: sum(1 for item in votes if item["vote"] == state)
        for state in ("PASS", "FAIL", "CONDITIONAL")
    }
    return {
        "automatic": True,
        "roles": roles,
        "votes": tuple(votes),
        "summary": summary,
        "authority_granted": False,
        "human_authority_final": True,
    }


def evidence_swot_for_failed_build(evidence: object) -> dict[str, object]:
    """Bounded SWOT from verified GitHub failure evidence, never an AI vote.

    Returns nothing actionable unless run, failed-job and log-category proof
    is complete. No new engine, model call, permission, or production write.
    """
    base = {"ready": False, "strengths": (), "weaknesses": (),
            "opportunities": (), "threats": (), "next_action": None,
            "execution_granted": False, "approval_granted": False,
            "human_authority_final": True}
    if not isinstance(evidence, dict) or evidence.get("ready") is not True:
        return base
    log_analysis = evidence.get("log_analysis")
    if not isinstance(log_analysis, dict) or log_analysis.get("ready") is not True:
        return base
    categories = log_analysis.get("log_categories")
    if not isinstance(categories, (tuple, list)) or not categories:
        return base
    allowed = {"signing_configuration", "source_verification",
               "gradle_compile", "dependency_resolution", "android_sdk"}
    seen = set()
    for row in categories:
        if not isinstance(row, dict) or not isinstance(row.get("categories"), (tuple, list)):
            return base
        if any(not isinstance(x, str) or x not in allowed for x in row["categories"]):
            return base
        seen.update(row["categories"])
    if not seen:
        return base
    return {**base, "ready": True,
            "strengths": ("A completed failed run and bounded job-log evidence were collected.",),
            "weaknesses": tuple(sorted(seen)),
            "opportunities": ("Prepare one targeted reversible correction after exact-commit review.",),
            "threats": ("Unverified fixes, signing bypass and stale CI evidence must not grant Green.",),
            "next_action": "NIRMATA review classified failure; require exact-head CI and Founder Final for release."}
