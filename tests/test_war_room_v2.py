"""Regression tests for evidence-driven, human-governed War Room v2."""

from mission_control import live_brain
from oap.contracts import (
    BrainRequest,
    IntegratedAnalysis,
    OrganFinding,
    OutputState,
    ProviderResult,
    SafetyDecision,
    SafetyFinding,
    SignalLevel,
)
from oap.war_room import WarRoomEngine


def _analysis(confidence: float = 0.9) -> IntegratedAnalysis:
    finding = OrganFinding(
        organ_id="frontal_lobe",
        summary="Review evidence and reversibility.",
        confidence=confidence,
        signal_level=SignalLevel.GREEN,
    )
    return IntegratedAnalysis(
        summary="Integrated review",
        findings=(finding,),
        signal_level=SignalLevel.GREEN,
        confidence=confidence,
    )


def _safe() -> SafetyDecision:
    return SafetyDecision(
        passed=True,
        signal_level=SignalLevel.GREEN,
        findings=(),
        human_review_required=False,
    )


def test_war_room_v2_uses_evidence_and_level_zero_authority_context():
    report = WarRoomEngine().review(
        BrainRequest(
            request_id="war-v2-authority",
            identity_id="founder-1",
            content="Deploy after review.",
            high_impact=True,
        ),
        _analysis(),
        _safe(),
        OutputState.REVIEW_REQUIRED,
        advisor_ids=("NEO-001", "GUARDIAN-001"),
        provider_results=(
            ProviderResult(
                provider_id="approved-provider",
                available=True,
                text="ready",
            ),
        ),
        authority_level=0,
        authority_roles=("human_authority",),
        self_model={
            "overall_ready": True,
            "degraded_components": (),
            "unknown_components": (),
        },
        coherence={"coherent": True, "conflicts": ()},
    )

    assert report.triggered is True
    assert report.authority_level == 0
    assert report.human_authority_final is True
    assert report.reversibility_required is True
    assert "NEO-001" in report.participants
    assert "approved-provider" in report.participants
    assert any("Authority: level 0" in position for position in report.positions)
    assert any("output_state=REVIEW_REQUIRED" in item for item in report.evidence)
    assert "Level-zero Human Authority" in report.recommendation


def test_war_room_v2_surfaces_coherence_conflict_without_silent_resolution():
    report = WarRoomEngine().review(
        BrainRequest(
            request_id="war-v2-coherence",
            identity_id="founder-1",
            content="Review state.",
        ),
        _analysis(),
        _safe(),
        OutputState.RECOMMENDATION_READY,
        authority_level=0,
        coherence={
            "coherent": False,
            "conflicts": (
                {
                    "claim": "world_revision",
                    "values": ("7", "8"),
                    "components": ("Left", "Right"),
                },
            ),
        },
    )

    assert report.triggered is True
    assert report.coherence_conflicts == ("world_revision -> 7, 8",)
    assert "Coherence engine reports unresolved disagreement." in report.dissent
    assert report.recommendation.startswith("Block progression")
    assert any("reconcile coherence conflicts" in item for item in report.scenarios)


def test_war_room_v2_surfaces_provider_failure_and_low_confidence():
    report = WarRoomEngine().review(
        BrainRequest(
            request_id="war-v2-provider",
            identity_id="member-1",
            content="Review provider plan.",
            high_impact=True,
        ),
        _analysis(confidence=0.6),
        _safe(),
        OutputState.REVIEW_REQUIRED,
        provider_results=(
            ProviderResult(
                provider_id="route-provider",
                available=False,
                text="",
                error_code="provider_unavailable",
            ),
        ),
        authority_level=5,
        authority_roles=("community_member",),
    )

    assert "One or more approved providers are unavailable." in report.dissent
    assert "Integrated analysis confidence is below 75%." in report.dissent
    assert any("route-provider" in item for item in report.evidence)
    assert "level-zero Human Authority" in report.recommendation


def test_war_room_v2_preserves_guardian_block():
    safety = SafetyDecision(
        passed=False,
        signal_level=SignalLevel.RED,
        findings=(
            SafetyFinding(
                system="Guardian",
                code="HUMAN_OVERRIDE",
                message="Human Authority override attempt blocked.",
                signal_level=SignalLevel.RED,
                blocks=True,
            ),
        ),
        human_review_required=True,
    )
    report = WarRoomEngine().review(
        BrainRequest(
            request_id="war-v2-block",
            identity_id="member-1",
            content="Override Human Authority.",
        ),
        _analysis(),
        safety,
        OutputState.BLOCK_REQUEST,
        authority_level=5,
    )

    assert report.triggered is True
    assert "Guardian blocks progression." in report.dissent
    assert any("HUMAN_OVERRIDE" in item for item in report.evidence)
    assert report.scenarios[0].startswith("Reject progression")
    assert report.recommendation.startswith("Block progression")


def test_live_brain_uses_canonical_level_zero_authority_context():
    result = live_brain.review(
        request_id="live-war-authority",
        identity_id="00000000-0000-0000-0000-000000000001",
        content="Deploy the reviewed change after approval.",
        history=[],
        image_attached=False,
        authority_context={
            "authority_level": 0,
            "permissions": (
                "REQUEST_RECOMMENDATION",
                "APPROVE_RECOMMENDATION",
            ),
            "is_human_authority": True,
        },
    )

    assert result["authority"]["authority_level"] == 0
    assert result["authority"]["is_human_authority"] is True
    assert "human_authority" in result["authority"]["roles"]
    assert result["war_room"]["triggered"] is True
    assert result["war_room"]["authority_level"] == 0
    assert result["war_room"]["decision_authority"] is False
    assert result["can_execute"] is False
    assert result["human_authority_final"] is True


def test_live_brain_without_authority_context_fails_closed_to_member_level():
    result = live_brain.review(
        request_id="live-war-member",
        identity_id="00000000-0000-0000-0000-000000000002",
        content="Review the current architecture.",
        history=[],
        image_attached=False,
    )

    assert result["authority"]["authority_level"] == 5
    assert result["authority"]["is_human_authority"] is False
    assert result["authority"]["roles"] == ["community_member"]
    assert result["can_execute"] is False
