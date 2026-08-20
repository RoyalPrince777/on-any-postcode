from __future__ import annotations

import json

from mission_control import config, infrastructure


def test_locked_infrastructure_scope_has_exactly_four_unique_modules():
    assert infrastructure.LOCKED_MODULE_NAMES == (
        "Maps",
        "Weather",
        "eSIM",
        "Connectivity",
    )
    assert infrastructure.LOCKED_MODULE_IDS == (
        "maps",
        "weather",
        "esim",
        "connectivity",
    )

    validation = infrastructure.validate_infrastructure_scope()

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"] == {
        "canonical_modules": 4,
        "duplicate_ids": 0,
        "naming_conflicts": 0,
        "ownership_overlaps": 0,
        "mutation_controls": 0,
    }


def test_navigation_mobility_and_health_are_not_owned_modules():
    module_ids = set(infrastructure.LOCKED_MODULE_IDS)
    boundaries = {
        item["id"]: item for item in infrastructure.RELATED_SYSTEM_BOUNDARIES
    }

    assert {"navigation", "mobility", "system_health"}.isdisjoint(module_ids)
    assert boundaries["mobility"]["owner"] == "Separate OAP layer"
    assert "Deliveries, Transport and Travel" in boundaries["mobility"]["relationship"]
    assert boundaries["system_health"]["owner"] == "Shared Mission Control widget"


def test_duplicate_or_overlapping_system_is_rejected():
    overlapping = {
        **infrastructure.LOCKED_INFRASTRUCTURE_MODULES[0],
        "id": "navigation",
        "name": "Navigation",
    }
    validation = infrastructure.validate_infrastructure_scope(
        modules=(*infrastructure.LOCKED_INFRASTRUCTURE_MODULES, overlapping)
    )

    assert validation["passed"] is False
    assert validation["checks"]["ownership_overlaps"] == 1
    assert any("ownership overlaps" in error for error in validation["errors"])
    assert any("Unapproved Infrastructure modules" in error for error in validation["errors"])


def test_infrastructure_ui_is_read_only_and_does_not_create_database(
    client, tmp_path, monkeypatch
):
    database_path = tmp_path / "infrastructure.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/infrastructure")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Infrastructure boundaries verified" in page
    assert "Maps, Weather, eSIM and Connectivity" in page
    assert "No lawful telecom provider approved" in page
    assert "Activation unavailable" in page
    assert "Operational controls unavailable" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/infrastructure").status_code == 405
    assert not database_path.exists()


def test_infrastructure_ui_preserves_system_boundaries(client):
    page = client.get("/mission/infrastructure").get_data(as_text=True)

    assert "Related systems stay separate" in page
    assert "Navigation" in page
    assert "Mobility" in page
    assert "Deliveries, Transport and Travel" in page
    assert "Shared system health" in page
    assert "not a fifth Infrastructure module" in page
    assert "No network control, credentials, Wi-Fi or satellite service" in page


def test_every_proposed_infrastructure_connection_requires_human_approval():
    projection = infrastructure.get_public_infrastructure()

    assert projection["proposed_connections"]
    assert all(
        proposal["status"] == "Requires human approval"
        for proposal in projection["proposed_connections"]
    )
    assert projection["human_authority"]["status"] == "Final approval required"


def test_public_infrastructure_projection_is_redacted_and_non_operational():
    serialized = json.dumps(infrastructure.get_public_infrastructure()).lower()

    for private_key in (
        "secret",
        "token",
        "password",
        "credential_value",
        "correlation_id",
        "mfa",
        "totp",
    ):
        assert private_key not in serialized
    assert '"mutation_enabled": true' not in serialized
    assert '"execute"' not in serialized


def test_infrastructure_route_does_not_reflect_query_input(client):
    attack = '<script>alert("network")</script>'

    page = client.get(
        "/mission/infrastructure", query_string={"provider": attack}
    ).get_data(as_text=True)

    assert attack not in page
    assert "&lt;script&gt;" not in page
