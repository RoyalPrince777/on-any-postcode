"""Real Chromium proof for the OAP Bank installable app shell."""

from __future__ import annotations

import threading

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module

BASE = "http://127.0.0.1:8774"


def main():
    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="oap-bank-browser-ci",
        SESSION_COOKIE_SECURE=False,
    )
    server = make_server("127.0.0.1", 8774, app_module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 393, "height": 852},
                is_mobile=True,
                has_touch=True,
            )
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))

            response = page.goto(BASE + "/pay/bank", wait_until="domcontentloaded")
            assert response is not None and response.status == 200

            expect(page.get_by_text("OAP Bank", exact=True).first).to_be_visible()
            expect(page.locator('[aria-label="OAP Bank navigation"]')).to_be_visible()
            expect(page.get_by_text("Bank Home", exact=True)).to_be_visible()
            expect(page.locator("#accounts")).to_be_visible()
            expect(page.locator("#transfers")).to_be_visible()
            expect(page.locator("#activity")).to_be_visible()
            expect(page.locator("#more")).to_be_visible()
            expect(page.locator("#capabilities")).to_be_visible()

            page.get_by_text("Accounts", exact=True).last.click()
            page.wait_for_url("**/pay/bank/accounts")
            expect(page.get_by_text("Accounts", exact=True).first).to_be_visible()
            expect(page.get_by_text("Evidence-gated / unavailable", exact=True)).to_be_visible()

            page.goto(BASE + "/pay/bank", wait_until="domcontentloaded")
            page.get_by_text("Transfers", exact=True).last.click()
            page.wait_for_url("**/pay/bank/transfers")
            expect(page.get_by_text("Transfers", exact=True).first).to_be_visible()

            manifest_href = page.locator('link[rel="manifest"]').get_attribute("href")
            assert manifest_href == "/pay/bank/manifest.webmanifest"

            assert not errors, errors
            print("OAP_BANK_REAL_CHROMIUM_PASS")
            context.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
