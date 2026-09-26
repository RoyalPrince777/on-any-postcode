from pathlib import Path

from mission_control import studio_intelligence

ROOT = Path(__file__).resolve().parents[1]


def test_auto_workspace_routes_to_smallest_sufficient_mode():
    assert studio_intelligence.select_workspace("build me a mobile app and preview")["id"] == "build"
    assert studio_intelligence.select_workspace("inspect this database schema migration")["id"] == "data"
    assert studio_intelligence.select_workspace("debug this code and tests")["id"] == "code"
    assert studio_intelligence.select_workspace("animate this image into a video scene")["id"] == "motion"
    assert studio_intelligence.select_workspace("write a song beat and mix plan")["id"] == "music"
    assert studio_intelligence.select_workspace("deep research with sources")["id"] == "research"
    assert studio_intelligence.select_workspace("quick rewrite")["id"] == "fast"


def test_workspace_preflights_are_real_actions_and_keep_authority_locked(monkeypatch):
    monkeypatch.setattr(studio_intelligence.studio_media_backend, "status", lambda: {
        "configured": True, "scene_builder_ready": True, "bring_alive_ready": True
    })
    monkeypatch.setattr(studio_intelligence.smi_founder_assets, "schema_status", lambda: {
        "schema_ready": True, "studio_generated_asset_count": 1
    })
    monkeypatch.setattr(studio_intelligence.smi_receipt_backend, "backend_configuration_status", lambda: {
        "durable_backend_configured": True
    })
    monkeypatch.setattr(studio_intelligence.postgres_db, "postgres_status", lambda: {
        "initialized": True
    })
    monkeypatch.setattr(studio_intelligence.capability_fabric, "status", lambda: {
        "provider_neutral": True
    })

    for workspace_id in ("build", "data", "code", "fast", "motion", "music", "omni", "research"):
        result = studio_intelligence.workspace_preflight(workspace_id)
        assert result["action"]
        assert result["execution_granted"] is False
        assert result["human_authority_final"] is True
        assert result["privacy_fail_closed"] is True
        assert result["stop_available"] is True

    data = studio_intelligence.workspace_preflight("data")
    assert data["write_performed"] is False
    assert data["migration_preview_supported"] is True

    music = studio_intelligence.workspace_preflight("music")
    assert music["audio_generation_proven"] is False
    assert music["rights_proof_required"] is True


def test_studio_live_certificate_requires_real_indexed_generation(monkeypatch):
    monkeypatch.setattr(studio_intelligence.studio_media_backend, "status", lambda: {
        "configured": True
    })
    monkeypatch.setattr(studio_intelligence.smi_receipt_backend, "backend_configuration_status", lambda: {
        "durable_backend_configured": True
    })
    monkeypatch.setattr(studio_intelligence.smi_founder_assets, "schema_status", lambda: {
        "schema_ready": True, "studio_generated_asset_count": 0, "error": None
    })
    assert studio_intelligence.status()["full_live_certificate"] is False

    monkeypatch.setattr(studio_intelligence.smi_founder_assets, "schema_status", lambda: {
        "schema_ready": True, "studio_generated_asset_count": 2, "error": None
    })
    state = studio_intelligence.status()
    assert state["full_live_certificate"] is True
    assert state["full_live_certificate_reason"] == "proven_generated_artifact_indexed"


def test_threat_posture_fails_closed(monkeypatch):
    monkeypatch.setattr(studio_intelligence.studio_media_backend, "status", lambda: {"configured": False})
    monkeypatch.setattr(studio_intelligence.smi_founder_assets, "schema_status", lambda: {"schema_ready": True})
    monkeypatch.setattr(studio_intelligence.smi_receipt_backend, "backend_configuration_status", lambda: {"durable_backend_configured": True})
    posture = studio_intelligence.threat_posture()
    assert posture["provider_outage_fails_closed"] is True
    assert posture["silent_database_write_allowed"] is False
    assert posture["silent_publish_allowed"] is False
    assert posture["silent_distribution_allowed"] is False
    assert posture["silent_payment_allowed"] is False
    assert posture["external_named_agent_authority"] is False


def test_stream_and_ui_carry_real_workspace_and_button_proof_contract():
    views = (ROOT / "mission_control" / "views.py").read_text()
    final = (ROOT / "mission_control" / "static" / "smi_chat_final.js").read_text()
    template = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()

    stream_index = views.index("events = smi_chat_runtime.chat_events(")
    stream_block = views[stream_index:stream_index + 1200]
    assert 'studio_workspace=str(payload.get("studio_workspace") or "auto")' in stream_block
    assert '@bp.get("/studio/workspace/<workspace_id>")' in views
    assert '@bp.get("/studio/threat-posture")' in views

    for workspace_id in ("build", "data", "code", "fast", "motion", "music", "omni", "research"):
        assert f'"studio-workspace-{workspace_id}"' in views
    assert "studioWorkspaceUrl" in template
    assert "studioThreatPostureUrl" in template
    assert 'recordButtonProof("studio-workspace-"+id' in final
    assert "Studio Threat Posture" in final
