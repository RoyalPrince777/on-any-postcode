from datetime import datetime, timezone

from mission_control import ecosystem_intelligence, world_observation

NOW = datetime(2026, 10, 3, 3, 30, tzinfo=timezone.utc)


def _observation(**overrides):
    payload = {
        "object_id": "WX-1",
        "object_type": "weather",
        "event_type": "weather_observation",
        "evidence_class": "observed",
        "source": "api.open-meteo.com",
        "source_ownership": "external_public",
        "observed_at": "2026-10-03T03:29:30Z",
        "fresh_for_seconds": 60,
        "stale_after_seconds": 300,
        "expires_after_seconds": 3600,
        "evidence": ("provider:api.open-meteo.com",),
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
                "evidence": ("provider:api.open-meteo.com",),
                "geography": {"country": "United Kingdom"},
                "observation": _observation(),
            },
        )
    )

    assert result["observation_count"] == 1
    assert result["observations"][0]["source_ownership"] == "external_public"
    assert result["observation_evidence_mix"]["observed"] == 1
    assert result["execution_granted"] is False


def test_future_observation_beyond_clock_skew_is_rejected():
    try:
        world_observation.normalise(
            _observation(observed_at="2026-10-03T03:32:00Z"),
            now=NOW,
        )
    except ValueError as exc:
        assert "too far in the future" in str(exc)
    else:
        raise AssertionError("future-dated observation must fail closed")


def test_observed_at_cannot_be_after_received_at():
    try:
        world_observation.normalise(
            _observation(
                observed_at="2026-10-03T03:29:30Z",
                received_at="2026-10-03T03:29:00Z",
            ),
            now=NOW,
        )
    except ValueError as exc:
        assert "cannot be after received_at" in str(exc)
    else:
        raise AssertionError("impossible chronology must fail closed")


def test_stale_observation_is_context_only_and_cannot_drive_current_pressure():
    result = ecosystem_intelligence.analyse(
        (
            {
                "domain": "nature",
                "summary": "Stale severe weather",
                "pressure": 100,
                "confidence": 100,
                "truth_state": "observed",
                "horizon": "now",
                "source": "stale_weather_source",
                "evidence": ("provider:stale",),
                "risk": "Severe current disruption",
                "recommendation": "Escalate now",
                "observation": _observation(
                    observed_at="2026-10-03T03:20:00Z"
                ),
            },
            {
                "domain": "infrastructure",
                "summary": "Current healthy runtime",
                "pressure": 10,
                "confidence": 90,
                "truth_state": "observed",
                "horizon": "now",
                "source": "oap_runtime",
                "evidence": ("runtime:healthy",),
            },
        ),
        scope="Red Team",
    )

    assert result["state"] == "stable"
    assert result["average_pressure"] == 10.0
    assert result["contextual_only_signal_count"] == 1
    assert "Severe current disruption" not in result["risks"]
    assert "Escalate now" not in result["recommendations"]
    assert result["war_room_required"] is False


def test_only_stale_observations_fail_closed_to_zero_current_pressure():
    result = ecosystem_intelligence.analyse(
        (
            {
                "domain": "nature",
                "summary": "Old severe observation",
                "pressure": 100,
                "confidence": 100,
                "truth_state": "observed",
                "horizon": "now",
                "source": "old_source",
                "evidence": ("old:evidence",),
                "risk": "Current emergency",
                "observation": _observation(
                    observed_at="2026-10-03T03:20:00Z"
                ),
            },
        ),
        scope="Red Team",
    )

    assert result["average_pressure"] == 0.0
    assert result["state"] == "stable"
    assert result["current_signal_count"] == 0
    assert result["war_room_required"] is False
    assert result["risks"] == ()


def test_unregistered_source_cannot_claim_live_or_trusted_ownership():
    result = world_observation.normalise(
        _observation(
            source="unregistered.example",
            source_ownership="unknown",
            evidence=("provider:unregistered.example", "observation_time:2026-10-03T03:29:30Z"),
        ),
        now=NOW,
    )
    assert result["source_registered"] is False
    assert result["source_ownership"] == "unknown"
    assert result["live_claim_allowed"] is False


def test_unregistered_source_cannot_self_claim_external_public_ownership():
    try:
        world_observation.normalise(
            _observation(
                source="unregistered.example",
                source_ownership="external_public",
            ),
            now=NOW,
        )
    except ValueError as exc:
        assert "unregistered source cannot claim trusted ownership" in str(exc)
    else:
        raise AssertionError("unregistered source ownership must fail closed")


def test_registered_source_requires_evidence_bound_to_same_provider_and_time():
    result = world_observation.normalise(
        _observation(
            evidence=(
                "provider:wrong.example",
                "observation_time:2026-10-03T03:29:30Z",
            )
        ),
        now=NOW,
    )
    assert result["source_registered"] is True
    assert result["evidence_bound"] is False
    assert result["live_claim_allowed"] is False


def test_registered_source_rejects_freshness_beyond_source_policy():
    try:
        world_observation.normalise(
            _observation(fresh_for_seconds=901),
            now=NOW,
        )
    except ValueError as exc:
        assert "exceeds trusted source policy" in str(exc)
    else:
        raise AssertionError("caller cannot extend trusted freshness policy")
