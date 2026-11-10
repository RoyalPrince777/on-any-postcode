from mission_control import smi_chat_tools


def test_smi_chat_tool_router_selects_movement_and_data():
    selected = smi_chat_tools.select_tools(
        "SMI fetch current travel data and show the best movement route"
    )
    assert "movement" in selected
    assert "fetch_data" in selected


def test_smi_chat_tool_router_is_read_only():
    result = smi_chat_tools.execute_selected("inspect the SMI system")
    assert result["execution_authority_expanded"] is False
    assert result["human_authority_final"] is True
    assert all(item["read_only"] for item in result["results"])


def test_smi_chat_tool_router_does_not_invent_tools():
    selected = smi_chat_tools.select_tools("tell me a joke about chess")
    assert selected == ()


def test_smi_chat_tool_definitions_are_unique():
    ids = [item["id"] for item in smi_chat_tools.definitions()]
    assert len(ids) == len(set(ids))
    assert {item["id"] for item in smi_chat_tools.definitions()} == {
        "movement",
        "inspect",
        "signals_21",
        "oap_world",
        "war_room",
        "fetch_data",
    }
