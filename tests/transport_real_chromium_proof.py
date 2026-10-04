"""Real Chromium proof for OAP Global Transport software surfaces.

This proves the public transport front door, Rider, Driver and My Transport
dashboard navigation in an actual Chromium browser against the real Flask app.
It does not claim external operator feeds, real dispatch, ticket issuance,
money movement, or physical vehicle control.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module

BASE = "http://127.0.0.1:8774"

DASHBOARDS = {
    "/transport/ride/rider": (
        "Request Journey", "Current Journey", "My Journeys", "Find Match",
        "My Matches", "OAP Pay", "Guardian",
    ),
    "/transport/ride/driver": (
        "Go Active / Quiet", "Current Journey", "Incoming Journey",
        "Accept Journey", "My Drive", "Earnings", "Journey History", "Guardian",
    ),
    "/transport/my": (
        "Rider", "Driver", "Current Journey", "My Journeys",
        "My Drive", "Payments", "Guardian",
    ),
}


def assert_layout(page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= window.innerWidth + 2"
    ), "Transport surface has horizontal overflow"


def assert_navigation_target(context, href: str):
    target = urlsplit(href)
    path = target.path or "/"
    response = context.request.get(BASE + path, max_redirects=0)
    assert response.status != 404, f"Button target missing: {href}"
    assert response.status < 500, f"Button target server failure: {href} -> {response.status}"


def prove_transport(browser, viewport):
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    response = page.goto(BASE + "/transport", wait_until="domcontentloaded")
    assert response is not None and response.status == 200
    expect(page.locator("h1")).to_have_text("Global Transport")
    expect(page.locator('link[rel="manifest"]')).to_have_attribute(
        "href", "/transport/manifest.webmanifest"
    )
    expect(page.locator("[data-oap-install-status]")).to_be_visible()
    assert_layout(page)

    api = page.evaluate(
        """async () => {
          const [status, caps, readiness] = await Promise.all([
            fetch('/transport/status').then(r => r.json()),
            fetch('/transport/capabilities').then(r => r.json()),
            fetch('/transport/execution-readiness').then(r => r.json()),
          ]);
          return {status, caps, readiness};
        }"""
    )
    assert api["status"]["software_surface_install_ready"] is True
    assert api["caps"]["capability_count"] == 21
    assert api["readiness"]["software_execution_layer_ready"] is True
    assert api["readiness"]["live_execution_authorised"] is False

    for route, labels in DASHBOARDS.items():
        response = page.goto(BASE + route, wait_until="domcontentloaded")
        assert response is not None and response.status == 200, route
        assert_layout(page)
        for label in labels:
            link = page.get_by_role("link", name=label, exact=True)
            expect(link).to_be_visible()
            href = link.get_attribute("href")
            assert href and href.startswith("/"), (route, label, href)
            assert_navigation_target(context, href)

    # Explicitly prove the direct Global Transport ride aliases exist and redirect
    # to their durable Movement owners instead of dead-ending.
    aliases = (
        ("/transport/ride/request", "/movement/bookings"),
        ("/transport/ride/driver/availability", "/movement/availability"),
    )
    for source, expected in aliases:
        result = context.request.post(BASE + source, max_redirects=0)
        assert result.status == 307, (source, result.status)
        assert result.headers["location"].endswith(expected), result.headers

    assert not errors, errors
    context.close()


def main():
    os.environ.setdefault("OAP_AUTH_REQUIRED", "false")
    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="transport-browser-ci",
        SESSION_COOKIE_SECURE=False,
    )
    server = make_server("127.0.0.1", 8774, app_module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            prove_transport(browser, {"width": 393, "height": 852})
            prove_transport(browser, {"width": 1280, "height": 800})
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)
    print("TRANSPORT_REAL_CHROMIUM_PASS")


if __name__ == "__main__":
    main()
