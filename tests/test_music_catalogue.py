"""Contract tests for first-party OAP Music discovery catalogue."""

import pytest

from mission_control.music_catalogue import (
    CatalogueEntry,
    CatalogueSelection,
    estimate_metadata_bytes,
    select_entries,
)


def test_multiple_founder_picks_deduplicate_cross_country_artist():
    entry = CatalogueEntry(
        "release-1", ("artist-1",), ("GH", "GB"), ("highlife",), ("2020s",)
    )
    picks = (
        CatalogueSelection("artist", "artist-1"),
        CatalogueSelection("country", "GH"),
        CatalogueSelection("genre", "highlife"),
    )
    assert select_entries((entry, entry), picks) == (entry,)


def test_discovery_only_never_grants_playback_or_sales():
    entry = CatalogueEntry("release-1", ("artist-1",), ("GH",), ("highlife",), ("2020s",))
    assert entry.can_play is False
    assert entry.can_sell is False


def test_licensed_state_still_does_not_grant_sales():
    entry = CatalogueEntry(
        "release-1", ("artist-1",), ("GH",), ("highlife",), ("2020s",),
        rights_state="licensed",
    )
    assert entry.can_play is True
    assert entry.can_sell is False


def test_reject_invalid_choices_and_rights():
    with pytest.raises(ValueError):
        CatalogueSelection("anything", "x")
    with pytest.raises(ValueError):
        CatalogueEntry("x", (), (), (), (), rights_state="pirated")


def test_metadata_storage_estimate_is_raw_only():
    assert estimate_metadata_bytes(10_000_000) == 10_240_000_000
    with pytest.raises(ValueError):
        estimate_metadata_bytes(-1)
