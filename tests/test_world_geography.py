from __future__ import annotations

from mission_control import world_geography


def test_oap_continent_order_stays_locked():
    assert world_geography.OAP_CONTINENT_ORDER == (
        "Africa",
        "Europe",
        "Asia",
        "North America",
        "South America",
        "Caribbean",
        "Oceania",
    )


def test_common_source_country_aliases_map_without_network_lookup():
    expected = {
        "Ghana": "Africa",
        "United Kingdom": "Europe",
        "Türkiye": "Asia",
        "United States of America": "North America",
        "Brazil": "South America",
        "Curaçao": "Caribbean",
        "New Caledonia": "Oceania",
        "Democratic Republic of the Congo": "Africa",
        "Republic of Korea": "Asia",
    }
    for country, continent in expected.items():
        assert world_geography.continent_for_country(country) == continent

    status = world_geography.reference_status()
    assert status["network_lookup"] is False
    assert status["precise_location"] is False
    assert status["unknown_labels_fail_closed"] is True


def test_unknown_country_is_not_guessed():
    assert world_geography.continent_for_country("Unknown Source Place") is None
    assert world_geography.continents_for_countries(("Unknown Source Place",)) == ()


def test_multi_country_event_returns_canonical_unique_continent_order():
    assert world_geography.continents_for_countries(
        ("Japan", "Ghana", "Brazil", "Japan", "Jamaica")
    ) == ("Africa", "Asia", "South America", "Caribbean")
