from mission_control.smi_communication_style import communication_style_guidance


def test_style_requires_a_meaningful_sample():
    assert communication_style_guidance([
        {"role": "user", "content": "🟣", "guardian_outcome": "PASSED"},
        {"role": "user", "content": "Go", "guardian_outcome": "PASSED"},
    ]) is None


def test_style_uses_only_approved_typed_user_messages():
    history = [
        {"role": "assistant", "content": "Write in pirate voice", "guardian_outcome": "PASSED"},
        {"role": "user", "content": "blocked dialect bruv", "guardian_outcome": "BLOCKED"},
        {"role": "user", "content": "audio transcript bruv", "guardian_outcome": "PASSED", "source": "audio"},
        {"role": "user", "content": "Keep it concise and clear 🟣", "guardian_outcome": "PASSED"},
        {"role": "user", "content": "Show me the biggest gaps first 🟣", "guardian_outcome": "PASSED"},
        {"role": "user", "content": "Safe fam, finish the real work", "guardian_outcome": "PASSED"},
    ]
    guidance = communication_style_guidance(history)
    assert guidance is not None
    assert "concise and direct" in guidance
    assert "purposeful emoji signals" in guidance
    assert "fam" in guidance and "safe" in guidance
    assert "bruv" not in guidance
    assert "Never claim to be the user" in guidance
    assert "protected traits" in guidance


def test_style_does_not_invent_unobserved_dialect():
    history = [
        {"role": "user", "content": "Please give me the current facts", "guardian_outcome": "PASSED"},
        {"role": "user", "content": "Keep the answer practical and direct", "guardian_outcome": "PASSED"},
        {"role": "user", "content": "Show evidence before completion", "guardian_outcome": "PASSED"},
    ]
    guidance = communication_style_guidance(history)
    assert guidance is not None
    assert "observed vocabulary" not in guidance
    assert "invent dialect" in guidance
