from mission_control import sika_reconciliation_exception_store


def test_schema_persists_exception_ownership_and_resolution_state():
    sql = "\n".join(sika_reconciliation_exception_store.SCHEMA_STATEMENTS)
    assert "owner_reference TEXT" in sql
    assert "'OPEN','IN_REVIEW','RESOLVED','CLOSED'" in sql
    assert "'PENDING','MISMATCH','EXCEPTION'" in sql


def test_open_exception_requires_human_review():
    case = sika_reconciliation_exception_store.ReconciliationException(
        exception_id="ex-1",
        payment_id="pay-1",
        provider_id="provider-1",
        provider_reference="ref-1",
        reconciliation_state="MISMATCH",
        owner_reference=None,
        resolution_status="OPEN",
        resolution_note=None,
        evidence_hash="hash",
    )
    assert case.human_review_required is True


def test_status_keeps_exception_store_non_executing():
    status = sika_reconciliation_exception_store.status()
    assert status["persistent_exception_cases"] is True
    assert status["owner_assignment_supported"] is True
    assert status["automatic_retry"] is False
    assert status["journal_mutation"] is False
    assert status["provider_calling"] is False
    assert status["money_movement"] is False
