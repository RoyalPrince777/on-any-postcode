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


def _partner(count=0):
    return {
        "component": "OAP Partner Supply",
        "ready": True,
        "offers": [],
        "count": count,
        "external_provider_authority": False,
    }


def test_hybrid_policy_locks_external_provider_as_optional():
    policy = travel_supply_policy.public_policy()

    assert travel_supply_policy.NO_EXTERNAL_SUPPLIER_INDISPENSABLE is True
    assert travel_supply_policy.BOOKING_COM_REQUIRED is False
    assert travel_supply_policy.DIRECT_SUPPLY_PREFERRED is True
    assert travel_supply_policy.PREFERRED_SOURCE_ORDER == (
        "oap_direct",
        "partner_supply",
    )
    assert policy["no_external_supplier_indispensable"] is True
    assert policy["booking_com_required"] is False
    assert policy["external_provider_authority"] is False


def test_public_catalogue_exposes_direct_first_policy(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "public_offers",
        lambda **_kwargs: _direct(2),
    )
    monkeypatch.setattr(
        travel_supply_views.partner_supply,
        "public_offers",
        lambda **_kwargs: _partner(5),
    )

    response = anonymous_client.get("/travel/api/catalogue?category=stay")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["source_order"] == ["oap_direct", "partner_supply"]
    assert payload["direct_count"] == 2
    assert payload["partner_count"] == 5
    assert payload["booking_com_required"] is False
    assert payload["partner_supply_is_replaceable"] is True
    assert payload["policy"]["direct_supply_preferred"] is True


def test_partner_category_gap_never_breaks_oap_direct(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "public_offers",
        lambda **_kwargs: _direct(1),
    )

    def unsupported_partner(**_kwargs):
        raise ValueError("invalid_partner_supply_category")

    monkeypatch.setattr(
        travel_supply_views.partner_supply,
        "public_offers",
        unsupported_partner,
    )

    response = anonymous_client.get("/travel/api/catalogue?category=activity")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["direct_count"] == 1
    assert payload["partner_count"] == 0
    assert payload["partner"]["filtered_out_for_category"] is True


def test_public_travel_listing_labels_sources_and_direct_first(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "public_offers",
        lambda **_kwargs: _direct(),
    )
    monkeypatch.setattr(
        travel_supply_views.partner_supply,
        "public_offers",
        lambda **_kwargs: _partner(),
    )

    response = anonymous_client.get("/travel")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    assert "No external supplier may become indispensable to OAP Travel" in page
    assert "🟢 OAP Direct" in page
    assert "👑 Certified OAP Supplier" in page
    assert "🔗 Partner Supply" in page
    assert page.index('id="direct-title"') < page.index('id="partner-title"')


def test_direct_listing_keeps_oap_source_labels():
    with open(
        "mission_control/templates/travel_direct.html",
        encoding="utf-8",
    ) as handle:
        page = handle.read()

    assert "🟢 OAP Direct" in page
    assert "👑 Certified OAP Supplier" in page
    assert 'href="/travel"' in page
