from mission_control import live_working_intelligence, smi_workbench


def test_live_working_profile_unifies_existing_intelligence_without_claiming_agi():
    payload = live_working_intelligence.status()
    stack = {item["id"]: item for item in payload["capability_stack"]}

    assert payload["mode"] == "live_working"
    assert payload["read_only"] is False
    assert payload["live_working"] is True
    assert payload["autonomy_class"] == "A4_supervised_live_working"
    assert set(stack) == {
        "smi",
        "omni",
        "hybrid",
        "civilisation",
        "adaptive",
        "coherent",
        "distribution",
        "agi",
        "guardian",
        "hrm",
    }
    assert payload["adaptive_ready"] is True
    assert payload["coherent_ready"] is True
    assert payload["distribution_ready"] is True
    assert payload["agi_routing_ready"] is True
    assert payload["seven_world_model"] is True
    assert payload["world_count"] == 7
    assert payload["agi_target"] is True
    assert payload["agi_achieved"] is False
    assert payload["general_intelligence_certified"] is False
    assert payload["internal_governed_work_enabled"] is True
    assert payload["external_consequential_execution"] is False
    assert payload["independent_approval"] is False
    assert payload["silent_authority_escalation"] is False
    assert payload["human_authority_final"] is True
    assert payload["no_fake_green"] is True


def test_workbench_activates_live_working_mode_only_with_durable_runtime(monkeypatch):
    monkeypatch.setattr(
        smi_workbench.smi_chat_runtime,
        "health",
        lambda: {
            "status": "green",
            "checks": {
                "database": True,
                "schema": True,
                "chat_route": True,
                "conversation_memory": True,
                "war_room": True,
            },
        },
    )

    payload = smi_workbench.get_workbench_status()
    mode = payload["intelligence_mode"]

    assert payload["surface"] == "Founder-only Live Working SMI"
    assert mode["mode"] == "live_working"
    assert mode["read_only"] is False
    assert mode["durable_runtime_ready"] is True
    assert mode["active"] is True
    assert payload["governance"]["recommendation_only"] is False
    assert payload["governance"]["internal_governed_work_enabled"] is True
    assert payload["governance"]["external_consequential_execution"] is False
    assert payload["governance"]["agi_achieved"] is False
    assert payload["governance"]["human_authority_final"] is True
