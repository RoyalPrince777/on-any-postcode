from pathlib import Path


def test_unified_incoming_projection_is_first_party():
    source = Path("mission_control/link_incoming.py").read_text(encoding="utf-8")

    assert "external_notification_provider_required" in source
    assert '"external_notification_provider_required": False' in source
    assert "link_request" in source
    assert "missed_call" in source
    assert "circle_invite" in source


def test_unified_incoming_requires_existing_sources():
    source = Path("mission_control/link_incoming.py").read_text(encoding="utf-8")

    for table in (
        "messages",
        "link_relationships",
        "link_voice_notes",
        "link_call_sessions",
        "link_circle_invites",
        "link_circles",
    ):
        assert f'"{table}"' in source


def test_unified_incoming_api_is_authenticated():
    source = Path("mission_control/link_incoming_routes.py").read_text(encoding="utf-8")

    assert '@bp.get("/linkup/incoming/status")' in source
    assert '@bp.get("/linkup/incoming")' in source
    assert source.count("@web_security.login_required(api=True)") == 2


def test_linkup_template_loads_unified_incoming():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "data-oap-incoming-unified" in page
    assert "linkup_incoming.js" in page


def test_unified_incoming_client_polls_and_opens_links():
    script = Path("static/linkup_incoming.js").read_text(encoding="utf-8")

    assert "/linkup/incoming/status" in script
    assert "/linkup/incoming" in script
    assert "window.setInterval(poll, 5000)" in script
    assert 'event.event_type === "link"' in script
