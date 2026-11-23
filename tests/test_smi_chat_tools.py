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
        "build_gaps",
        "movement",
        "inspect",
        "signals_21",
        "oap_world",
        "war_room",
        "fetch_data",
    }


def test_jog_memory_reads_canonical_build_gaps_without_status_or_mutations(monkeypatch):
    def no_runtime_probe():
        raise AssertionError("source inventory must not trigger runtime probes")

    monkeypatch.setattr(smi_chat_tools, "_safe_dashboard_status", no_runtime_probe)
    result = smi_chat_tools.execute_selected(
        "SMI jog memory what's not done everything built in code fix"
    )
    assert result["selected_tools"] == ["build_gaps"]
    entry = result["results"][0]
    assert entry["ok"] and entry["read_only"]
    data = entry["result"]
    assert data["runtime_proof"] == "not_collected_by_this_tool"
    assert data["release_green"] is False
    assert data["write_performed"] is False
    assert len(data["capabilities"]) == len(smi_chat_tools.products.SPOT_CAPABILITIES)
    for actual, canonical in zip(data["capabilities"], smi_chat_tools.products.SPOT_CAPABILITIES, strict=True):
        assert actual["declared_code_status"] == canonical["status"]
        assert actual["remaining_blocker"] == canonical["blocked_by"]
    assert result["execution_authority_expanded"] is False


def test_build_inventory_prompt_does_not_promote_source_declarations_to_live():
    context = smi_chat_tools.prompt_context("what's built in code and what's left")
    assert "Declared source inventory is not live-runtime or release proof" in context
    assert '"release_green":false' in context
    assert '"remaining_blocker"' in context


def test_m3gan_specialist_conversation_is_explicit_and_uses_one_smi_brain():
    from mission_control import smi_chat_grounded

    assert smi_chat_grounded.m3gan_dialogue_contract("SMI: review M3GAN code") == ""
    assert smi_chat_grounded.m3gan_dialogue_contract("Tell me about M3GAN") == ""
    assert smi_chat_grounded.m3gan_dialogue_contract("M3GAN 2.0") == ""
    prompt = smi_chat_grounded.m3gan_dialogue_contract("M3GAN: think through this")
    assert prompt.startswith("\n\nM3GAN SPECIALIST DIALOGUE")
    assert "same governed SMI model" in prompt
    assert "Founder Final" in prompt
    assert "never claim memories" in prompt


def test_m3gan_specialist_reuses_existing_grounded_provider_and_history():
    from mission_control import smi_chat_grounded

    calls = []

    def provider(message, image, history, brain, memory, media, **kwargs):
        calls.append((message, history, kwargs))
        return "bounded answer"

    history = [{"role": "user", "content": "first question"}]
    output = smi_chat_grounded.grounded_provider(
        provider, lambda: {"status": "unknown", "checks": {}},
        "M3GAN: can we discuss OAP World?", history=history,
    )
    assert output == "bounded answer"
    assert len(calls) == 1
    assert calls[0][1] is history
    assert "M3GAN SPECIALIST DIALOGUE" in calls[0][0]
    assert "PERSONAL SMI CONTRACT" in calls[0][0]
    assert calls[0][2]["code_mode"] is False
    calls.clear()
    smi_chat_grounded.grounded_provider(
        provider, lambda: {"status": "unknown", "checks": {}},
        "Review M3GAN functionality",
    )
    assert "M3GAN SPECIALIST DIALOGUE" not in calls[0][0]
