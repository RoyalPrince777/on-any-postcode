import pytest

from oap_cloud.mission_record import build_mission_record


def record(**changes):
    params = {
        "mission": "OAP Cloud", "candidates": {"Fox": {"rating": None}}, "ballots": [],
        "evidence_gates": {f"gate_{i}": i < 2 for i in range(10)},
        "done": ["local storage tests"], "next_actions": ["verify Cloud auth"],
        "recovery": ["no persistent storage"], "evidence_links": ["commit:2980aae"],
    }
    params.update(changes)
    return build_mission_record(**params)


def test_mission_record_preserves_dissent_and_evidence():
    result = record(ballots=[{"voter": "Guardian", "candidate": "Fox",
                             "vote": "AGAINST", "reason": "security incomplete"}])
    assert result["schema"] == "oap.mission.v1"
    assert result["completion"]["percentage"] == 20
    assert result["council"]["votes"]["Fox"]["AGAINST"] == 1
    assert result["recovery"] == ["no persistent storage"]
    assert result["production_green"] is False
    assert result["leadership"]["founder_final"] == "pending"


def test_founder_approval_does_not_override_missing_evidence():
    assert record(founder_decision="approved")["production_green"] is False


def test_full_gates_do_not_override_founder_pending():
    assert record(evidence_gates={f"gate_{i}": True for i in range(10)})["production_green"] is False


def test_invalid_founder_decision_fails_closed():
    with pytest.raises(ValueError):
        record(founder_decision="automatic")


def test_invalid_action_rejected():
    with pytest.raises(ValueError):
        record(evidence_links=[""])
