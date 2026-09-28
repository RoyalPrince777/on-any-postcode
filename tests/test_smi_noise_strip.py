from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_noise_strip_assets_are_loaded_last():
    template = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    assert "smi_noise_strip.css" in template
    assert "smi_noise_strip.js" in template
    assert template.index("smi_noise_strip.css") > template.index("smi_live_chat_dashboard.css")
    assert template.index("smi_noise_strip.js") > template.index("smi_command_centre.js")


def test_smi_noise_strip_preserves_core_controls_and_functions():
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text()
    js = (ROOT / "mission_control" / "static" / "smi_noise_strip.js").read_text()
    for control_id in ("plus-button", "mic-button", "pause-button", "stop-button", "send"):
        assert f'id="{control_id}"' in base
        assert control_id in js
    assert "addEventListener('keydown'" not in js
    assert "canonical controller" in js
    assert "upgradeOnly:true" in js


def test_smi_noise_strip_is_visual_not_route_removal():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text()
    template = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    assert "display:none" in css
    assert "studioGenerateUrl" in template
    assert "studioBuildPreviewCreateUrl" in template
    assert "warRoomUrl" in template
    assert "greenGateUrl" in template
