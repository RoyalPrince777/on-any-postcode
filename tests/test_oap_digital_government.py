"""OAP Digital Government is a truthful Founder-only product, not a state."""
from __future__ import annotations

from mission_control import oap_digital_government as govt


def test_oap_constitution_links_real_162_seats_and_seven_houses():
    status = govt.status()
    assert status["checks_passed"] is True, status
    assert status["registered_existing_agents"] == 78
    assert status["draft_agent_seats"] == 84
    assert status["mapped_seat_count"] == 162
    assert len(status["houses"]) == len(status["oap_law"]) == 7
    assert len(status["ministries"]) == 7
    assert sum(m["draft_seats"] for m in status["ministries"]) == 84
    assert sum(len(m["family_keys"]) for m in status["ministries"]) == 28
    assert status["scope"] == "voluntary_first_party_internal_governance"


def test_all_oap_houses_link_to_existing_routes_or_honestly_label_absence():
    status = govt.status()
    live = [h for h in status["houses"] if h["route"] is not None]
    not_live = [h for h in status["houses"] if h["route"] is None]
    assert len(live) == 4
    assert len(not_live) == 3
    assert all(h["state"].startswith("linked_") for h in live)
    assert all("not_implemented" in h["state"] for h in not_live)
    assert all(h["key"] != "court" for h in status["houses"])


def test_no_new_powers_elections_passports_or_automatic_rulings():
    status = govt.status()
    assert status["new_authority_granted"] is False
    assert status["new_agent_passports_issued"] == 0
    assert status["real_community_votes_recorded"] is None
    assert status["live_constituency_representatives"] is None
    assert status["overall_vpi_percent"] is None
    assert status["live_readiness_percent"] is None
    assert status["safeguards"]["founder_final_required"] is True
    assert status["safeguards"]["human_challenge_required"] is True
    assert all(value is False for key, value in status["safeguards"].items()
               if key not in {"founder_final_required", "human_challenge_required"})


def test_trust_boundary_fails_closed_on_invalid_agent_registry(monkeypatch):
    monkeypatch.setattr(govt.smi_secure_seats, "board",
                        lambda: {"checks_passed": False})
    status = govt.status()
    assert status["checks_passed"] is False
    assert status["errors"] == ("upstream_seat_integrity_failed",)
    assert "houses" not in status
    assert "mapped_seat_count" not in status


def test_duplicate_ministry_family_fails_closed(monkeypatch):
    invalid = list(govt.MINISTRIES)
    name, title, keys = invalid[0]
    invalid[0] = (name, title, (*keys, "court_jury"))
    monkeypatch.setattr(govt, "MINISTRIES", tuple(invalid))
    status = govt.status()
    assert status["checks_passed"] is False
    assert status["errors"] == ("digital_governance_integrity_failed",)


def test_founder_only_government_html_and_json_routes(client):
    page = client.get("/mission/digital-government")
    response = client.get("/mission/digital-government/status")
    assert page.status_code == response.status_code == 200
    assert "no-store" in page.headers["Cache-Control"]
    assert "no-store" in response.headers["Cache-Control"]
    text = page.get_data(as_text=True)
    assert "OAP DIGITAL" in text and "GOVERNMENT" in text
    assert "OAP Law" in text and "Founder Chamber" in text
    assert "OAP Borough Councils" in text and "No live voting" in text
    assert response.get_json()["mapped_seat_count"] == 162
    assert client.post("/mission/digital-government").status_code == 405
    assert client.post("/mission/digital-government/status").status_code == 405


def test_anonymous_government_routes_rejected(anonymous_client):
    response = anonymous_client.get("/mission/digital-government/status")
    assert response.status_code == 401
    assert "no-store" in response.headers["Cache-Control"]
    assert "houses" not in response.get_data(as_text=True)
    assert anonymous_client.get("/mission/digital-government").status_code == 302


def test_non_founder_government_routes_rejected(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed",
                        lambda _user: False)
    response = client.get("/mission/digital-government/status")
    assert response.status_code == 403
    assert "houses" not in response.get_data(as_text=True)
    assert client.get("/mission/digital-government").status_code == 403


def test_failed_seat_gate_denies_both_routes(client, monkeypatch):
    from mission_control import oap_digital_government as module

    monkeypatch.setattr(module.smi_secure_seats, "board",
                        lambda: {"checks_passed": False})
    response = client.get("/mission/digital-government/status")
    assert response.status_code == 503
    assert "houses" not in response.get_data(as_text=True)
    assert client.get("/mission/digital-government").status_code == 503


def test_founder_only_auth_route_metadata_and_war_room_link(client):
    from mission_control import views

    assert views.digital_government_view._oap_founder_only is True
    assert views.digital_government_status._oap_founder_only is True
    assert views.digital_government_status._oap_api is True
    page = client.get("/mission/war-room")
    assert 'href="/mission/digital-government"' in page.get_data(as_text=True)
