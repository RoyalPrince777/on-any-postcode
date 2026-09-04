from __future__ import annotations

import pytest

from mission_control import live_brain, smi_capabilities
from oap.contracts import BrainRequest, ProviderResult
from oap.nexus import NexusRouter
from oap.smi.input_manager import InputManager
from oap.smi.providers import ProviderRouter
from oap.smi.sovereign_controls import (
    SovereignControlPlane,
    SovereignControlViolation,
)

MASTER_EVIDENCE_ENV = (
    "OAP_SOVEREIGN_KEYS_LOCAL",
    "OAP_SOVEREIGN_DATA_SELF_HOSTED",
    "OAP_SOVEREIGN_MODEL_LOCAL",
    "OAP_SOVEREIGN_SOURCE_SELF_HOSTED",
    "OAP_SOVEREIGN_INFRA_SELF_HOSTED",
    "OAP_SOVEREIGN_NETWORK_EGRESS_CONTROLLED",
    "OAP_SOVEREIGN_RECOVERY_PROVEN",
    "OAP_SOVEREIGN_OBSERVABILITY_FIRST_PARTY",
    "OAP_SOVEREIGN_SUPPLY_CHAIN_ATTESTED",
)


def _clear_master(monkeypatch) -> None:
    monkeypatch.delenv("OAP_MASTER_SOVEREIGN_MODE", raising=False)
    for name in MASTER_EVIDENCE_ENV:
        monkeypatch.delenv(name, raising=False)


def _attest_master(monkeypatch) -> None:
    monkeypatch.setenv("OAP_MASTER_SOVEREIGN_MODE", "true")
    for name in MASTER_EVIDENCE_ENV:
        monkeypatch.setenv(name, "true")


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
    _clear_master(monkeypatch)
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    controls = SovereignControlPlane()
    status = controls.status()
    policy = controls.policy()

    assert status["ready"] is True
    assert status["brain_count"] == 0
    assert status["execution_enabled"] is True
    assert status["policy_version"] == "smi-master-sovereignty-v2"
    assert status["external_provider_egress_default"] == "deny"
    assert status["master_mode_external_provider_egress"] == "local_only"
    assert status["secret_export"] is False
    assert status["direct_main_write"] is False
    assert status["production_database_mutation"] is False
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["human_authority_final"] is True
    assert status["master_full_sovereignty_active"] is False
    assert status["full_sovereignty_claim"] is False
    assert status["sovereignty_grade"] == "CONTROLLED_HOSTED_OR_UNPROVEN"
    assert policy["default_execution"] == "deny"
    assert policy["signed_approval_receipt_required"] is True
    assert policy["exact_action_digest_required"] is True
    assert policy["single_use_receipt_required"] is True
    assert policy["append_only_audit_required"] is True
    assert policy["master_full_sovereignty_is_evidence_based"] is True


def test_master_full_sovereignty_requires_every_runtime_attestation(monkeypatch):
    _clear_master(monkeypatch)
    controls = SovereignControlPlane()
    default = controls.master_attestation()

    assert default["architecture_ready"] is True
    assert default["runtime_ready"] is False
    assert default["active"] is False
    assert default["runtime_gap_count"] == len(MASTER_EVIDENCE_ENV)
    assert default["full_sovereignty_claim"] is False

    _attest_master(monkeypatch)
    attested = controls.master_attestation()
    status = controls.status()

    assert attested["runtime_ready"] is True
    assert attested["active"] is True
    assert attested["runtime_gap_count"] == 0
    assert status["master_full_sovereignty_active"] is True
    assert status["full_sovereignty_claim"] is True
    assert status["sovereignty_grade"] == "MASTER_FULL"


def test_master_mode_requested_without_proof_fails_closed_for_execution(monkeypatch):
    _clear_master(monkeypatch)
    monkeypatch.setenv("OAP_MASTER_SOVEREIGN_MODE", "true")
    controls = SovereignControlPlane()

    review = controls.execution_review(**_valid_execution_kwargs())

    assert review["allowed"] is False
    assert "master_sovereignty_ready_if_requested" in review["failed_checks"]
    assert review["master_mode_requested"] is True
    assert review["master_sovereignty_active"] is False


def test_sovereign_execution_gate_allows_exact_governed_path(monkeypatch):
    _clear_master(monkeypatch)
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
    _clear_master(monkeypatch)
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    kwargs = _valid_execution_kwargs()
    kwargs[field] = value

    review = SovereignControlPlane().execution_review(**kwargs)

    assert review["allowed"] is False
    assert expected_failure in review["failed_checks"]


