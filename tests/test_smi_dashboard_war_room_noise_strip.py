from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_and_war_room_strip_noise_preserves_actions():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text()
    dashboard = (ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.js").read_text()
    room = (ROOT / "mission_control" / "static" / "smi_command_centre.js").read_text()
    template = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()

    for selector in (
        ".smi-dashboard-top .smi-kicker",
        ".smi-rail-footer",
        ".smi-command-top small",
        ".smi-command-note",
        ".smi-command-foot",
        ".smi-room-status-note",
    ):
        assert selector in css

    for token in (
        "smi-refresh",
        "data-smi-chat",
        "War Room",
        "21 Signals",
        "Guardian",
        "HRM",
        "Green Gate",
    ):
        assert token in dashboard

    for token in (
        "master-tools",
        "war-room",
        "hrm",
        "function-health",
        "green-gate",
        "Refresh evidence",
        "data-room-stat",
        "data-room-gate",
    ):
        assert token in room

    assert "warRoomUrl" in template
    assert "greenGateUrl" in template
    assert "functionHealthUrl" in template
    assert "signalsUrl" in template


def test_dashboard_war_room_noise_strip_keeps_mobile_navigation_and_touch_targets():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text()
    room = (ROOT / "mission_control" / "static" / "smi_command_centre.js").read_text()

    assert ".smi-command-mobile-views" in css
    assert "min-height:40px" in css
    assert "Presence" in room
    assert "Anatomy" in room
    assert "Evidence" in room


def test_dashboard_war_room_noise_strip_does_not_hide_live_evidence_cards():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text()

    forbidden_hidden = (
        ".smi-room-status-grid",
        ".smi-room-gates",
        ".smi-command-proof",
        ".smi-summary-strip",
        ".smi-command-grid",
        ".smi-command-universe",
        ".smi-command-status-actions",
    )
    for selector in forbidden_hidden:
        assert f"{selector} {{\n  display:none" not in css
        assert f"{selector}{{display:none" not in css
