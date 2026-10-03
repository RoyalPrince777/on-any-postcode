from mission_control import oap_bank_intelligence_catalog, oap_pay


def test_bank_intelligence_catalog_has_exact_21_domains():
    status = oap_bank_intelligence_catalog.status()
    assert status["system"] == "OAP Bank Intelligence"
    assert status["domain_count"] == 21
    assert len(status["domains"]) == 21
    assert len({item["id"] for item in status["domains"]}) == 21
    assert status["advisory_only"] is True
    assert status["execution_authority"] is False
    assert status["provider_calling"] is False
    assert status["journal_posting"] is False
    assert status["settlement_execution"] is False
    assert status["money_movement"] is False
    assert status["human_authority_final"] is True


def test_bank_intelligence_routes_are_no_store(client):
    page = client.get("/pay/bank/intelligence")
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    body = page.get_data(as_text=True)
    assert "All Bank Intelligence" in body
    assert "21 first-party intelligence domains" in body
    assert "Accounts" in body
    assert "Payments" in body
    assert "Treasury and Liquidity" in body
    assert "Rights and Remedy" in body
    assert "Regulated Evidence Gates" in body

    status = client.get("/pay/bank/intelligence/status")
    assert status.status_code == 200
    assert status.headers["Cache-Control"] == "no-store"
    payload = status.get_json()
    assert payload["domain_count"] == 21
    assert payload["money_movement"] is False


def test_bank_app_menu_exposes_intelligence(monkeypatch):
    monkeypatch.setattr(
        oap_pay.sika_execution_gate,
        "capability_matrix",
        dict,
    )
    status = oap_pay.bank_status()
    primary_ids = [item["id"] for item in status["app_primary_menu"]]
    more_ids = [item["id"] for item in status["app_more_menu"]]
    assert "intelligence" not in primary_ids
    assert "intelligence" in more_ids
