from mission_control import oap_pay


AUTH_USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "OAP Member",
    "email": "",
    "email_verified": True,
}


def test_personal_bank_status_requires_authentication(client, monkeypatch):
    monkeypatch.setattr(
        oap_pay.web_security,
        "current_authenticated_user",
        lambda: None,
    )
    response = client.get("/pay/bank/me/status")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_personal_bank_status_uses_authenticated_identity(client, monkeypatch):
    monkeypatch.setattr(
        oap_pay.web_security,
        "current_authenticated_user",
        lambda: AUTH_USER,
    )
    monkeypatch.setattr(
        oap_pay.sika_customer_view,
        "snapshot",
        lambda owner: {
            "owner_scoped": owner == AUTH_USER["id"],
            "accounts": [],
            "account_count": 0,
            "money_movement": False,
        },
    )
    response = client.get("/pay/bank/me/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["owner_scoped"] is True
    assert payload["money_movement"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_personal_bank_activity_uses_authenticated_identity(client, monkeypatch):
    monkeypatch.setattr(
        oap_pay.web_security,
        "current_authenticated_user",
        lambda: AUTH_USER,
    )
    monkeypatch.setattr(
        oap_pay.sika_customer_view,
        "activity",
        lambda owner: {
            "owner_scoped": owner == AUTH_USER["id"],
            "items": [],
            "money_movement": False,
        },
    )
    response = client.get("/pay/bank/me/activity")
    assert response.status_code == 200
    assert response.get_json()["owner_scoped"] is True
    assert response.headers["Cache-Control"] == "no-store"
