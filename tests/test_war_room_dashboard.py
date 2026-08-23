from __future__ import annotations

import json

from mission_control import config, war_room


def test_war_room_scope_has_no_duplicate_system_or_review_roles():
    validation = war_room.validate_war_room_scope()

    assert validation["passed"] is True
    assert validation["checks"]["duplicate_system_roles"] == 0
    assert validation["checks"]["duplicate_lenses"] == 0
    assert validation["checks"]["duplicate_gaps"] == 0
    assert validation["checks"]["final_authority"] == "Human Authority"


def test_war_room_projection_preserves_authority_boundaries():
    projection = war_room.get_public_war_room()
    flow = {item["component"]: item["role"] for item in projection["flow"]}

    assert projection["engine"]["mode"] == "simulation_only"
    assert projection["engine"]["decision_authority"] is False
    assert projection["controls_enabled"] is False
    assert projection["independent_decision_authority"] is False
    assert flow["SMI"] == "Forms one recommendation"
    assert flow["War Room"] == "Simulates bounded consequences"
    assert flow["Human Authority"] == "Approves or rejects"
    assert "EXECUTE" not in projection["allowed_outputs"]


def test_war_room_dashboard_is_read_only_and_does_not_create_database(
    client, tmp_path, monkeypatch
):
    database_path = tmp_path / "war-room.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/war-room")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "War Room scope verified" in page
    assert "not a second decision-maker" in page
    assert "Missing production gaps" in page
    assert "53 proposed passports remain disabled" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/war-room").status_code == 405
    assert client.post("/mission/war-room/review").status_code == 404
    assert not database_path.exists()


def test_war_room_status_is_coarse_and_redacted(client):
    response = client.get("/mission/war-room/status")
    serialized = response.get_data(as_text=True).lower()
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["validation"]["passed"] is True
    for private_key in (
        "password",
        "secret",
        "token",
        "private_key",
        "correlation_id",
        "message_body",
    ):
        assert private_key not in serialized
    assert "council" not in serialized
    assert '"kaa"' not in serialized
    assert json.dumps(payload).count('"Human Authority"') >= 1
