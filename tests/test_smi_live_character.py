from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mission_control" / "templates" / "ollama_chat_base.html"
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
CONTROLLER = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"
STYLE = ROOT / "mission_control" / "static" / "smi_live_character.css"


def test_live_smi_character_is_one_embodied_surface():
    base = BASE.read_text(encoding="utf-8")
    assert base.count('id="smi-character"') == 1
    assert 'id="live-character-toggle"' in base
    assert "SMI · Live Character" in base
    assert "Brain · Heart · Lungs · Blood · Guardian · HRM · Matrix" in base


def test_live_smi_character_style_models_person_and_anatomy():
    style = STYLE.read_text(encoding="utf-8")
    for marker in (
        ".smi-person",
        ".smi-head",
        ".smi-brain-glow",
        ".smi-heart",
        ".smi-lung",
        ".smi-blood",
        ".smi-mouth",
        '[data-state="listening"]',
        '[data-state="thinking"]',
        '[data-state="speaking"]',
        '[data-state="stopped"]',
    ):
        assert marker in style


def test_live_smi_character_uses_real_voice_state_events():
    text = CONTROLLER.read_text(encoding="utf-8")
    for marker in (
        "oapCharacterState('listening')",
        "oapCharacterState('thinking')",
        "oapCharacterState('speaking')",
        "oapCharacterState('ready')",
        "oapCharacterState('stopped')",
        "utterance.onstart",
        "utterance.onend",
        "oapRecognition.onstart",
        "oapRecognition.onend",
    ):
        assert marker in text


def test_live_smi_voice_is_half_duplex_and_human_stoppable():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "oapLiveConversation=false" in text
    assert "oapSpeaking=false" in text
    assert "if(!oapLiveConversation||oapLocked||oapListening||oapSpeaking||!oapRecognition)return" in text
    assert "if(oapLiveConversation){if(oapInput.value.trim())setTimeout(oapSubmit,120)" in text
    assert "if(oapLiveConversation)setTimeout(oapStartListening,320)" in text
    assert "oapSetLive(false);oapCharacterState('stopped')" in text
    assert "halfDuplexLiveVoice:true" in text
    assert "liveCharacter:true" in text


def test_live_smi_character_css_is_loaded_once():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    assert wrapper.count("smi_live_character.css") == 1
