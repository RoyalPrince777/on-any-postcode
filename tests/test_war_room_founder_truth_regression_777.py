"""War Room founder-authority and evidence-truth regression guards.

This test intentionally exercises existing contracts without creating a new
agent registry, vote engine, approval path, or production control surface.
"""

from mission_control import agents, war_room
from oap.war_room.engine import WarRoomEngine


def test_war_room_never_grants_production_or_decision_authority():
    status = WarRoomEngine().status()
    assert status["production_control_ready"] is False
    assert status["decision_authority"] is False
    assert status["mode"] == "simulation_only"
    assert status["truth_state"] == "simulation_ready"


def test_war_room_evidence_stars_do_not_skip_stages():
    rubric = war_room.RATING_RUBRIC
    assert tuple(entry["stars"] for entry in rubric) == tuple(range(6))
    assert rubric[0]["label"] == "Unproven"
    assert rubric[-1]["label"] == "Operationally certified"
    assert "Human approval" in rubric[-1]["meaning"]


def test_war_room_preserves_one_canonical_seven_world_registry():
    assert len(agents.INTELLIGENCE_WORLDS) == 7
    assert len(set(agents.LOCKED_WORLD_IDS)) == 7
    assert "War Room / Human Authority" in {
        item["components"] for item in war_room.RESOLVED_BOUNDARIES
    }
    boundary = next(
        item for item in war_room.RESOLVED_BOUNDARIES
        if item["components"] == "War Room / Human Authority"
    )
    assert boundary["resolution"] == (
        "War Room reviews consequences; Human Authority alone decides."
    )
