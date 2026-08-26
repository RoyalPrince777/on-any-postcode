from __future__ import annotations

from mission_control import status


def _database_status():
    return {
        "exists": True,
        "initialized": True,
        "backend": "postgresql",
        "db_path": "postgresql://redacted",
        "error": None,
        "brain_runtime_initialized": True,
    }


def _judgement_pending():
    return {
        "schema_ready": True,
        "automated_sections": 5,
        "total_sections": 6,
        "reviews": 0,
        "human_decisions": 0,
        "ready": False,
        "error": None,
    }


def _provider_status(runtime_verified: int = 0):
    return {
        "architecture_passed": True,
        "slots": 8,
        "wired": 4,
        "configured": 3,
        "runtime_verified": runtime_verified,
        "consequential_execution_enabled": False,
        "human_authority_required": True,
    }


def _prepare(monkeypatch, *, runtime_verified: int = 0):
    monkeypatch.setattr(status, "db_status", _database_status)
    monkeypatch.setattr(status.config, "OAP_LOCAL_MODE", False)
    monkeypatch.setattr(status.judgement, "status", _judgement_pending)
    monkeypatch.setattr(
        status.provider_fabric,
        "get_coarse_provider_status",
        lambda: _provider_status(runtime_verified),
    )


def _components_by_label(projection):
    return {item["label"]: item for item in projection["components"]}


def test_guardian_status_comes_from_constitutional_engine(monkeypatch):
    _prepare(monkeypatch, runtime_verified=2)

    projection = status.get_public_gateway_status()
    components = _components_by_label(projection)

    assert components["Guardian"] == {
        "label": "Guardian",
        "value": "Constitutional gate ready",
        "state": "healthy",
    }
    assert components["Guardian"]["value"] != "Not connected"
    assert projection["status_truth"]["guardian_source"] == "constitutional_engine"


def test_configured_cloud_mode_is_not_reported_as_degraded(monkeypatch):
    _prepare(monkeypatch)
    monkeypatch.setattr(status, "_probe_ollama", lambda: False)

    projection = status.get_public_gateway_status()
    components = _components_by_label(projection)

    assert projection["mode"] == "Configured Mode"
    assert components["Local Mode"] == {
        "label": "Local Mode",
        "value": "Disabled by configuration",
        "state": "healthy",
    }
    assert components["Local Ollama"] == {
        "label": "Local Ollama",
        "value": "Degraded local endpoint · optional in configured mode",
        "state": "healthy",
    }


def test_provider_fabric_status_separates_configuration_from_runtime_proof(monkeypatch):
    _prepare(monkeypatch, runtime_verified=1)
    provider = _provider_status(runtime_verified=1)

    projection = status.get_public_gateway_status()
    components = _components_by_label(projection)

    assert components["Provider Fabric"] == {
        "label": "Provider Fabric",
        "value": "3 configured · 1 runtime verified",
        "state": "healthy",
    }
    assert projection["provider_summary"] == provider
    assert projection["status_truth"] == {
        "fixed_live_labels": False,
        "external_network_probe_on_status": False,
        "guardian_source": "constitutional_engine",
        "provider_source": "configuration_and_observed_delivery",
        "approval_source": "judgement_and_human_authority_evidence",
    }
    assert projection["human_authority"]["status"] == "Final approval required"


def test_postgres_approval_schema_does_not_fake_human_evidence(monkeypatch):
    _prepare(monkeypatch)

    projection = status.get_public_gateway_status()
    components = _components_by_label(projection)
    summary = projection["approval_summary"]

    assert summary["initialized"] is True
    assert summary["evidence_ready"] is False
    assert summary["counts"] == {"reviews": 0, "human_decisions": 0}
    assert summary["automated_sections"] == 5
    assert summary["total_sections"] == 6
    assert summary["message"] == (
        "Judgement schema ready; Human Authority evidence pending"
    )
    assert components["Approval Queue"] == {
        "label": "Approval Queue",
        "value": "Schema ready · Human Authority evidence pending · 0 decisions",
        "state": "degraded",
    }


def test_postgres_approval_turns_healthy_only_with_real_human_decision(monkeypatch):
    _prepare(monkeypatch)
    monkeypatch.setattr(
        status.judgement,
        "status",
        lambda: {
            "schema_ready": True,
            "automated_sections": 5,
            "total_sections": 6,
            "reviews": 3,
            "human_decisions": 1,
            "ready": True,
            "error": None,
        },
    )

    projection = status.get_public_gateway_status()
    components = _components_by_label(projection)

    assert projection["approval_summary"]["counts"] == {
        "reviews": 3,
        "human_decisions": 1,
    }
    assert projection["approval_summary"]["evidence_ready"] is True
    assert components["Approval Queue"] == {
        "label": "Approval Queue",
        "value": "Human Authority evidence verified · 1 decisions",
        "state": "healthy",
    }
