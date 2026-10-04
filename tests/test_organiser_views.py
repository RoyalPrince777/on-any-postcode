"""Founder UI contract for the SMI Archive organiser surface."""
import app as app_module
from mission_control import (
    connectivity_briefs,
    organiser_schedules,
    public_store,
    web_security,
)


def _client(monkeypatch, *, founder=True):
    monkeypatch.setattr(
        web_security,
        "current_authenticated_user",
        lambda: {
            "id": "11111111-1111-4111-8111-111111111111",
            "name": "Founder", "email": "founder@example.test",
        },
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: founder)
    monkeypatch.setattr(public_store, "ensure_authenticated_user", lambda *a, **k: None)
    monkeypatch.setattr(organiser_schedules, "list_all", lambda owner: ())
    monkeypatch.setattr(connectivity_briefs, "list_all", lambda owner: ())
    return app_module.app.test_client()


def test_organiser_dashboard_is_founder_only_and_truthful(monkeypatch):
    blocked = _client(monkeypatch, founder=False)
    assert blocked.get("/mission/organiser").status_code == 403

    client = _client(monkeypatch)
    response = client.get("/mission/organiser")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "SMI Archive" in page
    assert "History" in page
    assert "Synthetic Mind Intelligence" in page
    assert "Sovereign Megaverse Intelligence" in page
    assert "Synthetic Machine Intelligence" in page
    assert "The Claw Test" in page
    assert "What can break this?" in page
    assert "No owner-scoped schedule receipt has reached SMI yet" in page
    assert "No reviewed briefing receipt exists inside OAP" in page
    assert "Automation authority" in page
    assert "None" in page


def test_connectivity_brief_import_requires_csrf(monkeypatch):
    client = _client(monkeypatch)
    response = client.post("/mission/organiser/connectivity-briefs", data={})
    assert response.status_code == 403
    assert "csrf_failed" in response.get_data(as_text=True)


def test_connectivity_brief_import_is_audited_draft_not_approval(monkeypatch):
    client = _client(monkeypatch)
    captured = {}

    def save(owner, brief, **kwargs):
        captured["owner"] = owner
        captured["brief"] = brief
        return {"changed": True, "brief_id": brief.brief_id}

    monkeypatch.setattr(connectivity_briefs, "upsert", save)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    response = client.post(
        "/mission/organiser/connectivity-briefs",
        data={
            "csrf_token": "a" * 48,
            "source_run_id": "a" * 32,
            "title": "SMI 6G + ISAC Brief",
            "completed_at": "2026-10-02T08:00:00+01:00",
            "summary": "Measured evidence only; no production-radio claim.",
            "evidence_links": "https://www.itu.int/imt-2030",
            "evidence_score": "72",
            "decision": "watch",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/mission/organiser?imported=")
    brief = captured["brief"]
    assert brief.source == "chatgpt_automation"
    assert brief.decision == "watch"
    assert brief.evidence_links == ("https://www.itu.int/imt-2030",)
