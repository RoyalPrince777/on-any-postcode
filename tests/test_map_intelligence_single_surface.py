from mission_control.products import PUBLIC_SPOT_CAPABILITIES, SPOT_CAPABILITIES, get_public_spot_capability


def test_map_intelligence_is_single_public_movement_surface():
    public = tuple(PUBLIC_SPOT_CAPABILITIES)
    map_surface = get_public_spot_capability("maps-weather-travel")

    assert map_surface is not None
    assert map_surface["name"] == "Map Intelligence"
    assert not any(item["slug"] == "movement-delivery" for item in public)
    assert not any(item["source_id"] == "runner" for item in public)


def test_map_intelligence_owns_movement_booking_delivery_and_weather():
    capability = next(item for item in SPOT_CAPABILITIES if item["id"] == "infrastructure")
    combined = " ".join((capability["name"], capability["purpose"], capability["function"])).casefold()

    for term in ("map", "route", "weather", "travel", "movement", "booking", "delivery"):
        assert term in combined

    assert capability["name"] == "Map Intelligence"
    assert not any(item["id"] == "runner" for item in SPOT_CAPABILITIES)
