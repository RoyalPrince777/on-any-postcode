from __future__ import annotations

import pytest

from mission_control import matrix_privacy_intelligence

EXPECTED = (
    "on_device_privacy_intelligence", "identity_shield",
    "network_intelligence", "offline_recovery",
    "evidence_intelligence", "governed_worker_automation",
)


def by_priority(result):
    return {row["priority"]: row for row in result["priorities"]}


def test_all_six_priorities_and_canonical_seven_without_autonomy():
    result = matrix_privacy_intelligence.review_matrix_privacy_priorities()
    assert tuple(item["priority"] for item in result["priorities"]) == EXPECTED
    assert result["priority_count"] == 6
    assert result["matrix_agents"] == (
        "Neo", "Morpheus", "Trinity", "Oracle", "Architect", "Keymaker", "Seraph"
    )
    assert result["matrix_role_count"] == 7
    assert result["overall_status"] == "unknown"
    assert result["live_device_access"] is False
    assert result["automatic_blocking"] is False
    assert result["runtime_dispatch_authorised"] is False
    assert result["green_gate_passed"] is False
    assert result["deployment_authorised"] is False
    assert result["guardian_hrm_independent_verification"] is False
    assert all(row["executed"] is False for row in result["priorities"])


def test_identity_alerts_are_review_and_not_an_attribution():
    result = matrix_privacy_intelligence.review_matrix_privacy_priorities(identity_facts={
        "unrecognised_signin_alert": True,
        "unexpected_recovery_alert": False,
        "account_mfa_enabled": True,
    })
    assert by_priority(result)["identity_shield"]["status"] == "review"
    assert result["overall_status"] == "review"
    assert result["security_certified"] is False


def test_network_concern_does_not_trigger_packet_capture():
    result = matrix_privacy_intelligence.review_matrix_privacy_priorities(network_facts={
        "unrecognised_network_count": 1,
        "unexpected_network_change": False,
        "private_dns_configured": True,
    })
    assert by_priority(result)["network_intelligence"]["status"] == "review"
    assert result["raw_network_traffic_collected"] is False
    assert result["network_calls_made"] is False
    assert result["automatic_blocking"] is False


def test_offline_recovery_no_auth_cache_or_restored_authority():
    result = matrix_privacy_intelligence.review_matrix_privacy_priorities(recovery_facts={
        "offline_guide_available": True,
        "recovery_walkthrough_tested": False,
    })
    assert by_priority(result)["offline_recovery"]["status"] == "review"
    assert result["data_persisted"] is False
    assert result["credentials_collected"] is False
    assert result["runtime_dispatch_authorised"] is False


def test_complete_self_report_still_unknown_not_certified():
    result = matrix_privacy_intelligence.review_matrix_privacy_priorities(
        device_facts={
            "unknown_tracker_alert": False,
            "unrecognised_app_count": 0,
            "location_permission_count": 0,
            "microphone_permission_count": 0,
            "camera_permission_count": 0,
            "security_updates_current": True,
            "account_mfa_enabled": True,
        },
        identity_facts={
            "unrecognised_signin_alert": False,
            "unexpected_recovery_alert": False,
            "account_mfa_enabled": True,
        },
        network_facts={
            "unexpected_network_change": False,
            "unrecognised_network_count": 0,
            "private_dns_configured": False,
        },
        recovery_facts={
            "offline_guide_available": True,
            "recovery_walkthrough_tested": True,
        },
    )
    rows = by_priority(result)
    assert rows["on_device_privacy_intelligence"]["status"] == "no_flag"
    assert rows["identity_shield"]["status"] == "no_flag"
    assert rows["network_intelligence"]["status"] == "no_flag"
    assert rows["offline_recovery"]["status"] == "no_flag"
    assert rows["evidence_intelligence"]["status"] == "unknown"
    assert rows["governed_worker_automation"]["status"] == "unknown"
    assert result["overall_status"] == "unknown"
    assert result["security_certified"] is False


def test_missing_facts_remain_unknown():
    result = matrix_privacy_intelligence.review_matrix_privacy_priorities(
        identity_facts={"unrecognised_signin_alert": False},
        network_facts={"unrecognised_network_count": 0},
        recovery_facts={"offline_guide_available": True},
    )
    rows = by_priority(result)
    assert all(rows[name]["status"] == "unknown" for name in (
        "identity_shield", "network_intelligence", "offline_recovery"
    ))


@pytest.mark.parametrize("field,facts", [
    ("identity_facts", {"session_cookie": "top-secret"}),
    ("identity_facts", {"unrecognised_signin_alert": "yes"}),
    ("identity_facts", {"account_mfa_enabled": 1}),
    ("identity_facts", {"unrecognised_signin_alert": 2}),
    ("network_facts", {"ip_address": "192.0.2.1"}),
    ("network_facts", {"unrecognised_network_count": -1}),
    ("network_facts", {"unrecognised_network_count": True}),
    ("network_facts", {"unrecognised_network_count": 1001}),
    ("network_facts", {"private_dns_configured": "yes"}),
    ("recovery_facts", {"recovery_code": "keep-private"}),
    ("recovery_facts", {"offline_guide_available": 1}),
    ("device_facts", {"raw_gps_history": "private"}),
])
def test_biometrics_credentials_and_unbounded_fields_are_rejected(field, facts):
    with pytest.raises(ValueError):
        matrix_privacy_intelligence.review_matrix_privacy_priorities(**{field: facts})


@pytest.mark.parametrize("field", [
    "identity_facts", "network_facts", "recovery_facts", "device_facts",
])
def test_invalid_non_mapping_input_rejected(field):
    with pytest.raises(TypeError):
        matrix_privacy_intelligence.review_matrix_privacy_priorities(**{field: ["not a mapping"]})


def test_no_sensitive_field_names_or_values_returned():
    result = matrix_privacy_intelligence.review_matrix_privacy_priorities(
        identity_facts={"unrecognised_signin_alert": True},
        network_facts={"unrecognised_network_count": 1},
    )
    printed = str(result)
    assert "unrecognised_signin_alert" not in printed
    assert "unrecognised_network_count" not in printed
    assert "session_cookie" not in printed
    assert result["gps_history_collected"] is False
    assert result["biometric_templates_collected"] is False


def test_worker_preflight_never_turns_into_execution_even_if_policy_changes(monkeypatch):
    monkeypatch.setattr(
        matrix_privacy_intelligence.autonomy_levels, "evaluate_runtime_job",
        lambda job_type: {"allowed": True, "reason": "allowed"},
    )
    result = matrix_privacy_intelligence.review_matrix_privacy_priorities()
    preflight = by_priority(result)["governed_worker_automation"]
    assert preflight["policy_allowed"] is True
    assert preflight["dispatch_authorised"] is False
    assert preflight["job_enqueued"] is False
    assert preflight["worker_launched"] is False
    assert result["runtime_dispatch_authorised"] is False
    assert result["permissions_expanded"] is False
