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
