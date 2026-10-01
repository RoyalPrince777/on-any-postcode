"""Founder API contract for importing reviewed connectivity briefs into SMI."""
from uuid import uuid4

import app as app_module
from mission_control import connectivity_briefs, public_store, web_security


def _client(monkeypatch, *, founder=True):
    monkeypatch.setattr(
        web_security,
        "current_authenticated_user",
        lambda: {
            "id": "11111111-1111-4111-8111-111111111111",
            "name": "Founder",
            "email": "founder@example.test",
            "email_verified": True,
        },
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: founder)
    monkeypatch.setattr(public_store, "ensure_authenticated_user", lambda *a, **k: None)
    return app_module.app.test_client()


def _payload(brief_id, **changes):
    value = {
        "brief_id": brief_id,
        "source_run_id": "a" * 32,
        "title": "SMI 6G + ISAC Brief",
        "completed_at": "2026-10-02T08:00:00+01:00",
        "summary": "Measured evidence only; Founder review remains required.",
        "evidence_links": ["https://www.itu.int/imt-2030"],
        "evidence_score": 72,
        "decision": "watch",
        "source": "chatgpt_automation",
        "expected_last_hash": "",
    }
    value.update(changes)
    return value


def test_put_requires_founder_and_csrf(monkeypatch):
    brief_id = str(uuid4())
    client = _client(monkeypatch, founder=False)
    assert client.put(
        f"/api/smi-organiser/connectivity-briefs/{brief_id}",
        json=_payload(brief_id),
    ).status_code == 403
    client = _client(monkeypatch)
    assert client.put(
        f"/api/smi-organiser/connectivity-briefs/{brief_id}",
        json=_payload(brief_id),
    ).status_code == 403


def test_put_and_get_are_owner_scoped_minimised_and_no_store(monkeypatch):
    brief_id = str(uuid4())
    captured = {}
    saved = {
        "brief_id": brief_id,
        "version": 1,
        "digest": "b" * 64,
        "brief": _payload(brief_id),
        "audit_readback_verified": True,
        "prompt_persisted": False,
        "execution_authorised": False,
        "founder_review_required": True,
        "founder_approved": False,
        "physical_acceptance": False,
        "changed": True,
    }

    def save(owner, brief, **kwargs):
        captured.update(owner=owner, brief=brief, kwargs=kwargs)
        return saved

    monkeypatch.setattr(connectivity_briefs, "upsert", save)
    monkeypatch.setattr(connectivity_briefs, "get", lambda owner, value: saved)
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    response = client.put(
        f"/api/smi-organiser/connectivity-briefs/{brief_id}",
        json=_payload(brief_id),
        headers={"X-OAP-CSRF": "a" * 48},
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.get_json()["prompt_persisted"] is False
    assert captured["brief"].evidence_links == ("https://www.itu.int/imt-2030",)
    assert captured["kwargs"] == {"expected_last_hash": "", "stopped": False}

    read = client.get(f"/api/smi-organiser/connectivity-briefs/{brief_id}")
    assert read.status_code == 200
    assert read.headers["Cache-Control"] == "no-store"


def test_id_link_shape_and_stop_fail_closed(monkeypatch):
    brief_id = str(uuid4())
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    headers = {"X-OAP-CSRF": "a" * 48}
    path = f"/api/smi-organiser/connectivity-briefs/{brief_id}"

    mismatch = client.put(
        path,
        json=_payload(str(uuid4())),
        headers=headers,
    )
    assert mismatch.status_code == 400
    assert mismatch.get_json()["error"]["code"] == "connectivity_brief_id_mismatch"

    bad_links = client.put(
        path,
        json=_payload(brief_id, evidence_links="https://example.test/paper"),
        headers=headers,
    )
    assert bad_links.status_code == 400
    assert bad_links.get_json()["error"]["code"] == "invalid_connectivity_brief_evidence_links"

    monkeypatch.setattr(
        connectivity_briefs,
        "upsert",
        lambda *a, **k: (_ for _ in ()).throw(
            PermissionError("STOP: connectivity brief import blocked")
        ),
    )
    stopped = client.put(
        path,
        json=_payload(brief_id, stopped=True),
        headers=headers,
    )
    assert stopped.status_code == 423
