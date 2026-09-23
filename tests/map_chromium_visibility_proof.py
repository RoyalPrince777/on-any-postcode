"""Actual Chromium rendering proof for the isolated OAP road-map UI.

All tile responses are TEST FIXTURES, not claims about production map-source health.
Requires: pip install playwright && python -m playwright install chromium
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "mission_control/templates/local_map.html").read_text(encoding="utf-8")
CSS = (ROOT / "mission_control/static/oap_map_navigation.css").read_text(encoding="utf-8")
NAV = (ROOT / "mission_control/static/oap_map_navigation.js").read_text(encoding="utf-8")
HTML = re.sub(r'{% include [^%]+%}', '', HTML)
HTML = re.sub(r'{{[^}]+}}', '', HTML)
HTML = re.sub(r'<link rel="stylesheet"[^>]*>', '', HTML)
HTML = re.sub(r'<script src="[^"]+"></script>', '', HTML)

def fixture(route):
    path = urlparse(route.request.url).path
    if "/road-geometry/" in path:
        # Tile-local linework: mock the first-party endpoint contract, not an external provider.
        parts = path.rsplit("/", 3)
        z, x, y = [int(v) for v in parts[-3:]]
        route.fulfill(status=200, content_type="application/json", body=json.dumps({
            "tile": {"z": z, "x": x, "y": y},
            "lines": [{"points": [[0.1, 0.5], [0.9, 0.5]],
                       "class": "primary", "name": "Fixture Road"}],
            "first_party": True, "source": "test fixture",
        }))
    elif "/route?" in route.request.url:
        route.fulfill(status=503, content_type="application/json",
                      body='{"error":{"code":"fixture_route_unavailable"}}')
    elif "/places?" in route.request.url:
        route.fulfill(status=200, content_type="application/json", body='{"results":[]}')
    else:
        route.fulfill(status=404, body="test-only endpoint")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for label, viewport, mobile in [
        ("desktop", {"width": 1280, "height": 800}, False),
        ("android_mobile_emulation", {"width": 393, "height": 852}, True),
    ]:
        context = browser.new_context(viewport=viewport, is_mobile=mobile,
                                      has_touch=mobile, device_scale_factor=2 if mobile else 1)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("https://oap-map.test/**", fixture)
        page.goto("https://oap-map.test/on-any-place")
        page.set_content(HTML, wait_until="load")
        page.add_style_tag(content=CSS)
        page.add_script_tag(content=NAV)
        page.wait_for_function(
            "() => document.querySelectorAll('#road-layer polyline').length > 0",
            timeout=15000,
        )
        count = page.locator("#road-layer polyline").count()
        assert count > 0, (label, "No actual SVG road polylines")
        assert page.locator("#roads-svg").is_visible(), label
        assert not errors, (label, errors)
        page.locator("#map-from").fill("Mitcham")
        page.locator("#map-to").fill("London Bridge")
        page.locator("#map-form button.go").click()
        page.wait_for_function(
            "() => document.querySelector('#route-state').textContent.includes('Route unavailable')"
            " || document.querySelector('#route-state').textContent.includes('temporarily unavailable')",
            timeout=10000,
        )
        assert page.locator("#road-layer polyline").count() > 0, label
        assert not errors, (label, errors)
        print(f"OAP_MAP_CHROMIUM_FIXTURE_PASS {label} roads={count} route_failure_retained=true")
        context.close()
    browser.close()
