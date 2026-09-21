"""Keep the Command Centre additive, with canonical Chat controls and no Live Status."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mission_control/static/smi_command_centre.js"
CHAT = ROOT / "mission_control/templates/ollama_chat_base.html"
CONFIG = ROOT / "mission_control/templates/ollama_chat.html"


def test_live_status_is_excluded_from_command_centre_when_chat_requests_it():
    source = SOURCE.read_text(encoding="utf-8")
    template = CONFIG.read_text(encoding="utf-8")
    assert "visibleLiveStatus:false" in template
    assert "if(cfg.visibleLiveStatus===false){" in source
    assert "statusActions.remove();" in source
    assert "dashboard.remove();" in source
    assert "if(cfg.visibleLiveStatus===false)return;" in source
    # Proof remains available privately; do not disable its checks globally.
    assert "data.checks[key]===true" in source


def test_shortcuts_delegate_to_existing_chat_controls_only():
    source = SOURCE.read_text(encoding="utf-8")
    base = CHAT.read_text(encoding="utf-8")
    for control_id in (
        "plus-button", "image-button", "file-button", "refresh-history",
        "speaker-button", "pause-button", "stop-button",
    ):
        assert f'"{control_id}"' in source
        assert f'id="{control_id}"' in base
    assert "canonical.click();" in source
    assert "setOpen(false);" in source
    assert "This SMI Chat control is unavailable." in source
    assert "↻ Refresh Saved Work" in source
    assert "new SpeechRecognition" not in source
    assert "new AbortController()" not in source.split("const chatShortcuts=[", 1)[1].split("panel.querySelector", 1)[0]
