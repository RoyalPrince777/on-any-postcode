from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
DASHBOARD_JS = ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.js"
DASHBOARD_CSS = ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.css"


def test_sovereign_dashboard_is_home_first_and_has_exactly_seven_top_level_rooms():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    script = DASHBOARD_JS.read_text(encoding="utf-8")
    stylesheet = DASHBOARD_CSS.read_text(encoding="utf-8")

    assert "visibleLiveStatus:false" in wrapper
    assert "smi_sovereign_dashboard.css" in wrapper
    assert "smi_sovereign_dashboard.js" in wrapper
    assert "missionsUrl:" in wrapper
    assert "archiveUrl:" in wrapper
    assert "controlCenterUrl:" in wrapper

    for label in ("Chat", "Missions", "War Room", "Agents", "Archive", "Tools", "Control Center"):
        assert f"'{label}'" in script

    assert "homeActions=[" in script
    assert script.count(",'link']") == 5
    assert script.count(",'chat']") == 1
    assert script.count(",'tools']") == 1
    assert "classList.add('smi-sovereign-ready','smi-home-open')" in script
    assert ".smi-home-open .smi-dashboard-layer{display:flex!important}" in stylesheet
    assert "smi-home-open .workspace-grid{display:none!important}" in stylesheet
    assert "approvedWallpaperUrl" in script


def test_dashboard_refresh_is_bounded_and_cannot_read_forever():
    script = DASHBOARD_JS.read_text(encoding="utf-8")
    assert "timeoutMs=4500" in script
    assert "new AbortController()" in script
    assert "signal:controller.signal" in script
    assert "throw new Error('timeout')" in script
    assert "dashboardRefreshing" in script
    assert "Promise.allSettled" in script


def test_dashboard_exposes_exactly_21_canonical_signal_ids():
    script = DASHBOARD_JS.read_text(encoding="utf-8")
    expected = (
        "healthy","starting","warning","critical","offline","learning","maintenance",
        "high_performance","connected","synchronising","memory_active","thinking",
        "mind_healthy","body_healthy","soul_healthy","protected","improving","alert",
        "complete","working","idle",
    )
    for signal_id in expected:
        assert f"['{signal_id}'" in script
    assert len(expected) == 21
    assert "['learning','🟣','Learning'" in script
    assert "['warning','🟡','Warning'" in script
    assert "['healthy','🟢','Healthy'" in script
    assert "['critical','🔴','Critical'" in script


def test_dashboard_buttons_route_to_existing_first_party_rooms_only():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    script = DASHBOARD_JS.read_text(encoding="utf-8")

    assert "mission_control.mission_workspace" in wrapper
    assert "mission_control.agent_intelligence" in wrapper
    assert "smi_organiser.dashboard" in wrapper
    assert "mission_control.infrastructure_dashboard" in wrapper
    assert "mission_control.war_room_dashboard" in wrapper
    assert "data-smi-tools" in script
    assert "document.getElementById('plus-button')?.click()" in script
    assert "Truth Mode." in script
    assert "does not silently deploy, spend, dispatch, migrate or approve consequential actions" in script


def test_home_boot_and_room_navigation_do_not_auto_fetch_status():
    script = DASHBOARD_JS.read_text(encoding="utf-8")
    boot = script[script.index("function boot(){"):]
    go_dashboard = script[script.index("const goDashboard="):script.index("const scrollToPanel=")]

    assert "refresh();" not in go_dashboard
    assert "setInterval" not in boot
    assert "zero status requests on boot" in boot
    assert "smi-refresh" in boot
    assert "addEventListener('click',refresh)" in boot
