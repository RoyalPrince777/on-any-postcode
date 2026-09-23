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


def test_learning_without_reviewed_outcome_ref_has_no_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_write(*args, **kwargs):
        raise AssertionError("Missing review must not write a receipt")

    monkeypatch.setattr(rsi.smi_receipt_backend, "write_receipt", unexpected_write)
    with pytest.raises(ValueError, match="Reviewed outcome reference"):
        rsi.record_learning(
            _proposal(),
            outcome="not reviewed",
            before_state="before",
            after_state="after",
            lesson="unreviewed lesson",
            tests_passed=True,
            rollback_available=True,
        )


def test_sqlite_success_cannot_be_accepted_as_durable_learning(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OAP_SMI_RECEIPT_DB_PATH", str(tmp_path / "local.sqlite3"))
    result = rsi.record_learning(
        _proposal(),
        outcome="fallback design reviewed",
        before_state="single path",
        after_state="bounded fallback proposed",
        lesson="Prove fallback resilience.",
        tests_passed=True,
        rollback_available=True,
        reviewed_outcome_ref="war-room-review-001",
    )
    assert result["state"] == "durable_learning_unproven"
    assert result["matrix_update_allowed"] is False
    assert result["receipt"]["read_back_ok"] is False
    assert result["receipt"]["durable"] is False
    assert result["receipt"]["status"] == "blocked_durable_hrm_unconfigured"
    assert result["execution_granted"] is False
    assert result["full_green"] is False


@pytest.mark.parametrize(
    "receipt",
    [
        {"ok": True, "read_back_ok": True, "durable": False, "fallback_used": False, "receipt_kind": "matrix_learning_receipt"},
        {"ok": True, "read_back_ok": False, "durable": True, "fallback_used": False, "receipt_kind": "matrix_learning_receipt"},
        {"ok": True, "read_back_ok": True, "durable": True, "fallback_used": True, "receipt_kind": "matrix_learning_receipt"},
        {"ok": True, "read_back_ok": True, "durable": True, "fallback_used": False, "receipt_kind": "war_room_live_proof_receipt"},
        {"ok": False, "read_back_ok": True, "durable": True, "fallback_used": False, "receipt_kind": "matrix_learning_receipt"},
    ],
)
def test_insufficient_learning_receipts_fail_closed(
    monkeypatch: pytest.MonkeyPatch, receipt: dict[str, object]
) -> None:
    monkeypatch.setattr(
        rsi.smi_receipt_backend,
        "write_receipt",
        lambda *args, **kwargs: receipt,
    )
    result = rsi.record_learning(
        _proposal(),
        outcome="reviewed",
        before_state="before",
        after_state="after",
        lesson="preserve recovery",
        tests_passed=True,
        rollback_available=True,
        reviewed_outcome_ref="war-room-review-002",
    )
    assert result["matrix_update_allowed"] is False
    assert result["state"] == "durable_learning_unproven"
    assert result["full_green"] is False


def test_durable_receipt_is_required_but_never_grants_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests = []

    def durable_write(kind, payload, *, require_durable=False):
        requests.append((kind, payload, require_durable))
        return {
            "ok": True,
            "read_back_ok": True,
            "durable": True,
            "fallback_used": False,
            "receipt_kind": "matrix_learning_receipt",
        }

    monkeypatch.setattr(rsi.smi_receipt_backend, "write_receipt", durable_write)
    result = rsi.record_learning(
        _proposal(),
        outcome="reviewed",
        before_state="before",
        after_state="after",
        lesson="preserve recovery",
        tests_passed=True,
        rollback_available=True,
        reviewed_outcome_ref="war-room-review-003",
    )
    assert len(requests) == 1
    assert requests[0][0] == "matrix_learning_receipt"
    assert requests[0][1]["safe_payload"]["reviewed_outcome_ref"] == "war-room-review-003"
    assert requests[0][2] is True
    assert result["state"] == "learning_recorded"
    assert result["matrix_update_allowed"] is True
    assert result["authority_changed"] is False
    assert result["permissions_changed"] is False
    assert result["execution_granted"] is False
    assert result["full_green"] is False
