from datetime import datetime, timezone

from mission_control import evidence_gate
from oap.smi import planetary_intelligence

NOW = datetime(2026, 10, 4, 0, 30, tzinfo=timezone.utc)


def _observation(**overrides):
    value = {
        "object_id": "WX-1",
        "object_type": "weather",
        "event_type": "weather_observation",
        "evidence_class": "observed",
        "source": "bounded-weather",
        "source_ownership": "external_public",
        "observed_at": "2026-10-04T00:29:30Z",
        "fresh_for_seconds": 60,
        "stale_after_seconds": 300,
        "expires_after_seconds": 3600,
        "evidence": ("provider:bounded-weather",),
        "first_party": {
            "software": True,
            "processing": True,
            "storage": True,
            "observation": False,
        },
    }
    value.update(overrides)
    return value


def _signal(**overrides):
    value = {
        "id": "sig-1",
        "domain": "nature",
        "horizon": "now",
        "truth_state": "observed",
        "summary": "Bounded weather context",
        "source": "authorised-test-source",
        "evidence": ("receipt:sig-1",),
        "pressure": 20,
        "confidence": 85,
        "geography": {
            "postcode": "SW16 1AA",
            "country": "United Kingdom",
            "continent": "Europe",
        },
        "affected_systems": ("OAP Nature",),
    }
    value.update(overrides)
    return value


def test_evidence_gate_preserves_provenance_and_analysis_only_authority():
    result = evidence_gate.assess((_signal(),))

    assert result["evidence_complete"] is True
    assert result["gates"]["provenance"] is True
    assert result["gates"]["truth_class"] is True
    assert result["gates"]["authority"] is True
    assert result["consequential_green_allowed"] is False
    assert result["execution_granted"] is False
    assert result["provenance"][0]["source"] == "authorised-test-source"


def test_evidence_gate_fails_closed_on_contradiction():
    result = evidence_gate.assess(
        (_signal(contradictions=("Independent source disagrees",)),)
    )

    assert result["gates"]["contradiction_check"] is False
    assert result["consequential_green_allowed"] is False
    assert result["contradictions"] == ("Independent source disagrees",)


def test_evidence_gate_uses_world_observation_freshness(monkeypatch):
    monkeypatch.setattr(
        "mission_control.world_observation.datetime",
        type(
            "FixedDateTime",
            (),
            {
                "now": staticmethod(lambda tz=None: NOW),
                "fromisoformat": staticmethod(datetime.fromisoformat),
            },
        ),
    )
    result = evidence_gate.assess(
        (_signal(observation=_observation(observed_at="2026-10-04T00:20:00Z")),)
    )

    assert result["gates"]["freshness"] is False
    assert result["gates"]["runtime_observation"] is False
    assert result["consequential_green_allowed"] is False


def test_planetary_correlation_emits_evidence_assessment():
    result = planetary_intelligence.correlate((_signal(),))

    assessment = result["evidence_assessment"]
    assert assessment["kind"] == "smi_evidence_assessment"
    assert assessment["evidence_complete"] is True
    assert assessment["consequential_green_allowed"] is False
    assert assessment["execution_granted"] is False


def test_missing_evidence_or_truth_class_fails_closed():
    missing_evidence = _signal(evidence=())
    try:
        evidence_gate.assess((missing_evidence,))
    except ValueError as exc:
        assert "evidence references" in str(exc)
    else:
        raise AssertionError("missing evidence must fail closed")

    missing_truth = _signal(truth_state="")
    try:
        evidence_gate.assess((missing_truth,))
    except ValueError as exc:
        assert "truth class" in str(exc)
    else:
        raise AssertionError("missing truth class must fail closed")
