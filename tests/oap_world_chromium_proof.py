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
                expect(page.locator("#world-web-extra")).to_be_visible()
                expect(page.locator("#world-query")).to_be_hidden()
                page.locator("#world-web-extra summary").click()
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
                assert not errors, errors

                # Browse and Apps share the existing KORADASO route and OAP
                # catalogue/search; this is not a second installable browser.
                world = page.goto(BASE + "/world")
                assert world is not None and world.status == 200
                expect(page.locator('nav[aria-label="Browse and Apps across OAP World"] a')).to_have_count(3)
                assert page.locator('nav[aria-label="Browse and Apps across OAP World"]').evaluate(
                    "(nav) => getComputedStyle(nav).display === 'grid'"
                )
                page.locator('[data-oap-browse-koradaso]').click()
                assert page.url.startswith(BASE + "/koradaso")
                page.goto(BASE + "/world")
                page.locator('[data-oap-world-apps]').click()
                assert page.url.startswith(BASE + "/store")
                expect(page.locator('[data-oap-store-app="oap.koradaso"]')).to_have_count(1)
                page.goto(BASE + "/world")
                page.locator('[data-oap-world-search]').click()
                assert page.url.startswith(BASE + "/search")
                page.get_by_role("searchbox", name="Search OAP").fill("koradaso")
                page.get_by_role("button", name="Search").click()
                expect(page.get_by_role("link", name="Open KORADASO Internet")).to_be_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                assert not errors, errors

                # Reuse the same real browser session for public KORADASO;
                # never visit the external destination when consent is denied.
                browser_home = page.goto(BASE + "/koradaso")
                assert browser_home is not None and browser_home.status == 200
                expect(page.locator("#address")).to_be_visible()
                expect(page.locator(".grid.tile-collection")).to_have_count(0)
                icon_columns = page.locator('nav[aria-label="KORADASO destinations"]').evaluate(
                    "(nav) => getComputedStyle(nav).gridTemplateColumns.split(' ').length"
                )
                assert icon_columns == 4, (mobile, icon_columns)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                expect(page.locator('a[href="/store"]')).to_have_count(1)
                expect(page.locator('a[href="/my-world"]')).to_have_count(1)
                # The restored Compass, Saved Places and session Open Places
                # must work in a real browser without recording private routes.
                assert page.locator("img[src='/static/oap/koradaso_internet_logo.jpg']").evaluate("(img) => img.complete && img.naturalWidth > 0")
                page.get_by_label("Compass browser menu").click()
                expect(page.get_by_role("heading", name="Royal Compass")).to_be_visible()
                page.locator("#place-route").select_option("/arena")
                page.locator("#open-place-add").click()
                expect(page.locator("#open-place-list a[href='/arena']")).to_have_count(1)
                page.locator("#bookmark-add").click()
                expect(page.locator("#bookmark-list a[href='/arena']")).to_have_count(1)
                page.locator("#quiet-appearance").check()
                assert page.locator("body").evaluate("(el) => el.classList.contains('quiet-appearance')")
                page.locator("#drawer-close").click()
                page.locator("#address").fill("a search phrase")
                page.get_by_role("button", name="GO").click()
                assert page.url.startswith(BASE + "/search?q=")
                browser_home = page.goto(BASE + "/koradaso")
                assert browser_home is not None and browser_home.status == 200
                page.locator("#address").fill("http://example.org")
                page.get_by_role("button", name="GO").click()
                expect(page.locator("#address-note")).to_contain_text("valid HTTPS domains")

                page.once("dialog", lambda dialog: dialog.dismiss())
                page.locator("#address").fill("example.org")
                page.get_by_role("button", name="GO").click()
                expect(page.locator("#address-note")).to_contain_text("Stayed in KORADASO Internet")
                assert page.url.startswith(BASE + "/koradaso")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                page.locator('a[href="/my-world"]').click()
                assert page.url.startswith(BASE + "/enter-my-world")
                assert "Founder Home doors" not in page.content()
                assert not errors, errors
                context.close()
            browser.close()
        print("OAP_WORLD_REAL_CHROMIUM_PASS")
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
