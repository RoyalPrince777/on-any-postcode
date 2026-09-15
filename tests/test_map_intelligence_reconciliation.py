from mission_control import products


def test_map_intelligence_is_single_public_front_door():
    capabilities = products.get_public_product_hierarchy()["capabilities"]
    slugs = [item["slug"] for item in capabilities]
    names = [item["name"] for item in capabilities]

    assert slugs.count("maps-weather-travel") == 1
    assert "movement-delivery" not in slugs
    assert names.count("Map Intelligence") == 1


def test_legacy_movement_public_route_redirects_to_map_intelligence(client):
    response = client.get(
        "/the-spot/movement-delivery?location=Mitcham",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/the-spot/maps-weather-travel?location=Mitcham"


def test_map_consolidation_does_not_unlock_movement_execution():
    capability = next(
        item for item in products.SPOT_CAPABILITIES if item["id"] == "infrastructure"
    )

    assert capability["name"] == "Map Intelligence"
    assert "payments" in capability["blocked_by"]
    assert "automatic dispatch" in capability["blocked_by"]
    assert "confirmed supplier bookings" in capability["blocked_by"]
