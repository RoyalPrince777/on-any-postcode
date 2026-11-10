from mission_control import sika_human_rights


def _record(**overrides):
    row = {
        "action": "account_freeze",
        "authority_reference": "sika:policy:freeze:001",
        "evidence_reference": "sika:evidence:case:123",
        "scope": "outgoing-payments-only",
        "duration": "24h-review-window",
        "explanation_reference": "sika:notice:reason:456",
        "remedy_reference": "sika:appeal:789",
        "recorded_at": "2026-10-02T17:30:00Z",
        "rights": {
            key: True for key in sika_human_rights.RIGHTS_DIMENSIONS
        },
        "less_restrictive_option_considered": True,
        "human_review_required": True,
        "human_approved": True,
    }
    row.update(overrides)
    return row


def test_all_controls_pass_allows_without_claiming_legal_authority():
    result = sika_human_rights.evaluate_rights_gate(_record())
    assert result["decision"] == "ALLOW"
    assert result["human_authority_final"] is True
    assert result["automatic_confiscation_enabled"] is False
    assert result["automatic_permanent_blacklist_enabled"] is False
    assert result["legal_compliance_verified_by_software"] is False
    assert result["regulatory_authorization_inferred"] is False
    assert len(result["decision_hash"]) == 64


def test_failed_rights_dimension_blocks():
    rights = {key: True for key in sika_human_rights.RIGHTS_DIMENSIONS}
    rights["property"] = False
    result = sika_human_rights.evaluate_rights_gate(_record(rights=rights))
    assert result["decision"] == "BLOCK"
    assert "rights_check_failed:property" in result["reasons"]


def test_missing_human_approval_requires_review_when_required():
    result = sika_human_rights.evaluate_rights_gate(
        _record(human_review_required=True, human_approved=False)
    )
    assert result["decision"] == "REVIEW"
    assert "human_approval_missing" in result["reasons"]


def test_less_restrictive_option_must_be_considered():
    result = sika_human_rights.evaluate_rights_gate(
        _record(less_restrictive_option_considered=False)
    )
    assert result["decision"] == "REVIEW"
    assert "less_restrictive_option_not_considered" in result["reasons"]


def test_hash_changes_when_rights_record_changes():
    first = sika_human_rights.evaluate_rights_gate(_record(scope="payments"))
    second = sika_human_rights.evaluate_rights_gate(_record(scope="full-account"))
    assert first["decision_hash"] != second["decision_hash"]


def test_status_keeps_truth_mode_boundaries():
    state = sika_human_rights.status()
    assert state["human_authority_final"] is True
    assert state["fails_closed_to_review"] is True
    assert state["automatic_confiscation_enabled"] is False
    assert state["legal_compliance_verified_by_software"] is False
