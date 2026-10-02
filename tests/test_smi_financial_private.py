"""CC21 private financial destination security and truthful readiness tests."""

import app as app_module
from mission_control import web_security


def test_financial_intelligence_private_destination_is_founder_only(client):
    page = client.get("/mission/financial-intelligence")
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    html = page.get_data(as_text=True)
    assert "Financial Intelligence" in html
    assert "Not connected" in html
    assert "Not proven" in html
    assert "Founder Final" in html
    assert "SMI Command Center" in html


def test_financial_intelligence_readiness_is_read_only(client):
    response = client.get("/mission/financial-intelligence/status")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    state = response.get_json()
    assert state["research_validator_available"] is True
    for name in (
        "trusted_source_registry_connected",
        "live_market_feed_connected",
        "research_observations_available",
        "sika_ledger_connected",
        "trading_enabled",
        "payment_enabled",
        "production_acceptance_proven",
    ):
        assert state[name] is False
    assert state["human_authority_final"] is True
    assert "value" not in state
    assert "price" not in state


def test_financial_intelligence_fails_closed_for_anonymous_users(anonymous_client):
    page = anonymous_client.get("/mission/financial-intelligence")
    assert page.status_code == 302
    assert "/enter-my-world" in page.headers["Location"]
    api = anonymous_client.get("/mission/financial-intelligence/status")
    assert api.status_code == 401
    assert api.headers["Cache-Control"] == "no-store"
    assert api.get_json()["error"]["code"] == "authentication_required"


def test_financial_intelligence_routes_are_get_only_with_existing_auth_contract():
    rules = {
        rule.rule: rule
        for rule in app_module.app.url_map.iter_rules()
        if rule.rule.startswith("/mission/financial-intelligence")
    }
    assert set(rules) == {
        "/mission/financial-intelligence",
        "/mission/financial-intelligence/status",
    }
    for rule in rules.values():
        assert rule.methods == {"GET", "HEAD", "OPTIONS"}
        view = app_module.app.view_functions[rule.endpoint]
        assert view._oap_login_required is True
        assert view._oap_founder_only is True


def test_financial_intelligence_rejects_signed_in_non_founder(client, monkeypatch):
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda _user: False)
    for path in (
        "/mission/financial-intelligence",
        "/mission/financial-intelligence/status",
    ):
        response = client.get(path)
        assert response.status_code == 403
        assert response.headers["Cache-Control"] == "no-store"
        assert response.get_json()["error"]["code"] == "human_authority_required"


def test_financial_intelligence_has_no_write_method_or_market_data(client):
    for path in (
        "/mission/financial-intelligence",
        "/mission/financial-intelligence/status",
    ):
        assert client.post(path, json={"value": "123.45"}).status_code == 405
        assert client.put(path, json={"source": "untrusted"}).status_code == 405
    result = client.get("/mission/financial-intelligence/status?live=true&price=100")
    assert result.status_code == 200
    state = result.get_json()
    assert state["live_market_feed_connected"] is False
    assert state["trusted_source_registry_connected"] is False
    assert "price" not in state


def test_financial_intelligence_uses_existing_command_deck(client):
    page = client.get("/mission")
    assert page.status_code == 200
    assert 'href="/mission/financial-intelligence"' in page.get_data(as_text=True)
