from mission_control import (
    ecosystem_live_sources,
    intelligence_runtime_proof,
    location_intelligence,
)


def _provider_status(weather_verified: bool) -> dict[str, object]:
    return {
        "postcode_provider_verified": weather_verified,
        "global_provider_verified": weather_verified,
        "weather_provider_verified": weather_verified,
        "weather_intelligence": {},
        "weather_intelligence_architecture_passed": True,
        "weather_intelligence_component_count": 7,
        "weather_intelligence_ready": weather_verified,
        "weather_intelligence_first_party_ready": False,
        "spatial_levels": (),
        "spatial_contract": "POSTCODE_TO_UNIVERSE",
        "bounded_timeout": 6,
        "cache_seconds": 300,
        "last_success_epoch": {},
        "errors": {},
        "ready": weather_verified,
    }


def test_location_weather_refresh_builds_real_place_and_nature_signals(monkeypatch):
    monkeypatch.setattr(
        location_intelligence,
        "lookup_with_weather",
        lambda value: {
            "query": value,
            "postcode": "CR4 1AB",
            "borough": "Merton",
            "county": "Greater London",
            "country": "United Kingdom",
            "continent": "Europe",
            "global": "Global",
            "provider": "UK postcode service",
            "weather": {
                "provider": "Live weather service",
                "time": "2026-09-13T16:00",
                "intelligence": {
                    "condition": "Rain",
                    "advisory_level": "yellow",
                    "observation_time": "2026-09-13T16:00",
                },
            },
        },
    )
    monkeypatch.setattr(location_intelligence, "status", lambda: _provider_status(True))

    result = ecosystem_live_sources.location_weather("CR4 1AB")

    assert result["weather_environment_proven"] is True
    assert result["all_required_live_sources_proven"] is False
    assert result["silent_location_tracking"] is False
    assert result["analysis"]["execution_granted"] is False
    assert {signal["domain"] for signal in result["analysis"]["signals"]} == {
        "place",
        "nature",
    }
    weather_signal = next(
        signal for signal in result["analysis"]["signals"] if signal["domain"] == "nature"
    )
    assert weather_signal["pressure"] == 35
    assert weather_signal["geography"]["postcode"] == "CR4 1AB"


def test_live_source_status_makes_no_network_call(monkeypatch):
    monkeypatch.setattr(location_intelligence, "status", lambda: _provider_status(True))
    current = ecosystem_live_sources.status()

    assert current["live_external_source_present"] is True
    assert current["all_required_live_sources_proven"] is False
    assert current["network_calls_made"] is False
    assert current["execution_granted"] is False


def test_runtime_proof_uses_observed_provider_attestation(monkeypatch):
    monkeypatch.setattr(location_intelligence, "status", lambda: _provider_status(True))
    current = intelligence_runtime_proof.status()
    worlds = {item["id"]: item for item in current["worlds"]}
    cross = {item["id"]: item for item in current["cross_system"]}

    assert current["weather_provider_verified"] is True
    assert worlds["earth"]["live_external_ready"] is True
    assert worlds["earth"]["full_runtime_ready"] is False
    assert cross["ecosystem"]["live_external_ready"] is True
    assert cross["ecosystem"]["full_runtime_ready"] is False
    assert current["universal_runtime_green"] is False


def test_founder_live_source_endpoint_requires_explicit_location(client, monkeypatch):
    missing = client.get("/mission/intelligence/ecosystem/source/location-weather")
    assert missing.status_code == 400

    monkeypatch.setattr(
        ecosystem_live_sources,
        "location_weather",
        lambda location: {
            "location_query": location,
            "weather_environment_proven": True,
            "all_required_live_sources_proven": False,
            "silent_location_tracking": False,
            "execution_granted": False,
        },
    )
    response = client.get(
        "/mission/intelligence/ecosystem/source/location-weather?location=Mitcham"
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["location_query"] == "Mitcham"
    assert payload["weather_environment_proven"] is True
    assert payload["execution_granted"] is False
    assert response.headers["Cache-Control"] == "no-store"
