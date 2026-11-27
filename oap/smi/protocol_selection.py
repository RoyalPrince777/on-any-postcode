"""Advisory protocol-specific SMI team selection; no authority or agent execution."""
from __future__ import annotations

from dataclasses import dataclass

# Named specialist roles are recommendations, not verified active agent processes.
PROTOCOL_TEAMS: dict[str, tuple[str, tuple[str, ...]]] = {
    "coordination": ("Captain ALL IN", ("Oracle", "Octopus", "Gyata")),
    "creation": ("NIRMATA", ("Architect", "Tigress", "Benji")),
    "execution": ("Neo", ("Trinity", "Tigress")),
    "stealth": ("Bagheera", ("Batman", "Luther", "Ilsa")),
    "guardian": ("Guardian", ("Seraph", "Gorilla", "Bagheera")),
    "adversarial": ("Shere Khan", ("Agent Smith", "Shark")),
    "pack": ("Akela", ("Octopus",)),
    "swarm": ("Queen Bee", ("Spider",)),
    "patterns": ("Octopus", ("Oracle", "Lucy", "Owl")),
    "dependencies": ("Spider", ("Architect", "Keymaker")),
    "recovery": ("Fox", ("Dozer", "Tank", "Benji")),
    "last_line_defence": ("Gorilla", ("Guardian", "Gyata")),
    "command": ("Gyata", ("Lioness", "Tigress")),
    "memory": ("Hathi", ("Elephant",)),
    "investigation": ("Batman", ("Robin", "Oracle", "Shere Khan")),
    "complex_missions": ("Ethan Hunt", ("Luther", "Benji", "Ilsa")),
    "matrix": ("Morpheus", ("Neo", "Trinity", "Oracle")),
    "identity": ("Seraph", ("Keymaker", "Guardian")),
    "verification": ("Tigress", ("The Twins", "Oracle")),
    "audit": ("HRM", ("Hathi", "Oracle")),
    "economics": ("MANSA", ("Owl", "Octopus", "Tigress")),
    "civic_rights": ("Batman", ("Nyah", "Ilsa", "Bagheera")),
    "language": ("NYANSA", ("Lucy", "Morpheus")),
    "science": ("NIRMATA", ("Lucy", "Octopus", "Tigress")),
    "threat_awareness": ("Shark", ("Eagle", "Owl", "Guardian")),
    "living_kernel": ("Architect", ("Neo", "Tank", "Guardian")),
    "deployment": ("Neo", ("Benji", "Trinity", "Dozer")),
    "green_gate": ("Independent verification", ("Tigress", "Oracle", "Guardian")),
}


# Capability acquisition candidates, not installed tools or benchmark winners.
# These requirements belong to the existing protocol selector, not a second brain.
PROTOCOL_CAPABILITIES: dict[str, tuple[tuple[str, ...], tuple[str, ...], str]] = {
    "coordination": (("dependency-aware scheduling",), ("existing mission queue", "NetworkX"), "dependency order and cancellation"),
    "creation": (("architecture reasoning", "blueprint generation"), ("local inference gateway", "Qwen3-4B"), "contract-valid reproducible blueprint"),
    "execution": (("repository coding", "isolated engineering"), ("Qwen3-Coder-Next", "OpenHands"), "sandbox patch and independent regression"),
    "stealth": (("privacy minimisation",), ("Presidio",), "redaction and consent boundary"),
    "guardian": (("deterministic policy", "static analysis"), ("OPA", "Semgrep"), "deny forbidden actions"),
    "adversarial": (("defensive property testing",), ("Hypothesis",), "reproduce a controlled fault"),
    "pack": (("bounded collaboration",), ("existing worker queue",), "no duplicate claims"),
    "swarm": (("resource-bounded parallel jobs",), ("existing worker queue",), "concurrency and isolation limits"),
    "patterns": (("anomaly detection",), ("scikit-learn",), "labelled holdout accuracy"),
    "dependencies": (("graph analysis",), ("NetworkX",), "cycle and missing dependency detection"),
    "recovery": (("fault diagnosis", "rollback"), ("existing recovery path", "Git"), "restore known-good state"),
    "last_line_defence": (("process containment",), ("Podman", "existing Aegis"), "isolation and emergency stop"),
    "command": (("priority reasoning",), ("local inference gateway",), "respect mission dependencies and authority"),
    "memory": (("semantic retrieval", "provenance"), ("BGE-M3", "pgvector"), "retrieval accuracy and authorised recall"),
    "investigation": (("source retrieval", "provenance"), ("SearXNG", "PaddleOCR"), "reproducible primary-source citations"),
    "complex_missions": (("bounded multi-step planning",), ("local inference gateway", "existing mission queue"), "recover interrupted task without duplication"),
    "matrix": (("spatial simulation",), ("Babylon.js",), "reproducible world-state and collision test"),
    "identity": (("authentication", "permission validation"), ("WebAuthn", "existing identity engine"), "reject invalid identity and replay"),
    "verification": (("independent regression",), ("pytest", "Playwright"), "independent witness reproduces result"),
    "audit": (("durable provenance", "telemetry"), ("existing HRM", "OpenTelemetry"), "receipt readback and integrity"),
    "economics": (("optimisation", "statistical modelling"), ("OR-Tools", "SciPy"), "reconcile constraints and totals"),
    "civic_rights": (("legal-source retrieval", "privacy review"), ("SearXNG", "Presidio"), "dated sources and uncertainty"),
    "language": (("multilingual understanding", "speech recognition"), ("Qwen3-4B", "whisper.cpp"), "multilingual accuracy on held-out samples"),
    "science": (("scientific computation",), ("SymPy", "SciPy"), "reproduce numerical result"),
    "threat_awareness": (("defensive anomaly monitoring",), ("Wazuh", "OpenTelemetry"), "detect controlled threat without external action"),
    "living_kernel": (("transactional execution", "policy validation"), ("existing Living Kernel", "OPA"), "atomic approved action and rollback"),
    "deployment": (("reproducible build",), ("Podman", "existing CI"), "exact-revision artifact and approval gate"),
    "green_gate": (("independent functional proof",), ("pytest", "Playwright", "existing HRM"), "live receipt and independent review"),
}

