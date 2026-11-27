"""Acceptance and security boundaries for SMI machine learning."""

from pathlib import Path

import app as app_module
import numpy as np
import pytest
from mission_control import smi_machine_learning_runtime as runtime, web_security


def _client(monkeypatch, *, authenticated=True, founder=True):
    user = {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Founder",
        "email": "founder@example.test",
    }
    monkeypatch.setattr(
        web_security,
        "current_authenticated_user",
        lambda: user if authenticated else None,
    )
    monkeypatch.setattr(
        web_security,
        "private_authority_allowed",
        lambda _user: founder,
    )
    return app_module.app.test_client()


def test_all_video_algorithms_pass_synthetic_acceptance():
    receipt = runtime.synthetic_acceptance()
    assert receipt["passed"] is True
    assert len(receipt["checks"]) == 8
    assert all(receipt["checks"].values())
    assert receipt["production_fitness"] == "unknown"
    assert receipt["publication_granted"] is False


def test_bounded_local_evaluation_keeps_production_unknown():
    result = runtime.evaluate({
        "model": "linear",
        "features": [[0, 0], [1, 0], [0, 1], [1, 1]],
        "target": [2, 5, 1, 4],
    })
    assert result["metric"]["training_rmse"] < 1e-8
    assert result["production_fitness"] == "unknown"
    assert result["publication_granted"] is False


@pytest.mark.parametrize("payload", [
    {"model": "unknown", "features": [[1]], "target": [1]},
    {"model": "linear", "features": [[float("nan")]], "target": [1]},
    {"model": "linear", "features": [[1], [2]], "target": [1]},
])
def test_invalid_or_unbounded_requests_fail_closed(payload):
    with pytest.raises(ValueError):
        runtime.evaluate(payload)


def test_kmeans_is_unsupervised_and_bounded():
    points = np.vstack((np.zeros((5, 2)), np.ones((5, 2)) * 10))
    result = runtime.evaluate({"model": "kmeans", "features": points.tolist(), "clusters": 2})
    assert len(set(result["predictions"])) == 2
    assert result["training_only"] is True


def test_routes_are_founder_only_and_mutation_is_csrf_guarded():
    source = Path("mission_control/smi_machine_learning_views.py").read_text(
        encoding="utf-8"
    )
    assert source.count("founder_only=True") == 3
    assert '@bp.post("/ml/evaluate")' in source
    assert "web_security.csrf_valid(request)" in source


def test_live_route_map_denies_anonymous_and_non_founder(monkeypatch):
    anonymous = _client(monkeypatch, authenticated=False)
    response = anonymous.get("/mission/ml/status")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"

    non_founder = _client(monkeypatch, founder=False)
    response = non_founder.get("/mission/ml/status")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "human_authority_required"


def test_founder_can_read_status_and_synthetic_receipt(monkeypatch):
    client = _client(monkeypatch)
    status_response = client.get("/mission/ml/status")
    assert status_response.status_code == 200
    assert status_response.headers["Cache-Control"] == "no-store"
    assert status_response.get_json()["algorithm_count"] == 8
    assert status_response.get_json()["production_fitness"] == "unknown"

    verify_response = client.get("/mission/ml/verify")
    assert verify_response.status_code == 200
    assert verify_response.get_json()["passed"] is True
    assert verify_response.get_json()["redmi_a5_runtime"] == "unknown"


def test_founder_evaluation_requires_csrf_and_remains_training_only(monkeypatch):
    client = _client(monkeypatch)
    payload = {
        "model": "linear",
        "features": [[0, 0], [1, 0], [0, 1], [1, 1]],
        "target": [2, 5, 1, 4],
    }
    denied = client.post("/mission/ml/evaluate", json=payload)
    assert denied.status_code == 403
    assert denied.get_json()["error"] == "csrf_failed"

    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    accepted = client.post(
        "/mission/ml/evaluate",
        json=payload,
        headers={"X-OAP-CSRF": "a" * 48},
    )
    assert accepted.status_code == 200
    result = accepted.get_json()
    assert result["training_only"] is True
    assert result["production_fitness"] == "unknown"
    assert result["publication_granted"] is False
