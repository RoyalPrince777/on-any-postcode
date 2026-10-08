"""Pure first-party catalogue metadata contract tests."""
import pytest

from mission_control.music_catalogue_metadata import normalize_metadata


def test_normalization():
    assert normalize_metadata({"genre": "  Highlife ", "language": "ak",
        "country": "GH", "isrc": "GBABC1234567", "instruments": ["Guitar", "Drums"]}) == {
        "genre": "Highlife", "language": "ak", "country": "GH",
        "isrc": "GBABC1234567", "instruments": ["Guitar", "Drums"]}


@pytest.mark.parametrize("data", [
    {"owner_identity_id": "forged"},
    {"genre": ""},
    {"language": "not a valid language"},
    {"country": "GHA"},
    {"isrc": "unverified"},
    {"instruments": ["Drum", "drum"]},
    {"instruments": ["X"] * 13},
    {"genre": 123},
])
def test_reject_invalid(data):
    with pytest.raises(ValueError):
        normalize_metadata(data)


def test_does_not_grant_playback_or_payment():
    result = normalize_metadata({"genre": "Hiplife"})
    assert "playback_enabled" not in result
    assert "rights_status" not in result
    assert "payment_authorized" not in result
