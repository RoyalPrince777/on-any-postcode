from pathlib import Path


def test_link_share_schema_activation_is_serialized():
    source = Path("mission_control/link_share.py").read_text(encoding="utf-8")

    assert "pg_advisory_xact_lock" in source
    assert "oap_link_share_v1" in source
    assert "CREATE TABLE IF NOT EXISTS link_shares" in source


def test_link_share_routes_are_first_party_and_guarded():
    source = Path("mission_control/link_voice_routes.py").read_text(encoding="utf-8")

    assert '@bp.get("/linkup/share/status")' in source
    assert '@bp.post("/linkup/share")' in source
    assert '@bp.get("/linkup/share/<share_id>/media")' in source
    assert '@bp.delete("/linkup/share/<share_id>")' in source
    assert "link_share.MAX_SHARE_BYTES" in source


def test_link_share_client_unlocks_only_after_runtime_status():
    script = Path("static/linkup_share.js").read_text(encoding="utf-8")

    assert '/linkup/share/status' in script
    assert 'status.ready === true && status.first_party === true' in script
    assert 'control.disabled = !state.ready' in script


def test_link_share_is_bounded_and_first_party():
    source = Path("mission_control/link_share.py").read_text(encoding="utf-8")

    assert "MAX_SHARE_BYTES = 25 * 1024 * 1024" in source
    assert "MAX_SENDER_STORAGE_BYTES = 500 * 1024 * 1024" in source
    assert '"external_media_provider_required": False' in source
    assert "link_relationships.accepted_between" in source
    assert "linkup_safety.blocked_between" in source


def test_linkup_messaging_gate_uses_share_not_ping():
    source = Path("app.py").read_text(encoding="utf-8")

    assert 'and link_share.status().get("ready")' in source
    assert 'and link_ping.status().get("ready")' not in source


def test_link_share_explicit_cli_and_boot_gate_exist():
    source = Path("mission_control/__init__.py").read_text(encoding="utf-8")

    assert "OAP_LINK_SHARE_MIGRATION_ON_BOOT" in source
    assert 'oap-link-share-status' in source
    assert 'oap-init-link-share' in source
