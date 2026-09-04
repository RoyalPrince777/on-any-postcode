"""First-party Infrastructure Intelligence inside Technology Intelligence.

This is a bounded SMI specialist capability. It observes OAP-owned infrastructure
status projections, analyses dependency and continuity risk, and feeds evidence to
the War Room. It is not another Intelligence World, brain, infrastructure system,
provider, operator or execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from . import live_signals

INFRASTRUCTURE_INTELLIGENCE_FOCUSES: tuple[dict[str, str], ...] = (
    {"id": "compute", "name": "Compute Intelligence", "purpose": "Assess local, edge and hosted compute capacity, health and fallback readiness."},
    {"id": "network", "name": "Network Intelligence", "purpose": "Assess OAP connectivity state, reachability and network dependency risk."},
    {"id": "storage", "name": "Storage & Database Intelligence", "purpose": "Assess persistence, replication, integrity and recovery evidence."},
    {"id": "hosting", "name": "Hosting Intelligence", "purpose": "Assess service hosting health, concentration risk and failover readiness."},
    {"id": "maps", "name": "Maps Infrastructure Intelligence", "purpose": "Assess first-party map context readiness without becoming Navigation."},
    {"id": "connectivity", "name": "Connectivity Infrastructure Intelligence", "purpose": "Assess Connectivity and eSIM readiness without network-control authority."},
    {"id": "device_edge", "name": "Device & Edge Intelligence", "purpose": "Assess trusted-device and local edge capability for degraded operation."},
    {"id": "power_energy", "name": "Power & Energy Intelligence", "purpose": "Assess power dependency, continuity and energy constraints where evidence exists."},
    {"id": "resilience_failover", "name": "Resilience & Failover Intelligence", "purpose": "Assess isolation, fallback, rollback and recovery paths across infrastructure."},
    {"id": "observability", "name": "Observability Intelligence", "purpose": "Assess whether health states are evidence-derived, fresh and internally consistent."},
)

FIRST_PARTY_POLICY = {
    "owner": "ON ANY POSTCODE",
    "system_identity": "OAP Infrastructure Intelligence",
    "oap_owns_intelligence": True,
    "oap_owns_signal_language": True,
    "oap_owns_health_model": True,
    "external_identity_allowed": False,
    "external_authority_allowed": False,
    "external_source_role": "replaceable_data_only_when_needed",
    "external_source_can_execute": False,
    "external_source_can_approve": False,
    "human_authority_final": True,
}


def _module_map(modules: object) -> dict[str, Mapping[str, Any]]:
    if not isinstance(modules, Sequence) or isinstance(modules, (str, bytes)):
        return {}
    return {
        str(item.get("id", "")): item
        for item in modules
        if isinstance(item, Mapping) and item.get("id")
    }


def _focus_signal(focus_id: str, modules: Mapping[str, Mapping[str, Any]]) -> tuple[dict[str, str], str]:
    if focus_id == "maps":
        module = modules.get("maps")
        if module:
            return live_signals.resolve_runtime_signal(module.get("state"), status=module.get("status")), str(module.get("data") or "Maps evidence unavailable")
    if focus_id in {"network", "connectivity"}:
        module = modules.get("connectivity")
        if module:
            return live_signals.resolve_runtime_signal(module.get("state"), status=module.get("status")), str(module.get("data") or "Connectivity evidence unavailable")
    if focus_id == "resilience_failover":
        healthy = sum(str(item.get("state")) == "healthy" for item in modules.values())
        if modules and healthy == len(modules):
            return live_signals.get_signal("healthy"), "All currently registered Infrastructure modules report healthy runtime state"
        return live_signals.get_signal("warning"), "One or more Infrastructure modules still require runtime or continuity proof"
    if focus_id == "observability":
        if modules and all(item.get("signal") for item in modules.values()):
            return live_signals.get_signal("connected"), "Canonical OAP signal annotations are present on Infrastructure modules"
        return live_signals.get_signal("warning"), "Canonical signal evidence is incomplete"
    return live_signals.get_signal("warning"), "No first-party runtime evidence is supplied for this focus yet"


def review(infrastructure_projection: Mapping[str, Any]) -> dict[str, Any]:
    """Review one OAP Infrastructure projection without performing network I/O."""

    modules = _module_map(infrastructure_projection.get("modules"))
    focus_results: list[dict[str, Any]] = []
    for focus in INFRASTRUCTURE_INTELLIGENCE_FOCUSES:
        signal, evidence = _focus_signal(focus["id"], modules)
        focus_results.append(
            {
                **focus,
                "signal": signal,
                "evidence": evidence,
                "advisory_only": True,
                "can_execute": False,
            }
        )

    critical = sum(item["signal"]["id"] == "critical" for item in focus_results)
    warnings = sum(item["signal"]["id"] in {"warning", "offline"} for item in focus_results)
    overall_signal = (
        live_signals.get_signal("critical")
        if critical
        else live_signals.get_signal("warning")
        if warnings
        else live_signals.get_signal("healthy")
    )
    return {
        "id": "infrastructure_intelligence",
        "name": "Infrastructure Intelligence",
        "parent": "Technology Intelligence",
        "kind": "first_party_cross_system_specialist_intelligence",
        "mode": "first_party_evidence_review",
        "demo_mode": False,
        "brain_count": 0,
        "intelligence_world_count_added": 0,
        "first_party_policy": FIRST_PARTY_POLICY,
        "signal": overall_signal,
        "focuses": tuple(focus_results),
        "focus_count": len(focus_results),
        "war_room_feed": {
            "enabled": True,
            "fields": ("signal", "evidence", "dependency_risk", "continuity_gap", "recommended_next_gate"),
            "decision_authority": False,
        },
        "recommendations": (
            "Keep one OAP-owned health truth for every critical infrastructure dependency.",
            "Treat outside data as replaceable evidence only; never as OAP identity or authority.",
            "Lower confidence when evidence is stale, missing or contradictory.",
            "Require fallback, rollback and recovery proof before operational certification.",
        ),
        "independent_execute": False,
        "independent_approval": False,
        "can_execute": False,
        "can_approve": False,
        "human_authority_final": True,
        "truth_boundary": "Infrastructure Intelligence advises on OAP infrastructure evidence; it cannot provision networks, mutate infrastructure or certify missing live proof.",
    }


def infrastructure_intelligence_status() -> dict[str, Any]:
    ids = tuple(item["id"] for item in INFRASTRUCTURE_INTELLIGENCE_FOCUSES)
    signal_validation = live_signals.validate_signal_language()
    architecture_ready = (
        len(ids) == 10
        and len(ids) == len(set(ids))
        and signal_validation["passed"] is True
        and FIRST_PARTY_POLICY["oap_owns_intelligence"] is True
        and FIRST_PARTY_POLICY["external_authority_allowed"] is False
    )
    return {
        "id": "infrastructure_intelligence",
        "name": "Infrastructure Intelligence",
        "parent": "Technology Intelligence",
        "kind": "first_party_cross_system_specialist_intelligence",
        "architecture_ready": architecture_ready,
        "mode": "first_party_evidence_review",
        "demo_mode": False,
        "focuses": INFRASTRUCTURE_INTELLIGENCE_FOCUSES,
        "focus_count": len(INFRASTRUCTURE_INTELLIGENCE_FOCUSES),
        "first_party_policy": FIRST_PARTY_POLICY,
        "signal_language": live_signals.public_legend(),
        "brain_count": 0,
        "intelligence_world_count_added": 0,
        "independent_execute": False,
        "independent_approval": False,
        "can_execute": False,
        "can_approve": False,
        "human_authority_final": True,
    }
