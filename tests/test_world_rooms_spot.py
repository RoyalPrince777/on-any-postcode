from mission_control import products


def test_world_rooms_replace_postcode_rooms_as_product_name():
    rooms = next(item for item in products.SPOT_CAPABILITIES if item["id"] == "postcode-rooms")
    assert rooms["name"] == "World Rooms"
    assert "Global" in rooms["purpose"]
    assert "Continent" in rooms["purpose"]
    assert "Country" in rooms["purpose"]
    assert "Postcode" in rooms["purpose"]


def test_world_rooms_hierarchy_is_locked_and_ordered():
    validation = products.validate_world_room_levels()
    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"]["levels"] == 7
    assert tuple(item["id"] for item in products.WORLD_ROOM_LEVELS) == (
        "global",
        "continent",
        "country",
        "county-region",
        "borough-district",
        "postcode",
        "local",
    )


def test_public_spot_uses_oap_language_and_world_rooms():
    by_source = {item["source_id"]: item for item in products.PUBLIC_SPOT_CAPABILITIES}
    assert by_source["signal"]["name"] == "Signal"
    assert "feed" in by_source["signal"]["purpose"].lower()
    assert by_source["postcode-rooms"]["name"] == "World Rooms"
    assert by_source["events"]["name"] == "Activity / Adventure"
    assert by_source["identity"]["name"] == "My World"


def test_world_languages_follow_real_geographic_learning_hierarchy():
    languages = next(item for item in products.SPOT_CAPABILITIES if item["id"] == "languages")
    assert "Continent" in languages["function"]
    assert "Country/Territory" in languages["function"]
    assert "Region" in languages["function"]
    assert "Language" in languages["function"]
    assert "Dialect/Variant" in languages["function"]
