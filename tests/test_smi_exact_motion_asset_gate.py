"""Exact-character animation must be signed-off, first-party and fail closed."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "mission_control/static/smi_command_centre.js").read_text()
CSS = (ROOT / "mission_control/static/smi_command_centre.css").read_text()
HTML = (ROOT / "mission_control/templates/ollama_chat.html").read_text()


def test_rigged_media_never_inferred_from_flattened_png():
    assert 'cfg.approvedMotionClips||{}' in JS
    assert 'panel.classList.contains("smi-room-art-loaded")' in JS
    assert 'motionBlobUrl=URL.createObjectURL' in JS
    assert 'motion.classList.add("smi-approved-motion-playing")' in JS
    assert "smi_motion" not in HTML  # no unapproved video silently enabled
    assert "approvedWallpaperUrl" in HTML


def test_media_must_be_same_origin_and_match_founder_checksum():
    assert '/^[a-f0-9]{64}$/i.test(clip.sha256)' in JS
    assert 'url.origin!==window.location.origin' in JS
    assert 'url.pathname.startsWith("/static/oap/smi_motion/")' in JS
    assert 'crypto.subtle.digest("SHA-256",bytes)' in JS
    assert 'digest.toLowerCase()!==clip.sha256.toLowerCase()' in JS
    assert "15000000" in JS
    assert 'credentials:"same-origin"' in JS


def test_stop_and_reduced_motion_revert_to_original_still():
    assert "motion.pause()" in JS
    assert 'motion.classList.remove("smi-approved-motion-playing")' in JS
    assert "URL.revokeObjectURL(motionBlobUrl)" in JS
    assert 'if(detail.live&&active)setOpen(false)' in JS
    assert 'else if(active)applyApprovedMotion(detail.state)' in JS
    assert "prefers-reduced-motion: reduce" in JS
    assert "prefers-reduced-motion:reduce" in CSS
    assert 'display:none!important' in CSS
    assert '.smi-command-scene .smi-approved-motion-clip' in CSS


def test_original_image_and_existing_controls_not_replaced():
    assert 'wallpaper.src=cfg.approvedWallpaperUrl' in JS
    assert 'stage.append(character)' in JS
    assert 'marker.parentNode.insertBefore(character,marker)' in JS
    assert 'stage.append(presence)' in JS
    assert 'data-room-gate' in JS
