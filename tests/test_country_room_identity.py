import pytest

from mission_control.country_room_identity import (
    COUNTRY_ROOM_FIELDS, COUNTRY_ROOM_SERVICES, country_room_contract,
)


def test_nationality_country_room_fields_preserved():
    for field in ("flag", "nationality_demonym", "citizenship_reference",
                  "passport_reference", "anthem_title", "languages",
                  "national_teams", "culture", "country_room"):
        assert field in COUNTRY_ROOM_FIELDS
    assert "the_spot" in COUNTRY_ROOM_SERVICES


@pytest.mark.parametrize("country,continent", [
    ("Ghana", "africa"),
    ("United Kingdom", "europe"),
    ("Barbados", "north-america"),
])
def test_country_room_continent_and_privacy(country, continent):
    profile = country_room_contract(country)
    assert profile["continent"] == continent
    assert profile["anthem_autoplay"] is False
    assert profile["passport_issuance_enabled"] is False
    assert profile["citizenship_determination_enabled"] is False
    assert profile["nationality_inferred_from_location"] is False
    assert profile["verified_profile_data"] is False


def test_unknown_country_fails_closed():
    with pytest.raises(ValueError, match="unknown_country"):
        country_room_contract("Unknown Neverland")


@pytest.mark.parametrize("country,continent,legacy", [
    ("Ghana", "africa", "Africa"),
    ("United Kingdom", "europe", "Europe"),
    ("Barbados", "north-america", "Caribbean"),
])
def test_existing_country_reference_only_populates_known_fields(country, continent, legacy):
    from mission_control.country_room_identity import country_room_reference
    reference = country_room_reference(country)
    assert reference["continent"] == continent
    assert reference["legacy_region"] == legacy
    assert reference["source_backed_fields"] == ("country", "continent", "legacy_region")
    assert "passport_reference" in reference["unverified_fields"]
    assert "nationality_demonym" in reference["unverified_fields"]
    assert reference["country_room_route_published"] is False


def test_country_reference_unknown_fails_closed():
    from mission_control.country_room_identity import country_room_reference
    with pytest.raises(ValueError, match="unknown_country"):
        country_room_reference("Unknown Neverland")
