"""Seven-star War Room upgrades must never inflate the established evidence score."""

from mission_control import war_room


def _ratings(board):
    return [item for category in board["categories"] for item in category["items"]]


def test_seven_star_rubric_is_additive_and_ordered():
    board = war_room.get_war_room_dashboard()
    rubric = board["rubric"]
    assert [row["stars"] for row in rubric] == list(range(8))
    assert rubric[5]["label"] == "Operationally certified"
    assert rubric[6]["label"] == "Stability & resilience certified"
    assert rubric[7]["label"] == "Sovereign Gold certified"
    assert board["sovereign_gold_scale"]["higher_certifications_active"] is False


def test_higher_stars_are_fail_closed_and_legacy_score_is_unchanged():
    board = war_room.get_war_room_dashboard()
    ratings = _ratings(board)
    for item in ratings:
        gold = item["sovereign_gold"]
        assert gold["stars"] == item["stars"]
        assert gold["max_stars"] == 7
        assert len(gold["display"]) == 7
        assert gold["stability_certified"] is False
        assert gold["sovereign_gold_certified"] is False
        assert gold["higher_gate_evidence"] is None
        assert item["score"] == item["stars"] * 20
        assert len(item["stages"]) == 5
        assert len(item["stars_display"]) == 5
        if item["stars"] == 5:
            assert gold["next_certification"] == "Stability & resilience certified"

    expected = round(
        sum(item["stars"] for item in ratings) / (len(ratings) * 5) * 100
    )
    assert board["summary"]["overall_evidence_score"] == expected
