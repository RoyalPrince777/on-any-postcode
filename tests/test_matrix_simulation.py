from mission_control import matrix_simulation


def test_matrix_simulation_is_environment_not_agent():
    status = matrix_simulation.status()
    assert status["kind"] == "bounded_training_environment"
    assert status["execution_granted"] is False
    assert status["production_mutation_allowed"] is False
    assert status["self_approval_allowed"] is False
    assert status["agent_creation_allowed"] is False
    assert status["human_authority_final"] is True


def test_matrix_simulation_preserves_core_and_requires_real_world_gates():
    result = matrix_simulation.run_simulation("route conflict", "recovery")
    assert result["matrix_core_unchanged"] is True
    assert result["execution_granted"] is False
    assert result["external_action_taken"] is False
    assert result["guardian_required_before_real_action"] is True
    assert result["green_gate_required_before_real_action"] is True
    assert result["founder_final_required"] is True


def test_war_room_exposes_simulation_as_training_not_authority():
    from mission_control import war_room

    dashboard = war_room.get_war_room_dashboard()
    training = dashboard["training_environment"]

    assert training["name"] == "Matrix Simulation / Training Ground"
    assert training["kind"] == "bounded_training_environment"
    assert training["execution_granted"] is False
    assert dashboard["can_approve"] is False
    assert dashboard["can_execute"] is False
    assert "War Room review" in dashboard["training_flow"]
    assert "Human Authority" in dashboard["training_flow"]
