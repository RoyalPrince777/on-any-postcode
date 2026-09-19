"""The approved still scene has real SMI-state-linked ambient motion, never fake body animation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "mission_control/static/smi_command_centre.js").read_text()
CSS = (ROOT / "mission_control/static/smi_command_centre.css").read_text()


def test_motion_follows_single_canonical_character_state():
    assert 'window.addEventListener("oap-smi-character-state"' in JS
    assert 'setPresenceState(detail.state)' in JS
    assert '"listening","thinking","speaking","paused","stopped"' in JS
    assert 'stage.append(presence)' in JS
    assert 'if(detail.live&&active)setOpen(false)' not in JS
    assert 'setPresenceState(detail.state)' in JS


def test_approved_image_and_controls_are_preserved():
    assert 'wallpaper.src=cfg.approvedWallpaperUrl' in JS
    assert 'panel.classList.add("smi-room-art-loaded")' in JS
    assert 'stage.append(character)' not in JS
    assert 'getElementById("live-character-toggle")' in JS
    assert 'marker.parentNode.insertBefore(character,marker)' not in JS
    assert 'setOpen(false);' in JS
    assert 'data-room-gate' in JS
    assert 'approved still' in CSS.lower()


def test_motion_is_passive_and_fails_closed():
    assert '.smi-room-art-loaded .smi-scene-presence{display:block}' in CSS
    for state in ("listening", "thinking", "speaking"):
        assert f'data-presence-state="{state}"' in CSS
    assert 'data-presence-state="stopped"' not in CSS
    assert 'data-presence-state="paused"' not in CSS
    assert "prefers-reduced-motion:reduce" in CSS
    assert "animation:none!important" in CSS
    assert 'pointer-events:none' in CSS
