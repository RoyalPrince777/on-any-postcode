from __future__ import annotations

from pathlib import Path

from mission_control import location_intelligence


def test_location_lookup_completes_postcode_to_universe(monkeypatch):
    location_intelligence._CACHE.clear()

    def fake_json(url: str, expected_host: str):
        assert expected_host == "api.postcodes.io"
        assert "/postcodes/CR41AB" in url
        return {
            "result": {
                "postcode": "CR4 1AB",
                "admin_district": "Merton",
                "admin_county": "Greater London",
                "country": "England",
                "latitude": 51.4,
                "longitude": -0.16,
            }
        }

    monkeypatch.setattr(location_intelligence, "_json", fake_json)
    result = location_intelligence.lookup("CR4 1AB")

    assert location_intelligence.SPATIAL_LEVELS == (
        "postcode",
        "borough",
        "county",
        "country",
        "continent",
        "global",
        "universe",
    )
    assert [item["level"] for item in result["hierarchy"]] == list(
        location_intelligence.SPATIAL_LEVELS
    )
    assert result["postcode"] == "CR4 1AB"
    assert result["borough"] == "Merton"
    assert result["county"] == "Greater London"
    assert result["country"] == "England"
    assert result["continent"] == "Europe"
    assert result["global"] == "Global"
    assert result["universe"] == "Universe"


def test_location_status_names_the_seven_tier_contract():
    status = location_intelligence.status()

    assert status["spatial_contract"] == "POSTCODE_TO_UNIVERSE"
    assert tuple(status["spatial_levels"]) == location_intelligence.SPATIAL_LEVELS


def test_world_front_door_is_local_first_and_keeps_football_separate():
    html = Path("templates/home.html").read_text(encoding="utf-8")
    hierarchy = (
        "📍 Postcode",
        "🏙️ Borough / District",
        "🧭 County / Region",
        "🏳️ Country",
        "🌍 Continent",
        "🌐 Global",
        "✨ Universe",
    )

    positions = [html.index(label) for label in hierarchy]
    assert positions == sorted(positions)
    assert "Postcode to Universe" in html
    assert "Football has its own home; it no longer defines the whole product." in html
    assert "url_for('world_cup')" in html
