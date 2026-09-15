from mission_control import (
    ecosystem_live_sources,
    humanitarian_emergency_tracker,
    intelligence_runtime_proof,
    location_intelligence,
    smi_receipt_backend,
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
    assert current["weather_environment_proven"] is True


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


def test_full_proof_reports_pending_gates_and_durable_hrm_truth(monkeypatch):
    monkeypatch.setattr(
        ecosystem_live_sources,
        "location_weather",
        lambda location: {
            "location_query": location,
            "weather_environment_proven": True,
            "execution_granted": False,
        },
    )
    monkeypatch.setattr(
        humanitarian_emergency_tracker,
        "humanitarian_emergency_snapshot",
        lambda **kwargs: {
            "live_data_ready": True,
            "live_source_count": 2,
            "live_sources": ("gdacs", "who_don"),
            "event_count": 3,
            "fetched_at": "2026-09-13T16:00:00Z",
        },
    )
    monkeypatch.setattr(
        smi_receipt_backend,
        "receipt_backend_status",
        lambda: {
            "independent_durable_hrm_ready": False,
            "receipt_backend": "local_sqlite_receipt_store",
        },
    )
    gates = tuple(
        {
            "id": gate_id,
            "domain": "test",
            "required": "proof",
            "evidence": "test",
            "proven": gate_id in {
                "weather_environment",
                "infrastructure_telemetry",
                "people_aggregate",
                "trust_guardian",
            },
        }
        for gate_id in (
            "weather_environment",
            "movement_navigation",
            "civic_public_services",
            "culture_provenance",
            "infrastructure_telemetry",
            "market_activity",
            "people_aggregate",
            "trust_guardian",
        )
    )
    monkeypatch.setattr(
        ecosystem_live_sources,
        "status",
        lambda: {"external_source_gates": gates},
    )

    result = ecosystem_live_sources.prove_full("Mitcham")

    assert result["proven_gate_count"] == 4
    assert result["required_gate_count"] == 8
    assert result["durable_hrm_write_read_proven"] is False
    assert result["full_ecosystem_green"] is False
    assert "market_activity" in result["pending_gates"]
    assert result["execution_granted"] is False
    assert result["human_authority_final"] is True


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


def test_founder_full_proof_endpoint_requires_location_and_never_executes(client, monkeypatch):
    missing = client.post("/mission/intelligence/ecosystem/prove-full", json={})
    assert missing.status_code == 400

    monkeypatch.setattr(
        ecosystem_live_sources,
        "prove_full",
        lambda location: {
            "location_query": location,
            "proven_gate_count": 4,
            "required_gate_count": 8,
            "full_ecosystem_green": False,
            "execution_granted": False,
            "human_authority_final": True,
        },
    )
    response = client.post(
        "/mission/intelligence/ecosystem/prove-full",
        json={"location": "Mitcham"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["location_query"] == "Mitcham"
    assert payload["full_ecosystem_green"] is False
    assert payload["execution_granted"] is False
    assert response.headers["Cache-Control"] == "no-store"
