from mission_control import oap_pay


def test_oap_pay_public_status_is_truthful(monkeypatch):
    monkeypatch.setattr(
        oap_pay.sika_execution_gate,
        "capability_matrix",
        lambda: {
            "execute_payments": False,
            "hold_customer_funds": False,
        },
    )
    status = oap_pay.public_status()
    assert status["system"] == "OAP Pay"
    assert status["sika_pay_gateway"] is True
    assert status["customer_payment_authority_required"] is True
    assert status["real_payment_execution_enabled"] is False
    assert status["customer_fund_holding_enabled"] is False
    assert status["provider_calling"] is False
    assert status["money_movement"] is False
    activity = next(item for item in status["features"] if item["id"] == "activity")
    assert activity["enabled"] is True
    pay = next(item for item in status["features"] if item["id"] == "pay")
    assert pay["enabled"] is False


def test_oap_pay_page_and_status_are_no_store(client):
    page = client.get("/pay")
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    assert "OAP Pay" in page.get_data(as_text=True)
    assert "Pay. Request. Move through one door." in page.get_data(as_text=True)

    alias = client.get("/oap-pay")
    assert alias.status_code == 200

    status = client.get("/pay/status")
    assert status.status_code == 200
    assert status.headers["Cache-Control"] == "no-store"
    payload = status.get_json()
    assert payload["provider_calling"] is False
    assert payload["money_movement"] is False


def test_oap_pay_fail_closes_regulated_features(monkeypatch):
    def unavailable():
        raise oap_pay.sika_execution_gate.bank_authorisation_store.BankEvidenceUnavailable(
            "unavailable"
        )

    monkeypatch.setattr(
        oap_pay.sika_execution_gate,
        "capability_matrix",
        unavailable,
    )
    status = oap_pay.public_status()
    assert status["evidence_available"] is False
    assert status["real_payment_execution_enabled"] is False
    assert status["customer_fund_holding_enabled"] is False
    for item in status["features"]:
        if item["capability"] is not None:
            assert item["enabled"] is False
