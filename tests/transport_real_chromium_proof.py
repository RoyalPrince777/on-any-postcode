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


def assert_seven_door_alignment(page, viewport):
    """Exercise actual Chromium layout, focus and routes instead of CSS-only claims."""
    cards = page.locator('nav[aria-label="Global Transport main menu"] a.card')
    assert cards.count() == 7, "Seven main doors must remain visible"
    bounds = [cards.nth(i).bounding_box() for i in range(7)]
    assert all(box is not None for box in bounds), "Hidden transport door"
    for i, box in enumerate(bounds):
        assert box["width"] >= 120, (i, box)
        assert box["height"] >= 44, (i, box)
        assert box["x"] >= 0
        assert box["x"] + box["width"] <= viewport["width"] + 2
    if viewport["width"] > 320:
        for left, right in ((0, 1), (2, 3), (4, 5)):
            a, b = bounds[left], bounds[right]
            assert abs(a["y"] - b["y"]) <= 2, (left, right, bounds)
            assert abs(a["height"] - b["height"]) <= 2, (left, right, bounds)
            assert b["x"] > a["x"] + a["width"], (left, right, bounds)
        assert bounds[6]["y"] > bounds[4]["y"], "Control Center must follow last pair"
        assert bounds[6]["width"] > bounds[0]["width"], "Last door spans remaining row"
    links = [cards.nth(i).get_attribute("href") for i in range(7)]
    assert len(set(links)) == 7, "Duplicate door routes"
    for href in links:
        assert href and href.startswith("/")
        assert_navigation_target(page.context, href)
    cards.nth(0).focus()
    assert cards.nth(0).evaluate("(el) => document.activeElement === el")


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
    assert_seven_door_alignment(page, viewport)
    for submenu in ("/transport/guardian", "/transport/operators", "/transport/control-center"):
        result = page.goto(BASE + submenu, wait_until="domcontentloaded")
        assert result is not None and result.status == 200
        assert_layout(page)
        items = page.locator('section.grid a.card')
        assert items.count() == 3, submenu
        for i in range(items.count()):
            rect = items.nth(i).bounding_box()
            assert rect and rect["height"] >= 44 and rect["width"] >= 120, (submenu, i, rect)
            href = items.nth(i).get_attribute("href")
            assert href and href.startswith("/"), (submenu, i, href)

    # Human-facing Control Center must not dump JSON or hide an unknown gate.
    for route, title in (
        ("/transport/control-center/capabilities", "Capabilities"),
        ("/transport/control-center/status", "Transport Status"),
    ):
        result = page.goto(BASE + route, wait_until="domcontentloaded")
        assert result is not None and result.status == 200, route
        assert_layout(page)
        expect(page.locator("h1")).to_have_text(title)
        expect(page.locator('a.back[href="/transport/control-center"]')).to_be_visible()
    expect(page.get_by_text("Unknown · blocked").first).to_be_visible()

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
            prove_transport(browser, {"width": 320, "height": 750})
            prove_transport(browser, {"width": 393, "height": 852})
            prove_transport(browser, {"width": 768, "height": 900})
            prove_transport(browser, {"width": 1280, "height": 800})
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)
    print("TRANSPORT_REAL_CHROMIUM_PASS")


if __name__ == "__main__":
    main()
