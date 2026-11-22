"""Real Chromium interaction proof for OAP World; external destinations are never visited."""
from __future__ import annotations

import threading

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module

BASE = "http://127.0.0.1:8786"


def main():
    app_module.app.config.update(TESTING=True, SECRET_KEY="oap-world-chromium-ci", SESSION_COOKIE_SECURE=False)
    server = make_server("127.0.0.1", 8786, app_module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for mobile in (False, True):
                context = browser.new_context(
                    viewport={"width": 393 if mobile else 1280, "height": 852 if mobile else 800},
                    is_mobile=mobile, has_touch=mobile,
                )
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda exc, sink=errors: sink.append(str(exc)))
                response = page.goto(BASE + "/world?source=oap-os")
                assert response is not None and response.status == 200
                expect(page.locator("#world-query")).to_be_visible()
                expect(page.locator('nav[aria-label="Quick destinations"] a')).to_have_count(4)
                assert page.locator('a[href="/the-spot"]').count() > 0

                page.locator("#world-query").fill("javascript:alert(1)")
                page.get_by_role("button", name="Open").click()
                expect(page.locator("#world-search-note")).to_contain_text("valid web address")
                assert page.url.startswith(BASE + "/world")

                page.locator("#world-query").fill("https://user:secret@example.org")
                page.get_by_role("button", name="Open").click()
                expect(page.locator("#world-search-note")).to_contain_text("valid web address")
                assert page.url.startswith(BASE + "/world")

                page.once("dialog", lambda dialog: dialog.dismiss())
                page.locator("#world-query").fill("example.org")
                page.locator("#world-query").press("Enter")
                expect(page.locator("#world-search-note")).to_contain_text("Stayed in OAP World")
                assert page.url.startswith(BASE + "/world")
                # One OAP journey on the same real browser: Spot → Link → My Card.
                response = page.goto(BASE + "/the-spot")
                assert response is not None and response.status == 200
                expect(page.get_by_role("heading", name="The Spot")).to_be_visible()
                expect(page.locator('a[href="/the-link"]')).to_have_count(1)
                expect(page.locator('a[href="/my-card"]')).to_have_count(1)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")

                page.locator('a[href="/the-link"]').click()
                assert page.url.endswith("/the-link"), page.url
                expect(page.get_by_role("heading", name="The Link")).to_be_visible()
                expect(page.locator('a[href="/linkup?intent=message"]')).to_have_count(1)
                expect(page.locator('a[href="/my-card"]')).to_have_count(1)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")

                response = page.goto(BASE + "/my-card/create")
                assert response is not None and response.status == 200
                expect(page.get_by_role("heading", name="Create My Card")).to_be_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")

                # Link Up royal desktop + mobile responsive acceptance.
                response = page.goto(BASE + "/linkup")
                assert response is not None and response.status == 200
                expect(page.locator('main[aria-label="Link Up app"]')).to_be_visible()
                bottom = page.locator('nav[aria-label="Link Up public bottom navigation"]')
                expect(bottom).to_be_visible() if mobile else expect(bottom).to_be_hidden()
                expect(page.locator(".linkup-rich-features > *")).to_have_count(9)
                assert page.locator('main[aria-label="Private Link Up messenger"]').count() == 0
                rail = page.locator('nav[aria-label="Link Up desktop navigation"]')
                expect(rail).to_be_hidden() if mobile else expect(rail).to_be_visible()
                cols = page.locator(".linkup-rich-features").evaluate(
                    "(el) => getComputedStyle(el).gridTemplateColumns.split(' ').length"
                )
                assert cols == 5, (mobile, cols)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                field = page.locator("[data-oap-public-filter]")
                field.fill("safety")
                expect(page.locator("[data-public-filter-item]:not([hidden])")).to_have_count(1)
                expect(page.locator("[data-oap-public-search-note]")).to_contain_text("1 matching public sections")
                field.fill("nearby")
                expect(page.locator("[data-public-filter-item]:not([hidden])")).to_have_count(1)
                assert page.locator("[data-linkup-secondary]").evaluate("(el) => el.open") is True
                expect(page.get_by_role("link", name="Nearby People")).to_be_visible()
                field.press("Escape")
                expect(field).to_have_value("")
                expect(page.locator("[data-public-filter-item]:not([hidden])")).to_have_count(12)
                # Click the visible navigation surface for this viewport.
                # Desktop hides the mobile bar; the source still retains one private route.
                if mobile:
                    page.locator('nav[aria-label="Link Up public bottom navigation"] a[href="/linkup?intent=message"]').click()
                else:
                    page.locator('nav[aria-label="Link Up desktop navigation"] a[href="/linkup?intent=message"]').click()
                assert ("/auth" in page.url or "/enter-my-world" in page.url), page.url
                assert not errors, errors
                context.close()
            browser.close()
        print("OAP_WORLD_REAL_CHROMIUM_PASS")
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
