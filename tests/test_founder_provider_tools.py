from __future__ import annotations

import json
from pathlib import Path

import pytest

from mission_control import founder_neon, founder_render, web_security


def test_founder_tools_are_denied_to_authenticated_non_founder(client, monkeypatch):
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: False)

    for path in (
        "/mission/tools/github/status",
        "/mission/tools/render/status",
        "/mission/tools/render/services",
        "/mission/tools/neon/status",
    ):
        response = client.get(path)
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "human_authority_required"


def test_new_provider_routes_require_authentication(anonymous_client):
    for path in (
        "/mission/tools/render/status",
        "/mission/tools/render/services",
        "/mission/tools/neon/status",
        "/mission/tools/neon/project",
    ):
        response = anonymous_client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"


def test_render_reader_is_limited_to_approved_oap_services(monkeypatch):
    adapter = founder_render.FounderRenderReadAdapter(token="test-render-token")

    def fake_request(path, *, query=None):
        del query
        if path.endswith("srv-d8gfsv0jo6nc73egdlf0"):
            return {
                "id": "srv-d8gfsv0jo6nc73egdlf0",
                "name": "on-any-postcode",
                "type": "web_service",
                "branch": "main",
                "autoDeploy": "no",
                "suspended": "not_suspended",
                "updatedAt": "2026-09-10T11:06:32Z",
                "serviceDetails": {
                    "runtime": "python",
                    "region": "oregon",
                    "plan": "free",
                    "healthCheckPath": "/healthz",
                    "numInstances": 1,
                    "url": "https://on-any-postcode.onrender.com",
                },
            }
        if path.endswith("srv-da6tp615efls73ct81q0"):
            return {
                "id": "srv-da6tp615efls73ct81q0",
                "name": "oap-smi",
                "type": "web_service",
                "branch": "main",
                "autoDeploy": "no",
                "suspended": "not_suspended",
                "updatedAt": "2026-09-10T10:52:17Z",
                "serviceDetails": {
                    "runtime": "python",
                    "region": "oregon",
                    "plan": "free",
                    "healthCheckPath": "/healthz",
                    "numInstances": 1,
                    "url": "https://oap-smi.onrender.com",
                },
            }
        raise AssertionError(path)

    monkeypatch.setattr(adapter, "_request_json", fake_request)
    result = adapter.services_summary()

    assert [item["alias"] for item in result.data["services"]] == ["world", "smi"]
    assert all(item["health_check_path"] == "/healthz" for item in result.data["services"])
    with pytest.raises(PermissionError):
        adapter.deploys("other-service")


def test_render_logs_are_bounded_and_secret_redacted(monkeypatch):
    adapter = founder_render.FounderRenderReadAdapter(token="test-render-token")

    def fake_request(path, *, query=None):
        assert path == "/logs"
        assert query["resource"] == ["srv-d8gfsv0jo6nc73egdlf0"]
        return {
            "logs": [
                {
                    "timestamp": "2026-09-10T11:00:00Z",
                    "labels": [
                        {"name": "level", "value": "error"},
                        {"name": "resource", "value": "should-not-leak"},
                    ],
                    "message": "Authorization: Bearer super-secret-token DATABASE_URL=postgresql://user:pass@host/db",
                }
            ]
        }

    monkeypatch.setattr(adapter, "_request_json", fake_request)
    result = adapter.logs("world", limit=100)
    serialized = json.dumps(result.data)

    assert result.data["logs"][0]["labels"] == {"level": "error"}
    assert "super-secret-token" not in serialized
    assert "postgresql://" not in serialized
    assert "[REDACTED]" in serialized


def test_neon_database_status_reuses_redacted_cached_probe(monkeypatch):
    adapter = founder_neon.FounderNeonReadAdapter(token="test-neon-token")
    monkeypatch.setattr(
        founder_neon.database,
        "db_status",
        lambda: {
            "backend": "postgresql",
            "configured": True,
            "reachable": False,
            "initialized": False,
            "pending": ["0001"],
            "checksum_mismatches": [],
            "error": "database_unavailable",
            "db_path": None,
        },
    )

    result = adapter.database_status().data

    assert result == {
        "backend": "postgresql",
        "configured": True,
        "reachable": False,
        "initialized": False,
        "pending": ["0001"],
        "checksum_mismatches": [],
        "error": "database_unavailable",
    }


def test_neon_project_projection_drops_owner_identity_and_secrets(monkeypatch):
    adapter = founder_neon.FounderNeonReadAdapter(token="test-neon-token")
    monkeypatch.setattr(
        adapter,
        "_request_json",
        lambda path: {
            "project": {
                "id": "autumn-thunder-02808657",
                "name": "oap-production-db",
                "region_id": "aws-us-west-2",
                "pg_version": 17,
                "data_transfer_bytes": 5525244200,
                "consumption_period_start": "2026-09-01T00:00:00Z",
                "consumption_period_end": "2026-10-01T00:00:00Z",
                "owner": {
                    "subscription_type": "free_v3",
                    "email": "private-owner@example.test",
                },
                "connection_uri": "postgresql://secret@host/db",
            }
        },
    )

    result = adapter.project_summary().data
    serialized = json.dumps(result)

    assert result["project"]["plan"] == "free_v3"
    assert result["project"]["data_transfer_bytes"] == 5525244200
    assert "private-owner@example.test" not in serialized
    assert "postgresql://" not in serialized


def test_render_and_neon_routes_expose_no_mutation_endpoint():
    source = Path("mission_control/founder_tool_views.py").read_text(encoding="utf-8")

    assert '@bp.post("/tools/render' not in source
    assert '@bp.post("/tools/neon' not in source
    assert "founder_only=True" in source
