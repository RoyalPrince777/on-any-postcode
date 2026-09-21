"""Release gate for the exact approved OAP artwork, not mock images."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTER = ROOT / "static/oap/enter_my_world_wallpaper.png"
ROOM = ROOT / "static/oap/smi_global_intelligence_command_centre.png"
LIVE_CHAT = ROOT / "static/oap/smi_live_chat_dashboard.jpg"


def test_exact_founder_and_dashboard_png_assets_are_in_repo():
    for path in (ENTER, ROOM):
        assert path.is_file(), f"Approved original artwork missing: {path.relative_to(ROOT)}"
        assert path.read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a")), f"Not PNG: {path}"
        assert path.stat().st_size > 100_000, f"Placeholder artwork blocked: {path}"
    assert hashlib.sha256(ENTER.read_bytes()).hexdigest() == "114852c665388f8b3cba5c3a5f667631e4a69ac88de2af2b30a3c5f6fbaec01b"
    assert hashlib.sha256(ROOM.read_bytes()).hexdigest() == "9417a1293108350ccb6c3751377c9530d287a628c54f0659272c7c990cda4df3"
    assert LIVE_CHAT.is_file(), "Approved SMI Live Chat artwork missing"
    assert LIVE_CHAT.read_bytes().startswith(bytes.fromhex("ffd8ff")), "Not JPEG"
    assert LIVE_CHAT.stat().st_size > 100_000, "Placeholder artwork blocked"
    assert hashlib.sha256(LIVE_CHAT.read_bytes()).hexdigest() == "f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b"


def test_enter_world_uses_unchanged_secure_form_over_static_wallpaper():
    page = (ROOT / "templates/auth.html").read_text(encoding="utf-8")
    assert "oap/enter_my_world_wallpaper.png" in page
    assert "if founder_only" in page
    assert 'action="{{ url_for(\'auth_sign_in\') }}"' in page
    assert 'name="csrf_token"' in page
    assert 'name="password" type="password"' in page
    assert "animation:none!important" in page
    assert "transition:none!important" in page


def test_dashboard_shows_approved_image_only_when_loaded():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    controller = (ROOT / "mission_control/static/smi_command_centre.js").read_text(encoding="utf-8")
    css = (ROOT / "mission_control/static/smi_command_centre.css").read_text(encoding="utf-8")
    assert "oap/smi_live_chat_dashboard.jpg" in wrapper
    assert "wallpaper.onload" in controller and "wallpaper.onerror" in controller
    assert 'panel.classList.add("smi-room-art-loaded")' in controller
    assert "smi-room-art-loaded" in css
    assert 'setOpen(true);' in controller
    assert 'stage.append(character);' in controller
    assert "data-proven" in css


def test_live_chat_uses_full_screen_art_and_real_bottom_controls():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text(encoding="utf-8")
    css = (ROOT / "mission_control/static/smi_live_chat_dashboard.css").read_text(encoding="utf-8")
    assert "smi_live_chat_dashboard.css" in wrapper
    assert "smi_live_chat_dashboard.jpg" in css
    assert "background-position:50% center" in css
    for control in ("plus-button", "mic-button", "thinking-level", "send"):
        assert f'#{control}' in css
        assert f'id="{control}"' in base
    assert "AUTO 3/7/21" in base
    assert "send-label" in base


def test_live_chat_excludes_visible_status_and_uses_governed_presence_state():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    room = (ROOT / "mission_control/static/smi_command_centre.js").read_text(encoding="utf-8")
    presence = (ROOT / "mission_control/static/smi_live_chat_presence.js").read_text(encoding="utf-8")
    css = (ROOT / "mission_control/static/smi_live_chat_dashboard.css").read_text(encoding="utf-8")
    assert "singleLiveChatSurface:true" in wrapper
    assert "visibleLiveStatus:false" in wrapper
    assert "backgroundListening:false" in wrapper
    assert "!cfg.singleLiveChatSurface" in room
    assert "oap-smi-character-state" in presence
    for state in ("listening", "thinking", "speaking", "paused", "stopped"):
        assert f'data-smi-presence="{state}"' in css


def test_live_chat_keeps_character_clear_and_all_primary_mobile_controls_visible():
    css = (ROOT / "mission_control/static/smi_live_chat_dashboard.css").read_text(encoding="utf-8")
    assert ".thinking{position:fixed!important;z-index:40;top:70px;left:12px" in css
    assert 'thinking[data-complete="true"] .thinking-log{display:none!important}' in css
    assert ".smi-character{display:contents!important}" in css
    assert "#live-character-toggle{position:fixed!important" in css
    assert "#plus-button,#mic-button{display:grid!important" in css
    assert "#thinking-level{display:block!important" in css
    mobile = css.split("@media(max-width:760px){", 1)[1]
    assert "#mic-button,#thinking-level,.send-label{display:none!important}" not in mobile
