from mission_control import sika_human_rights, sika_rights_decision_record


def _record(**overrides):
    row = {
        "action": "account_freeze",
        "authority_reference": "sika:policy:freeze:001",
        "evidence_reference": "sika:evidence:case:123",
        "scope": "outgoing-payments-only",
        "duration": "24h-review-window",
        "explanation_reference": "sika:notice:reason:456",
        "remedy_reference": "sika:appeal:789",
        "recorded_at": "2026-10-02T18:00:00Z",
        "rights": {key: True for key in sika_human_rights.RIGHTS_DIMENSIONS},
        "less_restrictive_option_considered": True,
        "human_review_required": True,
        "human_approved": True,
    }
    row.update(overrides)
    return row


def test_builds_hash_bound_allow_record_without_execution():
    record = sika_rights_decision_record.build_decision_record(_record())
    assert record["decision"] == "ALLOW"
    assert len(record["gate_decision_hash"]) == 64
    assert len(record["record_hash"]) == 64
    assert record["execution_enabled"] is False
    assert sika_rights_decision_record.verify_decision_record(record)["verified"] is True


def test_tampering_breaks_record_integrity():
    record = sika_rights_decision_record.build_decision_record(_record())
    record["scope"] = "full-account"
    check = sika_rights_decision_record.verify_decision_record(record)
    assert check["verified"] is False


def test_review_record_never_reports_execution_ready():
    record = sika_rights_decision_record.build_decision_record(
        _record(human_approved=False)
    )
    gate = sika_rights_decision_record.execution_gate(record)
    assert record["decision"] == "REVIEW"
    assert gate["ready"] is False
    assert gate["execution_enabled"] is False
    assert gate["reason"] == "rights_gate_not_allow"


def test_allow_record_is_ready_for_external_authorized_executor_only():
    record = sika_rights_decision_record.build_decision_record(_record())
    gate = sika_rights_decision_record.execution_gate(record)
    assert gate["ready"] is True
    assert gate["execution_enabled"] is False
    assert gate["requires_external_authorized_executor"] is True
    assert gate["human_authority_final"] is True


def test_failed_right_blocks_and_remains_non_executable():
    rights = {key: True for key in sika_human_rights.RIGHTS_DIMENSIONS}
    rights["privacy"] = False
    record = sika_rights_decision_record.build_decision_record(_record(rights=rights))
    gate = sika_rights_decision_record.execution_gate(record)
    assert record["decision"] == "BLOCK"
    assert "rights_check_failed:privacy" in record["reasons"]
    assert gate["ready"] is False
    assert gate["execution_enabled"] is False


def test_status_preserves_truth_boundary():
    state = sika_rights_decision_record.status()
    assert state["hash_bound"] is True
    assert state["gate_hash_bound"] is True
    assert state["execution_enabled"] is False
    assert state["requires_external_authorized_executor"] is True
    assert state["human_authority_final"] is True
