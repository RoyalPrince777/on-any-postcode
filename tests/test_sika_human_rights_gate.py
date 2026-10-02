import pytest

from mission_control import sika_human_rights_gate


def _review(**overrides):
    values = {
        "action_type": "ACCOUNT_FREEZE",
        "subject_reference": "acct-1",
        "evidence_reference": "evidence-1",
        "reason_code": "risk_review",
        "privacy_minimised": True,
        "non_discrimination_reviewed": True,
        "accessibility_considered": True,
        "explanation_available": True,
        "remedy_available": True,
    }
    values.update(overrides)
    return sika_human_rights_gate.review(**values)


def test_complete_rights_review_passes_only_to_human_review():
    result = _review()
    assert result.state == "PASS_TO_HUMAN_REVIEW"
    assert result.may_enter_human_financial_review is True
    assert result.human_review_required is True
    assert result.money_moved is False


@pytest.mark.parametrize(
    "field",
    [
        "privacy_minimised",
        "non_discrimination_reviewed",
        "accessibility_considered",
        "explanation_available",
        "remedy_available",
    ],
)
def test_missing_rights_control_holds_action(field):
    result = _review(**{field: False})
    assert result.state == "HOLD"
    assert result.may_enter_human_financial_review is False
    assert result.money_moved is False


def test_unsupported_action_fails_closed():
    with pytest.raises(
        sika_human_rights_gate.HumanRightsGateError,
        match="unsupported_consequential_action",
    ):
        _review(action_type="AUTO_CONFISCATE")


def test_status_does_not_claim_legal_entitlement_or_execution():
    status = sika_human_rights_gate.status()
    assert status["creates_legal_entitlement"] is False
    assert status["overrides_applicable_law"] is False
    assert status["automated_punishment"] is False
    assert status["financial_execution"] is False
    assert status["money_movement"] is False
    assert status["human_authority_final"] is True
