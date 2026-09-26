"""First-party OAP Host control-plane truth model.

This module defines OAP's canonical hosting inventory and fail-closed release
readiness. It does not provision machines, move traffic, expose secrets, or
claim that third-party hosted services are already self-hosted.
"""
from __future__ import annotations

import os
from typing import Any

from oap.smi.sovereign_controls import SovereignControlPlane

_TRUE = frozenset({"1", "true", "yes", "on"})

_SERVICE_REGISTRY: tuple[dict[str, object], ...] = (
    {"service_id": "public-app", "name": "On Any Postcode", "class": "web"},
    {"service_id": "smi", "name": "SMI", "class": "intelligence"},
    {"service_id": "routing-london", "name": "OAP Route Core · London", "class": "routing"},
    {"service_id": "routing-east-sussex", "name": "OAP Route Core · East Sussex", "class": "routing"},
    {"service_id": "routing-scotland", "name": "OAP Route Core · Scotland", "class": "routing"},
    {"service_id": "routing-northern-ireland", "name": "OAP Route Core · Northern Ireland", "class": "routing"},
    {"service_id": "database", "name": "OAP Data · PostgreSQL", "class": "data"},
    {"service_id": "object-storage", "name": "OAP Object Storage", "class": "storage"},
    {"service_id": "turn", "name": "OAP TURN", "class": "network"},
)


def _enabled(name: str) -> bool:
    return os.getenv(name, "").strip().casefold() in _TRUE


def service_registry() -> tuple[dict[str, object], ...]:
    """Return the canonical first-party service inventory without live-state claims."""

    return tuple(dict(item) for item in _SERVICE_REGISTRY)


def host_attestation() -> dict[str, Any]:
    sovereign = SovereignControlPlane().status()
    runtime_checks = {
        "node_identity_present": bool(os.getenv("OAP_HOST_NODE_ID", "").strip()),
        "infrastructure_self_hosted": _enabled("OAP_SOVEREIGN_INFRA_SELF_HOSTED"),
        "data_custody_self_hosted": _enabled("OAP_SOVEREIGN_DATA_SELF_HOSTED"),
        "network_egress_controlled": _enabled("OAP_SOVEREIGN_NETWORK_EGRESS_CONTROLLED"),
        "observability_first_party": _enabled("OAP_SOVEREIGN_OBSERVABILITY_FIRST_PARTY"),
        "recovery_restore_proven": _enabled("OAP_SOVEREIGN_RECOVERY_PROVEN"),
        "supply_chain_attested": _enabled("OAP_SOVEREIGN_SUPPLY_CHAIN_ATTESTED"),
        "host_deploy_rollback_proven": _enabled("OAP_HOST_DEPLOY_ROLLBACK_PROVEN"),
    }
    failed = tuple(name for name, passed in runtime_checks.items() if not passed)
    return {
        "architecture_ready": True,
        "runtime_ready": not failed,
        "runtime_checks": runtime_checks,
        "runtime_gaps": failed,
        "runtime_gap_count": len(failed),
        "sovereign_halt_active": bool(sovereign["emergency_halt_active"]),
        "human_authority_final": True,
        "external_hosting_can_count_as_self_hosted": False,
        "physical_server_ownership_claimed": False,
    }


def deployment_review(
    *,
    service_id: object,
    exact_commit: object,
    rollback_ref: object,
    health_proven: bool,
    human_authority_approved: bool,
) -> dict[str, Any]:
    service = str(service_id or "").strip()
    commit = str(exact_commit or "").strip()
    rollback = str(rollback_ref or "").strip()
    attestation = host_attestation()
    known = {str(item["service_id"]) for item in _SERVICE_REGISTRY}

    checks = {
        "known_service": service in known,
        "host_runtime_ready": bool(attestation["runtime_ready"]),
        "sovereign_halt_clear": not bool(attestation["sovereign_halt_active"]),
        "exact_commit_present": len(commit) >= 7,
        "rollback_ref_present": len(rollback) >= 7,
        "health_proven": bool(health_proven),
        "human_authority_approved": bool(human_authority_approved),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return {
        "allowed": not failed,
        "checks": checks,
        "failed_checks": failed,
        "service_id": service,
        "execution_performed": False,
        "traffic_changed": False,
        "secret_exposed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    attestation = host_attestation()
    registry = service_registry()
    return {
        "component": "OAP Host Core",
        "policy_version": "oap-host-core-v1",
        "architecture_ready": True,
        "runtime_ready": bool(attestation["runtime_ready"]),
        "service_count": len(registry),
        "service_ids": tuple(str(item["service_id"]) for item in registry),
        "host_attestation": attestation,
        "provider_independent_target": True,
        "current_provider_migration_complete": False,
        "self_hosted_claim": bool(attestation["runtime_ready"]),
        "deployment_execution_enabled": False,
        "rollback_execution_enabled": False,
        "secret_export": False,
        "human_authority_final": True,
    }
