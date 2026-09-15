from __future__ import annotations

import pytest

from mission_control import recursive_self_improvement as rsi


def _observation(domain: str = "reliability") -> dict[str, object]:
    return {
        "domain": domain,
        "problem": "One dependency can interrupt the evidence path",
        "evidence": ("dependency-map", "failure-test"),
        "metric": "recovery_path_count",
        "current_value": 1,
        "target_value": 2,
        "severity": "high",
    }


def _proposal(*, consequential: bool = False) -> dict[str, object]:
    return rsi.propose_improvement(
        _observation(),
        recommendation="Add a bounded fallback and prove failover before promotion.",
        rollback="Remove the fallback and restore the previous dependency path.",
        tests=("primary path remains green", "fallback recovers without authority drift"),
        consequential=consequential,
    )


def test_status_keeps_recursive_improvement_bounded() -> None:
    result = rsi.status()

    assert result["mode"] == "governed_learning_loop"
    assert result["human_authority"] == "final"
    assert result["execution_granted"] is False
    assert result["self_approval_allowed"] is False
    assert result["permission_change_allowed"] is False
    assert result["authority_growth_allowed"] is False
    assert result["automatic_deploy_allowed"] is False
    assert result["full_green"] is False


def test_proposal_routes_through_matrix_without_execution() -> None:
    result = _proposal()
    signal = result["matrix_signal"]

    assert result["matrix_lead"] == "Neo"
    assert signal["sender"] == "Neo"
    assert signal["recipients"] == ("Trinity", "SMI")
    assert "Matrix System" in signal["delivery_path"]
    assert result["execution_granted"] is False
    assert result["external_action_taken"] is False
    assert result["self_approval_allowed"] is False
    assert result["automatic_deploy_allowed"] is False


def test_protected_authority_domains_cannot_enter_self_improvement() -> None:
    for domain in rsi.FORBIDDEN_SELF_CHANGE_DOMAINS:
        with pytest.raises(ValueError, match="protected domain"):
            rsi.propose_improvement(
                _observation(domain),
                recommendation="Change protected authority.",
                rollback="Restore it.",
                tests=("test",),
            )


def test_consequential_change_requires_war_room_and_human_authority() -> None:
    proposal = _proposal(consequential=True)

    blocked = rsi.review_gate(
        proposal,
        guardian_pass=True,
        war_room_reviewed=False,
        human_authority_approved=False,
        rollback_ready=True,
        tests_defined=True,
    )
    assert blocked["ready_for_separate_builder_path"] is False
    assert blocked["execution_granted"] is False

    reviewed = rsi.review_gate(
        proposal,
        guardian_pass=True,
        war_room_reviewed=True,
        human_authority_approved=True,
        rollback_ready=True,
        tests_defined=True,
    )
    assert reviewed["ready_for_separate_builder_path"] is True
    assert reviewed["builder_may_be_requested"] is True
    assert reviewed["execution_granted"] is False
    assert reviewed["automatic_deploy_allowed"] is False


def test_learning_uses_existing_matrix_receipt_backend(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "OAP_SMI_RECEIPT_DB_PATH",
        str(tmp_path / "recursive-learning.sqlite3"),
    )
    proposal = _proposal()

    result = rsi.record_learning(
        proposal,
        outcome="fallback design reviewed",
        before_state="single evidence path",
        after_state="bounded fallback proposed",
        lesson="Resilience needs an independently provable recovery path.",
        tests_passed=True,
        rollback_available=True,
    )

    assert result["state"] == "learning_recorded"
    assert result["receipt"]["receipt_kind"] == "matrix_learning_receipt"
    assert result["receipt"]["read_back_ok"] is True
    assert result["matrix_update_allowed"] is True
    assert result["authority_changed"] is False
    assert result["permissions_changed"] is False
    assert result["execution_granted"] is False
    assert result["full_green"] is False
