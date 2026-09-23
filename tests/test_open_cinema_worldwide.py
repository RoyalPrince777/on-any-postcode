"""OAP worldwide open cinema private rights claim matrix, always fail closed."""
from __future__ import annotations

from uuid import uuid4

from mission_control import open_cinema, open_cinema_worldwide as world


def _claim(**overrides):
    row = {
        "country": "GB",
        "models": ["FREE_TO_VIEW"],
        "starts_on": "2026-09-23",
        "ends_on": "2027-09-23",
        "agreement_verified": True,
        "worldwide_cleared": True,
        "playback_enabled": True,
    }
    return {**row, **overrides}


def test_claim_never_mints_country_or_worldwide_licence():
    claim = world.country_claim(_claim())
    assert claim["country"] == "GB"
    assert claim["claimed_models"] == ["FREE_TO_VIEW"]
    assert claim["agreement_verified"] is False
    assert claim["available"] is False
    assert claim["playback_enabled"] is False
    assert len(claim["blockers"]) == 3
    assert "worldwide_cleared" not in claim


def test_global_and_uk_ghana_claims_all_blocked():
    projection = world.matrix([_claim(country="GB"), _claim(country="GH"),
                               _claim(country="US")])
    assert projection["country_count"] == 3
    assert projection["worldwide_cleared"] is False
    assert projection["licensed_countries"] == []
    assert projection["playback_enabled"] is False
    assert all(not item["available"] for item in projection["countries"])


def test_invalid_dates_countries_modes_and_duplicate_claims_fail_closed():
    for override in (
        {"country": "*"}, {"country": "GLOBAL"}, {"country": "G1"},
        {"models": ["FREE_TO_VIEW", "FREE_TO_VIEW"]},
        {"models": ["ALL_RIGHTS"]}, {"models": ["SVOD", "CC_BY"]},
        {"models": True}, {"models": []},
        {"starts_on": "2026-02-30"}, {"ends_on": "2020-01-01"},
        {"ends_on": "none"},
    ):
        assert world.country_claim(_claim(**override)) is None
    assert world.matrix([_claim(), _claim()])["country_count"] == 1
    assert world.matrix([_claim()] * 300)["country_count"] == 1


def test_existing_first_party_open_cinema_preview_reuses_matrix():
    lead = {
        "candidate_id": str(uuid4()), "title": "World Cinema",
        "source": "wikimedia_commons",
        "reference_url": "https://commons.wikimedia.org/wiki/File:World.webm",
        "licence_claim": "CC0",
        "territories": [_claim(country="GB"), _claim(country="GH")],
        "stream_url": "https://example.invalid/stream",
    }
    preview = open_cinema.preview([lead])
    assert preview["worldwide_rights_enabled"] is False
    item = preview["items"][0]
    assert item["worldwide_rights"]["country_count"] == 2
    assert item["worldwide_rights"]["playback_enabled"] is False
    assert item["worldwide_rights"]["licensed_countries"] == []
    assert item["stream_url"] is None
    assert "territories" not in item


def test_missing_territory_claim_is_not_worldwide_permission():
    lead = {
        "candidate_id": str(uuid4()), "title": "No rights",
        "source": "direct_creator", "licence_claim": "DIRECT_PERMISSION",
    }
    item = open_cinema.candidate(lead)
    assert item["worldwide_rights"]["country_count"] == 0
    assert item["worldwide_rights"]["worldwide_cleared"] is False
