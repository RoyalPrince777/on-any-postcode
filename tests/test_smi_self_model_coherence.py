"""Regression tests for the bounded SMI self-model and coherence gate."""

from oap.smi.coherence import CoherenceEngine
from oap.smi.self_model import SelfModel


def test_self_model_records_truthful_ready_snapshot_without_sentience_claims():
    model = SelfModel()
    snapshot = model.observe(
        (
            {"component": "A", "ready": True, "mode": "observe"},
            {"component": "B", "ready": True, "mode": "recommendation_only"},
        )
    )

    payload = snapshot.as_dict()
    assert snapshot.revision == 1
    assert snapshot.overall_ready is True
    assert snapshot.degraded_components == ()
    assert snapshot.unknown_components == ()
    assert payload["sentience_claimed"] is False
    assert payload["consciousness_claimed"] is False


def test_self_model_marks_unknown_readiness_as_degraded_and_increments_revision():
    model = SelfModel()
    first = model.observe(({"component": "Known", "ready": True},))
    second = model.observe(({"component": "Unknown"},))

    assert first.revision == 1
    assert second.revision == 2
    assert second.overall_ready is False
    assert second.degraded_components == ("Unknown",)
    assert second.unknown_components == ("Unknown",)


def test_coherence_engine_accepts_matching_shared_claims():
    report = CoherenceEngine().evaluate(
        (
            {
                "component": "Left",
                "ready": True,
                "coherence_claims": {"world_revision": 7},
            },
            {
                "component": "Right",
                "ready": True,
                "coherence_claims": {"world_revision": 7},
            },
        )
    )

    assert report.coherent is True
    assert report.human_review_required is False
    assert report.conflicts == ()
    assert report.uncertainty == 0.0


def test_coherence_engine_exposes_conflicting_claims_for_human_review():
    report = CoherenceEngine().evaluate(
        (
            {
                "component": "Left",
                "ready": True,
                "coherence_claims": {"world_revision": 7},
            },
            {
                "component": "Right",
                "ready": True,
                "coherence_claims": {"world_revision": 8},
            },
        )
    )

    assert report.coherent is False
    assert report.human_review_required is True
    assert report.conflicts[0].claim == "world_revision"
    assert set(report.conflicts[0].components) == {"Left", "Right"}
    assert report.uncertainty > 0.0


def test_coherence_engine_detects_duplicate_component_readiness_disagreement():
    report = CoherenceEngine().evaluate(
        (
            {"component": "Provider Fabric", "ready": True},
            {"component": "Provider Fabric", "ready": False},
        )
    )

    assert report.coherent is False
    assert report.human_review_required is True
    assert any(conflict.claim == "ready:Provider Fabric" for conflict in report.conflicts)
