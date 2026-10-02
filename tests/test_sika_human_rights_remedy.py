from mission_control import sika_human_rights_gate, sika_human_rights_remedy


def test_schema_persists_reviews_and_appeals():
    sql = "\n".join(sika_human_rights_remedy.SCHEMA_STATEMENTS)
    assert "oap_sika_human_rights_reviews" in sql
    assert "oap_sika_human_rights_appeals" in sql
    assert "'OPEN','IN_REVIEW','UPHELD','REMEDIED','CLOSED'" in sql


def test_open_appeal_requires_human_review():
    appeal = sika_human_rights_remedy.HumanRightsAppeal(
        appeal_id="a-1",
        review_id="r-1",
        subject_reference="subject-1",
        status="OPEN",
        owner_reference=None,
        appeal_reason="incorrect restriction",
    )
    assert appeal.human_review_required is True


def test_review_contract_can_be_persisted_without_execution_claim():
    review = sika_human_rights_gate.review(
        action_type="ACCOUNT_FREEZE",
        subject_reference="subject-1",
        evidence_reference="evidence-1",
        reason_code="fraud_review",
        privacy_minimised=True,
        non_discrimination_reviewed=True,
        accessibility_considered=True,
        explanation_available=True,
        remedy_available=True,
    )
    assert review.may_enter_human_financial_review is True
    assert review.money_moved is False


def test_status_preserves_legal_and_execution_boundaries():
    status = sika_human_rights_remedy.status()
    assert status["durable_review_receipts"] is True
    assert status["durable_appeals"] is True
    assert status["automatic_reversal"] is False
    assert status["creates_legal_entitlement"] is False
    assert status["overrides_applicable_law"] is False
    assert status["money_movement"] is False
