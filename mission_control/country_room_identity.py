"""Read-only national identity field contract for OAP World country rooms.

This is a schema, not a populated global registry, passport issuer, or proof
of nationality. No inferred citizenship, location or anthem licensing.
"""
from __future__ import annotations

from mission_control.continent_spot_paths import world_continent_for_country

COUNTRY_ROOM_FIELDS = (
    "country", "continent", "flag", "nationality_demonym",
    "citizenship_reference", "passport_reference", "anthem_title",
    "anthem_audio_rights", "languages", "map_reference",
    "regions", "districts", "postcodes", "national_symbols",
    "history", "culture", "heritage", "sports", "national_teams",
    "food", "music", "creators", "humour", "communities",
    "country_room",
)

COUNTRY_ROOM_SERVICES = (
    "pulse", "signal", "chronicle", "the_link", "oap_market",
    "oap_movement", "arena", "oap_tv", "explorer", "the_spot",
)

def country_room_contract(country: str) -> dict[str, object]:
    """Expose approved fields without inventing unverified country facts."""
    continent = world_continent_for_country(country)
    if continent is None:
        raise ValueError("unknown_country")
    return {
        "country": country,
        "continent": continent,
        "fields": COUNTRY_ROOM_FIELDS,
        "services": COUNTRY_ROOM_SERVICES,
        "anthem_autoplay": False,
        "citizenship_determination_enabled": False,
        "passport_issuance_enabled": False,
        "nationality_inferred_from_location": False,
        "verified_profile_data": False,
    }
