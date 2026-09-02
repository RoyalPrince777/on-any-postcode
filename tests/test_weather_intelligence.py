from mission_control import weather_intelligence


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
