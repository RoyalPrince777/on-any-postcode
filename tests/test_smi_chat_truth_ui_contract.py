from pathlib import Path


def test_smi_chat_truth_ui_requires_real_completion_and_bounded_autofix():
    root = Path(__file__).resolve().parents[1]
    js = (root / "mission_control/static/smi_chat_final.js").read_text(encoding="utf-8")
    template = (root / "mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")

    assert "Truth gate green" not in js
    assert "Chat unproven · send a real message" in js
    assert "PROVEN THIS SESSION" in js
    assert "behaviour_receipt?.durable===true" in js
    assert "🟣 AUTO FIX" in js
    assert "Consequential execution: NOT PERFORMED" in js
    assert "AUTO FIX stopped at the truth boundary" in js
    assert "alignment-check" in js
    assert "aegis-check" in js
    assert "function-health" in js
    assert "green-gate" in js
    assert "hrm-receipt" in js
    assert "warRoomActionsUrl" in template
