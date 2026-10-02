from pathlib import Path

# ruff: noqa: I001

from mission_control import (
    ai_behaviour_protocol,
    live_brain,
    live_signals,
    smi_brain_protocol,
)


EXPECTED_MAJOR_LINKS = (
    "Mission",
    "Continue",
    "Risk / Guardian",
    "War Room / Judgement",
    "Founder Final",
    "Recovery / Rollback",
    "Outcome / Learning",
)

EXPECTED_CORE_REVIEW_SIGNALS = (
    "Truth",
    "Evidence",
    "Risk",
    "Safety",
    "Security",
    "Privacy",
    "Identity",
    "Permission",
    "Intent",
    "Dependency",
    "Architecture",
    "Alignment",
    "Resilience",
    "Performance",
    "Reversibility",
    "Impact",
    "Readiness",
    "Coherence",
    "Recovery",
    "Outcome",
    "Human Authority",
)


def test_smi_has_exactly_seven_major_links():
    assert smi_brain_protocol.MAJOR_LINKS_7 == EXPECTED_MAJOR_LINKS
    assert len(smi_brain_protocol.MAJOR_LINKS_7) == 7


def test_core_review_and_thinking_signals_are_distinct_21_item_sets():
    assert smi_brain_protocol.CORE_REVIEW_SIGNALS_21 == EXPECTED_CORE_REVIEW_SIGNALS
    assert len(smi_brain_protocol.CORE_REVIEW_SIGNALS_21) == 21
    assert len(smi_brain_protocol.THINKING_SIGNALS_21) == 21
    assert smi_brain_protocol.CORE_REVIEW_SIGNALS_21 != smi_brain_protocol.THINKING_SIGNALS_21
    assert smi_brain_protocol.SIGNALS_21 is smi_brain_protocol.THINKING_SIGNALS_21


def test_behaviour_protocol_uses_canonical_signal_contracts():
    status = ai_behaviour_protocol.status()

    assert status["seven_major_links"] == smi_brain_protocol.MAJOR_LINKS_7
    assert status["twenty_one_core_review_signals"] == (
        smi_brain_protocol.CORE_REVIEW_SIGNALS_21
    )
    assert status["twenty_one_thinking_signals"] == (
        smi_brain_protocol.THINKING_SIGNALS_21
    )
    assert status["twenty_one_signals"] == smi_brain_protocol.THINKING_SIGNALS_21


def test_live_signal_vocabulary_remains_separate():
    assert len(live_signals.LIVE_SIGNALS) == 21
    live_labels = tuple(str(item["label"]) for item in live_signals.LIVE_SIGNALS)
    assert live_labels != smi_brain_protocol.CORE_REVIEW_SIGNALS_21
    assert live_labels != smi_brain_protocol.THINKING_SIGNALS_21


def test_live_core_review_record_has_all_21_signals_without_fake_green():
    record = live_brain._core_review_signal_record(
        action_risk={"route": "DIRECT_ANSWER"},
        safety_passed=True,
        high_impact=False,
        identity_authority_level=0,
        is_human_authority=True,
        permission_verified=True,
        output_state="RECOMMENDATION_READY",
        coherence={"coherent": True},
        self_model={"overall_ready": True},
        war_room={"reversibility_required": True},
    )

    assert tuple(item["signal"] for item in record) == EXPECTED_CORE_REVIEW_SIGNALS
    assert len(record) == 21
    assert all(item["green"] is False for item in record)
    assert {item["state"] for item in record} <= {"reviewed", "required", "gated"}

    by_signal = {item["signal"]: item for item in record}
    assert by_signal["Risk"]["owner"] == "action_risk_router"
    assert by_signal["Safety"]["passed"] is True
    assert by_signal["Permission"]["state"] == "reviewed"
    assert by_signal["Evidence"]["state"] == "required"
    assert by_signal["Security"]["state"] == "required"
    assert by_signal["Privacy"]["state"] == "required"
    assert by_signal["Recovery"]["state"] == "required"
    assert by_signal["Human Authority"]["is_human_authority"] is True


def test_permission_signal_fails_closed_when_permission_not_verified():
    record = live_brain._core_review_signal_record(
        action_risk={"route": "DIRECT_ANSWER"},
        safety_passed=True,
        high_impact=False,
        identity_authority_level=5,
        is_human_authority=False,
        permission_verified=False,
        output_state="REVIEW_REQUIRED",
        coherence={"coherent": False},
        self_model={"overall_ready": False},
        war_room={"reversibility_required": True},
    )
    permission = next(item for item in record if item["signal"] == "Permission")
    assert permission["state"] == "gated"
    assert permission["green"] is False


def test_live_brain_exposes_signal_record_without_score_or_percentage():
    source = (Path(__file__).resolve().parents[1] / "mission_control" / "live_brain.py").read_text()
    assert '"core_review_signals_21"' in source
    assert '"core_review_signal_count"' in source
    assert '"core_review_signal_green_count": 0' in source
    assert '"core_review_signal_scoring": "disabled_without_request_specific_evidence"' in source
    signal_block = source[source.index("def _core_review_signal_record"):source.index("def review(")]
    assert "percentage" not in signal_block
    assert "score" not in signal_block
