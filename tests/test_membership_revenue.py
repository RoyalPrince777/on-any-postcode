from pathlib import Path

from flask import Flask

from mission_control import membership_revenue

CHECKOUT_ENVS = tuple(str(tier["checkout_env"]) for tier in membership_revenue.MEMBERSHIP_TIERS)


def _app() -> Flask:
    app = Flask(__name__, template_folder=str(Path("mission_control/templates").resolve()))
    app.register_blueprint(membership_revenue.bp)
    return app


def _clear_checkout_envs(monkeypatch):
    for name in CHECKOUT_ENVS:
        monkeypatch.delenv(name, raising=False)


def test_membership_tiers_lock_first_money_prices():
    assert [tier["id"] for tier in membership_revenue.MEMBERSHIP_TIERS] == [
        "postcode-founder",
        "borough-builder",
        "country-champion",
    ]
    assert [tier["price_pence"] for tier in membership_revenue.MEMBERSHIP_TIERS] == [
        500,
        1000,
        2500,
    ]


def test_membership_status_is_truthful_when_checkout_is_not_configured(monkeypatch):
    _clear_checkout_envs(monkeypatch)
    payload = membership_revenue.public_offer_status()

    assert payload["status"] == "setup_required"
    assert payload["configured_tiers"] == 0
    assert payload["public_browsing_free"] is True
    assert payload["payment_processed_by_oap"] is False
    assert payload["card_data_collected_by_oap"] is False
    assert payload["founder_authority_granted"] is False
    assert payload["fulfilment"] == "provider_receipt_then_manual_confirmation"


def test_checkout_url_rejects_unsafe_destinations(monkeypatch):
    tier = membership_revenue.MEMBERSHIP_TIERS[0]
    env_name = str(tier["checkout_env"])
    for unsafe in (
        "http://payments.example/checkout",
        "https://user:pass@payments.example/checkout",
        "https://localhost/checkout",
        "https://127.0.0.1/checkout",
        "https://10.0.0.8/checkout",
        "https://payments.example/checkout#secret",
    ):
        monkeypatch.setenv(env_name, unsafe)
        assert membership_revenue.checkout_url(tier) == ""


def test_checkout_redirects_only_to_configured_https_provider(monkeypatch):
    _clear_checkout_envs(monkeypatch)
    monkeypatch.setenv(
        "OAP_MEMBERSHIP_POSTCODE_FOUNDER_CHECKOUT_URL",
        "https://payments.example/secure/postcode-founder",
    )
    client = _app().test_client()

    response = client.get("/membership/checkout/postcode-founder")

    assert response.status_code == 303
    assert response.headers["Location"] == "https://payments.example/secure/postcode-founder"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "Set-Cookie" not in response.headers


def test_unconfigured_checkout_fails_closed_without_payment_claim(monkeypatch):
    _clear_checkout_envs(monkeypatch)
    client = _app().test_client()

    response = client.get("/membership/checkout/postcode-founder")
    text = response.get_data(as_text=True)

    assert response.status_code == 503
    assert "Payment setup required" in text
    assert "Not collecting money yet" in text
    assert "Founder dashboard" in text


def test_payment_return_never_claims_browser_return_proves_payment():
    client = _app().test_client()
    response = client.get("/membership/payment-return")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Confirmation is pending" in text
    assert "is not proof that money was received" in text
    assert "No membership entitlement" in text
    assert "Founder authority" in text
    assert response.headers["Cache-Control"] == "no-store"


def test_public_status_never_exposes_provider_url(monkeypatch):
    _clear_checkout_envs(monkeypatch)
    secret_url = "https://payments.example/secret-configured-path"
    monkeypatch.setenv("OAP_MEMBERSHIP_COUNTRY_CHAMPION_CHECKOUT_URL", secret_url)
    client = _app().test_client()

    response = client.get("/membership/status")

    assert response.status_code == 200
    assert secret_url not in response.get_data(as_text=True)
    assert response.get_json()["configured_tiers"] == 1


def test_live_app_initialiser_registers_membership_revenue_blueprint():
    source = Path("mission_control/__init__.py").read_text(encoding="utf-8")
    assert "from .membership_revenue import bp as membership_revenue_bp" in source
    assert "app.register_blueprint(membership_revenue_bp)" in source
