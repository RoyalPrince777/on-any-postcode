from mission_control import smi_deep_dive_protocol as protocol


def test_full_master_depth_modes_include_auto_3_7_21():
    modes = {item["id"]: item for item in protocol.DEPTH_MODES}

    assert tuple(modes) == ("auto", "instant_3", "medium_7", "high_21")
    assert modes["instant_3"]["depth"] == 3
    assert modes["medium_7"]["depth"] == 7
    assert modes["high_21"]["depth"] == 21


def test_war_room_signals_never_equate_simulation_with_production():
    rules = protocol.SIGNAL_RULES

    assert "🟢 SIMULATION PASSED" in rules
    assert "🟢 PRODUCTION PROVEN" in rules
    assert rules["🟢 SIMULATION PASSED"] != rules["🟢 PRODUCTION PROVEN"]
    assert protocol.status()["locks"]["simulation_pass_is_production_proof"] is False
    assert protocol.status()["locks"]["approve_equals_execute"] is False


def test_full_master_agent_choices_are_current_registered_names_only():
    rendered = repr(protocol.AGENT_BUTTONS)

    for expected in ("Neo", "Nirmata", "Guardian", "Akela", "Mowgli", "Bagheera", "Shere Khan"):
        assert expected in rendered
    for stale in ("Seraph", "Keymaker", "Spider", "Gyata"):
        assert stale not in rendered


def test_safe_progress_is_telemetry_not_private_reasoning():
    state = protocol.status()

    assert state["safe_progress_stages"] == (
        "Understanding",
        "Evidence",
        "Memory",
        "Agents",
        "Challenge",
        "Guardian",
        "Judgement",
        "Solution",
    )
    assert state["locks"]["show_thinking_is_telemetry_only"] is True
    assert state["locks"]["private_chain_of_thought_hidden"] is True
