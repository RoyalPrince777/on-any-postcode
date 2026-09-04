from __future__ import annotations

import pytest

from mission_control import live_brain, smi_capabilities
from oap.smi.sovereign_controls import (
    SovereignControlPlane,
    SovereignControlViolation,
)


def _valid_execution_kwargs() -> dict[str, object]:
    return {
        "action_type": "github.pr.create",
        "is_human_authority": True,
        "authority_level": 0,
        "signed_receipt": True,
        "exact_action_digest": True,
        "receipt_unconsumed": True,
        "audit_ready": True,
    }


def test_sovereign_policy_is_fail_closed_and_adds_no_brain(monkeypatch):
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    controls = SovereignControlPlane()
    status = controls.status()
    policy = controls.policy()

    assert status["ready"] is True
    assert status["brain_count"] == 0
    assert status["execution_enabled"] is True
    assert status["external_provider_egress_default"] == "deny"
    assert status["secret_export"] is False
    assert status["direct_main_write"] is False
    assert status["production_database_mutation"] is False
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["human_authority_final"] is True
    assert policy["default_execution"] == "deny"
    assert policy["signed_approval_receipt_required"] is True
    assert policy["exact_action_digest_required"] is True
    assert policy["single_use_receipt_required"] is True
    assert policy["append_only_audit_required"] is True


def test_sovereign_execution_gate_allows_only_exact_governed_path(monkeypatch):
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    controls = SovereignControlPlane()

    review = controls.require_execution(**_valid_execution_kwargs())

    assert review["allowed"] is True
    assert review["failed_checks"] == ()
    assert review["human_authority_final"] is True


@pytest.mark.parametrize(
    ("field", "value", "expected_failure"),
    (
        ("action_type", "render.deploy", "action_allowlisted"),
        ("is_human_authority", False, "human_authority"),
        ("authority_level", 5, "authority_level_zero"),
        ("signed_receipt", False, "signed_receipt"),
        ("exact_action_digest", False, "exact_action_digest"),
        ("receipt_unconsumed", False, "receipt_unconsumed"),
        ("audit_ready", False, "audit_ready"),
    ),
)
def test_sovereign_execution_gate_fails_closed(
    monkeypatch,
    field: str,
    value: object,
    expected_failure: str,
):
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    kwargs = _valid_execution_kwargs()
    kwargs[field] = value

    review = SovereignControlPlane().execution_review(**kwargs)

    assert review["allowed"] is False
    assert expected_failure in review["failed_checks"]


def test_emergency_halt_blocks_even_an_otherwise_valid_execution(monkeypatch):
    monkeypatch.setenv("OAP_SOVEREIGN_HALT", "true")
    controls = SovereignControlPlane()

    with pytest.raises(SovereignControlViolation, match="emergency_halt_clear"):
        controls.require_execution(**_valid_execution_kwargs())

    assert controls.status()["emergency_halt_active"] is True
    assert controls.status()["execution_enabled"] is False


def test_external_provider_egress_defaults_to_deny(monkeypatch):
    monkeypatch.delenv("OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST", raising=False)
    controls = SovereignControlPlane()

    assert controls.provider_allowed("ollama", local=True) is True
    assert controls.provider_allowed("openai", local=False) is False

    monkeypatch.setenv("OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST", "openai")
    assert controls.provider_allowed("openai", local=False) is True


def test_policy_fingerprint_is_stable_for_locked_policy(monkeypatch):
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    controls = SovereignControlPlane()

    first = controls.policy_fingerprint()
    second = controls.policy_fingerprint()

    assert len(first) == 64
    assert first == second


def test_smi_registry_keeps_seven_worlds_and_registers_sovereign_controls():
    validation = smi_capabilities.validate_smi_capabilities()
    status = smi_capabilities.smi_capability_status()

    assert validation["passed"] is True
    assert validation["checks"]["intelligence_worlds"] == 7
    assert validation["checks"]["brain_count_added_by_sovereign_controls"] == 0
    assert validation["checks"]["external_provider_egress_default"] == "deny"
    assert status["sovereign_controls"]["human_authority_final"] is True
    assert status["independent_execution"] is False


def test_live_smi_review_exposes_sovereign_controls_without_execution(monkeypatch):
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    result = live_brain.review(
        request_id="sovereign-live-1",
        identity_id="00000000-0000-0000-0000-000000000001",
        content="Review the sovereign control architecture.",
        history=[],
        image_attached=False,
        authority_context={
            "authority_level": 0,
            "permissions": (
                "REQUEST_RECOMMENDATION",
                "APPROVE_RECOMMENDATION",
            ),
            "is_human_authority": True,
        },
    )

    assert result["sovereign_controls"]["ready"] is True
    assert result["sovereign_controls"]["brain_count"] == 0
    assert "SOVEREIGN_CONTROLS_REVIEWED" in result["processing_states"]
    assert result["can_execute"] is False
    assert result["human_authority_final"] is True
