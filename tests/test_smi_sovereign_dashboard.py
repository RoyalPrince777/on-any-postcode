from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
DASHBOARD_JS = ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.js"
DASHBOARD_CSS = ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.css"


def test_sovereign_dashboard_is_primary_smi_surface():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    script = DASHBOARD_JS.read_text(encoding="utf-8")
    stylesheet = DASHBOARD_CSS.read_text(encoding="utf-8")

    assert "Sovereign Megaverse Intelligence" in wrapper
    assert "Live Intelligence Monitor" in wrapper
    assert "smi_sovereign_dashboard.css" in wrapper
    assert "smi_sovereign_dashboard.js" in wrapper
    assert "warRoomStatusUrl" in wrapper
    assert "mission_control.smi_workbench_status" in wrapper
    assert "mission_control.smi_chat_health" in wrapper
    assert "mission_control.war_room_status" in wrapper
    assert "founder_recovery.recover_founder" in wrapper
    assert "smi-dashboard-mode" in script
    assert "smi-chat-mode" in script
    assert "Default deny." in script
    assert "Human Authority final" in script
    assert "green only" not in script.lower()
    assert ".smi-dashboard-layer" in stylesheet


def test_dashboard_exposes_exactly_21_canonical_signal_ids():
    script = DASHBOARD_JS.read_text(encoding="utf-8")
    expected = (
        "healthy",
        "starting",
        "warning",
        "critical",
        "offline",
        "learning",
        "maintenance",
        "high_performance",
        "connected",
        "synchronising",
        "memory_active",
        "thinking",
        "mind_healthy",
        "body_healthy",
        "soul_healthy",
        "protected",
        "improving",
        "alert",
        "complete",
        "working",
        "idle",
    )
    for signal_id in expected:
        assert f"['{signal_id}'" in script
    assert len(expected) == 21
    assert "['learning','🟣','Learning'" in script
    assert "['warning','🟡','Warning'" in script
    assert "['healthy','🟢','Healthy'" in script
    assert "['critical','🔴','Critical'" in script
    assert "['busy_high_load'" not in script
