"""Provider-loss readiness contract for OAP/SMI.

This module does not fail over infrastructure or mutate external providers.
It evaluates supplied evidence for whether OAP can survive loss of GitHub,
Render, or both without granting deployment, publication, or execution authority.
"""
from __future__ import annotations

from collections.abc import Mapping

_REQUIRED_CHECKS: tuple[str, ...] = (
    "local_git_history_available",
    "independent_repo_mirror_available",
    "release_manifest_preserved",
    "source_integrity_hashes_preserved",
    "provider_neutral_build_definition",
    "provider_neutral_start_command",
    "environment_inventory_preserved",
    "secrets_not_embedded_in_backup",
    "database_provider_separated",
    "database_backup_available",
    "database_restore_readback_proven",
    "object_storage_recovery_defined",
    "dns_recovery_defined",
    "health_check_provider_neutral",
    "rollback_artifact_preserved",
    "fresh_machine_restore_documented",
    "fresh_machine_restore_tested",
    "home_node_recovery_available",
    "alternate_host_path_defined",
    "audit_receipts_preserved",
    "human_authority_required",
)

_PROVIDER_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "github": (
        "local_git_history_available",
        "independent_repo_mirror_available",
        "release_manifest_preserved",
        "source_integrity_hashes_preserved",
    ),
    "render": (
        "provider_neutral_build_definition",
        "provider_neutral_start_command",
        "environment_inventory_preserved",
        "health_check_provider_neutral",
        "rollback_artifact_preserved",
        "alternate_host_path_defined",
    ),
    "github_and_render": _REQUIRED_CHECKS,
}


def required_checks() -> tuple[str, ...]:
    """Return the canonical 21-check provider-loss gate."""
    return _REQUIRED_CHECKS


def assess_provider_loss(
    evidence: Mapping[str, object],
    *,
    scenario: str = "github_and_render",
) -> dict[str, object]:
    """Evaluate supplied evidence and fail closed when proof is incomplete.

    Evidence values count only when they are literally True. Names, URLs,
    credentials, provider reachability, and architectural intent are not proof.
    """
    if scenario not in _PROVIDER_REQUIREMENTS:
        raise ValueError("unsupported_provider_loss_scenario")
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence_mapping_required")

    required = _PROVIDER_REQUIREMENTS[scenario]
    passed = tuple(name for name in required if evidence.get(name) is True)
    missing = tuple(name for name in required if evidence.get(name) is not True)

    full_gate_passed = not missing
    dual_provider_survival_proven = scenario == "github_and_render" and full_gate_passed

    return {
        "scenario": scenario,
        "required_checks": required,
        "passed_checks": passed,
        "missing_checks": missing,
        "passed_count": len(passed),
        "required_count": len(required),
        "evidence_percent": round((len(passed) / len(required)) * 100, 1),
        "provider_independence_proven": full_gate_passed,
        "dual_provider_survival_proven": dual_provider_survival_proven,
        "github_is_replaceable_connector": full_gate_passed
        if scenario in ("github", "github_and_render")
        else None,
        "render_is_replaceable_connector": full_gate_passed
        if scenario in ("render", "github_and_render")
        else None,
        "automatic_failover_authorised": False,
        "deployment_authorised": False,
        "secret_recovery_proven": False,
        "database_restore_proven": evidence.get("database_restore_readback_proven") is True,
        "human_authority_final": True,
        "status": "CERTIFIED_EVIDENCE_SET" if full_gate_passed else "BUILDING",
    }
