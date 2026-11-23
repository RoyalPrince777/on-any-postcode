from __future__ import annotations

import pytest

from mission_control import matrix_privacy_workers


def test_offline_review_returns_canonical_seven_and_never_executes():
    result = matrix_privacy_workers.review_founder_device_facts({})
    assert tuple(row["agent"] for row in result["workers"]) == (
        "Neo", "Morpheus", "Trinity", "Oracle", "Architect", "Keymaker", "Seraph"
    )
    assert result["status"] == "unknown"
    assert result["actual_device_scan"] is False
    assert result["agent_runtime_connected"] is False
    assert result["independent_agent_execution_proven"] is False
    assert result["external_action_taken"] is False
    assert result["permission_changes_made"] is False
    assert result["execution_granted"] is False
    assert result["green_gate_passed"] is False
    assert result["founder_final_required"] is True
    assert result["input_fields_observed"] == 0


def test_tracker_alert_is_review_not_tracking_confirmation():
    result = matrix_privacy_workers.review_founder_device_facts(
        {"unknown_tracker_alert": True}
    )
    statuses = {row["agent"]: row["status"] for row in result["workers"]}
    assert statuses["Neo"] == "review"
    assert statuses["Trinity"] == "review"
    assert all(row["proof"] == "founder_supplied_facts_only" for row in result["workers"])
    assert "confirmed" not in str(result).lower()


def test_permissions_are_review_prompts_not_evidence_of_tracking():
    result = matrix_privacy_workers.review_founder_device_facts(
        {"location_permission_count": 2, "camera_permission_count": 0}
    )
    seraph = next(row for row in result["workers"] if row["agent"] == "Seraph")
    assert seraph["status"] == "review"
    assert "not proof of tracking" in seraph["finding"]


def test_no_flags_never_becomes_green_or_certification():
    result = matrix_privacy_workers.review_founder_device_facts({
        "unknown_tracker_alert": False,
        "unrecognised_app_count": 0,
        "location_permission_count": 0,
        "microphone_permission_count": 0,
        "camera_permission_count": 0,
        "security_updates_current": True,
        "account_mfa_enabled": True,
    })
    assert result["status"] == "no_flag"
    assert result["no_flag_is_not_security_certification"] is True
    assert result["green_gate_passed"] is False
    assert result["actual_device_scan"] is False


@pytest.mark.parametrize("facts", [
    {"location_permission_count": -1},
    {"location_permission_count": True},
    {"location_permission_count": 1001},
    {"location_permission_count": "2"},
    {"unknown_tracker_alert": 1},
    {"account_mfa_enabled": "yes"},
    {"private_location_history": "full GPS traces"},
])
def test_rejects_unbounded_or_unapproved_device_information(facts):
    with pytest.raises(ValueError):
        matrix_privacy_workers.review_founder_device_facts(facts)


def test_rejects_non_mapping_input():
    with pytest.raises(TypeError):
        matrix_privacy_workers.review_founder_device_facts("any string")


def test_does_not_echo_private_device_facts():
    facts = {"unrecognised_app_count": 7, "security_updates_current": False}
    result = matrix_privacy_workers.review_founder_device_facts(facts)
    assert "unrecognised_app_count" not in str(result)
    assert "security_updates_current" not in str(result)
    assert result["input_source"] == "founder_supplied_not_device_verified"
