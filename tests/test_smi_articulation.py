import pytest

from mission_control.smi_articulation import APPLICATIONS, articulation_plan


@pytest.mark.parametrize("application", sorted(APPLICATIONS))
def test_all_seven_applications_remain_advisory(application):
    plan = articulation_plan(application, consent=True)
    assert plan.execution_class == "advisory"
    assert "No external actions, purchases, bookings or dispatch" in plan.safeguards


def test_voice_requires_explicit_consent():
    with pytest.raises(PermissionError):
        articulation_plan("voice")


def test_unknown_application_and_pressure_fail_closed():
    with pytest.raises(ValueError):
        articulation_plan("payment")
    with pytest.raises(ValueError):
        articulation_plan("founder", "panic_inferred")


def test_emergency_never_claims_dispatch():
    plan = articulation_plan("emergency", "urgent")
    assert "human emergency escalation" in plan.structure
    assert "No external actions, purchases, bookings or dispatch" in plan.safeguards


def test_agent_messages_require_evidence_and_authority():
    plan = articulation_plan("agent")
    assert {"authority", "evidence", "uncertainty", "verification"} <= set(plan.structure)


def test_pressure_only_changes_structure_not_permissions():
    normal = articulation_plan("negotiation")
    challenged = articulation_plan("negotiation", "challenged")
    assert challenged.safeguards == normal.safeguards
    assert challenged.structure[1:] == normal.structure
