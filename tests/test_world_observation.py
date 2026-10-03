from datetime import datetime, timezone

from mission_control import ecosystem_intelligence, world_observation


NOW = datetime(2026, 10, 3, 3, 30, tzinfo=timezone.utc)


def _observation(**overrides):
    payload = {
        "object_id": "WX-1",
        "object_type": "weather",
        "event_type": "weather_observation",
        "evidence_class": "observed",
        "source": "bounded_weather_provider",
        "source_ownership": "external_public",
        "observed_at": "2026-10-03T03:29:30Z",
        "fresh_for_seconds": 60,
        "stale_after_seconds": 300,
        "expires_after_seconds": 3600,
        "evidence": ("provider:bounded_weather_provider",),
        "first_party": {
            "software": True,
            "processing": True,
            "storage": True,
            "observation": False,
        },
    }
    payload.update(overrides)
    return payload


def test_world_observation_separates_first_party_processing_from_external_observation():
    result = world_observation.normalise(_observation(), now=NOW)

    assert result["freshness_state"] == "fresh"
    assert result["live_claim_allowed"] is True
    assert result["first_party"]["software"] is True
    assert result["first_party"]["processing"] is True
    assert result["first_party"]["observation"] is False
    assert result["source_ownership"] == "external_public"
    assert result["execution_granted"] is False


def test_external_source_cannot_claim_first_party_observation():
    observation = _observation(
        first_party={
            "software": True,
            "processing": True,
            "storage": True,
            "observation": True,
        }
    )

    try:
        world_observation.normalise(observation, now=NOW)
    except ValueError as exc:
        assert "external source cannot be marked" in str(exc)
    else:
        raise AssertionError("external observation ownership must fail closed")


def test_stale_observation_cannot_claim_live():
    result = world_observation.normalise(
        _observation(observed_at="2026-10-03T03:20:00Z"),
        now=NOW,
    )

    assert result["freshness_state"] == "stale"
    assert result["live_claim_allowed"] is False


def test_unverified_observation_cannot_claim_live_even_when_fresh():
    result = world_observation.normalise(
        _observation(evidence_class="unverified"),
        now=NOW,
    )

    assert result["freshness_state"] == "fresh"
    assert result["live_claim_allowed"] is False


def test_ecosystem_analysis_preserves_structured_world_observation():
    result = ecosystem_intelligence.analyse(
        (
            {
                "domain": "nature",
                "summary": "Weather observation",
                "pressure": 35,
                "confidence": 90,
                "truth_state": "observed",
                "horizon": "now",
                "source": "oap_weather_live_source",
                "evidence": ("provider:bounded_weather_provider",),
                "geography": {"country": "United Kingdom"},
                "observation": _observation(),
            },
        )
    )

    assert result["observation_count"] == 1
    assert result["observations"][0]["source_ownership"] == "external_public"
    assert result["observation_evidence_mix"]["observed"] == 1
    assert result["execution_granted"] is False
