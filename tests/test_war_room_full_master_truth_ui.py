from pathlib import Path


def test_war_room_ui_never_treats_configuration_as_readiness():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")

    assert "item.ready === true" in page
    assert "item.ready === undefined ? Boolean(item.configured)" not in page
    assert "Configured is not ready" in page
    assert "🟢 Evidence first" not in page
    assert "🟢 Routed" not in page
    assert "⚪ Unknown until checked" in page


def test_war_room_ui_exposes_full_master_depth_and_read_only_controls():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")

    for label in ("◎ Auto", "⚡ Instant 3", "🧠 Medium 7", "👑 High 21"):
        assert label in page
    for control in (
        "▶ Run War Room",
        "↻ Challenge Again",
        "⚖ Compare",
        "👥 Agents",
        "🔎 Evidence",
        "🛡 Guardian",
        "⚖ Judgement",
        "💾 HRM / JOOG",
        "↩ Rollback",
        "➡ Next Gate",
    ):
        assert control in page

    assert 'method="post"' not in page.lower()
    assert "Approve is not execute" in page
    assert "This page itself exposes no execution control" in page


def test_war_room_ui_shows_safe_progress_not_private_reasoning():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")

    for stage in (
        "Understanding",
        "Evidence",
        "Memory",
        "Agents",
        "Challenge",
        "Guardian",
        "Judgement",
        "Solution",
    ):
        assert stage in page
    assert "Private chain-of-thought is never displayed" in page
