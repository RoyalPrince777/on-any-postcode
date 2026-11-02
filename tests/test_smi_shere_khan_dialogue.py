"""Focused Shere Khan conversational routing and governance regression."""
from mission_control.smi_shere_khan_dialogue import (
    SHERE_KHAN_INSTRUCTION, SHERE_KHAN_CAPABILITIES,
    capability_instruction, shere_khan_requested,
)


def test_explicit_invocation_and_existing_persona_selection():
    assert shere_khan_requested("Shere Khan, speak to me")
    assert shere_khan_requested("Hey Shere Khan")
    assert shere_khan_requested("hello", {"conversation_persona": "shere_khan"})
    assert not shere_khan_requested("What is Shere Khan's test role?")
    assert not shere_khan_requested("Shere Khan", {"conversation_persona": "other"})


def test_loyalty_never_displaces_truth_guardian_or_founder_final():
    for phrase in ("LOYALTY OVER EVERYTHING", "Guardian", "Founder Final",
                   "challenge respectfully", "no fabricated proof",
                   "repetitive", "microphone", "automation"):
        assert phrase in SHERE_KHAN_INSTRUCTION


def test_seven_bounded_capabilities_are_unique_and_advisory_only():
    names = [name for name, _ in SHERE_KHAN_CAPABILITIES]
    assert len(names) == len(set(names)) == 7
    instructions = capability_instruction()
    for name in names:
        assert name in instructions
    for boundary in ("no autonomous", "Guardian", "Founder Final",
                     "never invent completion percentages", "execution evidence"):
        assert boundary in instructions
