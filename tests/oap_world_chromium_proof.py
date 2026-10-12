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
                assert not errors, errors
                context.close()
            browser.close()
        print("OAP_WORLD_REAL_CHROMIUM_PASS")
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
