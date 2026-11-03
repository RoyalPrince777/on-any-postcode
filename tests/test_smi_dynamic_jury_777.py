"""Regression tests for the advisory OAP Court dynamic jury selector."""
from mission_control.smi_dynamic_jury_777 import founding_candidates, recommend_jury

CASE = {"case_id": "TEST-777", "topics": ("legal", "rights"),
        "excluded_agent_ids": ()}

def candidate(i, **updates):
    result = {"id": f"A{i}", "expertise": ("legal", "rights"),
              "verified": True, "independent": True,
              "conflicts_checked": True, "conflict_free": True}
    result.update(updates)
    return result

def test_founders_are_not_assumed_cleared():
    assert len(founding_candidates()) == 7
    assert recommend_jury(CASE, founding_candidates())["ready"] is False

def test_seven_eligible_produce_advisory_only():
    result = recommend_jury(CASE, [candidate(i) for i in range(7)])
    assert result["ready"] is True
    assert len(result["jurors"]) == 7
    assert result["appointments_executed"] is False
    assert result["requires_founder_approval"] is True

def test_conflicts_and_unverified_agents_fail_closed():
    people = [candidate(i) for i in range(7)]
    people[0]["conflict_free"] = False
    assert recommend_jury(CASE, people)["ready"] is False
    people[0]["conflict_free"] = True
    people[1]["verified"] = False
    assert recommend_jury(CASE, people)["ready"] is False
    assert recommend_jury({**CASE, "excluded_agent_ids": ("A2",)}, people)["ready"] is False

def test_duplicates_do_not_fill_seats():
    people = [candidate(i) for i in range(6)] + [candidate(0)]
    assert recommend_jury(CASE, people)["ready"] is False

def test_missing_case_and_topics_fail_closed():
    people = [candidate(i) for i in range(7)]
    assert recommend_jury({}, people)["ready"] is False
    assert recommend_jury({**CASE, "topics": ()}, people)["ready"] is False

def test_ranking_prefers_matching_expertise():
    people = [candidate(i) for i in range(8)]
    people[0]["expertise"] = ("legal",)
    result = recommend_jury(CASE, people)
    assert result["ready"] is True
    assert "A0" not in result["jurors"]
