from __future__ import annotations

import json

from mission_control import brain, config


def test_brain_status_reports_one_brain_and_all_regions():
    projection = brain.get_public_brain_status()

    assert projection["validation"]["passed"] is True
    assert projection["brain_count"] == 1
    assert projection["regions"] == 14
    assert projection["families"] == 7
    assert projection["agents"] == 78
    assert projection["validation"]["checks"]["proposed_passports"] == 0
    assert projection["validation"]["checks"]["registry_ready_for_activation"] is False
    assert "EXECUTE" not in projection["allowed_outputs"]
    assert len(projection["processing_cycle"]) == 14


def test_brain_dashboard_is_read_only_and_does_not_create_database(
    client, tmp_path, monkeypatch
):
    database_path = tmp_path / "brain-dashboard.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/brain")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "SMI Brain Runtime" in page
    assert "Single-brain boundaries verified" in page
    assert "SMI cannot produce EXECUTE" in page
    assert "Zero default Builder actions" in page
    assert "Human approval required" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/brain").status_code == 405
    assert client.get("/mission/brain/run").status_code == 404
    assert not database_path.exists()


def test_brain_status_json_is_coarse_and_redacted(client):
    response = client.get("/mission/brain/status")
    serialized = response.get_data(as_text=True).lower()
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["brain_count"] == 1
    assert payload["mode"] == "Recommendation-only; no public execution route"
    for private_key in (
        "signing_key",
        "password",
        "secret",
        "token",
        "private_key",
        "message_body",
        "correlation_id",
    ):
        assert private_key not in serialized


def test_brain_projection_contains_no_duplicate_provider_intelligence_worlds():
    serialized = json.dumps(brain.get_public_brain_status()).lower()

    assert "gpt intelligence" not in serialized
    assert "ollama local intelligence" not in serialized
    assert '"brain_count": 1' in serialized
