from mission_control import smi_deep_dive_protocol as protocol


def test_seven_x_is_accumulated_research_not_depth_modes():
    state = protocol.status()
    passes = state["seven_x"]["passes"]

    assert state["seven_x"]["is_depth_mode"] is False
    assert tuple(item["name"] for item in passes) == (
        "Discovery",
        "Verification",
        "Alternatives",
        "Adversarial",
        "Systems",
        "Consequence",
        "Synthesis",
    )


def test_war_room_signals_never_equate_learning_with_production():
    rules = protocol.SIGNAL_RULES

    assert "🟣 LEARNING" in rules
    assert "🟢 PROVEN" in rules
    assert "not production proof" in rules["🟣 LEARNING"]
    assert protocol.status()["locks"]["production_write"] is False
    assert protocol.status()["locks"]["deploy"] is False


def test_registered_review_roles_are_explicit_in_flow_and_ui_contract():
    rendered = repr(protocol.CANONICAL_FLOW) + repr(protocol.WAR_ROOM_BUTTONS)

    for expected in (
        "Registered Agent Challenge",
        "AGENTS",
        "SMITH ATTACK",
        "GUARDIAN",
        "JUDGEMENT",
        "HRM / JOOG",
    ):
        assert expected in rendered


def test_safe_progress_is_governed_protocol_not_private_reasoning():
    state = protocol.status()

    assert state["protocol_loop"] == (
        "Observe",
        "Classify",
        "Verify",
        "Fix / Plan",
        "Retest",
        "Record",
        "Learn",
    )
    assert "UI presence is not readiness." in state["final_law"]
    assert "Simulation passed is not production proven." in state["final_law"]
