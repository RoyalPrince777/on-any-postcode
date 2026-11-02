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


def test_matrix_simulation_forbids_self_promotion():
    status = matrix_simulation.status()
    assert "No agent may promote itself; promotion requires evidence and Founder approval." in status["rules"]



def test_morpheus_mouse_training_plan_reuses_existing_matrix_ground_without_execution():
    from mission_control import matrix_simulation
    plan = matrix_simulation.morpheus_mouse_training_plan("Practice spotting distractions")
    assert plan["mission_director"] == "Morpheus"
    assert plan["program_designer"] == "Mouse"
    assert plan["runtime_operator"] == "Tank"
    assert plan["environment"] == matrix_simulation.SIMULATION_NAME
    assert plan["training_flow"][0] == "Morpheus defines lesson"
    assert plan["scenario_created"] is False
    assert plan["scenario_executed"] is False
    assert plan["observations_verified"] is False
    assert plan["hrm_receipt_written"] is False
    assert plan["execution_granted"] is False
    assert plan["guardian_required"] and plan["green_gate_required"]
    assert plan["founder_final_required"]


def test_morpheus_mouse_training_plan_rejects_unsupported_or_blank_scenario():
    import pytest
    from mission_control import matrix_simulation
    for objective, mode in (("", "scenario"), ("practice", "invalid"), ("x" * 2001, "scenario")):
        with pytest.raises(ValueError):
            matrix_simulation.morpheus_mouse_training_plan(objective, mode=mode)


def test_mouse_training_runs_bounded_decision_and_returns_morpheus_feedback():
    case = matrix_simulation.run_mouse_attention_training("Spot an unsafe distraction")
    assert case["scenario_created"] is True
    assert case["scenario_executed"] is False
    assert len(case["options"]) == 3
    answer = matrix_simulation.run_mouse_attention_training(
        "Spot an unsafe distraction", choice="observe_surroundings"
    )
    assert answer["exercise_completed"] is True
    assert answer["scenario_executed"] is True
    assert "Correct" in answer["feedback"]
    assert answer["hrm_receipt_written"] is False
    assert answer["external_action_taken"] is False
    assert answer["execution_granted"] is False
    assert answer["founder_final_required"] is True


def test_mouse_training_rejects_invalid_choices():
    import pytest
    with pytest.raises(ValueError):
        matrix_simulation.run_mouse_attention_training("Practice", choice="deploy")
