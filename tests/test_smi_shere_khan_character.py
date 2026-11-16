"""Optional Shere Khan view must reuse SMI control and voice ownership."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mission_control/templates/ollama_chat.html"
SCRIPT = ROOT / "mission_control/static/smi_shere_khan_character.js"
STYLE = ROOT / "mission_control/static/smi_shere_khan_character.css"


def test_shere_khan_view_is_opt_in_and_reuses_character_state():
    page = WRAPPER.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    assert "smi_shere_khan_character.js" in page
    assert "smi_shere_khan_character.css" in page
    assert "oap-smi-character-state" in script
    assert 'panel.hidden = true' in script
    assert 'aria-expanded' in script
    assert "oap-smi-character-state" in script
    assert "AudioContext" not in script
    assert "getUserMedia" not in script
    assert "fetch(" not in script
    assert "localStorage" not in script


def test_pause_stop_and_reduced_motion_disable_animation():
    css = STYLE.read_text(encoding="utf-8")
    for expected in ("prefers-reduced-motion", 'data-state="paused"',
                     'data-state="stopped"', "animation:none"):
        assert expected in css
