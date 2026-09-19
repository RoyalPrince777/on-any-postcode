import pytest

from mission_control import location_intelligence, weather_intelligence


def test_weather_intelligence_enriches_live_observation_without_fetching():
    observation = {
        "temperature": 18.0,
        "feels_like": 17.0,
        "precipitation": 0.2,
        "weather_code": 61,
        "wind_speed": 12.0,
        "time": "2026-09-02T16:00",
        "days": [
            {"date": "2026-09-02", "maximum": 20, "minimum": 13, "rain_chance": 75},
            {"date": "2026-09-03", "maximum": 19, "minimum": 12, "rain_chance": 30},
        ],
        "provider": "Live weather service",
    }

    result = weather_intelligence.enrich(observation)

    assert result["temperature"] == 18.0
    assert result["provider"] == "Live weather service"
    assert result["intelligence"]["name"] == "OAP Weather Intelligence"
    assert result["intelligence"]["condition"] == "Light rain"
    assert result["intelligence"]["rain_signal"] == "high"
    assert result["intelligence"]["wind_signal"] == "light"
    assert result["intelligence"]["thermal_signal"] == "mild"
    assert result["intelligence"]["advisory_level"] == "yellow"
    assert result["intelligence"]["spatial_binding"] == "THE_SPOT_POSTCODE_TO_UNIVERSE"


def test_weather_intelligence_escalates_severe_conditions():
    result = weather_intelligence.enrich(
        {
            "temperature": 21,
            "precipitation": 9,
            "weather_code": 95,
            "wind_speed": 65,
            "days": [],
        }
    )

    assert result["intelligence"]["condition"] == "Thunderstorm"
    assert result["intelligence"]["advisory_level"] == "red"
    assert result["intelligence"]["wind_signal"] == "strong"


def test_weather_intelligence_status_is_truthful_about_source_boundary():
    cold = weather_intelligence.status(False)
    live = weather_intelligence.status(True)

    assert cold["architecture_passed"] is True
    assert cold["component_count"] == 7
    assert cold["ready"] is False
    assert live["ready"] is True
    assert live["the_spot_connected"] is True
    assert live["first_party_observation_ready"] is False
    assert live["external_dependency_present"] is True
    assert live["source_mode"] == "external_live_bootstrap"


def test_missing_weather_fields_never_report_reassuring_conditions():
    result = weather_intelligence.enrich({})
    signals = result["intelligence"]

    assert signals["condition"] == "Conditions unavailable"
    assert signals["advisory_level"] == "unavailable"
    assert signals["rain_signal"] == "unavailable"
    assert signals["wind_signal"] == "unavailable"
    assert signals["thermal_signal"] == "unavailable"
    assert result["earth_intelligence"]["live_environment_ready"] is False


def test_missing_weather_field_only_affects_its_own_signal():
    result = weather_intelligence.enrich({"weather_code": 0, "temperature": 18})

    assert result["intelligence"]["condition"] == "Clear"
    assert result["intelligence"]["advisory_level"] == "green"
    assert result["intelligence"]["rain_signal"] == "unavailable"
    assert result["intelligence"]["wind_signal"] == "unavailable"
    assert result["intelligence"]["thermal_signal"] == "mild"


def test_invalid_weather_payload_revokes_transport_success(monkeypatch):
    monkeypatch.setattr(location_intelligence, "_CACHE", {})
    monkeypatch.setattr(
        location_intelligence, "_PROVIDER_SUCCESS", {"api.open-meteo.com": 123.0}
    )
    monkeypatch.setattr(location_intelligence, "_PROVIDER_ERROR", {})
    monkeypatch.setattr(
        location_intelligence, "_json", lambda *_: {"current": {}, "daily": {}}
    )

    with pytest.raises(
        location_intelligence.LocationUnavailable, match="invalid_weather_response"
    ):
        location_intelligence.weather(9.87654, 8.76543)

    assert location_intelligence.status()["weather_provider_verified"] is False
    assert location_intelligence.status()["weather_intelligence_ready"] is False


def test_invalid_weather_payload_missing_time_revokes_transport_success(monkeypatch):
    monkeypatch.setattr(location_intelligence, "_CACHE", {})
    monkeypatch.setattr(
        location_intelligence, "_PROVIDER_SUCCESS", {"api.open-meteo.com": 123.0}
    )
    monkeypatch.setattr(location_intelligence, "_PROVIDER_ERROR", {})
    monkeypatch.setattr(
        location_intelligence,
        "_json",
        lambda *_: {"current": {"weather_code": 0}, "daily": {}},
    )

    with pytest.raises(location_intelligence.LocationUnavailable, match="invalid_weather_response"):
        location_intelligence.weather(9.87655, 8.76544)

    assert location_intelligence.status()["weather_provider_verified"] is False
