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


def test_direct_policy_locks_external_travel_to_lookup_only():
    policy = travel_supply_policy.public_policy()

    assert travel_supply_policy.NO_EXTERNAL_SUPPLIER_INDISPENSABLE is True
    assert travel_supply_policy.BOOKING_COM_REQUIRED is False
    assert travel_supply_policy.BOOKING_COM_PARTNER is False
    assert travel_supply_policy.DIRECT_SUPPLY_PREFERRED is True
    assert travel_supply_policy.EXTERNAL_LOOKUP_PERSISTED is False
    assert travel_supply_policy.PREFERRED_SOURCE_ORDER == ("oap_direct",)
    assert policy["no_external_supplier_indispensable"] is True
    assert policy["booking_com_required"] is False
    assert policy["booking_com_partner"] is False
    assert policy["external_lookup_persisted"] is False
    assert policy["external_provider_authority"] is False


def test_public_catalogue_exposes_oap_direct_only_persisted_supply(
    anonymous_client, monkeypatch
):
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
    assert "partner_count" not in payload
    assert payload["external_lookup"]["mode"] == "on_demand_only"
    assert payload["external_lookup"]["persisted"] is False
    assert payload["external_lookup"]["partner_supply"] is False
    assert payload["external_lookup"]["booking_authority"] is False
    assert payload["policy"]["direct_supply_preferred"] is True


def test_external_lookup_is_not_a_public_persisted_supply_route(anonymous_client):
    response = anonymous_client.get("/travel/partner/api/offers")
    assert response.status_code == 404


def test_public_travel_labels_direct_and_lookup_boundary(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "public_offers",
        lambda **_kwargs: _direct(),
    )

    response = anonymous_client.get("/travel")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    assert "OAP Direct. Your marketplace." in page
    assert "🟢 OAP Direct" in page
    assert "👑 Certified OAP Supplier" in page
    assert "🔎 External Lookup" in page
    assert "Fetch when needed. Do not import." in page
    assert "catalogue.partner" not in page


def test_direct_listing_keeps_oap_source_labels_and_media_contract():
    with open(
        "mission_control/templates/travel_direct.html",
        encoding="utf-8",
    ) as handle:
        page = handle.read()

    assert "🟢 OAP Direct" in page
    assert "👑 Certified OAP Supplier" in page
    assert "cover_image_url" in page
    assert 'href="/travel"' in page
