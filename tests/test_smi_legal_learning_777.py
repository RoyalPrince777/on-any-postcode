"""SMI legal learning 777 evidence and authority regression tests."""
from mission_control.smi_legal_learning_777 import (
    legal_agent_passports, evaluate_legal_source, legal_learning_status
)

def test_twenty_one_distinct_fail_closed_passports():
    agents = legal_agent_passports()
    assert len(agents) == 21
    assert len({a["id"] for a in agents}) == 21
    for a in agents:
        assert a["operational"] is False
        assert a["training_verified"] is False
        assert a["legal_representation_authorised"] is False
        assert a["tax_filing_authorised"] is False
        assert a["external_monitoring_authorised"] is False
        assert a["guardian_hrm_required"] is True

def test_missing_or_proposed_law_is_not_binding_evidence():
    assert not evaluate_legal_source({})["accepted_for_legal_conclusion"]
    base = dict(jurisdiction="England and Wales", source_url="https://www.legislation.gov.uk/",
                source_date="2026-01-01", effective_date="2026-01-01",
                verified_at="2026-10-22", primary_source_verified=True)
    assert not evaluate_legal_source({**base, "legal_status":"proposed"})["accepted_for_legal_conclusion"]
    assert evaluate_legal_source({**base, "legal_status":"binding"})["accepted_for_legal_conclusion"]

def test_tax_and_training_truth():
    status = legal_learning_status()
    assert status["learning_domains"] == 22
    assert status["trained_agents_verified"] is None
    assert status["overall_vpi"] is None
    assert status["lawful_tax_planning_only"] is True
    assert status["tax_evasion_or_concealment"] is False
