# ruff: noqa: I001

from mission_control import (
    ai_behaviour_protocol,
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
