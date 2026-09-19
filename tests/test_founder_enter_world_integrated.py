"""Founder entrance: the approved art belongs to sign-in, not a noisy dashboard."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "templates" / "auth.html"


def test_founder_wallpaper_and_form_share_one_surface():
    page = AUTH.read_text(encoding="utf-8")
    assert "body.oap-founder-wallpaper .grid{" in page
    assert "oap/enter_my_world_wallpaper.png" in page
    assert "background-position:35% top" in page
    assert 'name="password" type="password"' in page
    assert 'name="csrf_token"' in page
    assert 'action="{{ url_for(\'auth_sign_in\') }}"' in page
    assert "Founder sign-in" in page


def test_founder_entrance_has_only_one_card_and_no_public_copy():
    # Render with Jinja rather than trusting text that may exist on the public branch.
    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    env.globals["url_for"] = lambda endpoint, **kwargs: (
        "/static/" + kwargs["filename"] if endpoint == "static"
        else "/" + endpoint
    )
    view = env.get_template("auth.html")
    founder = view.render(
        founder_only=True, auth_configured=True, auth_error=None,
        auth_notice=None, oap_csrf_token="test-token", next_path="/my-world",
    )
    public = view.render(
        founder_only=False, auth_configured=True, auth_error=None,
        auth_notice=None, oap_csrf_token="test-token", next_path="/my-world",
    )
    assert founder.count('<section class="card') == 1
    assert "Founder-only boundary" not in founder
    assert "Public OAP World is open" not in founder
    assert "name=\"email\"" not in founder
    assert "Founder sign-in" in founder
    assert 'name="csrf_token"' in founder
    assert 'name="password" type="password"' in founder
    assert 'type="submit"' in founder
    assert "Return to public OAP World" in public
    assert "Public access stays free" in public
    assert 'name="email"' in public
