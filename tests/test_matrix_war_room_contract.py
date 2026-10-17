"""MATRIX is projected through canonical War Room without extra authority."""

import inspect

from mission_control import matrix_status, war_room


def test_matrix_war_room_projection_is_read_only():
    source = inspect.getsource(war_room.get_war_room_dashboard)
    assert '"matrix_council": _safe_mapping(lambda: matrix_status.matrix_registry_status())' in source
    assert '"can_approve": False' in source
    assert '"can_execute": False' in source
    status = matrix_status.matrix_registry_status()
    assert status["runtime_active"] is False
    assert status["execution_authorised"] is False
    assert status["production_ready"] is False
    assert len(status["modes"]) == 7
    assert len(status["ranks"]) == 7
