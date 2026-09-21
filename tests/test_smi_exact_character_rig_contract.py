"""Exact-art rig stays disabled and invisible until independently proven."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exact_art_and_passive_rig_are_the_only_character_foundation():
    art = ROOT / "static/oap/smi_live_chat_dashboard.jpg"
    rig = (ROOT / "mission_control/static/smi_exact_character_rig.js").read_text()
    chat = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert art.is_file()
    assert 'path:"/static/oap/smi_live_chat_dashboard.jpg"' in rig
    assert "f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b" in rig
    assert 'enabled:false' in rig and 'active:false' in rig
    assert "function frame(){return null;}" in rig
    assert "smi_exact_character_rig.js" in chat
    assert chat.index("smi_live_character_state.js") < chat.index(
        "smi_exact_character_rig.js"
    )


def test_character_foundation_creates_no_visible_status_or_sensing():
    rig = (ROOT / "mission_control/static/smi_exact_character_rig.js").read_text()
    assert "oap-smi-character-state" in rig
    assert 'proofState:"not_proven"' in rig
    for forbidden in (
        "getUserMedia(", "getDisplayMedia(", "fetch(",
        "localStorage", "sessionStorage", "new Audio(",
        "appendChild(", "innerHTML", "requestAnimationFrame(",
    ):
        assert forbidden not in rig
    chat = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "visibleLiveStatus:false" in chat
