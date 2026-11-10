from mission_control import sika_payment_disputes


def test_dispute_schema_has_append_only_event_trigger():
    sql = "\n".join(sika_payment_disputes.SCHEMA_STATEMENTS)
    assert "oap_sika_payment_dispute_events" in sql
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "dispute_event_append_only" in sql


def test_dispute_status_keeps_case_system_non_executing():
    status = sika_payment_disputes.status()
    assert status["persistent_dispute_cases"] is True
    assert status["append_only_chronology"] is True
    assert status["external_chargeback_filing"] is False
    assert status["liability_decision"] is False
    assert status["money_movement"] is False
