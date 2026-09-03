from pathlib import Path


def test_public_link_loads_only_first_party_motion_assets(client):
    page = client.get("/linkup").get_data(as_text=True)

    assert "/static/oap_motion.css" in page
    assert "/static/linkup_realtime.js" in page
    assert "/static/oap_motion.svg#link-up" in page
    assert "OAP Motion preview" not in page
    assert "https://" not in page


def test_link_device_permissions_are_allowed_only_by_route_policy(client):
    link = client.get("/linkup")
    home = client.get("/")

    assert link.headers["Permissions-Policy"] == (
        "camera=(self), microphone=(self), geolocation=(self), payment=()"
    )
    assert home.headers["Permissions-Policy"] == (
        "camera=(self), microphone=(self), geolocation=(), payment=()"
    )


def test_link_composer_keeps_runtime_controls_fail_closed_in_template():
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert 'data-oap-link-composer' in template
    assert 'data-oap-plus' in template
    assert 'placeholder="Type a Link…"' in template
    assert '>Send<' in template
    assert '>Send Link<' not in template
    assert 'data-oap-voice-control' in template
    assert 'data-oap-voice-stop' in template
    assert 'data-oap-voice-status' in template
    assert 'data-runtime-locked' in template
    assert 'disabled data-runtime-locked' in template
    assert 'Share <small>locked</small>' not in template
    assert ' Share</button>' in template
    assert '> My Spot<' not in template  # icon precedes the compact label
    assert ' My Spot</button>' in template
    assert 'Live Spot' in template
    assert 'Circle' not in template


def test_oap_motion_css_has_static_reduced_motion_fallback():
    css = Path("static/oap_motion.css").read_text(encoding="utf-8")

    assert "@media(prefers-reduced-motion:reduce)" in css
    assert "animation:none!important" in css


def test_oap_motion_sprite_is_local_vector_art():
    sprite = Path("static/oap_motion.svg").read_text(encoding="utf-8")

    for symbol in (
        "link-up",
        "voice",
        "call",
        "face-up",
        "around-now",
        "live-spot",
        "seen",
        "motion",
        "share",
        "circle",
    ):
        assert f'id="{symbol}"' in sprite
    assert "http://www.w3.org/2000/svg" in sprite
    assert "https://" not in sprite
