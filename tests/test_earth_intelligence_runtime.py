from mission_control import earth_intelligence, weather_intelligence


def test_earth_intelligence_uses_weather_without_inventing_other_domains():
    weather = weather_intelligence.enrich(
        {
            "temperature": 18,
            "feels_like": 17,
            "precipitation": 0,
            "weather_code": 2,
            "wind_speed": 12,
            "time": "2026-09-02T15:00",
            "days": [{"date": "2026-09-02", "maximum": 20, "minimum": 12, "rain_chance": 20}],
        }
    )
    earth = weather["earth_intelligence"]
    assert earth["world_id"] == "earth"
    assert earth["weather_intelligence_connected"] is True
    assert earth["spatial_binding"] == "THE_SPOT_POSTCODE_TO_UNIVERSE"
    assert earth["current_environment"]["condition"] == "Partly cloudy"
    assert earth["coverage"]["water"] == "not_connected"
    assert earth["coverage"]["ecosystems"] == "not_connected"
    assert earth["full_earth_runtime_ready"] is False
    assert earth["can_execute"] is False


def test_earth_status_preserves_governed_world_and_nature_boundary():
    status = earth_intelligence.status(weather_ready=True)
    assert status["architecture_passed"] is True
    assert status["component_count"] == 10
    assert status["nature_organ_connected"] is True
    assert status["weather_intelligence_connected"] is True
    assert status["the_spot_connected"] is True
    assert status["full_earth_runtime_ready"] is False
    assert status["human_authority_final"] is True
    assert status["can_execute"] is False


def test_weather_status_exposes_earth_connection_truthfully():
    status = weather_intelligence.status(True)
    assert status["earth_intelligence_connected"] is True
    earth = status["earth_intelligence"]
    assert earth["world_id"] == "earth"
    assert earth["full_earth_runtime_ready"] is False
