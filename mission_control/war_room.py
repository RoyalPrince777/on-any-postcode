"""Founder-only, read-only readiness view for the complete OAP programme.

The War Room aggregates existing canonical status sources.  It does not create
another architecture registry, probe external providers, mutate state, approve
work or execute actions.  Ratings are evidence stages rather than opinions:
later evidence cannot skip an earlier missing stage.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from oap.guardian.engine import GuardianEngine
from oap.war_room import WarRoomEngine

from . import (
    agents,
    authority,
    brain,
    infrastructure,
    judgement,
    neon_auth,
    organism,
    organism_runtime,
    postgres_db,
    product_cores,
    product_store,
    products,
    provider_fabric,
    public_store,
    routing,
    silicon_architecture,
    silicon_reference_platform,
    sovereign_digital_soc,
    sovereign_digital_soc_v02,
    telemetry,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

RATING_RUBRIC: tuple[dict[str, Any], ...] = (
    {
        "stars": 0,
        "label": "Unproven",
        "signal": "red",
        "meaning": "No canonical evidence has been confirmed.",
    },
    {
        "stars": 1,
        "label": "Approved scope",
        "signal": "yellow",
        "meaning": "The boundary or requirement is defined.",
    },
    {
        "stars": 2,
        "label": "Implemented",
        "signal": "amber",
        "meaning": "A bounded implementation exists.",
    },
    {
        "stars": 3,
        "label": "Proof verified",
        "signal": "purple",
        "meaning": "Automated verification or simulation proof exists.",
    },
    {
        "stars": 4,
        "label": "Runtime verified",
        "signal": "green",
        "meaning": "Current runtime evidence has been observed.",
    },
    {
        "stars": 5,
        "label": "Operationally certified",
        "signal": "green",
        "meaning": "Live outcome evidence and required Human approval exist.",
    },
)

WAR_ROOM_FLOW = tuple(
    {
        "order": index,
        "component": step["actor"],
        "role": step["action"],
        "authority": step.get("authority"),
    }
    for index, step in enumerate(organism.GOVERNANCE_LAW, start=1)
)

REVIEW_LENSES = (
    {
        "id": "proof",
        "name": "Proof",
        "question": "What is directly evidenced rather than merely labelled ready?",
        "owner": "Intelligence",
    },
    {
        "id": "protection",
        "name": "Protection",
        "question": "Which safety, privacy or constitutional boundary could fail?",
        "owner": "Guardian",
    },
    {
        "id": "creation",
        "name": "Creation",
        "question": "Is there one bounded implementation with a clear owner?",
        "owner": "Builder",
    },
    {
        "id": "identity",
        "name": "Identity",
        "question": "Is the requester, permission and authority level certified?",
        "owner": "Identity",
    },
    {
        "id": "decision",
        "name": "Decision",
        "question": "Is Human Authority making the final consequential decision?",
        "owner": "Sovereign",
    },
    {
        "id": "memory",
        "name": "Memory",
        "question": "Can HRM prove the evidence, decision, outcome and lesson?",
        "owner": "HRM",
    },
    {
        "id": "growth",
        "name": "Growth",
        "question": "Is the refinement reversible, coherent and upgrade-only?",
        "owner": "Organism",
    },
)

RESOLVED_BOUNDARIES = (
    {
        "components": "OAPDATA / metadata / OAP CORE",
        "status": "Resolved",
        "resolution": "OAP CORE is canonical; older names are compatibility aliases only.",
    },
    {
        "components": "OAP Market / OAP Commerce Core",
        "status": "Resolved",
        "resolution": "Market is the product surface; Commerce Core owns its workflow.",
    },
    {
        "components": "OAP Music / OAP Tune Core",
        "status": "Resolved",
        "resolution": "Music is the product surface; Tune Core owns its workflow.",
    },
    {
        "components": "The Spot / The Link / Link Up",
        "status": "Resolved",
        "resolution": "Place, connection rooms and protected conversation remain distinct layers.",
    },
    {
        "components": "Managed Neon Auth / Identity Engine",
        "status": "Bounded",
        "resolution": "Neon authenticates sessions; OAP Identity owns roles and authority.",
    },
    {
        "components": "Colonel Hathi / Hathi",
        "status": "Resolved",
        "resolution": "Hathi is an alias of the single Colonel Hathi passport.",
    },
    {
        "components": "SMI / Synthetic Mind",
        "status": "Resolved",
        "resolution": "Synthetic Mind remains an internal SMI organ, never a second brain.",
    },
    {
        "components": "War Room / Human Authority",
        "status": "Resolved",
        "resolution": "War Room reviews consequences; Human Authority alone decides.",
    },
)

_ORGAN_SOURCES: dict[str, tuple[str, ...]] = {
    "infrastructure": ("mission_control/infrastructure.py",),
    "trust": ("oap/aegis/engine.py", "oap/guardian/engine.py"),
    "world_spot": ("mission_control/products.py", "mission_control/location_intelligence.py"),
    "link_up": ("mission_control/linkup.py", "mission_control/product_store.py"),
    "tune_core": ("mission_control/product_core_services.py",),
    "commerce_core": ("mission_control/product_core_services.py",),
    "sika": ("mission_control/product_store.py",),
    "post_core": ("mission_control/product_core_services.py",),
    "movement": ("mission_control/movement.py", "mission_control/routing.py"),
    "media": ("mission_control/products.py",),
    "youth": ("mission_control/products.py",),
    "nature": ("mission_control/products.py",),
    "arena": ("mission_control/products.py",),
}

_ORGAN_TESTS: dict[str, tuple[str, ...]] = {
    "infrastructure": ("tests/test_infrastructure_runtime_truth.py",),
    "trust": ("tests/test_smi_runtime.py",),
    "world_spot": ("tests/test_complete_spot_surface.py",),
    "link_up": ("tests/test_linkup_ui.py",),
    "tune_core": ("tests/test_product_cores.py",),
    "commerce_core": ("tests/test_product_cores.py",),
    "sika": ("tests/test_digital_product_organs.py",),
    "post_core": ("tests/test_product_cores.py",),
    "movement": ("tests/test_movement_operations.py",),
    "media": ("tests/test_digital_product_organs.py",),
    "youth": ("tests/test_digital_product_organs.py",),
    "nature": ("tests/test_digital_product_organs.py",),
    "arena": ("tests/test_digital_product_organs.py",),
}

_RTL_PROOFS = (
    {
        "id": "rtl_guardian_nexus",
        "name": "RTL Guardian / NEXUS Proof",
        "source": "rtl/oap_guardian_nexus_slice.sv",
        "testbench": "rtl/tb_oap_guardian_nexus_slice.sv",
        "marker": "OAP_RTL_PROOF_SLICE_V0_PASS",
        "summary": "21-gate Guardian policy, internal NEXUS and HRM receipt registers.",
        "next_gate": "Integrate only with later cryptographic and hardware proofs.",
    },
    {
        "id": "rtl_memory_guard",
        "name": "RTL Memory Guard / IOMMU",
        "source": "rtl/oap_memory_guard_slice.sv",
        "testbench": "rtl/tb_oap_memory_guard_slice.sv",
        "marker": "OAP_RTL_MEMORY_GUARD_V0_PASS",
        "summary": "Seven-zone decoding, fail-closed isolation and domain-mask checks.",
        "next_gate": "Add a separately reviewed data-path proof before any DMA claim.",
    },
    {
        "id": "rtl_attestation",
        "name": "RTL Trust / Attestation",
        "source": "rtl/oap_trust_attestation_core.sv",
        "testbench": "rtl/tb_oap_trust_attestation_core.sv",
        "marker": "OAP_RTL_ATTESTATION_V0_PASS",
        "summary": "Measured-boot registers, nonce freshness and HRM-linked simulation proof.",
        "next_gate": "Prove a real RTL cryptographic primitive before FPGA integration.",
    },
)


def _safe_mapping(call: Callable[[], Mapping[str, Any]]) -> dict[str, Any]:
    """Read one status source and fail closed without leaking exception details."""

    try:
        value = call()
    except Exception:  # noqa: BLE001 - readiness aggregation must fail closed.
        return {"ready": False, "error": "status_unavailable"}
    return dict(value) if isinstance(value, Mapping) else {"ready": False}


def _paths_present(paths: tuple[str, ...]) -> bool:
    return bool(paths) and all((_REPOSITORY_ROOT / path).is_file() for path in paths)


def _ci_marker_present(marker: str) -> bool:
    workflow = _REPOSITORY_ROOT / ".github/workflows/ci.yml"
    try:
        return marker in workflow.read_text(encoding="utf-8")
    except OSError:
        return False


def _stages(
    approved: bool,
    implemented: bool,
    verified: bool,
    runtime: bool,
    operational: bool,
    evidence: tuple[str, str, str, str, str],
) -> tuple[dict[str, Any], ...]:
    states = (approved, implemented, verified, runtime, operational)
    return tuple(
        {
            "stage": RATING_RUBRIC[index]["label"],
            "passed": state is True,
            "evidence": evidence[index - 1],
        }
        for index, state in enumerate(states, start=1)
    )


def _rating(
    *,
    item_id: str,
    name: str,
    category: str,
    summary: str,
    stages: tuple[dict[str, Any], ...],
    next_gate: str,
    impact: int,
    parent: str | None = None,
    truth_boundary: str | None = None,
) -> dict[str, Any]:
    if len(stages) != 5:
        raise ValueError("Every War Room rating requires exactly five evidence stages")

    stars = 0
    stage_blocked = False
    for stage in stages:
        if stage["passed"] and not stage_blocked:
            stars += 1
        else:
            stage_blocked = True

    rubric = RATING_RUBRIC[stars]
    first_missing = next(
        (stage["stage"] for stage in stages if not stage["passed"]),
        None,
    )
    return {
        "id": item_id,
        "name": name,
        "category": category,
        "parent": parent,
        "summary": summary,
        "stars": stars,
        "stars_display": "★" * stars + "☆" * (5 - stars),
        "score": stars * 20,
        "label": rubric["label"],
        "signal": rubric["signal"],
        "first_missing_stage": first_missing,
        "next_gate": next_gate,
        "impact": impact,
        "truth_boundary": truth_boundary,
        "human_approval_required": stars < 5,
        "stages": stages,
    }


def _component_ready(brain_status: Mapping[str, Any], name: str) -> bool:
    components = brain_status.get("components")
    if not isinstance(components, (tuple, list)):
        return False
    return any(
        isinstance(component, Mapping)
        and component.get("name") == name
        and component.get("state") == "ready"
        for component in components
    )


def _core_ratings(snapshot: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    architecture = snapshot["architecture"]
    brain_status = snapshot["brain"]
    auth_status = snapshot["auth"]
    authority_status = snapshot["authority"]
    postgres = snapshot["postgres"]
    judgement_status = snapshot["judgement"]
    guardian_status = snapshot["guardian"]
    agent_status = snapshot["agents"]

    architecture_passed = bool(architecture.get("validation", {}).get("passed"))
    human_decisions = int(judgement_status.get("human_decisions") or 0)
    brain_components = brain_status.get("components") or ()
    brain_runtime_ready = bool(brain_components) and all(
        isinstance(component, Mapping) and component.get("state") == "ready"
        for component in brain_components
    )

    return [
        _rating(
            item_id="digital_organism",
            name="Digital Organism Architecture",
            category="Command and governance",
            summary="One overall anatomy, one SMI Brain and Soul–Mind–Body per agent.",
            stages=_stages(
                True,
                _paths_present(("mission_control/organism.py",)),
                architecture_passed,
                False,
                False,
                (
                    "Canonical anatomy approved",
                    "Executable architecture registry present",
                    "Duplicate and boundary validators pass",
                    "Live organism outcome evidence observed",
                    "Operational certification recorded",
                ),
            ),
            next_gate="Certify the complete live signal path without changing locked anatomy.",
            impact=5,
            truth_boundary="Architecture proof is not live product proof.",
        ),
        _rating(
            item_id="identity_authority",
            name="Identity and Human Authority",
            category="Command and governance",
            summary="Founder-only private authority with Human approval final.",
            stages=_stages(
                True,
                _paths_present(
                    (
                        "mission_control/neon_auth.py",
                        "mission_control/authority.py",
                        "mission_control/web_security.py",
                    )
                ),
                _paths_present(
                    ("tests/test_neon_auth.py", "tests/test_public_private_auth.py")
                ),
                bool(auth_status.get("configured"))
                and bool(auth_status.get("valid"))
                and bool(postgres.get("initialized"))
                and bool(authority_status.get("ready")),
                human_decisions > 0,
                (
                    "Founder-only authority boundary approved",
                    "Session, authority and permission adapters implemented",
                    "Auth and public/private regression coverage present",
                    "Production Auth, authority store and active level-zero verified",
                    "At least one real Human Authority decision receipt exists",
                ),
            ),
            next_gate="Certify the Founder identity and record the first real approval receipt.",
            impact=5,
            truth_boundary="Authentication alone does not grant Human Authority.",
        ),
        _rating(
            item_id="smi_brain",
            name="Sovereign Megaverse Intelligence",
            category="Command and governance",
            summary="Fourteen biological regions produce recommendations only.",
            stages=_stages(
                True,
                _paths_present(("oap/smi/smi_core.py", "mission_control/brain.py")),
                architecture_passed
                and _paths_present(("tests/test_smi_runtime.py",)),
                brain_runtime_ready,
                bool(judgement_status.get("ready")),
                (
                    "Single-brain biological model approved",
                    "SMI coordinator and biological regions implemented",
                    "Architecture and SMI regression proof present",
                    "Every required SMI component reports runtime ready",
                    "Judgement and Human outcome evidence verified",
                ),
            ),
            next_gate="Connect the remaining identity, HRM, provider and approval evidence.",
            impact=5,
            truth_boundary="Recommendation intelligence has no independent execute state.",
        ),
        _rating(
            item_id="guardian_aegis",
            name="Aegis and Guardian",
            category="Command and governance",
            summary="Threat checks and constitutional protection fail closed.",
            stages=_stages(
                True,
                _paths_present(("oap/aegis/engine.py", "oap/guardian/engine.py")),
                _paths_present(("tests/test_smi_runtime.py",)),
                bool(guardian_status.get("ready")),
                False,
                (
                    "Protection boundary approved",
                    "Aegis and Guardian engines implemented",
                    "Fail-closed regression proof present",
                    "In-process Guardian reports ready",
                    "Live consequential block and receipt evidence observed",
                ),
            ),
            next_gate="Verify a live blocked consequence creates an immutable HRM receipt.",
            impact=5,
        ),
        _rating(
            item_id="war_room_engine",
            name="War Room Consequence Engine",
            category="Command and governance",
            summary="Evidence, dissent and reversible scenarios without decision authority.",
            stages=_stages(
                True,
                _paths_present(("oap/war_room/engine.py",)),
                _paths_present(("tests/test_war_room_v2.py",)),
                _component_ready(brain_status, "War Room"),
                human_decisions > 0,
                (
                    "War Room review boundary approved",
                    "Evidence-driven consequence engine implemented",
                    "War Room regression proof present",
                    "War Room is connected inside SMI runtime",
                    "Real reviewed decision outcome recorded",
                ),
            ),
            next_gate="Record the first complete review → decision → HRM outcome chain.",
            impact=4,
            truth_boundary="War Room recommends review, delay or block; it never approves.",
        ),
        _rating(
            item_id="living_kernel",
            name="Living Kernel and Builder",
            category="Command and governance",
            summary="The heart coordinates only receipt-bound approved actions.",
            stages=_stages(
                True,
                _paths_present(
                    ("oap/kernel/living_kernel.py", "oap/kernel/builder.py")
                ),
                _paths_present(("tests/test_human_approval_kernel.py",)),
                _component_ready(brain_status, "Living Kernel and Builder"),
                False,
                (
                    "Approved-action boundary defined",
                    "Living Kernel and empty-by-default Builder implemented",
                    "Receipt and double-gate tests present",
                    "At least one approved bounded handler is runtime ready",
                    "A reversible live outcome is certified",
                ),
            ),
            next_gate="Approve one reversible Builder handler with rollback and audit proof.",
            impact=5,
        ),
        _rating(
            item_id="agent_registry",
            name="78 Agent Passports",
            category="Command and governance",
            summary="Unique family, role and Soul–Mind–Body passport for every agent.",
            stages=_stages(
                int(agent_status.get("checks", {}).get("locked_agent_count") or 0)
                == 78,
                int(agent_status.get("checks", {}).get("registered_agents") or 0)
                == 78,
                bool(agent_status.get("passed"))
                and bool(agent_status.get("registry_complete")),
                bool(agent_status.get("ready_for_activation")),
                False,
                (
                    "Registry target remains 78 agents",
                    "All 78 passports are implemented",
                    "Duplicate-role and passport validation passes",
                    "Human activation and provider assignments are ready",
                    "Bounded production advisory outcomes are certified",
                ),
            ),
            next_gate="Approve runtime activation and provider assignments without changing passports.",
            impact=4,
            truth_boundary="Agent approval does not grant execution or final authority.",
        ),
    ]


def _world_ratings(snapshot: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    agent_status = snapshot["agents"]
    families = agents.INTELLIGENCE_FAMILIES
    ratings: list[dict[str, Any]] = []
    for world in agents.INTELLIGENCE_WORLDS:
        world_id = world["id"]
        world_families = tuple(
            family for family in families if family.get("world_id") == world_id
        )
        family_ids = {str(family["id"]) for family in world_families}
        world_agents = tuple(
            agent
            for agent in agents.AGENT_REGISTRY
            if str(agent.get("family_id")) in family_ids
        )
        providers_assigned = bool(world_agents) and all(
            bool(agent.get("provider_ids")) for agent in world_agents
        )
        verified = bool(world_families) and bool(world_agents) and bool(
            agent_status.get("passed")
        )
        purpose = str(
            world.get("purpose")
            or next(
                (
                    family.get("purpose")
                    for family in world_families
                    if family.get("purpose")
                ),
                "Approved specialist Intelligence world.",
            )
        )
        ratings.append(
            _rating(
                item_id=f"world_{world_id}",
                name=str(world["name"]),
                category="Intelligence worlds",
                summary=purpose,
                stages=_stages(
                    True,
                    bool(world_families),
                    verified,
                    providers_assigned,
                    False,
                    (
                        "Intelligence world approved",
                        f"{len(world_families)} family/families assigned",
                        f"{len(world_agents)} unique passports validated",
                        "Every passport has an approved provider assignment",
                        "Live bounded outcomes are certified",
                    ),
                ),
                next_gate=(
                    "Approve its first family and unique passports."
                    if not world_families
                    else "Assign approved analysis providers and verify bounded outcomes."
                ),
                impact=3,
                parent="OAP Intelligence",
                truth_boundary="Intelligence proposes; Human Authority remains final.",
            )
        )
    return ratings


def _organ_runtime_flags(
    organ_id: str,
    snapshot: Mapping[str, Mapping[str, Any]],
) -> tuple[bool, bool]:
    product_core_status = snapshot["product_cores"]
    store_status = snapshot["product_store"]
    public_status = snapshot["public_store"]
    route_status = snapshot["routing"]
    infra_status = snapshot["infrastructure"]
    judgement_status = snapshot["judgement"]

    if organ_id == "infrastructure":
        modules = infra_status.get("modules") or ()
        healthy = sum(
            isinstance(module, Mapping) and module.get("state") == "healthy"
            for module in modules
        )
        return healthy > 0, bool(modules) and healthy == len(modules)
    if organ_id == "trust":
        return bool(snapshot["guardian"].get("ready")), False
    if organ_id == "world_spot":
        return bool(public_status.get("schema_ready")), False
    if organ_id == "link_up":
        return bool(store_status.get("ready")), False
    if organ_id in {"tune_core", "commerce_core", "post_core"}:
        products_status = product_core_status.get("products") or ()
        matching_core = {
            "tune_core": "OAP Tune Core",
            "commerce_core": "OAP Commerce Core",
            "post_core": "OAP Post Core",
        }[organ_id]
        core_ready = any(
            isinstance(item, Mapping)
            and item.get("core") == matching_core
            and item.get("oap_core_ready") is True
            for item in products_status
        )
        external_ready = any(
            isinstance(item, Mapping)
            and item.get("core") == matching_core
            and item.get("external_edge_ready") is True
            for item in products_status
        )
        return core_ready, core_ready and external_ready
    if organ_id == "sika":
        return bool(store_status.get("ready")), False
    if organ_id == "movement":
        return bool(route_status.get("runtime_verified")), bool(
            route_status.get("production_ready")
        )
    if organ_id in {"media", "youth", "nature", "arena"}:
        return False, False
    return False, bool(judgement_status.get("ready"))


def _organ_ratings(snapshot: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    ratings: list[dict[str, Any]] = []
    for organ in organism.BODY_ORGANS:
        organ_id = str(organ["id"])
        source_paths = _ORGAN_SOURCES.get(organ_id, ())
        test_paths = _ORGAN_TESTS.get(organ_id, ())
        runtime_ready, operational_ready = _organ_runtime_flags(organ_id, snapshot)
        ratings.append(
            _rating(
                item_id=f"organ_{organ_id}",
                name=str(organ["name"]),
                category="Digital organs",
                summary=str(organ["responsibility"]),
                stages=_stages(
                    bool(organ.get("human_authority_final")),
                    _paths_present(source_paths),
                    _paths_present(test_paths),
                    runtime_ready,
                    operational_ready,
                    (
                        "Canonical organ and Human Authority boundary defined",
                        "Bounded product or service implementation present",
                        "Dedicated regression proof present",
                        "Current runtime dependency evidence is ready",
                        "Required live external edge is certified",
                    ),
                ),
                next_gate=(
                    "Connect and verify its current runtime dependencies."
                    if not runtime_ready
                    else "Certify its live outcome and any regulated external edge."
                ),
                impact=4 if organ_id in {"infrastructure", "trust", "world_spot", "link_up", "movement"} else 3,
                parent="Body Systems",
                truth_boundary="Consequential edges remain Human Authority-gated.",
            )
        )
    return ratings


def _operations_ratings(snapshot: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    postgres = snapshot["postgres"]
    runtime = snapshot["runtime"]
    routing_status = snapshot["routing"]
    telemetry_status = snapshot["telemetry"]
    provider = snapshot["providers"]
    infra_status = snapshot["infrastructure"]
    product_core_status = snapshot["product_cores"]
    judgement_status = snapshot["judgement"]
    public_status = snapshot["public_store"]

    modules = {
        str(module.get("id")): module
        for module in infra_status.get("modules") or ()
        if isinstance(module, Mapping)
    }
    ratings = [
        _rating(
            item_id="postgres_hrm",
            name="PostgreSQL, HRM and Judgement",
            category="Infrastructure and runtime",
            summary="Durable identity, audit, approval, memory and decision evidence.",
            stages=_stages(
                True,
                _paths_present(("mission_control/postgres_db.py",)),
                _paths_present(
                    ("tests/test_postgres_foundation.py", "tests/test_audit_brain_migrations.py")
                )
                and not bool(postgres.get("checksum_mismatches")),
                bool(postgres.get("reachable"))
                and bool(postgres.get("initialized"))
                and bool(judgement_status.get("schema_ready")),
                bool(judgement_status.get("ready")),
                (
                    "Durable evidence boundary approved",
                    "PostgreSQL adapters and explicit migrations implemented",
                    "Migration and audit-chain regression proof present",
                    "Production schema and Judgement store verified",
                    "Human decision evidence is operationally certified",
                ),
            ),
            next_gate="Apply and checksum-verify the reviewed production schema, then certify HRM.",
            impact=5,
            truth_boundary="No migration runs on startup or GET.",
        ),
        _rating(
            item_id="organism_runtime",
            name="24/7 Organism Runtime",
            category="Infrastructure and runtime",
            summary="Durable bounded work cycle with retry and dead-letter evidence.",
            stages=_stages(
                True,
                _paths_present(("mission_control/organism_runtime.py", "mission_control/organism_worker.py")),
                _paths_present(("tests/test_organism_runtime_24x7.py",)),
                bool(runtime.get("worker_fresh")) and bool(runtime.get("schema_ready")),
                bool(runtime.get("ready")) and not bool(runtime.get("dead_letter")),
                (
                    "Bounded 24/7 cycle approved",
                    "Worker, retry and dead-letter implementation present",
                    "Runtime regression proof present",
                    "Fresh worker heartbeat and schema observed",
                    "Healthy operational cycle with no dead letters",
                ),
            ),
            next_gate="Verify a fresh Home Node heartbeat against the current revision.",
            impact=5,
            truth_boundary="The worker cannot deploy or perform consequential execution.",
        ),
        _rating(
            item_id="home_node",
            name="Termux OAP Home Node",
            category="Infrastructure and runtime",
            summary="Local-first Generation 0 node and bounded supervisor.",
            stages=_stages(
                True,
                _paths_present(
                    (
                        "scripts/termux_home_node_setup.sh",
                        "scripts/termux_home_node_run.sh",
                        "scripts/termux_home_node_status.sh",
                    )
                ),
                _paths_present(("tests/test_termux_home_node.py",)),
                bool(runtime.get("worker_fresh")),
                False,
                (
                    "Generation 0 Home Node approved",
                    "Setup, run and status scripts implemented",
                    "Home Node regression proof present",
                    "Fresh bounded worker heartbeat observed",
                    "Dedicated hardware trust and recovery certified",
                ),
            ),
            next_gate="Sync the current revision and prove heartbeat, recovery and revision evidence.",
            impact=4,
        ),
        _rating(
            item_id="route_core",
            name="OAP Route Core",
            category="Infrastructure and runtime",
            summary="OAP-owned routing boundary with dispatch and mutation disabled.",
            stages=_stages(
                True,
                _paths_present(("mission_control/routing.py",)),
                _paths_present(("tests/test_movement_routing.py",)),
                bool(routing_status.get("runtime_verified")),
                bool(routing_status.get("production_ready")),
                (
                    "OAP-owned routing boundary approved",
                    "OSRM-compatible adapter and production gates implemented",
                    "Routing and failure-path regression proof present",
                    "Current outbound route runtime proof observed",
                    "Owned provider, capacity and monitoring approved",
                ),
            ),
            next_gate="Certify an approved OAP-owned production provider and capacity plan.",
            impact=4,
            truth_boundary="Public OSRM is verification-only; dispatch remains disabled.",
        ),
        _rating(
            item_id="provider_fabric",
            name="Provider Fabric",
            category="Infrastructure and runtime",
            summary="Explicit provider slots separated from OAP agents and authority.",
            stages=_stages(
                bool(provider.get("architecture_passed")),
                int(provider.get("wired") or 0) > 0,
                int(provider.get("configured") or 0) > 0,
                int(provider.get("runtime_verified") or 0) > 0,
                False,
                (
                    "Provider/agent boundary validates",
                    f"{int(provider.get('wired') or 0)} provider slots are wired",
                    f"{int(provider.get('configured') or 0)} providers are configured",
                    "At least one current provider delivery is verified",
                    "Production provider outcomes are certified",
                ),
            ),
            next_gate="Verify each configured provider at runtime without granting authority.",
            impact=4,
        ),
        _rating(
            item_id="observability",
            name="External Observability",
            category="Infrastructure and runtime",
            summary="Metrics delivery and independent evidence beyond fixed LIVE labels.",
            stages=_stages(
                True,
                _paths_present(("mission_control/telemetry.py",)),
                _paths_present(("tests/test_infrastructure_runtime_truth.py",)),
                bool(telemetry_status.get("delivery_verified")),
                bool(telemetry_status.get("ready")),
                (
                    "Evidence-driven status requirement approved",
                    "Bounded telemetry adapter implemented",
                    "Runtime-truth regression proof present",
                    "External metric delivery observed",
                    "Operational alerting and response evidence certified",
                ),
            ),
            next_gate="Connect Datadog or an approved equivalent and verify metric delivery.",
            impact=4,
        ),
        _rating(
            item_id="live_product_certification",
            name="Live Product Certification",
            category="Infrastructure and runtime",
            summary="Route-by-route proof for public, private and product workflows.",
            stages=_stages(
                True,
                _paths_present(("tests/test_green_product_gates.py",)),
                _paths_present(("tests/test_routes_regression.py", "tests/test_templating_xss.py")),
                bool(public_status.get("schema_ready"))
                and bool(product_core_status.get("ready")),
                False,
                (
                    "Per-route certification rule approved",
                    "Green product gate suite implemented",
                    "Route, authorization and XSS regression proof present",
                    "Durable product stores are runtime ready",
                    "Every critical live route has current outcome evidence",
                ),
            ),
            next_gate="Run the authenticated live route matrix and certify each route individually.",
            impact=5,
            truth_boundary="A rendered page is not proof that its real service works.",
        ),
    ]

    for module_id in ("maps", "weather", "esim", "connectivity"):
        module = modules.get(module_id, {})
        runtime_verified = module.get("state") == "healthy"
        ratings.append(
            _rating(
                item_id=f"infra_{module_id}",
                name=str(module.get("name") or module_id.title()),
                category="Infrastructure and runtime",
                summary=str(module.get("purpose") or "Bounded infrastructure module."),
                stages=_stages(
                    bool(module),
                    bool(module.get("readiness")),
                    bool(infra_status.get("validation", {}).get("passed")),
                    runtime_verified,
                    False,
                    (
                        "Canonical infrastructure scope defined",
                        str(module.get("readiness") or "Implementation evidence missing"),
                        "Infrastructure duplicate and ownership checks pass",
                        str(module.get("data") or "Runtime delivery not observed"),
                        "Approved operational provider outcome certified",
                    ),
                ),
                next_gate=str(module.get("boundary") or "Connect and verify an approved provider."),
                impact=3,
                parent="OAP Infrastructure",
            )
        )
    return ratings


def _silicon_ratings() -> list[dict[str, Any]]:
    silicon_contract = _safe_mapping(silicon_architecture.silicon_contract)
    reference = _safe_mapping(silicon_reference_platform.reference_platform_contract)
    soc_v01 = _safe_mapping(sovereign_digital_soc.digital_soc_contract)
    soc_v02 = _safe_mapping(sovereign_digital_soc_v02.v02_contract)
    ratings = [
        _rating(
            item_id="silicon_architecture",
            name="OAP Silicon Architecture",
            category="Silicon and hardware",
            summary="Seven layers, seven zones and the 7×3 = 21 gate contract.",
            stages=_stages(
                bool(silicon_contract),
                _paths_present(("mission_control/silicon_architecture.py",)),
                _paths_present(("tests/test_silicon_architecture.py",)),
                False,
                False,
                (
                    "Canonical silicon doctrine approved",
                    "Read-only silicon contract implemented",
                    "Constitutional invariant tests present",
                    "Physical trust platform observed",
                    "Operational hardware certification recorded",
                ),
            ),
            next_gate="Keep later hardware proofs subordinate to software and Human Authority.",
            impact=3,
            truth_boundary="Architecture does not mean custom silicon exists.",
        ),
        _rating(
            item_id="silicon_reference_v1",
            name="Silicon Reference Platform v1",
            category="Silicon and hardware",
            summary="Vendor-neutral Generation 1 dedicated Home Node contract.",
            stages=_stages(
                reference.get("status") == "SPECIFICATION_READY",
                _paths_present(("mission_control/silicon_reference_platform.py",)),
                _paths_present(("tests/test_silicon_reference_platform.py",)),
                bool(reference.get("physical_device_built")),
                False,
                (
                    "Generation 1 specification approved",
                    "Seven capability and acceptance-gate contract implemented",
                    "Reference platform invariant tests present",
                    "A physical candidate has passed all seven gates",
                    "Operational device fleet evidence certified",
                ),
            ),
            next_gate="Assess a real candidate only after Human Authority approves procurement.",
            impact=3,
        ),
        _rating(
            item_id="soc_sim_v01",
            name="Sovereign Digital SoC Simulator v0.1",
            category="Silicon and hardware",
            summary="Constitutional block, register and interrupt software simulator.",
            stages=_stages(
                soc_v01.get("status") == "SOFTWARE_SIMULATOR",
                _paths_present(("mission_control/sovereign_digital_soc.py",)),
                _paths_present(("tests/test_sovereign_digital_soc.py",)),
                False,
                False,
                (
                    "Simulator scope defined",
                    "Software simulator implemented",
                    "Simulator invariant tests present",
                    "RTL or FPGA execution observed",
                    "Physical SoC outcome certified",
                ),
            ),
            next_gate="Retain as the software reference model for later RTL comparison.",
            impact=2,
            truth_boundary="Software simulation is not RTL or hardware.",
        ),
        _rating(
            item_id="soc_sim_v02",
            name="Sovereign Digital SoC Simulator v0.2",
            category="Silicon and hardware",
            summary="Hardware-shaped memory map, MMIO and organ-interface simulator.",
            stages=_stages(
                soc_v02.get("status") == "HARDWARE_SHAPED_SOFTWARE_SIMULATOR",
                _paths_present(("mission_control/sovereign_digital_soc_v02.py",)),
                _paths_present(("tests/test_sovereign_digital_soc_v02.py",)),
                False,
                False,
                (
                    "Hardware-shaped simulator scope defined",
                    "Memory map and MMIO model implemented",
                    "v0.2 simulator tests present",
                    "Synthesised hardware model observed",
                    "Physical execution certified",
                ),
            ),
            next_gate="Use it as a comparison oracle for expanding RTL proofs.",
            impact=2,
            truth_boundary="Hardware-shaped software remains software.",
        ),
    ]

    for proof in _RTL_PROOFS:
        source_present = _paths_present((proof["source"],))
        simulation_proof = _paths_present((proof["testbench"],)) and _ci_marker_present(
            str(proof["marker"])
        )
        ratings.append(
            _rating(
                item_id=str(proof["id"]),
                name=str(proof["name"]),
                category="Silicon and hardware",
                summary=str(proof["summary"]),
                stages=_stages(
                    True,
                    source_present,
                    simulation_proof,
                    False,
                    False,
                    (
                        "Simulation-only RTL scope defined",
                        "Synthesizable-style SystemVerilog source present",
                        "Self-checking Icarus Verilog CI proof registered",
                        "FPGA synthesis and board execution observed",
                        "Physical hardware proof certified",
                    ),
                ),
                next_gate=str(proof["next_gate"]),
                impact=3,
                truth_boundary="RTL simulation is not FPGA, ASIC or fabricated silicon.",
            )
        )

    ratings.extend(
        (
            _rating(
                item_id="fpga_reference",
                name="FPGA Reference",
                category="Silicon and hardware",
                summary="Future programmable prototype for separately proven RTL blocks.",
                stages=_stages(
                    True,
                    False,
                    False,
                    False,
                    False,
                    (
                        "Generation 3 path defined",
                        "Synthesizable top-level and constraints implemented",
                        "Timing, formal and simulation proof verified",
                        "Approved board bitstream observed",
                        "FPGA prototype operationally certified",
                    ),
                ),
                next_gate="Do not select a board until the RTL cryptographic and integration gates pass.",
                impact=2,
            ),
            _rating(
                item_id="physical_oap_silicon",
                name="Physical OAP Silicon",
                category="Silicon and hardware",
                summary="Optional future custom RISC-V/ASIC path if scale justifies it.",
                stages=_stages(
                    True,
                    False,
                    False,
                    False,
                    False,
                    (
                        "Future option defined",
                        "Physical design implementation exists",
                        "Verification and sign-off complete",
                        "Fabricated device observed",
                        "Operational silicon certified",
                    ),
                ),
                next_gate="Remain on commodity hardware until economics and proof justify fabrication.",
                impact=1,
                truth_boundary="No fabricated OAP chip is claimed.",
            ),
        )
    )
    return ratings


def _snapshot() -> dict[str, dict[str, Any]]:
    return {
        "architecture": _safe_mapping(organism.get_public_anatomy),
        "agents": _safe_mapping(agents.validate_agent_registry),
        "authority": _safe_mapping(authority.status),
        "brain": _safe_mapping(brain.get_public_brain_status),
        "infrastructure": _safe_mapping(infrastructure.get_public_infrastructure),
        "judgement": _safe_mapping(judgement.status),
        "auth": _safe_mapping(neon_auth.status),
        "postgres": _safe_mapping(postgres_db.postgres_status),
        "product_cores": _safe_mapping(product_cores.platform_status),
        "product_store": _safe_mapping(product_store.status),
        "public_store": _safe_mapping(public_store.status),
        "providers": _safe_mapping(provider_fabric.get_coarse_provider_status),
        "routing": _safe_mapping(routing.status),
        "runtime": _safe_mapping(organism_runtime.runtime_status),
        "telemetry": _safe_mapping(telemetry.status),
        "guardian": _safe_mapping(GuardianEngine().status),
    }


def _conflict_audit(snapshot: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    validations = (
        snapshot["architecture"].get("validation"),
        snapshot["agents"],
        snapshot["infrastructure"].get("validation"),
        _safe_mapping(products.validate_product_hierarchy),
    )
    for validation in validations:
        if not isinstance(validation, Mapping):
            errors.append("One canonical duplicate validator is unavailable")
            continue
        if not validation.get("passed"):
            raw_errors = validation.get("errors") or ()
            if isinstance(raw_errors, (tuple, list)):
                errors.extend(str(error) for error in raw_errors)
            else:
                errors.append("A canonical duplicate validator failed closed")

    registered_names = {
        str(agent.get("name", "")).casefold() for agent in agents.AGENT_REGISTRY
    }
    kaa_registered = "kaa" in registered_names
    if kaa_registered:
        errors.append("Kaa must remain absent unless Human Authority explicitly approves it")

    return {
        "passed": not errors,
        "active_conflicts": tuple(dict.fromkeys(errors)),
        "active_conflict_count": len(tuple(dict.fromkeys(errors))),
        "resolved_boundaries": RESOLVED_BOUNDARIES,
        "duplicate_systems": int(
            snapshot["architecture"]
            .get("validation", {})
            .get("checks", {})
            .get("duplicate_systems", 0)
            or 0
        ),
        "duplicate_agent_ids": int(
            snapshot["agents"].get("checks", {}).get("duplicate_agent_ids", 0)
            or 0
        ),
        "duplicate_agent_roles": int(
            snapshot["agents"]
            .get("checks", {})
            .get("duplicate_approved_roles", 0)
            or 0
        ),
        "naming_conflicts": int(
            snapshot["infrastructure"]
            .get("validation", {})
            .get("checks", {})
            .get("naming_conflicts", 0)
            or 0
        ),
        "legacy_term_policy": "Intelligence terminology only in active architecture",
        "kaa_registered": kaa_registered,
    }


def validate_war_room_scope() -> dict[str, Any]:
    """Validate this projection without granting it another system role."""

    flow_components = [str(item["component"]) for item in WAR_ROOM_FLOW]
    lens_ids = [str(item["id"]) for item in REVIEW_LENSES]
    errors: list[str] = []
    if len(flow_components) != len(set(flow_components)):
        errors.append("Duplicate governance actor in War Room flow")
    if len(lens_ids) != len(set(lens_ids)):
        errors.append("Duplicate War Room review lens")
    if flow_components != [str(step["actor"]) for step in organism.GOVERNANCE_LAW]:
        errors.append("War Room governance flow drifted from the canonical law")
    if WarRoomEngine().status().get("decision_authority") is not False:
        errors.append("War Room must never gain decision authority")
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "checks": {
            "governance_steps": len(flow_components),
            "review_lenses": len(lens_ids),
            "duplicate_governance_roles": len(flow_components)
            - len(set(flow_components)),
            "decision_authority": False,
            "final_authority": "Human Authority",
        },
    }


def get_war_room_dashboard() -> dict[str, Any]:
    """Return the complete Founder-only, read-only programme projection."""

    snapshot = _snapshot()
    ratings = [
        *_core_ratings(snapshot),
        *_world_ratings(snapshot),
        *_organ_ratings(snapshot),
        *_operations_ratings(snapshot),
        *_silicon_ratings(),
    ]
    categories: list[dict[str, Any]] = []
    category_order = (
        "Command and governance",
        "Intelligence worlds",
        "Digital organs",
        "Infrastructure and runtime",
        "Silicon and hardware",
    )
    for name in category_order:
        items = tuple(item for item in ratings if item["category"] == name)
        categories.append(
            {
                "id": name.casefold().replace(" ", "-"),
                "name": name,
                "items": items,
                "count": len(items),
                "average_stars": round(
                    sum(int(item["stars"]) for item in items) / len(items), 1
                )
                if items
                else 0,
                "runtime_verified": sum(int(item["stars"]) >= 4 for item in items),
                "certified": sum(int(item["stars"]) == 5 for item in items),
            }
        )

    rating_by_id = {str(item["id"]): item for item in ratings}
    top_next_ids = (
        "identity_authority",
        "postgres_hrm",
        "live_product_certification",
    )
    top_next = tuple(
        {
            "rank": rank,
            "id": item_id,
            "name": rating_by_id[item_id]["name"],
            "stars": rating_by_id[item_id]["stars"],
            "stars_display": rating_by_id[item_id]["stars_display"],
            "signal": rating_by_id[item_id]["signal"],
            "next_gate": rating_by_id[item_id]["next_gate"],
            "impact": rating_by_id[item_id]["impact"],
            "human_approval_required": True,
        }
        for rank, item_id in enumerate(top_next_ids, start=1)
    )
    star_counts = {
        str(stars): sum(int(item["stars"]) == stars for item in ratings)
        for stars in range(6)
    }
    overall = round(
        sum(int(item["stars"]) for item in ratings) / (len(ratings) * 5) * 100
    )
    conflict_audit = _conflict_audit(snapshot)
    scope = validate_war_room_scope()
    validation_errors = tuple(scope["errors"]) + tuple(
        conflict_audit["active_conflicts"]
    )

    return {
        "name": "OAP War Room",
        "mode": "read_only_evidence_review",
        "validation": {
            "passed": not validation_errors,
            "errors": validation_errors,
            "checks": {
                **scope["checks"],
                "rated_areas": len(ratings),
                "categories": len(categories),
                "active_conflicts": conflict_audit["active_conflict_count"],
            },
        },
        "rubric": RATING_RUBRIC,
        "flow": WAR_ROOM_FLOW,
        "review_lenses": REVIEW_LENSES,
        "categories": tuple(categories),
        "summary": {
            "overall_evidence_score": overall,
            "average_stars": round(
                sum(int(item["stars"]) for item in ratings) / len(ratings), 1
            ),
            "rated_areas": len(ratings),
            "runtime_verified": sum(int(item["stars"]) >= 4 for item in ratings),
            "operationally_certified": sum(
                int(item["stars"]) == 5 for item in ratings
            ),
            "star_counts": star_counts,
            "meaning": "Portfolio evidence view; not a release or safety certification.",
        },
        "top_next": top_next,
        "conflict_audit": conflict_audit,
        "controls_enabled": False,
        "can_approve": False,
        "can_execute": False,
        "human_authority": {
            "status": "Final approval required",
            "message": (
                "Every proposed connection, activation, deployment and architecture "
                "change remains subject to explicit Human Authority approval."
            ),
        },
    }
