from __future__ import annotations

from mission_control import live_signals, smi_chat_runtime, smi_thinking_process


def test_thinking_process_is_first_party_seven_stage_and_non_executing():
    contract = smi_thinking_process.process_contract()
    stage_ids = tuple(item["id"] for item in contract["stages"])
    canonical_signal_ids = {item["id"] for item in live_signals.LIVE_SIGNALS}

    assert contract["owner"] == "ON ANY POSTCODE"
    assert contract["first_party_only"] is True
    assert contract["stage_count"] == 7
    assert stage_ids == (
        "understand",
        "context",
        "route",
        "evidence",
        "challenge",
        "synthesise",
        "govern",
    )
    assert all(item["signal"]["id"] in canonical_signal_ids for item in contract["stages"])
    assert contract["private_reasoning_exposed"] is False
    assert contract["chain_of_thought_exposed"] is False
    assert contract["decision_authority"] is False
    assert contract["execution_authority"] is False
    assert contract["human_authority_final"] is True
    assert smi_thinking_process.validate()["passed"] is True


def test_thinking_process_does_not_repurpose_learning_or_warning_signals():
    stages = {item["id"]: item for item in smi_thinking_process.process_contract()["stages"]}

    assert live_signals.get_signal("learning")["emoji"] == "🟣"
    assert live_signals.get_signal("warning")["emoji"] == "🟡"
    assert stages["evidence"]["signal"]["id"] == "working"
    assert all(item["signal"]["id"] != "learning" for item in stages.values())


def test_low_level_runtime_stages_are_translated_to_safe_public_stages():
    assert smi_thinking_process.public_stage_event("received")["stage"] == "understand"
    assert smi_thinking_process.public_stage_event("identity")["stage"] == "context"
    assert smi_thinking_process.public_stage_event("provider")["stage"] == "synthesise"
    assert smi_thinking_process.public_stage_event("hrm")["stage"] == "govern"
    event = smi_thinking_process.stage_event("challenge", source_stage="guardian")
    assert event["chain_of_thought"] is False
    assert event["private_reasoning_exposed"] is False
    assert "risks" in event["label"].lower()


def test_completion_summary_uses_runtime_evidence_without_private_reasoning():
    summary = smi_thinking_process.completion_summary(
        {
            "task_type": "TECHNICAL",
            "advisor_ids": ["NEO-001", "SERAPH-001"],
            "brain_regions": 7,
            "signal_level": "LOW",
            "guardian": "PASSED",
            "output_state": "RECOMMENDATION_READY",
            "war_room": {"triggered": True},
            "coherent": {"passed": True, "score": 96},
            "judgement": {"confidence": 91},
            "adaptive": {"active": True, "hrm_lessons": 3},
        }
    )

    assert summary["evidence_state"] == "SUPPORTED"
    assert summary["coherence_score"] == 96
    assert summary["judgement_confidence"] == 91
    assert summary["war_room_triggered"] is True
    assert summary["hrm_lessons_used"] == 3
    assert summary["private_reasoning_exposed"] is False
    assert summary["chain_of_thought_exposed"] is False
    assert summary["human_authority_final"] is True


def test_facade_chat_translates_and_deduplicates_stage_events(monkeypatch):
    low_level = (
        {"type": "stage", "stage": "received", "label": "Signal received"},
        {"type": "stage", "stage": "identity", "label": "Identity verified"},
        {"type": "stage", "stage": "permission", "label": "Permission checked"},
        {"type": "stage", "stage": "guardian", "label": "Guardian reviewed"},
        {"type": "stage", "stage": "provider", "label": "Provider"},
        {"type": "delta", "delta": "Direct answer"},
        {"type": "stage", "stage": "hrm", "label": "HRM recording"},
    )

    def fake_core_chat(*args, on_event, **kwargs):
        del args, kwargs
        for item in low_level:
            on_event(item)
        return {
            "status": "green",
            "response": "Direct answer",
            "output_state": "RECOMMENDATION_READY",
            "guardian": "PASSED",
            "task_type": "GENERAL",
            "advisor_ids": ["NEO-001"],
            "brain_regions": 6,
            "signal_level": "LOW",
            "war_room": {"triggered": False},
            "adaptive": {"active": True, "hrm_lessons": 2},
            "coherent": {"passed": True, "score": 100},
            "judgement": {"confidence": 90},
            "can_execute": False,
        }

    monkeypatch.setattr(smi_chat_runtime._core, "chat", fake_core_chat)
    events: list[dict] = []
    result = smi_chat_runtime.chat(
        "Review this.",
        "11111111-1111-4111-8111-111111111111",
        "OAP Founder",
        on_event=events.append,
    )

    stages = [item["stage"] for item in events if item["type"] == "stage"]
    assert stages == [
        "understand",
        "context",
        "route",
        "evidence",
        "challenge",
        "synthesise",
        "govern",
    ]
    assert sum(stage == "context" for stage in stages) == 1
    assert [item for item in events if item["type"] == "delta"] == [
        {"type": "delta", "delta": "Direct answer"}
    ]
    assert result["thinking_process"]["evidence_state"] == "SUPPORTED"
    assert result["thinking_process_contract"]["stage_count"] == 7
    assert result["thinking_process_contract"]["chain_of_thought_exposed"] is False