# Verified upstream locations for selected research candidates. Other candidate
# names still require source, licence, pinned-version and compatibility review.
CAPABILITY_SOURCE_CANDIDATES = {
    "Qwen3-4B": "https://huggingface.co/Qwen/Qwen3-4B",
    "Qwen3-Coder-Next": "https://huggingface.co/Qwen/Qwen3-Coder-Next",
    "OpenHands": "https://github.com/OpenHands/OpenHands",
    "OPA": "https://github.com/open-policy-agent/opa",
}


def protocol_capability_plan(protocol: str) -> dict[str, object]:
    """Return a proposal only; never install, rank untested models or grant authority."""
    selected = recommend_protocol_team(protocol)
    candidate = PROTOCOL_CAPABILITIES.get(selected.protocol)
    if selected.lead is None or candidate is None:
        return {"status": "UNRECOGNISED", "capabilities": (), "candidates": (),
                "execution_granted": False, "approval_granted": False}
    capabilities, tools, acceptance = candidate
    return {
        "protocol": selected.protocol,
        "status": "PROPOSED_UNVERIFIED",
        "capabilities": capabilities,
        "candidates": tools,
        "source_candidates": {
            tool: CAPABILITY_SOURCE_CANDIDATES[tool]
            for tool in tools if tool in CAPABILITY_SOURCE_CANDIDATES
        },
        "acceptance_test": acceptance,
        "required_evidence": ("source_and_licence", "pinned_version", "hardware_compatibility",
                              "sandbox_test", "independent_review", "hrm_receipt"),
        "local_first": True,
        "server_candidate_only": ("Qwen3-Coder-Next",) if "Qwen3-Coder-Next" in tools else (),
        "installed_verified": False,
        "benchmark_verified": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


@dataclass(frozen=True)
class ProtocolRecommendation:
    protocol: str
    lead: str | None
    specialists: tuple[str, ...]
    status: str
    advisory_only: bool = True
    grants_permissions: bool = False
    human_authority_final: bool = True


def recommend_protocol_team(protocol: str) -> ProtocolRecommendation:
    """Return advisory candidates; unknown input fails closed without fallback authority."""
    if not isinstance(protocol, str):
        return ProtocolRecommendation("", None, (), "UNRECOGNISED")
    key = protocol.strip().lower()
    team = PROTOCOL_TEAMS.get(key)
    if team is None:
        return ProtocolRecommendation(key, None, (), "UNRECOGNISED")
    return ProtocolRecommendation(key, team[0], team[1], "PROPOSED_UNVERIFIED")


@dataclass(frozen=True)
class MissionRoleRecommendation:
    """A bounded mission assignment proposal, never an execution grant."""

    mission: str
    protocol: str
    depth: str
    lead: str | None
    deputy: str | None
    specialists: tuple[str, ...]
    challenger: str | None
    verifier: str | None
    recovery: str | None
    status: str
    passport_verified: bool = False
    permissions_verified: bool = False
    evidence_verified: bool = False
    agent_execution_verified: bool = False
    grants_permissions: bool = False
    human_authority_final: bool = True


def recommend_mission_team(mission: str, protocol: str, depth: str = "AUTO") -> MissionRoleRecommendation:
    """Select advisory roles from existing mappings, with unknowns failing closed.

    AUTO uses a small team; it does not invent passport, performance or permission
    evidence. A separate authenticated registry/permission gate is required
    before any operational activation.
    """
    safe_mission = mission.strip() if isinstance(mission, str) else ""
    safe_depth = depth.upper().strip() if isinstance(depth, str) else ""
    selected = recommend_protocol_team(protocol)
    if not safe_mission or len(safe_mission) > 160 or safe_depth not in {"AUTO", "3", "7", "21", "FULL"} or selected.lead is None:
        return MissionRoleRecommendation(safe_mission[:160], selected.protocol, safe_depth, None, None, (), None, None, None, "UNRECOGNISED")
    pool = tuple(dict.fromkeys(selected.specialists))
    deputy = pool[0] if pool else None
    specialists = pool[1:] if safe_depth != "3" else ()
    # Reviewer and recovery roles are proposed only when their candidates exist.
    challenger = "Shere Khan" if safe_depth in {"AUTO", "7", "21", "FULL"} and selected.lead != "Shere Khan" else None
    verifier = "The Twins" if safe_depth in {"AUTO", "7", "21", "FULL"} else None
    recovery = "Fox" if selected.protocol in {"recovery", "deployment", "dependencies"} and selected.lead != "Fox" else None
    return MissionRoleRecommendation(safe_mission, selected.protocol, safe_depth, selected.lead, deputy, specialists, challenger, verifier, recovery, "PROPOSED_UNVERIFIED")


def check_mission_candidate_eligibility(
    agent_id: str, registry: object, *, required_permission: str = "ANALYSE", expected_name: str | None = None
) -> dict[str, object]:
    """Fail-closed read-only passport/permission eligibility for a candidate ID.

    Eligibility does not prove execution, performance, approval of a new role,
    or release readiness. Uses the existing RegistryEngine permission engine.
    """
    from oap.permissions import PermissionEngine

    if not isinstance(agent_id, str) or not agent_id.strip():
        return {"agent_id": "", "eligible": False, "reason": "INVALID_AGENT_ID", "grants_permissions": False}
    passport_lookup = getattr(registry, "passport", None)
    if not callable(passport_lookup):
        return {"agent_id": agent_id, "eligible": False, "reason": "REGISTRY_UNAVAILABLE", "grants_permissions": False}
    try:
        passport = passport_lookup(agent_id)
    except Exception:  # noqa: BLE001 - fail closed on untrusted registry failures
        return {"agent_id": agent_id, "eligible": False, "reason": "REGISTRY_LOOKUP_FAILED", "grants_permissions": False, "execution_verified": False}
    if not isinstance(passport, dict) or passport.get("agent_id") != agent_id:
        return {"agent_id": agent_id, "eligible": False, "reason": "PASSPORT_NOT_FOUND", "grants_permissions": False}
    try:
        if expected_name is not None:
            aliases = passport.get("aliases", ())
            if not isinstance(aliases, (list, tuple)) or not all(isinstance(alias, str) for alias in aliases):
                raise ValueError("Malformed passport aliases")
            labels = (passport.get("name"), *aliases)
            if expected_name not in labels:
                return {"agent_id": agent_id, "eligible": False, "reason": "PASSPORT_NAME_MISMATCH", "grants_permissions": False, "execution_verified": False}
        decision = PermissionEngine().authorize_agent(passport, required_permission=required_permission)
    except (TypeError, ValueError, AttributeError, KeyError):
        return {"agent_id": agent_id, "eligible": False, "reason": "MALFORMED_PASSPORT", "grants_permissions": False, "execution_verified": False, "performance_verified": False}
    return {
        "agent_id": agent_id,
        "eligible": bool(decision.allowed),
        "reason": decision.reason,
        "grants_permissions": False,
        "execution_verified": False,
        "performance_verified": False,
    }


def screen_mission_team_candidates(
    recommendation: MissionRoleRecommendation,
    registry: object,
    *,
    agent_ids: dict[str, str] | None = None,
) -> dict[str, object]:
    """Screen all proposed people against actual registry passports, fail closed.

    Names are not silently treated as passport IDs. Caller must provide an
    explicit verified name-to-ID mapping; no eligible result grants a role.
    """
    ids = agent_ids if isinstance(agent_ids, dict) else {}
    names = tuple(dict.fromkeys(
        name for name in (
            recommendation.lead,
            recommendation.deputy,
            *recommendation.specialists,
            recommendation.challenger,
            recommendation.verifier,
            recommendation.recovery,
        ) if name
    ))
    results: dict[str, dict[str, object]] = {}
    for name in names:
        identifier = ids.get(name)
        if not isinstance(identifier, str) or not identifier.strip():
            results[name] = {
                "eligible": False, "reason": "PASSPORT_ID_UNRESOLVED",
                "grants_permissions": False,
            }
            continue
        results[name] = check_mission_candidate_eligibility(identifier, registry, expected_name=name)
    return {
        "mission": recommendation.mission,
        "protocol": recommendation.protocol,
        "candidates": results,
        "all_eligible": bool(names) and all(item["eligible"] for item in results.values()),
        "status": "ADVISORY_SCREENED_NOT_ACTIVATED",
        "grants_permissions": False,
        "agent_execution_verified": False,
        "founder_final_required": True,
    }
