from mission_control import products


def test_global_earth_replaces_flag_vote_as_geography_identity():
    earth = next(item for item in products.SPOT_CAPABILITIES if item["id"] == "postcode-rooms")
    assert earth["name"] == "Global Earth"
    assert "Global Earth" in earth["purpose"]
    assert "Continent" in earth["purpose"]
    assert "Country + National Anthem" in earth["purpose"]
    assert "County/Region" in earth["purpose"]
    assert "Borough/District" in earth["purpose"]
    assert "Postcode" in earth["purpose"]
    assert "flag-vote" not in {item["id"] for item in products.SPOT_CAPABILITIES}


def test_global_earth_hierarchy_is_locked_and_ordered():
    validation = products.validate_world_room_levels()
    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"]["levels"] == 6
    assert tuple(item["id"] for item in products.WORLD_ROOM_LEVELS) == (
        "earth",
        "continent",
        "country",
        "county-region",
        "borough-district",
        "postcode",
    )
    assert tuple(item["parent_id"] for item in products.WORLD_ROOM_LEVELS) == (
        "",
        "earth",
        "continent",
        "country",
        "county-region",
        "borough-district",
    )


def test_public_spot_uses_oap_language_and_global_earth():
    by_source = {item["source_id"]: item for item in products.PUBLIC_SPOT_CAPABILITIES}
    assert by_source["signal"]["name"] == "Signal"
    assert "feed" in by_source["signal"]["purpose"].lower()
    assert by_source["postcode-rooms"]["name"] == "Global Earth"
    assert by_source["postcode-rooms"]["purpose"] == (
        "Move from Global Earth to Continent, Country + National Anthem, "
        "County/Region, Borough/District and Postcode."
    )
    assert "flag-vote" not in {item["source_id"] for item in products.PUBLIC_SPOT_CAPABILITIES}
    assert by_source["events"]["name"] == "Activity / Adventure"
    assert by_source["identity"]["name"] == "My World"


def test_national_anthem_stays_country_metadata_not_geography_level():
    ids = {item["id"] for item in products.WORLD_ROOM_LEVELS}
    country = next(item for item in products.WORLD_ROOM_LEVELS if item["id"] == "country")

    assert "national-anthem" not in ids
    assert "national anthem metadata" in country["purpose"].lower()
    assert "source-backed" in country["purpose"]
    assert "rights-safe" in country["purpose"]


def test_world_languages_follow_real_geographic_learning_hierarchy():
    languages = next(item for item in products.SPOT_CAPABILITIES if item["id"] == "languages")
    assert "Continent" in languages["function"]
    assert "Country/Territory" in languages["function"]
    assert "Region" in languages["function"]
    assert "Language" in languages["function"]
    assert "Dialect/Variant" in languages["function"]
