import pytest

from oap_cloud.mission_council import review_leadership


def gates(count):
    return {f"gate_{i}": i < count for i in range(10)}


def test_advisory_votes_and_verified_score():
    result = review_leadership(
        "OAP Cloud", {"Fox": {"rating": None}, "Octopus": {"rating": 5, "evidence": ["design-review-1"]}},
        [
            {"voter": "Owl", "candidate": "Fox", "vote": "FOR", "reason": "recovery fit"},
            {"voter": "Guardian", "candidate": "Fox", "vote": "AGAINST", "reason": "security gate incomplete"},
            {"voter": "Fox", "candidate": "Octopus", "vote": "ABSTAIN", "reason": "insufficient delivery proof"},
        ], gates(3),
    )
    assert result["percentage"] == 30
    assert result["mission_stars"] == 2
    assert result["leader"] == "pending_founder_final"
    assert result["production_green"] is False
    assert result["votes"]["Fox"]["AGAINST"] == 1
    assert len(result["dissent"]) == 2


def test_full_evidence_requires_all_ten_gates():
    result = review_leadership("OAP Cloud", {"Fox": {"rating": None}}, [], gates(10))
    assert result["percentage"] == 100
    assert result["mission_stars"] == 5
    assert result["production_green"] is False
    assert result["release_certification"] == "not_verified"
    assert result["leader"] == "pending_founder_final"


@pytest.mark.parametrize("ballots", [
    [{"voter": "Fox", "candidate": "Fox", "vote": "FOR", "reason": "self"}],
    [{"voter": "Owl", "candidate": "Fox", "vote": "YES", "reason": "unknown vote"}],
    [{"voter": "Owl", "candidate": "Fox", "vote": "FOR", "reason": "one"},
     {"voter": "Owl", "candidate": "Fox", "vote": "AGAINST", "reason": "two"}],
])
def test_rejects_invalid_votes(ballots):
    with pytest.raises(ValueError):
        review_leadership("OAP Cloud", {"Fox": {"rating": None}}, ballots, gates(0))


def test_unproven_rating_rejected():
    with pytest.raises(ValueError):
        review_leadership("OAP Cloud", {"Fox": {"rating": 7}}, [], gates(0))


def test_invented_percentage_rejected():
    with pytest.raises(ValueError):
        review_leadership("OAP Cloud", {"Fox": {"rating": None}}, [], {"gate_0": 0.5})


def test_rating_evidence_must_be_nonempty_list_of_references():
    for invalid in ("asserted", [], [""], [None]):
        with pytest.raises(ValueError):
            review_leadership("OAP Cloud", {"Fox": {"rating": 7, "evidence": invalid}}, [], gates(0))


def test_gate_names_cannot_be_empty():
    bad = gates(0)
    bad[""] = bad.pop("gate_0")
    with pytest.raises(ValueError):
        review_leadership("OAP Cloud", {"Fox": {"rating": None}}, [], bad)


def test_complete_self_reported_gates_never_self_certify_release():
    result = review_leadership(
        "OAP Cloud", {"Fox": {"rating": None}}, [], gates(10),
    )
    assert result["percentage"] == 100
    assert result["mission_stars"] < 7
    assert result["production_green"] is False
