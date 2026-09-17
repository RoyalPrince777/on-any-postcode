import pytest

from oap.smi.runtime_guard import (
    MAX_CHAIN_DEPTH,
    MAX_RETRIES,
    RuntimeGuardViolation,
    WorkBudget,
    assert_no_authority_growth,
    bounded_control_proof,
    validate_action_payload,
)


def test_bounded_control_proof_blocks_all_targeted_threats():
    proof = bounded_control_proof()
    assert proof["passed"] is True
    assert proof["duplicate_blocked"] is True
    assert proof["recursion_blocked"] is True
    assert proof["retry_blocked"] is True
    assert proof["escalation_blocked"] is True
    assert proof["protected_payload_blocked"] is True
    assert proof["production_state_mutated"] is False
    assert proof["execution_authority_expanded"] is False
    assert proof["human_authority_final"] is True


def test_work_budget_blocks_duplicate_recursion_and_retry_overflow():
    budget = WorkBudget("test")
    budget.admit(depth=1, retry=0, idempotency_key="job-1")

    with pytest.raises(RuntimeGuardViolation, match="duplicate_work_blocked"):
        budget.admit(depth=1, retry=0, idempotency_key="job-1")

    with pytest.raises(RuntimeGuardViolation, match="recursion_depth_blocked"):
        budget.admit(
            depth=MAX_CHAIN_DEPTH + 1,
            retry=0,
            idempotency_key="job-2",
        )

    with pytest.raises(RuntimeGuardViolation, match="retry_budget_exceeded"):
        budget.admit(
            depth=1,
            retry=MAX_RETRIES + 1,
            idempotency_key="job-3",
        )


def test_permission_growth_and_protected_payloads_fail_closed():
    with pytest.raises(RuntimeGuardViolation, match="authority_level_escalation_blocked"):
        assert_no_authority_growth(
            {"authority_level": 2, "permissions": ("read",)},
            {"authority_level": 1, "permissions": ("read",)},
        )

    with pytest.raises(RuntimeGuardViolation, match="permission_expansion_blocked"):
        assert_no_authority_growth(
            {"authority_level": 2, "permissions": ("read",)},
            {"authority_level": 2, "permissions": ("read", "deploy")},
        )

    with pytest.raises(RuntimeGuardViolation, match="protected_key_blocked:permissions"):
        validate_action_payload({"nested": {"permissions": ["deploy"]}})
