"""Non-executing SMI Court 777 agent registry safety checks."""
from mission_control.smi_court_agents_777 import COURT_AGENT_DEFINITIONS, court_status


def test_all_twenty_one_roles_have_unique_passports():
    assert len(COURT_AGENT_DEFINITIONS) == 21
    assert len({agent["id"] for agent in COURT_AGENT_DEFINITIONS}) == 21
    assert len({agent["role"] for agent in COURT_AGENT_DEFINITIONS}) == 21


def test_court_agents_cannot_self_authorise_or_claim_training():
    for agent in COURT_AGENT_DEFINITIONS:
        assert agent["operational"] is False
        assert agent["training_verified"] is False
        assert agent["independent_execution"] is False
        assert agent["independent_legal_advice"] is False
        assert agent["external_contact"] is False
        assert agent["human_approval_required"] is True


def test_court_status_is_evidence_honest():
    status = court_status()
    assert status["verified_running_agents"] is None
    assert status["operational_vpi"] is None
    assert status["guardian_hrm_required"] is True
    assert status["qualified_legal_review_required"] is True
    assert status["real_human_training"] == "consenting_authorised_participants_only"
