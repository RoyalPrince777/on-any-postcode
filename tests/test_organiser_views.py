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

def test_film_evidence_api_is_founder_only_and_read_only(monkeypatch):
    blocked = _client(monkeypatch, founder=False)
    assert blocked.get("/mission/organiser/research/film-evidence").status_code == 403

    client = _client(monkeypatch, founder=True)
    result = client.get("/mission/organiser/research/film-evidence")
    assert result.status_code == 200
    assert result.headers["Cache-Control"] == "no-store"
    assert result.headers["X-Content-Type-Options"] == "nosniff"
    research = result.get_json()
    assert len(research["entries"]) == 3
    assert len(research["source_receipts"]) == 4
    assert research["private_communication_ingestion_enabled"] is False
    assert research["execution_enabled"] is False


def test_founder_archive_shows_all_three_film_research_identities_under_existing_council(
    monkeypatch,
):
    blocked = _client(monkeypatch, founder=False)
    assert blocked.get("/mission/organiser").status_code == 403

    response = _client(monkeypatch, founder=True).get("/mission/organiser")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert page.count('data-film-reference="m3gan"') == 1
    assert page.count('data-film-reference="amelia"') == 1
    assert page.count('data-film-reference="black_box"') == 1
    assert "M3GAN · AMELIA · BLACK BOX" in page
    assert "Captain ALL IN" in page
    assert "Bagheera" in page and "Shere Khan" in page
    assert "Founder Final remains final" in page
    assert "no live crawler" in page
    assert "no verified character runtime" in page
    assert "Read Founder-only source receipts" in page
    assert response.headers["Cache-Control"] == "no-store"


def test_founder_technology_evidence_is_source_linked_and_not_on_public_brain(
    monkeypatch,
):
    blocked = _client(monkeypatch, founder=False)
    assert blocked.get("/mission/organiser").status_code == 403
    assert blocked.get("/mission/organiser/research/film-evidence").status_code == 403

    page_response = _client(monkeypatch, founder=True).get("/mission/organiser")
    page = page_response.get_data(as_text=True)
    assert page_response.status_code == 200
    assert page.count('data-real-technology="m3gan"') == 3
    assert page.count('data-real-technology="amelia"') == 2
    assert page.count('data-real-technology="black_box"') == 2
    assert "Amelia 7 (SoundHound AI)" in page
    assert "BLACKBOX AI coding agents" in page
    assert "no provider connected" in page
    assert "no physical robot proof" in page
    api = _client(monkeypatch, founder=True).get(
        "/mission/organiser/research/film-evidence"
    )
    assert api.status_code == 200
    assert len(api.get_json()["real_world_technology_evidence"]) == 7
    assert api.headers["Cache-Control"] == "no-store"


def test_founder_original_film_powers_view_links_real_film_references(monkeypatch):
    blocked = _client(monkeypatch, founder=False)
    assert blocked.get("/mission/organiser").status_code == 403

    founder = _client(monkeypatch, founder=True)
    response = founder.get("/mission/organiser")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    page = response.get_data(as_text=True)
    assert page.count('data-film-ability="m3gan:') == 6
    assert page.count('data-film-ability="amelia:') == 5
    assert page.count('data-film-ability="black_box:') == 4
    assert "Full film-canon ability evidence" in page
    assert "Film source</a>" in page
    assert "fictional; real OAP implementation requires independent proof" in page
    assert "Founder Final remains final" in page

    research_response = founder.get("/mission/organiser/research/film-evidence")
    assert research_response.status_code == 200
    research = research_response.get_json()
    assert len(research["film_canon_abilities"]) == 15
    assert len(research["source_receipts"]) == 4
    assert research["film_canon_runtime_proven"] is False
    assert research_response.headers["Cache-Control"] == "no-store"


def test_original_three_gateway_is_founder_only_and_csrf_guarded(monkeypatch):
    from mission_control import film_capability_gateway

    blocked = _client(monkeypatch, founder=False)
    assert blocked.get("/mission/organiser/original-three/status").status_code == 403
    assert blocked.post("/mission/organiser/original-three/evaluate",
                        json={"profile": "amelia", "payload": {"action": "deploy"}}).status_code == 403

    founder = _client(monkeypatch, founder=True)
    page = founder.get("/mission/organiser")
    html = page.get_data(as_text=True)
    assert 'data-original-profile="m3gan"' in html
    assert 'data-original-profile="amelia"' in html
    assert 'data-original-profile="black_box"' in html
    assert "smi_original_three.js" in html
    assert "data-original-three-endpoint" in html
    assert "not" in html.lower()

    status = founder.get("/mission/organiser/original-three/status")
    assert status.status_code == 200
    assert status.headers["Cache-Control"] == "no-store"
    assert status.get_json()["one_smi_brain"] is True
    assert status.get_json()["physical_motherboard_built"] is False

    fail = founder.post("/mission/organiser/original-three/evaluate",
                        json={"profile": "amelia", "payload": {"action": "deploy"}})
    assert fail.status_code == 403
    assert fail.get_json()["error"] == "csrf_failed"

    with founder.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    result = founder.post(
        "/mission/organiser/original-three/evaluate",
        json={"profile": "amelia", "payload": {"action": "deploy", "source_verified": True}},
        headers={"X-OAP-CSRF": "a" * 48},
    )
    assert result.status_code == 200
    assert result.headers["Cache-Control"] == "no-store"
    assert result.headers["X-Content-Type-Options"] == "nosniff"
    assert result.get_json()["decision"] == "hold"
    assert result.get_json()["operation_performed"] is False


def test_original_three_api_blocks_bad_json_without_hitting_inference(monkeypatch):
    from mission_control import film_capability_gateway

    founder = _client(monkeypatch, founder=True)
    with founder.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "b" * 48
    monkeypatch.setattr(
        film_capability_gateway, "evaluate",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must fail before evaluation")),
    )
    url = "/mission/organiser/original-three/evaluate"
    headers = {"X-OAP-CSRF": "b" * 48}
    assert founder.post(url, json={"profile": "m3gan"}, headers=headers).status_code == 400
    assert founder.post(url, json={"profile": "other", "payload": {}, "extra": 1}, headers=headers).status_code == 400
    assert founder.post(url, data="x" * 5000, headers=headers).status_code == 413
