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
    assert "Live Intelligence Monitor" not in wrapper
    assert "visibleLiveStatus:false" in wrapper
    assert "smi_sovereign_dashboard.css" in wrapper
    assert "smi_sovereign_dashboard.js" in wrapper
    assert "warRoomStatusUrl" in wrapper
    assert "mission_control.smi_workbench_status" in wrapper
    assert "mission_control.smi_chat_health" in wrapper
    assert "mission_control.war_room_status" in wrapper
    assert "founder_recovery.recover_founder" in wrapper
    assert "smi-status-open" in script
    assert "smi-dashboard-mode" not in script
    assert "smi-chat-mode" not in script
    assert "smi-status-open .workspace-grid{display:grid!important}" in stylesheet
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


def test_dashboard_is_quiet_first_party_surface_without_provider_panels():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    script = DASHBOARD_JS.read_text(encoding="utf-8")

    assert "OAP first-party surface" in wrapper
    assert "publicOapUrl:'/'" in wrapper
    assert "provider_fabric" not in wrapper

    for control in (
        "'SMI Chat'",
        "'War Room'",
        "'21 Signals'",
        "'Guardian'",
        "'HRM'",
        "'Green Gate'",
    ):
        assert control in script

    for duplicate in (
        "'Brain'",
        "'Agents'",
        "'Infrastructure'",
        "'Judgement'",
        "'Improvement'",
        "'Routes'",
    ):
        assert duplicate not in script

    # Legacy tool identifiers may survive in non-rendered wrapper comments for
    # compatibility, but the actual dashboard JavaScript must not render them.
    for provider_name in ("Render", "GitHub", "Neon"):
        assert provider_name not in script
    assert "credentials:'same-origin'" in script
    assert "Six first-party controls" in script
    assert "External infrastructure and evidence sources stay behind governed OAP server routes" in script
