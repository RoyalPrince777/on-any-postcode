"""Provider-loss readiness must remain evidence-driven and fail closed."""
from __future__ import annotations

import pytest

from mission_control import provider_loss_readiness


def test_gate_has_exactly_21_unique_checks():
    checks = provider_loss_readiness.required_checks()
    assert len(checks) == 21
    assert len(set(checks)) == 21
    assert checks[-1] == "human_authority_required"


def test_empty_evidence_cannot_claim_provider_independence():
    result = provider_loss_readiness.assess_provider_loss({})
    assert result["scenario"] == "github_and_render"
    assert result["passed_count"] == 0
    assert result["required_count"] == 21
    assert result["evidence_percent"] == 0.0
    assert result["provider_independence_proven"] is False
    assert result["dual_provider_survival_proven"] is False
    assert result["deployment_authorised"] is False
    assert result["automatic_failover_authorised"] is False
    assert result["status"] == "BUILDING"


def test_truthy_strings_do_not_count_as_evidence():
    evidence = {name: "yes" for name in provider_loss_readiness.required_checks()}
    result = provider_loss_readiness.assess_provider_loss(evidence)
    assert result["passed_count"] == 0
    assert result["provider_independence_proven"] is False


def test_github_loss_uses_bounded_required_subset():
    evidence = {
        "local_git_history_available": True,
        "independent_repo_mirror_available": True,
        "release_manifest_preserved": True,
        "source_integrity_hashes_preserved": True,
    }
    result = provider_loss_readiness.assess_provider_loss(evidence, scenario="github")
    assert result["required_count"] == 4
    assert result["provider_independence_proven"] is True
    assert result["github_is_replaceable_connector"] is True
    assert result["render_is_replaceable_connector"] is None
    assert result["dual_provider_survival_proven"] is False
    assert result["deployment_authorised"] is False


def test_render_loss_stays_building_when_alternate_host_is_unproven():
    evidence = {
        "provider_neutral_build_definition": True,
        "provider_neutral_start_command": True,
        "environment_inventory_preserved": True,
        "health_check_provider_neutral": True,
        "rollback_artifact_preserved": True,
    }
    result = provider_loss_readiness.assess_provider_loss(evidence, scenario="render")
    assert result["missing_checks"] == ("alternate_host_path_defined",)
    assert result["render_is_replaceable_connector"] is False
    assert result["status"] == "BUILDING"


def test_full_21_evidence_set_still_does_not_authorise_execution():
    evidence = {name: True for name in provider_loss_readiness.required_checks()}
    result = provider_loss_readiness.assess_provider_loss(evidence)
    assert result["passed_count"] == 21
    assert result["evidence_percent"] == 100.0
    assert result["provider_independence_proven"] is True
    assert result["dual_provider_survival_proven"] is True
    assert result["github_is_replaceable_connector"] is True
    assert result["render_is_replaceable_connector"] is True
    assert result["human_authority_final"] is True
    assert result["automatic_failover_authorised"] is False
    assert result["deployment_authorised"] is False


def test_database_restore_is_reported_separately_from_architecture():
    evidence = {name: True for name in provider_loss_readiness.required_checks()}
    evidence["database_restore_readback_proven"] = False
    result = provider_loss_readiness.assess_provider_loss(evidence)
    assert result["database_restore_proven"] is False
    assert result["provider_independence_proven"] is False
    assert "database_restore_readback_proven" in result["missing_checks"]


def test_unknown_scenario_is_rejected():
    with pytest.raises(ValueError, match="unsupported_provider_loss_scenario"):
        provider_loss_readiness.assess_provider_loss({}, scenario="unknown")


def test_non_mapping_evidence_is_rejected():
    with pytest.raises(TypeError, match="evidence_mapping_required"):
        provider_loss_readiness.assess_provider_loss([], scenario="github")


def test_repository_snapshot_reports_artifacts_without_claiming_recovery(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "deploy").mkdir()
    (tmp_path / "Dockerfile.runtime").write_text("FROM python:3.12")
    (tmp_path / "requirements.txt").write_text("Flask")
    (tmp_path / "scripts/home_node_run.sh").write_text("#!/bin/sh")
    (tmp_path / "scripts/oap_home_node_supervisor.py").write_text("")
    (tmp_path / "scripts/oap_home_node_status.py").write_text("")
    (tmp_path / "docs/HOME_NODE.md").write_text("home node")

    result = provider_loss_readiness.repository_artifact_snapshot(tmp_path)
    assert result["repository_root_exists"] is True
    assert result["artifact_groups"]["runtime_build"]["complete"] is True
    assert result["artifact_groups"]["home_node_posix"]["complete"] is True
    assert result["artifact_groups"]["release_control"]["complete"] is False
    assert result["artifact_inventory_only"] is True
    assert result["counts_as_provider_independence_proof"] is False
    assert result["automatic_failover_authorised"] is False
    assert result["deployment_authorised"] is False


def test_repository_snapshot_missing_root_stays_inventory_only(tmp_path):
    result = provider_loss_readiness.repository_artifact_snapshot(tmp_path / "missing")
    assert result["repository_root_exists"] is False
    assert all(
        group["complete"] is False
        for group in result["artifact_groups"].values()
    )
    assert result["counts_as_provider_independence_proof"] is False
