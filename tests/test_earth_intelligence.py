from mission_control import earth_intelligence


def test_earth_intelligence_composes_spatial_weather_context():
    location = {
        "postcode": "CR4 1AA",
        "borough": "Merton",
        "county": "London",
        "country": "England",
        "continent": "Europe",
        "global": "Global",
        "universe": "Universe",
    }
    weather = {
        "temperature": 18.0,
        "feels_like": 17.0,
        "precipitation": 0.1,
        "wind_speed": 12.0,
        "time": "2026-09-02T16:00",
        "intelligence": {
            "condition": "Partly cloudy",
            "advisory_level": "green",
        },
    }

    result = earth_intelligence.compose(location, weather)

    assert result["name"] == "OAP Earth Intelligence"
    assert result["spatial_context"]["postcode"] == "CR4 1AA"
    assert result["local_conditions"]["condition"] == "Partly cloudy"
    assert result["weather_intelligence_connected"] is True
    assert result["environment_intelligence_ready"] is False
    assert result["hazard_intelligence_ready"] is False
    assert result["earth_memory_connected"] is False


def test_earth_intelligence_status_is_truthful_and_bounded():
    status = earth_intelligence.status(weather_ready=True)

    assert status["architecture_passed"] is True
    assert status["component_count"] == 8
    assert status["weather_intelligence_connected"] is True
    assert status["ready"] is True
    assert status["fully_operational"] is False
    assert status["terrain_intelligence_ready"] is False
    assert status["nature_intelligence_ready"] is False
