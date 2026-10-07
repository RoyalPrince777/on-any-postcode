from flask import Flask

from mission_control import sika_account_engine, sika_founder_account, sika_founder_routes


def _client(monkeypatch, *, owner="11111111-1111-1111-1111-111111111111"):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-only"
    app.register_blueprint(sika_founder_routes.bp)
    monkeypatch.setattr(
        sika_founder_routes.web_security,
        "current_authenticated_user",
        lambda: {"id": owner},
    )
    monkeypatch.setattr(
        sika_founder_routes.web_security,
        "private_authority_allowed",
        lambda user: True,
    )
    monkeypatch.setattr(
        sika_founder_routes.web_security,
        "authenticated_identity",
        lambda: owner,
    )
    return app.test_client()


def test_founder_web_provision_uses_authenticated_owner_and_safe_contract(monkeypatch):
    owner = "11111111-1111-1111-1111-111111111111"
    captured = {}

    def fake_provision(**kwargs):
        captured.update(kwargs)
        account = sika_account_engine.BankAccount(
            account_id=kwargs["account_id"],
            owner_reference=kwargs["owner_reference"],
            legal_entity=kwargs["legal_entity"],
            jurisdiction=kwargs["jurisdiction"],
            currency=kwargs["currency"],
            ledger_account_id=kwargs["ledger_account_id"],
            status="OPEN",
        )
        return sika_founder_account.FounderAccount(
            account=account,
            sika_number="SIKA-777-000000000001",
        )

    monkeypatch.setattr(sika_founder_routes.sika_founder_account, "provision", fake_provision)
    response = _client(monkeypatch, owner=owner).post(
        "/pay/bank/founder/provision",
        json={"owner_reference": "attacker", "account_id": "attacker"},
    )

    assert response.status_code == 200
    assert captured["owner_reference"] == owner
    assert captured["legal_entity"] == "ON ANY POSTCODE LTD"
    assert captured["jurisdiction"] == "United Kingdom"
    assert captured["currency"] == "GBP"
    assert captured["account_id"] != "attacker"
    assert captured["ledger_account_id"]
    assert response.get_json() == {
        "founder": True,
        "sika_number": "SIKA-777-000000000001",
        "account_status": "OPEN",
        "currency": "GBP",
        "treasury_authority": False,
        "creates_balance": False,
        "money_movement": False,
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_founder_web_provision_fails_closed_on_authority_error(monkeypatch):
    def denied(**kwargs):
        raise sika_founder_account.FounderProvisioningError(
            "human_authority_owner_required"
        )

    monkeypatch.setattr(sika_founder_routes.sika_founder_account, "provision", denied)
    response = _client(monkeypatch).post("/pay/bank/founder/provision")

    assert response.status_code == 403
    assert response.get_json() == {
        "error": {"code": "human_authority_owner_required"}
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_founder_web_provision_reports_store_unavailable_without_leaking_details(monkeypatch):
    def unavailable(**kwargs):
        raise sika_founder_account.FounderProvisioningUnavailable(
            "database-secret-detail"
        )

    monkeypatch.setattr(
        sika_founder_routes.sika_founder_account,
        "provision",
        unavailable,
    )
    response = _client(monkeypatch).post("/pay/bank/founder/provision")

    assert response.status_code == 503
    assert response.get_json() == {
        "error": {"code": "founder_sika_provisioning_unavailable"}
    }
    assert "database-secret-detail" not in response.get_data(as_text=True)
