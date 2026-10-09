"""Integrated MATRIX council keeps routing and leadership evidence in one record."""

import pytest

from mission_control.matrix_system import mission_council


def test_mission_council_has_captain_and_fox_octopus_peers():
    result = mission_council(
        "database_migration",
        nominations=("dozer",),
        votes=(("architect", "dozer"), ("twins", "dozer")),
        evidence=("reviewed migration plan",),
    )
    assert result["command"] == "smi"
    assert result["captain"] == "captain_all_in"
    assert result["coordinators"] == ("fox", "octopus")
    assert result["recommended_lead"] == "dozer"
    assert result["approved"] is False
    assert result["permitted_to_execute"] is False
    assert result["production_ready"] is False
    assert any(agent["agent"] == "gorilla" for agent in result["specialists"])
    assert all(agent["intelligence"] for agent in result["specialists"])


def test_council_rejects_outside_nominee():
    with pytest.raises(ValueError, match="ineligible_nomination"):
        mission_council("runtime_recovery", nominations=("neo",))


def test_council_without_votes_still_selects_bounded_recommendation():
    result = mission_council("public_endpoint")
    assert result["recommended_lead"] == "neo"
    assert result["votes"] == ()
    assert result["approved"] is False
