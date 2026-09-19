"""Recovery regressions for OAP weather source-health truth boundaries."""

import json
import time

import pytest

from mission_control import location_intelligence as locations

HOST = "api.open-meteo.com"
URL = "https://api.open-meteo.com/v1/forecast"


class _Response:
    def __init__(self, body, url=URL):
        self.body = body
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, _size):
        return self.body


@pytest.fixture
def provider_state(monkeypatch):
    now = time.time()
    monkeypatch.setattr(locations, "_CACHE", {})
    monkeypatch.setattr(locations, "_PROVIDER_SUCCESS", {HOST: now})
    monkeypatch.setattr(locations, "_PROVIDER_ERROR", {})
    return now


def test_weather_timeout_revokes_previous_healthy_status(monkeypatch, provider_state):
    def timeout(_request, timeout):
        assert timeout == locations.LOOKUP_TIMEOUT_SECONDS
        raise TimeoutError("provider timed out")

    monkeypatch.setattr(locations.urlrequest, "urlopen", timeout)

    assert locations.status()["weather_provider_verified"] is True
    with pytest.raises(locations.LocationUnavailable, match="location_provider_unavailable"):
        locations._json(URL, HOST)

    health = locations.status()
    assert health["weather_provider_verified"] is False
    assert health["weather_intelligence_ready"] is False
    assert health["errors"][HOST] == "TimeoutError"


@pytest.mark.parametrize(
    ("body", "error"),
    [
        (b"{invalid", "invalid_location_response"),
        (b"[]", "invalid_location_response"),
        (b"0" * (locations.MAX_RESPONSE_BYTES + 1), "location_response_too_large"),
    ],
)
def test_invalid_provider_body_revokes_prior_success(monkeypatch, provider_state, body, error):
    monkeypatch.setattr(
        locations.urlrequest, "urlopen", lambda *_args, **_kwargs: _Response(body)
    )
    with pytest.raises(locations.LocationUnavailable, match=error):
        locations._json(URL, HOST)

    assert locations.status()["weather_provider_verified"] is False
    assert locations.status()["errors"][HOST] == error


def test_redirect_revokes_previous_success(monkeypatch, provider_state):
    monkeypatch.setattr(
        locations.urlrequest,
        "urlopen",
        lambda *_args, **_kwargs: _Response(b"{}", "https://unapproved.example/weather"),
    )

    with pytest.raises(locations.LocationUnavailable, match="location_provider_redirect_rejected"):
        locations._json(URL, HOST)

    assert locations.status()["weather_provider_verified"] is False


def test_recovered_valid_weather_reinstates_health(monkeypatch, provider_state):
    monkeypatch.setattr(
        locations.urlrequest, "urlopen",
        lambda *_args, **_kwargs: _Response(
            json.dumps({
                "current": {"time": "2026-09-19T10:00", "weather_code": 0,
                            "temperature_2m": 18, "wind_speed_10m": 8},
                "daily": {"time": [], "temperature_2m_max": [],
                          "temperature_2m_min": [], "precipitation_probability_max": []},
            }).encode("utf-8")
        ),
    )
    locations._PROVIDER_ERROR[HOST] = "TimeoutError"

    weather = locations.weather(51.403, -0.166)
    health = locations.status()

    assert weather["intelligence"]["condition"] == "Clear"
    assert health["weather_provider_verified"] is True
    assert HOST not in health["errors"]


def test_success_expires_without_new_observation(monkeypatch, provider_state):
    monkeypatch.setattr(
        locations.time, "time", lambda: provider_state + locations.CACHE_SECONDS + 1
    )
    health = locations.status()

    assert health["weather_provider_verified"] is False
    assert health["weather_intelligence_ready"] is False
    assert HOST in health["stale_providers"]
