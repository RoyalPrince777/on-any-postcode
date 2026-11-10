from __future__ import annotations

import re
from pathlib import Path

from flask import Flask

from mission_control import music_public_views, product_core_views

MUSIC_TEMPLATE = Path("mission_control/templates/oap_music.html")
MARKET_TEMPLATE = Path("mission_control/templates/market.html")


def _template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _app() -> Flask:
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.secret_key = "surface-integrity"
    app.register_blueprint(music_public_views.bp)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    return app


def _assert_route(app: Flask, path: str, method: str = "GET") -> None:
    adapter = app.url_map.bind("localhost")
    endpoint, _values = adapter.match(path, method=method)
    assert endpoint


def test_music_fragment_buttons_and_bottom_links_have_real_targets():
    template = _template(MUSIC_TEMPLATE)
    ids = set(re.findall(r'id="([^"]+)"', template))

    for target in re.findall(r'data-target="([^"]+)"', template):
        assert target in ids

    for target in re.findall(r'href="#([^"]+)"', template):
        assert target in ids

    assert 'href="#"' not in template
    assert "javascript:void" not in template


def test_music_visible_forms_are_wired_to_submit_handlers():
    template = _template(MUSIC_TEMPLATE)
    for form_id in (
        "release-form",
        "upload-form",
        "review-form",
        "station-form",
        "rotation-form",
        "show-form",
        "schedule-form",
        "stop-form",
    ):
        assert f'id="{form_id}"' in template
        variable_match = re.search(
            rf"const\s+(\w+)\s*=\s*document\.getElementById\('{re.escape(form_id)}'\);",
            template,
        )
        assert variable_match is not None
        assert f"{variable_match.group(1)}.addEventListener('submit'" in template


def test_music_ui_api_paths_are_registered_not_404_routes():
    app = _app()
    release = "11111111-1111-1111-1111-111111111111"
    station = "22222222-2222-2222-2222-222222222222"
    asset = "33333333-3333-3333-3333-333333333333"

    checks = (
        ("/music", "GET"),
        ("/music/api/catalogue", "GET"),
        ("/music/manifest.webmanifest", "GET"),
        ("/mission/organs/tune", "GET"),
        ("/mission/organs/tune/assets", "GET"),
        (f"/mission/organs/tune/assets/{asset}/audio", "GET"),
        ("/mission/organs/tune/releases", "POST"),
        (f"/mission/organs/tune/releases/{release}/upload", "POST"),
        (f"/mission/organs/tune/releases/{release}/review", "POST"),
        ("/mission/organs/radio", "GET"),
        ("/mission/organs/radio/stations", "POST"),
        (f"/mission/organs/radio/stations/{station}/shows", "POST"),
        (f"/mission/organs/radio/stations/{station}/schedule", "POST"),
        (f"/mission/organs/radio/stations/{station}/rotation", "POST"),
        (f"/mission/organs/radio/stations/{station}/stop", "POST"),
    )
    for path, method in checks:
        _assert_route(app, path, method)


def test_market_buttons_are_wired_and_fragments_are_real():
    template = _template(MARKET_TEMPLATE)
    ids = set(re.findall(r'id="([^"]+)"', template))

    assert "sell" in ids
    assert "basket" in ids
    assert 'href="#"' not in template
    assert "javascript:void" not in template

    for button_id, handler in (
        ("market-checkout", "market-checkout"),
        ("market-clear-basket", "market-clear-basket"),
        ("market-refresh-orders", "market-refresh-orders"),
        ("market-stop-transaction", "stopButton"),
    ):
        assert f'id="{button_id}"' in template
        if handler == "stopButton":
            assert "stopButton?.addEventListener('click'" in template
        else:
            assert f"document.getElementById('{handler}')?.addEventListener('click'" in template

    assert "document.querySelectorAll('.market-add').forEach" in template
    assert "row.querySelector('button').addEventListener('click'" in template
    assert "row.addEventListener('click', () => showOrder" in template


def test_market_ui_api_paths_are_registered_not_404_routes():
    app = _app()
    order = "11111111-1111-1111-1111-111111111111"
    transaction = "22222222-2222-2222-2222-222222222222"

    checks = (
        ("/mission/organs/market/orders", "GET"),
        ("/mission/organs/market/orders", "POST"),
        (f"/mission/organs/market/orders/{order}", "GET"),
        (f"/mission/organs/market/transactions/{transaction}", "GET"),
        (f"/mission/organs/market/transactions/{transaction}/stop", "POST"),
    )
    for path, method in checks:
        _assert_route(app, path, method)


def test_music_market_customer_surfaces_strip_internal_noise():
    combined = (_template(MUSIC_TEMPLATE) + "\n" + _template(MARKET_TEMPLATE)).casefold()
    for phrase in (
        "server truth",
        "transaction truth",
        "canonical commerce",
        "evidence-gated",
        "governed order",
        "provider-required",
        "checking private player",
        "checking install support",
    ):
        assert phrase not in combined
