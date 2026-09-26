from __future__ import annotations

import json

import pytest

from scripts import weather_live_green_gate as gate


def _resolved(*, advisory="yellow", observation_time="2026-09-26T12:00", received=1000):
    return {
        "postcode": "CR4 1AB",
        "weather": {
            "provider_id": "api.open-meteo.com",
            "source_received_epoch": received,
            "source_ttl_seconds": 300,
            "intelligence": {
                "advisory_level": advisory,
                "observation_time": observation_time,
            },
            "earth_intelligence": {"live_environment_ready": True},
        },
    }


def _status(*, ready=True):
    return {
        "postcode_provider_verified": ready,
        "weather_provider_verified": ready,
        "weather_intelligence_ready": ready,
        "weather_intelligence_first_party_ready": False,
    }


def test_receipt_proves_live_path_without_claiming_first_party_observation_network():
    receipt = gate.build_receipt(_resolved(), _status(), now=1100)

    assert receipt["live_path_proven"] is True
    assert receipt["fresh_receipt"] is True
    assert receipt["weather_provider_id"] == "api.open-meteo.com"
    assert receipt["first_party_intelligence"] is True
    assert receipt["first_party_observation_network"] is False
    assert receipt["precise_location_persisted"] is False
    assert receipt["silent_location_tracking"] is False
    assert receipt["execution_granted"] is False


@pytest.mark.parametrize(
    ("advisory", "observation_time", "received"),
    [
        ("unavailable", "2026-09-26T12:00", 1000),
        ("yellow", "", 1000),
        ("yellow", "2026-09-26T12:00", 600),
    ],
)
def test_receipt_fails_closed_on_unusable_or_stale_weather(advisory, observation_time, received):
    receipt = gate.build_receipt(
        _resolved(advisory=advisory, observation_time=observation_time, received=received),
        _status(),
        now=1100,
    )
    assert receipt["live_path_proven"] is False


def test_main_emits_failure_receipt_when_live_source_is_unavailable(monkeypatch, capsys):
    def fail(_location):
        raise gate.location_intelligence.LocationUnavailable("provider_down")

    monkeypatch.setattr(gate.location_intelligence, "lookup_with_weather", fail)

    with pytest.raises(SystemExit, match="failed closed"):
        gate.main()

    receipt = json.loads(capsys.readouterr().out.strip())
    assert receipt["live_path_proven"] is False
    assert receipt["failure_type"] == "LocationUnavailable"
    assert receipt["silent_location_tracking"] is False
