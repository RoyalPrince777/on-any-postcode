from __future__ import annotations

from mission_control import authority, oap_data, oap_data_views


def test_oap_data_is_a_named_first_party_product():
    product = oap_data.get_product_status()

    assert product["product"] == "OAP Data"
    assert product["owner"] == "ON ANY POSTCODE"
    assert product["consumer"] == "OAP Intelligence"
    assert product["core"] == "OAP CORE"
    assert product["raw_records_exposed"] is False
    assert product["destructive_actions_enabled"] is False
    assert len(product["domains"]) == 7
    assert product["first_party"]["oap_product"] is True
    assert product["first_party"]["oap_owned_contracts"] is True
    assert product["first_party"]["external_analytics_required"] is False
    assert product["first_party"]["external_tracking_required"] is False
    assert product["first_party"]["external_realtime_data_provider_required"] is False


def test_oap_data_dashboard_uses_product_language_only(client, monkeypatch):
    monkeypatch.setattr(oap_data_views, "_require_human_authority", lambda: None)

    response = client.get("/mission/data")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "OAP Data" in page
    assert "OAP Intelligence" in page
    assert "OAP Data domains" in page
    assert "First-party boundary" in page
    assert "metadata" not in page.casefold()
    assert 'method="post"' not in page.casefold()


def test_oap_data_status_is_coarse_and_contains_no_private_records(client, monkeypatch):
    monkeypatch.setattr(oap_data_views, "_require_human_authority", lambda: None)

    response = client.get("/mission/data/status")
    payload = response.get_json()
    serialized = response.get_data(as_text=True).casefold()

    assert response.status_code == 200
    assert payload["product"] == "OAP Data"
    assert payload["raw_records_exposed"] is False
    for private_key in (
        "password",
        "secret",
        "token",
        "private_key",
        "message_body",
        "email_address",
        "phone_number",
    ):
        assert private_key not in serialized


def test_oap_data_fails_closed_without_human_authority(client, monkeypatch):
    def reject():
        raise authority.HumanAuthorityRequired("level_zero_human_authority_required")

    monkeypatch.setattr(oap_data_views, "_require_human_authority", reject)

    response = client.get("/mission/data")

    assert response.status_code == 403
    assert response.get_data(as_text=True) == "Human Authority required."
