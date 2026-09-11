from oap.war_room.engine import WarRoomEngine


def test_war_room_advisory_readiness_is_not_production_control_readiness():
    status = WarRoomEngine().status()

    assert status["ready"] is True
    assert status["operational"] is True
    assert status["advisory_ready"] is True
    assert status["mode"] == "simulation_only"
    assert status["truth_state"] == "simulation_ready"

    assert status["production_control_ready"] is False
    assert status["decision_authority"] is False
    assert status["reversibility_required"] is True
    assert status["production_blocker"]
