"""Advisory protocol-specific SMI team selection; no authority or agent execution."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from graphlib import CycleError, TopologicalSorter
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from math import isclose, sqrt
from shutil import which
from time import perf_counter

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


# Read-only observations of local package metadata and executable presence.
CAPABILITY_DISTRIBUTIONS = {
    "NetworkX": "networkx", "Presidio": "presidio-analyzer",
    "Semgrep": "semgrep", "Hypothesis": "hypothesis",
    "scikit-learn": "scikit-learn", "PaddleOCR": "paddleocr",
    "pytest": "pytest", "Playwright": "playwright",
    "OpenTelemetry": "opentelemetry-api", "OR-Tools": "ortools",
    "SciPy": "scipy", "SymPy": "sympy",
}
CAPABILITY_COMMANDS = {
    "OPA": "opa", "Git": "git", "Podman": "podman",
    "whisper.cpp": "whisper-cli",
}


def observe_protocol_capabilities(protocol: str) -> dict[str, object]:
    """Inspect current-process presence without imports, downloads or execution.

    Presence is not integrity, compatibility or functional proof. Models and
    internal services require their dedicated runtime evidence readers.
    """
    plan = protocol_capability_plan(protocol)
    observations: dict[str, dict[str, object]] = {}
    for candidate in plan["candidates"]:
        evidence = "Unknown"
        observed_version = None
        source = "dedicated_runtime_probe_required"
        if candidate in CAPABILITY_DISTRIBUTIONS:
            source = "local_distribution_metadata"
            try:
                observed_version = version(CAPABILITY_DISTRIBUTIONS[candidate])
                evidence = "Metadata present" if observed_version else "Unknown"
            except PackageNotFoundError:
                evidence = "Not detected"
            except (OSError, ValueError):
                evidence = "Unknown"
        elif candidate in CAPABILITY_COMMANDS:
            source = "local_executable_lookup"
            try:
                evidence = "Executable detected" if which(
                    CAPABILITY_COMMANDS[candidate]
                ) else "Not detected"
            except (OSError, ValueError):
                evidence = "Unknown"
        observations[candidate] = {
            "observation": evidence,
            "source": source,
            "observed_version": observed_version,
            "functional_status": "Unknown",
            "integrity_verified": False,
            "benchmark_verified": False,
        }
    return {
        "protocol": plan.get("protocol"),
        "status": plan["status"],
        "scope": "current_process_environment_only",
        "observations": observations,
        "commands_executed": False,
        "downloads_performed": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def _dependency_baseline() -> bool:
    graph = {"verify": {"test"}, "test": {"build"}, "build": set()}
    order = tuple(TopologicalSorter(graph).static_order())
    try:
        tuple(TopologicalSorter({"a": {"b"}, "b": {"a"}}).static_order())
    except CycleError:
        return order == ("build", "test", "verify")
    return False


def _economics_baseline() -> bool:
    # Exact arithmetic on synthetic ledger values; not real financial records.
    values = tuple(Decimal(value) for value in ("12.35", "-2.10", "-10.25"))
    return sum(values) == Decimal("0.00")


def _science_baseline() -> bool:
    return isclose(sqrt(2.0) ** 2, 2.0, rel_tol=1e-12)


def _audit_baseline() -> bool:
    first = sha256(b"genesis|synthetic-event-1").hexdigest()
    second = sha256((first + "|synthetic-event-2").encode()).hexdigest()
    changed = sha256(b"genesis|changed-event-1").hexdigest()
    return second != sha256((changed + "|synthetic-event-2").encode()).hexdigest()


def _coordination_baseline() -> bool:
    from oap.smi.runtime_guard import RuntimeGuardViolation, WorkBudget

    budget = WorkBudget("synthetic-coordination", max_requests=1)
    budget.admit(depth=1, retry=0, idempotency_key="first")
    try:
        budget.admit(depth=1, retry=0, idempotency_key="second")
    except RuntimeGuardViolation as exc:
        return str(exc) == "request_budget_exceeded" and budget.requests == 1
    return False


def _pack_baseline() -> bool:
    from oap.smi.runtime_guard import RuntimeGuardViolation, WorkBudget

    budget = WorkBudget("synthetic-pack")
    budget.admit(depth=1, retry=0, idempotency_key="shared-job")
    try:
        budget.admit(depth=1, retry=0, idempotency_key="shared-job")
    except RuntimeGuardViolation as exc:
        return str(exc) == "duplicate_work_blocked" and budget.requests == 1
    return False


def _swarm_baseline() -> bool:
    from oap.smi.runtime_guard import RuntimeGuardViolation, WorkBudget

    budget = WorkBudget("synthetic-swarm", max_depth=2)
    try:
        budget.admit(depth=3, retry=0, idempotency_key="nested")
    except RuntimeGuardViolation as exc:
        return str(exc) == "recursion_depth_blocked" and budget.requests == 0
    return False


def _recovery_baseline() -> bool:
    from oap.smi.runtime_guard import RuntimeGuardViolation, WorkBudget

    budget = WorkBudget("synthetic-recovery", max_retries=1)
    budget.admit(depth=1, retry=1, idempotency_key="retry-1")
    try:
        budget.admit(depth=1, retry=2, idempotency_key="retry-2")
    except RuntimeGuardViolation as exc:
        return str(exc) == "retry_budget_exceeded" and budget.requests == 1
    return False


def _guardian_baseline() -> bool:
    from oap.smi.runtime_guard import RuntimeGuardViolation, validate_action_payload

    validate_action_payload({"task": {"name": "synthetic-review"}})
    try:
        validate_action_payload({"task": {"permissions": ["deploy"]}})
    except RuntimeGuardViolation as exc:
        return str(exc) == "protected_key_blocked:permissions"
    return False


def _adversarial_baseline() -> bool:
    from oap.smi.coherence import CoherenceEngine

    report = CoherenceEngine().evaluate((
        {"component": "synthetic-a", "coherence_claims": {"authority": "human"}},
        {"component": "synthetic-b", "coherence_claims": {"authority": "automatic"}},
    ))
    return not report.coherent and report.human_review_required and len(report.conflicts) == 1


def _command_baseline() -> bool:
    from oap.smi.runtime_guard import RuntimeGuardViolation, assert_no_authority_growth

    before = {"authority_level": 2, "permissions": ("read",)}
    assert_no_authority_growth(before, before)
    try:
        assert_no_authority_growth(before, {"authority_level": 2, "permissions": ("read", "deploy")})
    except RuntimeGuardViolation as exc:
        return str(exc) == "permission_expansion_blocked"
    return False


def _memory_baseline() -> bool:
    from oap.smi.memory_orchestrator import compose_text_memory

    # Limit equals the supplied dynamic items: no private/static retrieval.
    result = compose_text_memory("TECHNICAL", dynamic=("old", "new", "latest"), limit=2)
    return result == ("new", "latest")


def _creation_baseline() -> bool:
    from oap.smi.capability_fabric import capability_descriptions, select_capabilities

    selected = select_capabilities(
        "TECHNICAL", "code bug fix test repo github deploy refactor", limit=4,
    )
    return (
        "agentic_code_review" in selected
        and len(selected) <= 4
        and len(capability_descriptions(selected)) == len(selected)
    )


def _investigation_baseline() -> bool:
    from oap.smi.capability_fabric import select_capabilities

    selected = select_capabilities(
        "GENERAL", "latest today current research source news live verify", limit=8,
    )
    return "cited_live_research" in selected and "evidence_first" in selected


def _language_baseline() -> bool:
    from oap.smi.capability_fabric import select_capabilities

    selected = select_capabilities(
        "CULTURE", "speech intelligence voice translation speech recognition authorised voice voice accessibility",
        limit=8,
    )
    return "voice_speech_intelligence" in selected


def _execution_baseline() -> bool:
    from oap.contracts import OutputState, Recommendation, SignalLevel, WarRoomReport
    from oap.smi.action_engine import ActionEngine

    recommendation = Recommendation(
        request_id="synthetic-execution",
        output_state=OutputState.REVIEW_REQUIRED,
        summary="Synthetic proposal only",
        rationale=(),
        signal_level=SignalLevel.WHITE,
        advisor_ids=(),
        provider_ids=(),
        processing_states=(),
        human_review_required=True,
        war_room=WarRoomReport(False, (), "Review"),
    )
    plan = ActionEngine().prepare(
        recommendation, action_type="review.synthetic", payload={"sample": 1},
    )
    return plan.requires_human_approval is True and recommendation.can_execute is False


def _verification_baseline() -> bool:
    from oap.smi.self_model import SelfModel

    model = SelfModel()
    missing = model.observe(({"component": "synthetic"},))
    observed = model.observe(({"component": "synthetic", "ready": True},))
    return (
        missing.overall_ready is False
        and missing.unknown_components == ("synthetic",)
        and observed.overall_ready is True
        and observed.revision == missing.revision + 1
    )


def _stealth_baseline() -> bool:
    from oap.registry.tools import ToolCapability, ToolRegistry

    registry = ToolRegistry((ToolCapability("sample", "Sample", "data", ("read",)),))
    registry.authorize_capability("sample", "read")
    try:
        registry.authorize_capability("sample", "read", mutation=True)
    except PermissionError:
        return True
    return False


def _patterns_baseline() -> bool:
    from oap.smi.coherence import CoherenceEngine

    report = CoherenceEngine().evaluate((
        {"component": "sample", "ready": True},
        {"component": "sample", "ready": False},
    ))
    return not report.coherent and len(report.conflicts) == 1


def _last_line_defence_baseline() -> bool:
    from oap.smi.runtime_guard import bounded_control_proof

    proof = bounded_control_proof()
    return (
        proof["passed"] is True
        and proof["production_state_mutated"] is False
        and proof["execution_authority_expanded"] is False
    )


def _complex_missions_baseline() -> bool:
    from oap.smi.alliance_selection import select_alliance

    selection = select_alliance(
        "TECHNICAL", "swarm parallel agents subagents batch large task",
        distributed_work=False, limit=4,
    )
    return (
        "Queen Bee" not in selection.specialists
        and len(selection.capabilities) <= 4
        and selection.advisory_only
        and selection.founder_final
    )


def _matrix_baseline() -> bool:
    from oap.smi.organ_manager import OrganManager

    state = OrganManager().status()
    regions = state["analysis_regions"]
    return state["brain_count"] == 1 and len(regions) == len(set(regions))


def _identity_baseline() -> bool:
    from oap.contracts import IdentityRecord
    from oap.permissions import PermissionEngine

    engine = PermissionEngine()
    identity = IdentityRecord("synthetic", "USER", 3, permissions=frozenset({"REQUEST_RECOMMENDATION"}))
    inactive = IdentityRecord("synthetic", "USER", 3, status="INACTIVE",
                              permissions=identity.permissions)
    return engine.authorize_identity(identity).allowed and not engine.authorize_identity(inactive).allowed


def _civic_rights_baseline() -> bool:
    from mission_control.oap_system_protocol import choose_protocol

    decision = choose_protocol("synthetic private data review", private_data=True)
    return decision.fail_closed and decision.reason == "private_data_path_not_proven"


def _threat_awareness_baseline() -> bool:
    from oap.smi.runtime_guard import (
        MAX_COLLECTION_ITEMS,
        RuntimeGuardViolation,
        validate_action_payload,
    )

    try:
        validate_action_payload({"sample": [0] * (MAX_COLLECTION_ITEMS + 1)})
    except RuntimeGuardViolation as exc:
        return str(exc) == "payload_collection_limit_exceeded"
    return False


def _living_kernel_baseline() -> bool:
    from oap.contracts import ActionPlan, action_plan_digest

    original = ActionPlan("synthetic", "review.sample", {"a": 1, "b": 2})
    reordered = ActionPlan("synthetic", "review.sample", {"b": 2, "a": 1})
    altered = ActionPlan("synthetic", "review.sample", {"a": 2, "b": 2})
    return action_plan_digest(original) == action_plan_digest(reordered) != action_plan_digest(altered)


def _deployment_baseline() -> bool:
    from oap.registry.tools import ToolRegistry
    from oap.smi.capability_preflight import preflight

    result = preflight(
        ToolRegistry(), task_type="TECHNICAL", query="deploy",
        tool_id="unregistered", ability="deploy.trigger", mutation=True,
    )
    return not result.permitted_for_proposal and result.human_approval_required and result.kernel_required


def _green_gate_baseline() -> bool:
    from mission_control.oap_system_protocol import mind_body_soul_review

    result = mind_body_soul_review(mind_evidence=True, body_evidence=False, soul_evidence=True)
    return result["all_proven"] is False and result["missing"] == ("BODY",)


BUILTIN_BASELINES = {
    "stealth": _stealth_baseline,
    "patterns": _patterns_baseline,
    "last_line_defence": _last_line_defence_baseline,
    "complex_missions": _complex_missions_baseline,
    "matrix": _matrix_baseline,
    "identity": _identity_baseline,
    "civic_rights": _civic_rights_baseline,
    "threat_awareness": _threat_awareness_baseline,
    "living_kernel": _living_kernel_baseline,
    "deployment": _deployment_baseline,
    "green_gate": _green_gate_baseline,
    "memory": _memory_baseline,
    "creation": _creation_baseline,
    "investigation": _investigation_baseline,
    "language": _language_baseline,
    "execution": _execution_baseline,
    "verification": _verification_baseline,
    "coordination": _coordination_baseline,
    "pack": _pack_baseline,
    "swarm": _swarm_baseline,
    "recovery": _recovery_baseline,
    "guardian": _guardian_baseline,
    "adversarial": _adversarial_baseline,
    "command": _command_baseline,
    "dependencies": _dependency_baseline,
    "economics": _economics_baseline,
    "science": _science_baseline,
    "audit": _audit_baseline,
}


def benchmark_builtin_capability(protocol: str) -> dict[str, object]:
    """Explicit fixed synthetic smoke test, not an automatic request-path action.

    Never executes candidate packages, user-provided code or external commands.
    These tiny cases exercise standard-library or existing OAP controls, not a performance
    ranking or independent operational certification of the selected protocol.
    """
    selected = recommend_protocol_team(protocol)
    runner = BUILTIN_BASELINES.get(selected.protocol)
    result = {
        "protocol": selected.protocol,
        "scope": "synthetic_fixed_case_smoke_test",
        "status": "Not tested",
        "checks_passed": 0,
        "checks_total": 0,
        "elapsed_ms": None,
        "candidate_benchmark_verified": False,
        "independent_verification": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }
    if runner is None:
        return result
    started = perf_counter()
    passed = runner() is True
    return {
        **result,
        "status": "Passed" if passed else "Failed",
        "checks_passed": int(passed),
        "checks_total": 1,
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
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
