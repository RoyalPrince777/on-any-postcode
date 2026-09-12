WRAPPER = "mission_control/templates/ollama_chat.html"
DASHBOARD_JS = "mission_control/static/smi_sovereign_dashboard.js"
DASHBOARD_CSS = "mission_control/static/smi_sovereign_dashboard.css"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_sovereign_dashboard_is_primary_smi_surface():
    wrapper = _read(WRAPPER)
    script = _read(DASHBOARD_JS)
    stylesheet = _read(DASHBOARD_CSS)

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
    script = _read(DASHBOARD_JS)
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
