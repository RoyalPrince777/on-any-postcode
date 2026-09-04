from __future__ import annotations

from mission_control import live_signals


def test_live_signal_language_is_first_party_complete_and_unique():
    legend = live_signals.public_legend()
    ids = tuple(item["id"] for item in legend["signals"])

    assert legend["owner"] == "ON ANY POSTCODE"
    assert legend["first_party_only"] is True
    assert legend["external_identity_allowed"] is False
    assert legend["external_authority_allowed"] is False
    assert legend["can_approve"] is False
    assert legend["can_execute"] is False
    assert legend["validation"]["passed"] is True
    assert legend["core_signal_count"] == 21
    assert legend["validation"]["signal_count"] == 21
    assert len(ids) == 21
    assert len(ids) == len(set(ids))
    assert "busy" not in ids


def test_busy_is_preserved_as_orange_workload_modifier():
    legend = live_signals.public_legend()
    modifiers = legend["workload_modifiers"]

    assert modifiers == (
        {
            "id": "busy_high_load",
            "emoji": "🟠",
            "label": "Busy / High Load",
            "meaning": "Workload intensity modifier used with a core state such as Active / Working.",
        },
    )
    assert legend["validation"]["modifier_count"] == 1
    assert legend["verdict_rules"]["orange_is_workload_modifier"] is True
    assert live_signals.get_signal("busy")["id"] == "working"
    assert live_signals.get_signal("high_load")["id"] == "working"


def test_learning_is_the_only_purple_signal_and_never_a_verdict():
    legend = live_signals.public_legend()
    purple = [item for item in legend["signals"] if item["emoji"] == "🟣"]

    assert purple == [
        next(item for item in legend["signals"] if item["id"] == "learning")
    ]
    assert legend["verdict_rules"]["learning"] == "🟣"
    assert legend["verdict_rules"]["learning_is_verdict"] is False
    assert legend["verdict_rules"]["warning"] == "🟡"
    assert legend["verdict_rules"]["healthy"] == "🟢"
    assert legend["verdict_rules"]["critical"] == "🔴"


def test_existing_runtime_words_resolve_without_false_green():
    assert live_signals.resolve_runtime_signal("healthy")["id"] == "healthy"
    assert live_signals.resolve_runtime_signal("degraded")["id"] == "warning"
    assert live_signals.resolve_runtime_signal("degraded", status="Not connected")["id"] == "offline"
    assert live_signals.resolve_runtime_signal("error")["id"] == "critical"
    assert live_signals.resolve_runtime_signal("learning")["id"] == "learning"
    assert live_signals.resolve_runtime_signal("busy")["id"] == "working"
    assert live_signals.resolve_runtime_signal("unknown-state")["id"] == "warning"


def test_mind_body_soul_signal_cues_are_preserved():
    anatomy = live_signals.public_legend()["mind_body_soul"]

    assert [item["emoji"] for item in anatomy["mind"]] == ["🧠", "📚", "🔍", "🎯", "💡", "📖"]
    assert [item["emoji"] for item in anatomy["body"]] == ["⚙", "📡", "📥", "🔄", "🏃", "🛠"]
    assert [item["emoji"] for item in anatomy["soul"]] == ["❤️", "⚖", "🛡", "🤝", "🌍"]
