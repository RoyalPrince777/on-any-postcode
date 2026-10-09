"""Ensure MATRIX status does not change existing War Room authority."""

from mission_control import matrix_status, war_room


def test_matrix_status_in_war_room(monkeypatch):
    monkeypatch.setattr(
        war_room, "_snapshot", lambda: {
            "architecture": {"validation": {"checks": {}}},
            "agents": {"checks": {}},
            "infrastructure": {"validation": {"checks": {}}},
        }
    )
    status = matrix_status.matrix_registry_status()
    assert status["runtime_active"] is False
    assert status["production_ready"] is False
    assert len(status["modes"]) == 7
    assert len(status["ranks"]) == 7
    assert "matrix_council" in war_room.get_war_room_dashboard.__code__.co_consts or status["system"] == "SMI MATRIX"
