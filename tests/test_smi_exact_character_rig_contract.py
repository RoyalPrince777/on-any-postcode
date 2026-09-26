"""Exact-art rig is a passive proof aggregator over the one source-pixel renderer."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exact_art_rig_binds_one_canonical_renderer_without_duplicate_pixels():
    art = ROOT / "static/oap/smi_live_chat_dashboard.jpg"
    rig = (ROOT / "mission_control/static/smi_exact_character_rig.js").read_text()
    chat = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert art.is_file()
    assert 'path:"/static/oap/smi_live_chat_dashboard.jpg"' in rig
    assert "f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b" in rig
    assert 'rendererOwner:"smi_source_pixel_motion"' in rig
    assert "bindMotionSession" in rig
    assert "fullRigProven" in rig
    assert "accurateSoftwareLipSyncProven" in rig
    assert "accurateHumanLipSyncProven:false" in rig
    assert "smi_exact_character_rig.js" in chat
    assert "OAP_SMI_RIG_FOUNDATION.bindMotionSession(session)" in chat
    assert chat.index("smi_live_character_state.js") < chat.index("smi_exact_character_rig.js")


def test_rig_proof_aggregator_has_no_second_renderer_or_sensing():
    rig = (ROOT / "mission_control/static/smi_exact_character_rig.js").read_text()
    assert "oap-smi-character-state" in rig
    for forbidden in (
        "getUserMedia(", "getDisplayMedia(", "fetch(",
        "localStorage", "sessionStorage", "new Audio(",
        "appendChild(", "innerHTML", "requestAnimationFrame(",
        "createElement(", "canvas",
    ):
        assert forbidden not in rig
    chat = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "visibleLiveStatus:false" in chat
