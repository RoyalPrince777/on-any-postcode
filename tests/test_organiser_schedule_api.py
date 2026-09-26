"""Founder API contract for mirroring schedules into SMI Organiser."""
import app as app_module
from mission_control import organiser_schedules, public_store, web_security


def _client(monkeypatch, *, founder=True):
    monkeypatch.setattr(
        web_security, "current_authenticated_user",
        lambda: {
            "id": "11111111-1111-4111-8111-111111111111",
            "name": "Founder", "email": "founder@example.test",
        },
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: founder)
    monkeypatch.setattr(public_store, "ensure_authenticated_user", lambda *a, **k: None)
    return app_module.app.test_client()


def _payload(**changes):
    value = {
        "title": "OAP Data Research",
        "schedule": "BEGIN:VEVENT\nRRULE:FREQ=WEEKLY;BYDAY=FR\nEND:VEVENT",
        "timing_mode": "flexible_schedule", "timezone": "Europe/London",
        "enabled": True, "source": "chatgpt_automation",
        "expected_last_hash": "",
    }
    value.update(changes)
    return value


def test_put_requires_founder_and_csrf(monkeypatch):
    external_id = "a" * 32
    client = _client(monkeypatch, founder=False)
    assert client.put(f"/api/smi-organiser/schedules/{external_id}", json=_payload()).status_code == 403
    client = _client(monkeypatch)
    assert client.put(f"/api/smi-organiser/schedules/{external_id}", json=_payload()).status_code == 403


def test_put_and_get_are_owner_scoped_and_no_store(monkeypatch):
    external_id = "a" * 32
    saved = {
        "external_id": external_id, "version": 1, "digest": "b" * 64,
        "schedule": _payload(), "audit_readback_verified": True,
        "prompt_persisted": False, "execution_authorised": False, "changed": True,
    }
    monkeypatch.setattr(organiser_schedules, "upsert", lambda owner, schedule, **kw: saved)
    monkeypatch.setattr(organiser_schedules, "get", lambda owner, schedule_id: saved)
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    response = client.put(
        f"/api/smi-organiser/schedules/{external_id}",
        json=_payload(), headers={"X-OAP-CSRF": "a" * 48},
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.get_json()["prompt_persisted"] is False
    read = client.get(f"/api/smi-organiser/schedules/{external_id}")
    assert read.status_code == 200
    assert read.headers["Cache-Control"] == "no-store"


def test_stop_and_id_mismatch_fail_closed(monkeypatch):
    external_id = "a" * 32
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    headers = {"X-OAP-CSRF": "a" * 48}
    mismatch = client.put(
        f"/api/smi-organiser/schedules/{external_id}",
        json=_payload(external_id="b" * 32), headers=headers,
    )
    assert mismatch.status_code == 400
    monkeypatch.setattr(
        organiser_schedules, "upsert",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError("STOP: schedule mirror blocked")),
    )
    stopped = client.put(
        f"/api/smi-organiser/schedules/{external_id}",
        json=_payload(stopped=True), headers=headers,
    )
    assert stopped.status_code == 423
