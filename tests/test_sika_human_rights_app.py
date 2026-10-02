import app as app_module


def test_sika_human_rights_page_is_public_and_truthful():
    client = app_module.app.test_client()
    response = client.get("/sika/human-rights")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "SIKA · Guardian · Human Authority" in body
    assert "Human Rights" in body
    assert "not invented legal entitlement" in body
    assert "Financial execution disabled" in body


def test_sika_human_rights_status_is_public_safe():
    client = app_module.app.test_client()
    response = client.get("/api/sika/human-rights/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["first_party"] is True
    assert payload["automated_punishment"] is False
    assert payload["financial_execution"] is False
    assert payload["money_movement"] is False
    assert payload["human_authority_final"] is True


def test_human_rights_review_post_is_csrf_protected():
    client = app_module.app.test_client()
    response = client.post(
        "/sika/human-rights",
        data={
            "action_type": "ACCOUNT_FREEZE",
            "subject_reference": "acct-1",
            "evidence_reference": "evidence-1",
            "reason_code": "risk_review",
        },
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_sika_front_door_links_human_rights_app():
    client = app_module.app.test_client()
    response = client.get("/the-spot/sika")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "/sika/human-rights" in body
    assert "Rights gate:" in body
