from mission_control.continent_spot_paths import (
    CONTINENT_IDS, LEVEL_IDS, breadcrumbs, existing_product_routes, validate_path,
)


def test_language_continents_have_seven_unique_ids():
    assert len(CONTINENT_IDS) == len(set(CONTINENT_IDS)) == 7


def test_existing_geography_levels_are_preserved():
    assert LEVEL_IDS == ("earth", "continent", "country", "county-region",
                         "borough-district", "postcode")


def test_ghana_and_uk_routes():
    gh = breadcrumbs({"continent": "africa", "country": "Ghana",
                      "region": "Eastern Region", "district": "Begoro"})
    uk = breadcrumbs({"continent": "europe", "country": "United Kingdom",
                      "region": "Greater London", "district": "Merton", "postcode": "CR4"})
    assert gh[-1]["level"] == "the-spot"
    assert uk[-2]["label"] == "CR4"


def test_antarctica_has_no_fabricated_country_or_postcode():
    path = breadcrumbs({"continent": "antarctica", "region": "Research sector"})
    assert not any(item["level"] == "country" for item in path)
    assert path[-1]["level"] == "the-spot"
    assert validate_path({"continent": "antarctica", "country": "Antarctica"})


def test_unknown_continent_fails_closed():
    assert validate_path({"continent": "atlantis", "country": "Atlantis"})


def test_reuses_canonical_routes():
    routes = existing_product_routes()
    assert routes["the_spot"] == "/the-spot"
    assert routes["the_link"] == "/the-link"
    assert routes["linkup"] == "/linkup"


def test_every_non_antarctic_continent_accepts_a_country():
    for continent in CONTINENT_IDS:
        if continent == "antarctica":
            continue
        path = breadcrumbs({"continent": continent, "country": "Source-backed country"})
        assert path[2]["level"] == "country"
        assert path[-1]["level"] == "the-spot"


def test_continent_without_country_fails_closed():
    for continent in CONTINENT_IDS:
        if continent != "antarctica":
            assert "country_required" in validate_path({"continent": continent})


def test_no_private_spot_or_location_in_public_breadcrumbs():
    result = breadcrumbs({"continent": "africa", "country": "Ghana"})
    assert all(node["level"] != "my-spot" for node in result)
    assert all("route" not in node for node in result)


def test_public_continent_ui_keeps_existing_route_and_privacy_boundaries():
    from pathlib import Path
    template = (Path(__file__).resolve().parents[1] /
                "mission_control/templates/spot_capability.html").read_text()
    assert 'aria-label="OAP World continents"' in template
    assert 'capability_slug=\'postcode-rooms\'' in template
    assert 'selected_continent == continent_id' in template
    assert "No autoplay." in template
    assert "never published by selecting a continent" in template
    assert "not yet populated globally" in template


def test_country_adapter_keeps_legacy_caribbean_bucket():
    from mission_control.world_geography import continent_for_country
    from mission_control.continent_spot_paths import world_continent_for_country, country_breadcrumbs
    assert continent_for_country("Barbados") == "Caribbean"
    assert world_continent_for_country("Barbados") == "north-america"
    assert country_breadcrumbs("Barbados")[1]["label"] == "north-america"


def test_country_adapter_known_and_unknown():
    import pytest
    from mission_control.continent_spot_paths import world_continent_for_country, country_breadcrumbs
    assert world_continent_for_country("Ghana") == "africa"
    assert world_continent_for_country("United Kingdom") == "europe"
    assert world_continent_for_country("Unknown Neverland") is None
    with pytest.raises(ValueError, match="unknown_country"):
        country_breadcrumbs("Unknown Neverland")
    result = country_breadcrumbs("Ghana", region="Eastern Region", district="Begoro")
    assert result[-1]["level"] == "the-spot"
    assert all("route" not in item for item in result)
