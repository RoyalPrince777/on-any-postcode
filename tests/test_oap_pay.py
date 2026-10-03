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
    assert "Pay from your phone." in page.get_data(as_text=True)

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


def test_oap_pay_exposes_primary_more_and_regulated_menus(monkeypatch):
    monkeypatch.setattr(
        oap_pay.sika_execution_gate,
        "capability_matrix",
        lambda: {
            "execute_payments": False,
            "hold_customer_funds": False,
            "issue_payment_cards": False,
            "cash_out": False,
            "foreign_exchange": False,
            "bank_accounts": False,
        },
    )
    status = oap_pay.public_status()
    assert [item["id"] for item in status["primary_menu"]] == [
        "home", "pay", "request", "activity", "sika"
    ]
    assert [item["id"] for item in status["more_menu"]] == [
        "wallet", "business", "treasury", "rights", "guardian", "smi-pay", "settings"
    ]
    assert [item["id"] for item in status["admin_menu"]] == ["control-center"]
    assert [item["id"] for item in status["features"]] == [
        "home", "pay", "request", "wallet", "activity", "business", "sika",
        "treasury", "rights", "guardian", "cards", "cash", "fx", "bank",
        "smi-pay", "settings", "control-center"
    ]
    regulated = {item["id"]: item for item in status["regulated_menu"]}
    assert set(regulated) == {"cards", "cash", "fx", "bank"}
    assert all(item["enabled"] is False for item in regulated.values())


def test_oap_pay_page_contains_mobile_nav_and_more_drawer(client):
    page = client.get("/pay")
    body = page.get_data(as_text=True)
    assert 'aria-label="OAP Pay navigation"' in body
    assert ">Home</a>" in body
    assert ">Pay</a>" in body
    assert ">Request</a>" in body
    assert ">Activity</a>" in body
    assert ">My SIKA</a>" in body
    assert 'id="moreDrawer"' in body
    assert "Regulated capabilities" in body
    assert "Cards" in body
    assert "Cash / Post Office" in body
    assert "FX" in body
    assert "Bank" in body
    assert "Control Center" in body
    assert "Founder / Admin" in body


def test_oap_pay_phone_methods_are_truth_bound():
    status = oap_pay.public_status()
    methods = {item["id"]: item for item in status["phone_payment_methods"]}
    assert methods["qr"]["enabled"] is True
    assert methods["link"]["enabled"] is True
    assert methods["tap"]["enabled"] is False
    assert methods["phone"]["enabled"] is False
    assert methods["tap"]["requires"] == "contactless_provider_authority"


def test_oap_pay_phone_app_surface_is_installable(client):
    page = client.get("/pay")
    body = page.get_data(as_text=True)
    assert 'rel="manifest" href="/pay/manifest.webmanifest"' in body
    assert 'data-oap-install hidden' in body
    assert "Install OAP Pay" in body
    assert "Pay from your phone." in body
    assert "Scan QR" in body
    assert "Payment Link" in body
    assert "Tap to Pay" in body
    assert "Phone-to-Phone" in body
    assert "Contactless execution locked" in body


def test_oap_pay_bank_status_fails_closed(monkeypatch):
    monkeypatch.setattr(
        oap_pay.bank_authorisation_store,
        "readiness_status",
        lambda: {
            "institution": "United States of Africa Royalty Bank",
            "parent": "ON ANY POSTCODE LTD",
            "jurisdiction": "United Kingdom",
            "route": "PRA/FCA new-bank authorisation",
            "evidence_total": 30,
            "evidence_proven": 0,
            "application_ready": False,
            "authorised_bank": False,
        },
    )
    monkeypatch.setattr(oap_pay.bank_permission_scope, "current_scope", lambda: None)
    monkeypatch.setattr(
        oap_pay.sika_production_evidence_store,
        "readiness_status",
        lambda: {
            "evidence_total": 8,
            "evidence_proven": 0,
            "production_gate_passed": False,
            "money_movement_enabled": False,
            "human_authority_final": True,
        },
    )
    monkeypatch.setattr(
        oap_pay.sika_execution_gate,
        "capability_matrix",
        lambda: {
            "accept_deposits": False,
            "issue_redeemable_sika": False,
            "execute_payments": False,
            "hold_customer_funds": False,
            "issue_payment_cards": False,
            "cash_out": False,
            "foreign_exchange": False,
            "bank_accounts": False,
        },
    )
    status = oap_pay.bank_status()
    assert status["authorised_bank"] is False
    assert status["application_ready"] is False
    assert status["permission_scope_present"] is False
    assert status["production_gate_passed"] is False
    assert status["bank_accounts_enabled"] is False
    assert status["deposit_taking_enabled"] is False
    assert status["customer_fund_holding_enabled"] is False
    assert status["regulated_execution_enabled"] is False
    assert status["money_movement_enabled"] is False
    assert status["humanitarian_or_human_rights_purpose_bypasses_authorisation"] is False


def test_oap_pay_bank_page_and_status_are_no_store(client):
    page = client.get("/pay/bank")
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    body = page.get_data(as_text=True)
    assert "OAP Pay · Bank" in body
    assert "Regulated capabilities" in body
    assert "does not itself create bank authorisation" in body

    status = client.get("/pay/bank/status")
    assert status.status_code == 200
    assert status.headers["Cache-Control"] == "no-store"
    payload = status.get_json()
    assert payload["money_movement_enabled"] is False


def test_oap_pay_bank_menu_links_to_bank_screen(client):
    page = client.get("/pay")
    body = page.get_data(as_text=True)
    assert 'href="/pay/bank"' in body


def test_oap_pay_has_dedicated_install_manifest(client):
    response = client.get("/pay/manifest.webmanifest")
    manifest = response.get_json()

    assert response.status_code == 200
    assert response.content_type == "application/manifest+json"
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert manifest["id"] == "/pay"
    assert manifest["name"] == "OAP Pay"
    assert manifest["short_name"] == "OAP Pay"
    assert manifest["start_url"] == "/pay"
    assert manifest["scope"] == "/pay"
    assert manifest["display"] == "standalone"
    assert {item["url"] for item in manifest["shortcuts"]} == {
        "/pay#pay",
        "/pay#request",
        "/pay#activity",
        "/pay#sika",
    }


def test_oap_pay_page_uses_dedicated_manifest(client):
    page = client.get("/pay")
    body = page.get_data(as_text=True)
    assert 'rel="manifest" href="/pay/manifest.webmanifest"' in body
    assert 'rel="manifest" href="/manifest.webmanifest"' not in body
