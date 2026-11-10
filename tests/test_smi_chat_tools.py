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
        "sika_review",
    }


def test_sika_routing_uses_existing_read_only_gate(monkeypatch):
    monkeypatch.setattr(
        smi_chat_tools.smi_command_dashboard,
        "status",
        lambda: {"bank": {"regulated_unlock": {
            "evidence_available": True,
            "capabilities": {"execute_payments": False, "cash_out": False},
        }}},
    )
    result = smi_chat_tools.execute_selected("Review SIKA payment readiness")
    assert "sika_review" in result["selected_tools"]
    review = next(item["result"] for item in result["results"]
                  if item["tool"] == "sika_review")
    assert review["capabilities"]["execute_payments"] is False
    assert review["personal_balance_exposed"] is False
    assert review["money_movement"] is False
    assert result["execution_authority_expanded"] is False


def test_sika_review_unknown_when_evidence_missing(monkeypatch):
    monkeypatch.setattr(
        smi_chat_tools.smi_command_dashboard,
        "status",
        lambda: {"bank": {"regulated_unlock": {
            "evidence_available": False,
            "capabilities": {"execute_payments": True},
        }}},
    )
    review = smi_chat_tools._sika_review()
    assert review["state"] == "unknown"
    assert review["capabilities"] == {}
    assert review["human_authority_final"] is True
