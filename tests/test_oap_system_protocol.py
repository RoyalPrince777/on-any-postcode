from mission_control.hrm_agent_lifecycle import ReviewDepth
from mission_control.oap_system_protocol import (
    CANONICAL_FLOW,
    ExecutionPath,
    ProtocolLayer,
    agent_handoff,
    choose_protocol,
)


def test_canonical_protocol_contains_all_governed_layers():
    assert CANONICAL_FLOW == (
        ProtocolLayer.SIGNAL,
        ProtocolLayer.OMNI,
        ProtocolLayer.SMI,
        ProtocolLayer.HYBRID,
        ProtocolLayer.CIVILISATION,
        ProtocolLayer.GUARDIAN,
        ProtocolLayer.HRM,
    )


def test_low_risk_protocol_uses_quick_review():
    decision = choose_protocol("inspect system health", risk="low")
    assert decision.review_depth is ReviewDepth.QUICK
    assert decision.human_authority_required is False
    assert decision.fail_closed is False


def test_high_risk_protocol_escalates_to_full_human_gate():
    decision = choose_protocol("change authority", risk="high")
    assert decision.review_depth is ReviewDepth.FULL
    assert decision.human_authority_required is True
    assert ExecutionPath.HUMAN_AUTHORITY in decision.execution_paths


def test_external_action_without_proven_path_routes_to_human_authority():
    decision = choose_protocol("deploy", external_action=True)
    assert decision.human_authority_required is True
    assert decision.execution_paths == (ExecutionPath.HUMAN_AUTHORITY,)
    assert decision.review_depth is ReviewDepth.FULL


def test_private_data_without_permitted_path_fails_closed():
    decision = choose_protocol("inspect private record", private_data=True)
    assert decision.fail_closed is True
    assert decision.reason == "private_data_path_not_proven"


def test_agent_handoff_never_transfers_authority():
    signal = agent_handoff("Octopus", "Spider", "trace dependency", permitted_evidence=("service graph",))
    assert signal["status"] == "READY"
    assert signal["authority_transferred"] is False
    assert signal["hrm_receipt_required"] is True


def test_invalid_agent_handoff_locks():
    signal = agent_handoff("", "Spider", "trace dependency")
    assert signal["status"] == "LOCKED"
