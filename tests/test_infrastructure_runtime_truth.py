from __future__ import annotations

from mission_control import infrastructure


def _modules_by_id(projection):
    return {item["id"]: item for item in projection["modules"]}


def test_maps_and_weather_stay_degraded_without_observed_delivery(monkeypatch):
    monkeypatch.setattr(
        infrastructure.location_intelligence,
        "status",
        lambda: {
            "postcode_provider_verified": False,
            "global_provider_verified": False,
            "weather_provider_verified": False,
            "spatial_contract": "POSTCODE_TO_UNIVERSE",
        },
    )

    projection = infrastructure.get_public_infrastructure()
    modules = _modules_by_id(projection)

    assert modules["maps"]["state"] == "degraded"
    assert modules["maps"]["status"] == "Configured; runtime proof pending"
    assert modules["weather"]["state"] == "degraded"
    assert modules["weather"]["status"] == "Configured; runtime proof pending"
    assert projection["runtime_evidence"] == {
        "maps_runtime_verified": False,
        "weather_runtime_verified": False,
        "spatial_contract": "POSTCODE_TO_UNIVERSE",
        "network_probe_on_get": False,
        "evidence_mode": "observed_delivery",
    }


def test_maps_and_weather_turn_healthy_only_after_observed_delivery(monkeypatch):
    monkeypatch.setattr(
        infrastructure.location_intelligence,
        "status",
        lambda: {
            "postcode_provider_verified": True,
            "global_provider_verified": True,
            "weather_provider_verified": True,
            "spatial_contract": "POSTCODE_TO_UNIVERSE",
        },
    )

    projection = infrastructure.get_public_infrastructure()
    modules = _modules_by_id(projection)

    assert modules["maps"]["state"] == "healthy"
    assert modules["maps"]["status"] == "Runtime verified"
    assert modules["maps"]["readiness"] == "Location lookup ready"
    assert modules["weather"]["state"] == "healthy"
    assert modules["weather"]["status"] == "Runtime verified"
    assert modules["weather"]["readiness"] == "Weather lookup ready"
    assert modules["esim"]["readiness"] == "Activation unavailable"
    assert modules["connectivity"]["state"] == "degraded"
    assert projection["runtime_evidence"]["network_probe_on_get"] is False


def test_infrastructure_truth_projection_never_promotes_external_controls(monkeypatch):
    monkeypatch.setattr(
        infrastructure.location_intelligence,
        "status",
        lambda: {
            "postcode_provider_verified": True,
            "global_provider_verified": True,
            "weather_provider_verified": True,
            "spatial_contract": "POSTCODE_TO_UNIVERSE",
        },
    )

    projection = infrastructure.get_public_infrastructure()

    assert projection["human_authority"]["status"] == "Final approval required"
    assert all(
        item["status"] == "Requires human approval"
        for item in projection["proposed_connections"]
    )
    assert _modules_by_id(projection)["esim"]["status"] == "Provider required"
