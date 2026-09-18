from __future__ import annotations

from mission_control import a6_matrix_execution, autonomy_levels


def test_a6_operation_policy_requires_all_controls(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A6")
    monkeypatch.setattr(autonomy_levels, "A6_ENABLED", True)
    monkeypatch.setattr(autonomy_levels, "A6_MATRIX_CONTROL", True)

    allowed = autonomy_levels.evaluate_a6_operation(
        "ROUTE_MATRIX_CAPTURE",
        founder_approved=True,
        guardian_pass=True,
        green_gate_pass=True,
        rollback_proven=True,
        receipt_chain_ready=True,
        matrix_precheck_pass=True,
    )
    assert allowed["allowed"] is True
    assert allowed["matrix_postcheck_required"] is True
    assert allowed["human_authority_final"] is True

    blocked = autonomy_levels.evaluate_a6_operation(
        "ROUTE_MATRIX_CAPTURE",
        founder_approved=False,
        guardian_pass=True,
        green_gate_pass=True,
        rollback_proven=True,
        receipt_chain_ready=True,
        matrix_precheck_pass=True,
    )
    assert blocked["allowed"] is False
    assert blocked["reason"] == "operation_governance_incomplete"


def test_a6_forbidden_operation_is_not_allowlisted(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A6")
    monkeypatch.setattr(autonomy_levels, "A6_ENABLED", True)
    monkeypatch.setattr(autonomy_levels, "A6_MATRIX_CONTROL", True)

    result = autonomy_levels.evaluate_a6_operation(
        "MONEY_OR_VALUE_TRANSFER",
        founder_approved=True,
        guardian_pass=True,
        green_gate_pass=True,
        rollback_proven=True,
        receipt_chain_ready=True,
        matrix_precheck_pass=True,
    )
    assert result["allowed"] is False
    assert result["reason"] == "action_not_a6_allowlist"
    assert result["forbidden_domain_bypass_allowed"] is False


def test_a6_matrix_gate_requires_proven_readiness(monkeypatch):
    monkeypatch.setattr(
        a6_matrix_execution.autonomy_levels,
        "status",
        lambda: {
            "a6_enabled": True,
            "a6_matrix_control": True,
            "configured_level": "A6",
            "a6_execution_actions": ("ROUTE_MATRIX_CAPTURE",),
            "forbidden_domains": (),
        },
    )
    monkeypatch.setattr(
        a6_matrix_execution.a7_certification,
        "status",
        lambda: {"a6_proof_complete": False},
    )
    monkeypatch.setattr(
        a6_matrix_execution.matrix_signal_bus,
        "topology",
        lambda: {
            "registered_count": len(
                a6_matrix_execution.matrix_signal_bus.CORE_MATRIX_ORDER
            ),
            "final_authority": "Human Authority",
            "protector": "Guardian",
            "proof_gate": "Green Gate",
        },
    )
    result = a6_matrix_execution.status()
    assert result["enabled"] is False
    assert result["a6_readiness_proven"] is False


def test_a6_postcheck_halts_on_failed_receipt(monkeypatch):
    monkeypatch.setattr(
        a6_matrix_execution.matrix_signal_bus,
        "route_signal",
        lambda **kwargs: {"signal_id": "TEST", **kwargs},
    )
    result = a6_matrix_execution.postcheck(
        "ROUTE_MATRIX_CAPTURE",
        operation_succeeded=True,
        rollback_still_available=True,
        receipt_recorded=False,
    )
    assert result["passed"] is False
    assert result["rollback_required"] is True
    assert result["halt_further_execution"] is True