def test_emergency_halt_blocks_even_an_otherwise_valid_execution(monkeypatch):
    _clear_master(monkeypatch)
    monkeypatch.setenv("OAP_SOVEREIGN_HALT", "true")
    controls = SovereignControlPlane()

    with pytest.raises(SovereignControlViolation, match="emergency_halt_clear"):
        controls.require_execution(**_valid_execution_kwargs())

    assert controls.status()["emergency_halt_active"] is True
    assert controls.status()["execution_enabled"] is False


def test_external_provider_egress_defaults_to_deny(monkeypatch):
    _clear_master(monkeypatch)
    monkeypatch.delenv("OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST", raising=False)
    controls = SovereignControlPlane()

    assert controls.provider_allowed("ollama", local=True) is True
    assert controls.provider_allowed("openai", local=False) is False

    monkeypatch.setenv("OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST", "openai")
    assert controls.provider_allowed("openai", local=False) is True


def test_master_mode_is_local_only_even_if_external_provider_is_allowlisted(monkeypatch):
    _attest_master(monkeypatch)
    monkeypatch.setenv("OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST", "openai")
    controls = SovereignControlPlane()

    assert controls.provider_allowed("ollama", local=True) is True
    assert controls.provider_allowed("openai", local=False) is False


def test_provider_router_blocks_external_adapter_until_allowlisted(monkeypatch):
    class ExternalProvider:
        provider_id = "external-test"
        sovereign_scope = "external"

        def analyse(self, signal):
            return ProviderResult(
                provider_id=self.provider_id,
                available=True,
                text=f"External advisory for {signal.request_id}",
            )

    signal = InputManager().receive(
        NexusRouter().receive(
            BrainRequest(
                request_id="sovereign-provider-1",
                identity_id="founder-1",
                content="Review provider sovereignty.",
                task_type="ARCHITECTURE",
            )
        )
    )
    router = ProviderRouter(
        adapters=(ExternalProvider(),),
        approved_assignments={"architecture": "external-test"},
    )

    _clear_master(monkeypatch)
    monkeypatch.delenv("OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST", raising=False)
    blocked = router.route(signal)[0]
    assert blocked.available is False
    assert blocked.error_code == "sovereign_provider_blocked"

    monkeypatch.setenv(
        "OAP_SOVEREIGN_EXTERNAL_PROVIDER_ALLOWLIST",
        "external-test",
    )
    allowed = router.route(signal)[0]
    assert allowed.available is True
    assert allowed.error_code is None


def test_policy_fingerprint_is_stable_for_locked_policy(monkeypatch):
    _clear_master(monkeypatch)
    controls = SovereignControlPlane()

    first = controls.policy_fingerprint()
    second = controls.policy_fingerprint()

    assert len(first) == 64
    assert first == second


def test_smi_registry_keeps_seven_worlds_and_master_control_boundaries(monkeypatch):
    _clear_master(monkeypatch)
    validation = smi_capabilities.validate_smi_capabilities()
    status = smi_capabilities.smi_capability_status()

    assert validation["passed"] is True
    assert validation["checks"]["intelligence_worlds"] == 7
    assert validation["checks"]["brain_count_added_by_sovereign_controls"] == 0
    assert validation["checks"]["external_provider_egress_default"] == "deny"
    assert validation["checks"]["master_full_sovereignty_active"] is False
    assert status["master_tier_name"] == (
        "Master Full Sovereignty Megaverse Intelligence"
    )
    assert status["sovereign_controls"]["human_authority_final"] is True
    assert status["sovereign_controls"]["full_sovereignty_claim"] is False
    assert status["independent_execution"] is False


def test_live_smi_review_exposes_master_sovereign_controls_without_execution(
    monkeypatch,
):
    _clear_master(monkeypatch)
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    result = live_brain.review(
        request_id="sovereign-live-v2",
        identity_id="00000000-0000-0000-0000-000000000001",
        content="Review the master sovereign control architecture.",
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
    assert result["sovereign_controls"]["policy_version"] == (
        "smi-master-sovereignty-v2"
    )
    assert result["sovereign_controls"]["master_full_sovereignty_active"] is False
    assert result["sovereign_controls"]["full_sovereignty_claim"] is False
    assert "SOVEREIGN_CONTROLS_REVIEWED" in result["processing_states"]
    assert result["can_execute"] is False
    assert result["human_authority_final"] is True
