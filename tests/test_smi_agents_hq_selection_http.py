"""Founder-only mission selection never spawns or impersonates agents."""
import app as app_module
from mission_control import web_security


def _client(monkeypatch, founder=True):
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: {
        "id": "11111111-1111-4111-8111-111111111111", "name": "Founder",
    })
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: founder)
    client = app_module.app.test_client()
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    return client


def test_dynamic_selection_founder_only(monkeypatch):
    response = _client(monkeypatch, founder=False).post(
        "/mission/organiser/agents-hq/select",
        json={"mission": "review github code"},
        headers={"X-OAP-CSRF": "a" * 48},
    )
    assert response.status_code == 403


def test_dynamic_selection_requires_csrf(monkeypatch):
    response = _client(monkeypatch).post(
        "/mission/organiser/agents-hq/select",
        json={"mission": "review github code"},
    )
    assert response.status_code == 403


def test_dynamic_selection_grounded_and_advisory(monkeypatch):
    response = _client(monkeypatch).post(
        "/mission/organiser/agents-hq/select",
        json={"mission": "review github code", "task_type": "TECHNICAL"},
        headers={"X-OAP-CSRF": "a" * 48},
    )
    assert response.status_code == 200
    result = response.get_json()
    assert "Neo" in result["recommended_specialists"]
    assert result["advisory_only"] and result["founder_final"]
    assert not result["execution_authorised"]
    assert not result["agent_messages_generated"]
    assert response.headers["Cache-Control"] == "no-store"


def test_dynamic_selection_rejects_bad_mission(monkeypatch):
    response = _client(monkeypatch).post(
        "/mission/organiser/agents-hq/select",
        json={"mission": "x" * 2001},
        headers={"X-OAP-CSRF": "a" * 48},
    )
    assert response.status_code == 400
