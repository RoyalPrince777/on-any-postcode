from mission_control import travel_supply_policy, travel_supply_views


def _direct(count=0):
    return {
        "component": "OAP Direct",
        "ready": True,
        "offers": [],
        "count": count,
        "source": "oap_direct",
        "external_provider_authority": False,
    }


def _no_photos(monkeypatch):
    monkeypatch.setattr(travel_supply_views.listing_media, "photo_map", lambda _ids: {})
    monkeypatch.setattr(
        travel_supply_views.listing_media,
        "status",
        lambda: {"schema_ready": True, "photo_count": 0},
    )


def test_direct_policy_separates_external_research_from_catalogue():
    policy = travel_supply_policy.public_policy()

    assert travel_supply_policy.DIRECT_SUPPLY_PREFERRED is True
    assert travel_supply_policy.EXTERNAL_DATA_FETCH_ALLOWED is True
    assert travel_supply_policy.EXTERNAL_CATALOGUE_IMPORT_ALLOWED is False
    assert travel_supply_policy.PREFERRED_SOURCE_ORDER == ("oap_direct",)
    assert policy["model"] == "oap_direct_only_catalogue"
    assert policy["external_data_fetch_allowed"] is True
    assert policy["external_catalogue_import_allowed"] is False
    assert policy["external_provider_authority"] is False


def test_public_catalogue_is_oap_direct_only(anonymous_client, monkeypatch):
    _no_photos(monkeypatch)
    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "public_offers",
        lambda **_kwargs: _direct(2),
    )

    response = anonymous_client.get("/travel/api/catalogue?category=stay")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["source_order"] == ["oap_direct"]
    assert payload["direct_count"] == 2
    assert "partner" not in payload
    assert "partner_count" not in payload
    assert payload["external_data_fetch_allowed"] is True
    assert payload["external_catalogue_import_allowed"] is False
    assert payload["policy"]["direct_supply_preferred"] is True


def test_retired_partner_feed_fails_closed(anonymous_client):
    response = anonymous_client.get("/travel/partner/api/offers")
    assert response.status_code == 410
    payload = response.get_json()
    assert payload["error"]["code"] == "partner_supply_removed"


def test_public_travel_labels_only_oap_direct(anonymous_client, monkeypatch):
    _no_photos(monkeypatch)
    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "public_offers",
        lambda **_kwargs: _direct(),
    )

    response = anonymous_client.get("/travel")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    assert "🟢 OAP Direct" in page
    assert "👑 Certified OAP Supplier" in page
    assert "External Data Fetch" in page
    assert "Partner Supply" not in page
    assert "Booking.com" not in page


def test_direct_listing_keeps_oap_source_labels():
    with open("mission_control/templates/travel_direct.html", encoding="utf-8") as handle:
        page = handle.read()

    assert "🟢 OAP Direct" in page
    assert "👑 Certified OAP Supplier" in page
    assert "partner feed" in page
    assert 'href="/travel"' in page
