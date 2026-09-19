from pathlib import Path

from mission_control import link_ping


def test_ping_schema_is_explicit_and_additive():
    result = link_ping.init_schema(dry_run=True)

    assert result["version"] == "link_ping_v1"
    assert result["applied"] is False
    statements = " ".join(result["statements"])
    assert "CREATE TABLE IF NOT EXISTS link_ping_events" in statements
    assert "CREATE TABLE IF NOT EXISTS link_ping_mutes" in statements
    assert "DROP TABLE" not in statements
    assert "ALTER TABLE" not in statements
    source = Path("mission_control/link_ping.py").read_text(encoding="utf-8")
    assert "pg_advisory_xact_lock" in source


def test_ping_rejects_invalid_intensity_before_store_access(monkeypatch):
    monkeypatch.setattr(link_ping, "_peer_guard", lambda first, second: (str(first), str(second)))
    monkeypatch.setattr(link_ping, "_muted", lambda recipient, sender: False)

    try:
        link_ping.send(
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            intensity="blast",
        )
    except ValueError as exc:
        assert str(exc) == "invalid_ping_intensity"
    else:
        raise AssertionError("invalid Ping Up intensity must fail closed")


def test_ping_ui_and_client_runtime_are_wired():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")
    script = Path("static/linkup_ping.js").read_text(encoding="utf-8")

    assert "Ping Up" in page
    assert "Double Ping" in page
    assert "Mute Ping" in page
    assert "data-oap-incoming-pings" in page
    assert "linkup_ping.js" in page

    assert "/linkup/ping/status" in script
    assert "/linkup/ping/incoming" in script
    assert "/linkup/ping/mute" in script
    assert "playPingTone" in script
    assert "navigator.vibrate" in script


def test_ping_runtime_is_first_party_and_bodyless():
    source = Path("mission_control/link_ping.py").read_text(encoding="utf-8")

    assert "message_body_stored" in source
    assert '"message_body_stored": False' in source
    assert "link_relationships.accepted_between" in source
    assert "linkup_safety.blocked_between" in source
    assert "MAX_PINGS_PER_MINUTE" in source
    assert "PING_TTL_MINUTES" in source


def test_ping_routes_require_authenticated_linkup_surface():
    source = Path("mission_control/link_ping_routes.py").read_text(encoding="utf-8")

    assert '@bp.post("/linkup/ping")' in source
    assert '@bp.get("/linkup/ping/incoming")' in source
    assert '@bp.post("/linkup/ping/<ping_id>/seen")' in source
    assert '@bp.post("/linkup/ping/mute")' in source
    assert source.count("@web_security.login_required(api=True)") >= 5
