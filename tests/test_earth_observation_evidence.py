"""Fail-closed NASA Earth observation metadata tests."""
from mission_control.earth_intelligence import validate_earth_observation

GOOD = {
    "observation_id": "obs-777",
    "dataset": "NASA-example",
    "captured_at": "2026-10-20T12:00:00Z",
    "source_url": "https://cmr.earthdata.nasa.gov/search",
    "checksum_sha256": "a" * 64,
}


def test_valid_metadata_is_not_source_or_payload_proof():
    result = validate_earth_observation(GOOD)
    assert result["valid"] is True
    assert result["can_execute"] is False
    assert result["source_verified"] is False
    assert result["payload_integrity_verified"] is False
    assert result["full_earth_runtime_ready"] is False


def test_missing_required_metadata_fails_closed():
    assert validate_earth_observation({**GOOD, "dataset": ""})["reason"] == "missing_required_metadata"


def test_capture_time_must_have_timezone():
    assert validate_earth_observation({**GOOD, "captured_at": "2026-10-20T12:00:00"})["reason"] == "invalid_capture_time"


def test_rejects_untrusted_hosts_and_insecure_urls():
    for url in ("http://cmr.earthdata.nasa.gov/search",
                "https://cmr.earthdata.nasa.gov.evil.example/search",
                "https://attacker@cmr.earthdata.nasa.gov/search"):
        result = validate_earth_observation({**GOOD, "source_url": url})
        assert result["valid"] is False
        assert result["can_execute"] is False


def test_invalid_checksum_fails_closed():
    assert validate_earth_observation({**GOOD, "checksum_sha256": "not-a-digest"})["reason"] == "invalid_checksum"


def test_deterministic_metadata_fingerprint():
    assert validate_earth_observation(GOOD)["metadata_fingerprint"] == validate_earth_observation(dict(GOOD))["metadata_fingerprint"]
