from mission_control import oap_pay


IDENTITY = "11111111-1111-1111-1111-111111111111"


def _authenticated(monkeypatch):
    monkeypatch.setattr(
        oap_pay.web_security,
        "current_authenticated_user",
        lambda: {"id": IDENTITY},
    )
    monkeypatch.setattr(
        oap_pay.web_security,
        "authenticated_identity",
        lambda: IDENTITY,
    )


def test_my_bank_renders_persisted_founder_state(client, monkeypatch):
    _authenticated(monkeypatch)
    monkeypatch.setattr(
        oap_pay.sika_customer_view,
        "snapshot",
        lambda owner: {
            "accounts": [{
                "account_id": "acct-founder",
                "balance": {
                    "cleared": "100.00",
                    "reserved": "20.00",
                    "available": "80.00",
                },
            }],
            "founder": {
                "provisioned": True,
                "sika_number": "SIKA-777-123456789012",
                "account_id": "acct-founder",
            },
        },
    )
    response = client.get("/pay/bank/me")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "SIKA-777-123456789012" in body
    assert "S 80.00" in body
    assert "Ledger balance S 100.00" in body
    assert "Control Center" not in body


def test_my_bank_never_invents_unprovisioned_value(client, monkeypatch):
    _authenticated(monkeypatch)
    monkeypatch.setattr(
        oap_pay.sika_customer_view,
        "snapshot",
        lambda owner: {
            "accounts": [],
            "founder": {
                "provisioned": False,
                "sika_number": None,
                "account_id": None,
            },
        },
    )
    response = client.get("/pay/bank/me")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Not provisioned" in body
    assert "S 0.00" not in body
    assert "SIKA-777-" not in body
