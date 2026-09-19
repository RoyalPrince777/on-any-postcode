"""Release gate for the exact approved OAP artwork, not mock images."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTER = ROOT / "static/oap/smi_enter_my_world.png"
ROOM = ROOT / "static/oap/smi_global_intelligence_command_centre.png"


def test_exact_founder_and_dashboard_png_assets_are_in_repo():
    for path in (ENTER, ROOM):
        assert path.is_file(), f"Approved original artwork missing: {path.relative_to(ROOT)}"
        assert path.read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a")), f"Not PNG: {path}"
        assert path.stat().st_size > 100_000, f"Placeholder artwork blocked: {path}"


def test_enter_world_uses_unchanged_secure_form_over_static_wallpaper():
    page = (ROOT / "templates/auth.html").read_text(encoding="utf-8")
    assert "oap/smi_enter_my_world.png" in page
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
    assert "oap/smi_global_intelligence_command_centre.png" in wrapper
    assert "wallpaper.onload" in controller and "wallpaper.onerror" in controller
    assert 'panel.classList.add("smi-room-art-loaded")' in controller
    assert "smi-room-art-loaded" in css
    assert 'setOpen(true);' in controller
    assert 'stage.append(character);' in controller
    assert "data-proven" in css
