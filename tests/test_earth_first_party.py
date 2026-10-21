"""Founder-first OAP Earth intake negative boundary tests."""
from datetime import UTC, datetime

import pytest

from mission_control import earth_first_party, earth_intelligence

NOW = datetime(2026, 10, 21, 1, 0, tzinfo=UTC)
GOOD = {
    "source_ownership": "oap_owned",
    "node_id": "oap-ground-001",
    "measurement": "temperature",
    "value": 18.4,
    "unit": "celsius",
    "observed_at": "2026-10-21T00:00:00Z",
    "received_at": "2026-10-21T00:00:02Z",
}


def test_owned_sensor_metadata_never_claims_live_or_signature_proof():
    result = earth_first_party.intake(GOOD, now=NOW)
    assert result["source_ownership"] == "oap_owned"
    assert result["first_party"]["observation"] is False
    assert result["signature_verified"] is False
    assert result["calibration_verified"] is False
    assert result["live_claim_allowed"] is False
    assert result["execution_granted"] is False


@pytest.mark.parametrize("change", [
    {"source_ownership": "external_public"},
    {"source_ownership": "founder_approved_external"},
    {"node_id": "nasa-ground-001"},
    {"measurement": "unknown"},
    {"unit": "fahrenheit"},
    {"value": float("nan")},
    {"value": True},
    {"value": 1000.0},
    {"observed_at": "2026-10-21T00:00:00"},
    {"received_at": "2026-10-20T00:00:00Z"},
])
def test_rejects_untrusted_or_invalid_readings(change):
    with pytest.raises(ValueError):
        earth_first_party.intake({**GOOD, **change}, now=NOW)


def test_repeat_reading_has_deterministic_fingerprint():
    first = earth_first_party.intake(GOOD, now=NOW)
    second = earth_first_party.intake(dict(GOOD), now=NOW)
    assert first["reading_fingerprint_sha256"] == second["reading_fingerprint_sha256"]


def test_policy_forbids_external_feeds_and_hosted_storage():
    policy = earth_first_party.status()
    assert policy["external_observations_allowed"] is False
    assert policy["third_party_hosted_storage_allowed"] is False
    assert policy["infrastructure"] == "oap_owned_physical_servers_first"
    assert policy["sensor_nodes_verified"] == 0
    assert policy["first_party_observation_runtime_ready"] is False


def test_earth_core_accepts_owned_reading_but_never_claims_live():
    result = earth_intelligence.from_owned_sensor(GOOD, now=NOW)
    assert result["source_policy"] == "oap_owned_sensors_only"
    assert result["observation"]["source_ownership"] == "oap_owned"
    assert result["trusted_observations"] == 0
    assert result["live_environment_ready"] is False
    assert result["can_execute"] is False


def test_earth_core_rejects_external_observations():
    with pytest.raises(ValueError, match="external_observations_forbidden"):
        earth_intelligence.from_owned_sensor(
            {**GOOD, "source_ownership": "external_public"}, now=NOW
        )


def test_first_party_status_does_not_trust_legacy_weather():
    result = earth_intelligence.first_party_status()
    assert result["source_policy"] == "oap_owned_sensors_only"
    assert result["legacy_weather_is_authoritative"] is False
    assert result["nasa_adapter_enabled"] is False
    assert result["verified_owned_physical_servers"] == 0
    assert result["full_earth_runtime_ready"] is False
