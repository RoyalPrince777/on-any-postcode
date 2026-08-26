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


def _components_by_label(projection):
    return {item["label"]: item for item in projection["components"]}


def test_guardian_status_comes_from_constitutional_engine(monkeypatch):
    monkeypatch.setattr(status, "db_status", _database_status)
    monkeypatch.setattr(status.config, "OAP_LOCAL_MODE", False)
    monkeypatch.setattr(
        status.provider_fabric,
        "get_coarse_provider_status",
        lambda: {
            "architecture_passed": True,
            "slots": 8,
            "wired": 4,
            "configured": 3,
            "runtime_verified": 2,
            "consequential_execution_enabled": False,
            "human_authority_required": True,
        },
    )

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
    monkeypatch.setattr(status, "db_status", _database_status)
    monkeypatch.setattr(status.config, "OAP_LOCAL_MODE", False)
    monkeypatch.setattr(
        status.provider_fabric,
        "get_coarse_provider_status",
        lambda: {
            "architecture_passed": True,
            "slots": 8,
            "wired": 4,
            "configured": 3,
            "runtime_verified": 0,
            "consequential_execution_enabled": False,
            "human_authority_required": True,
        },
    )

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
        "value": "Optional local model inactive",
        "state": "healthy",
    }


def test_provider_fabric_status_separates_configuration_from_runtime_proof(monkeypatch):
    monkeypatch.setattr(status, "db_status", _database_status)
    monkeypatch.setattr(status.config, "OAP_LOCAL_MODE", False)
    provider = {
        "architecture_passed": True,
        "slots": 8,
        "wired": 4,
        "configured": 3,
        "runtime_verified": 1,
        "consequential_execution_enabled": False,
        "human_authority_required": True,
    }
    monkeypatch.setattr(
        status.provider_fabric,
        "get_coarse_provider_status",
        lambda: dict(provider),
    )

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
    }
    assert projection["human_authority"]["status"] == "Final approval required"
