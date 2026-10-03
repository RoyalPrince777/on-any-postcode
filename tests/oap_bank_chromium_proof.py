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
            expect(page.get_by_text("Available balance", exact=True)).to_be_visible()
            capture_guard = page.evaluate("window.OAP_BANK_CAPTURE_GUARD")
            assert capture_guard["webScreenshotDetectionReliable"] is False
            assert capture_guard["webScreenshotBlockingReliable"] is False
            assert capture_guard["privacyShieldOnBackground"] is True
            assert capture_guard["nativeAndroidFlagSecureRecommended"] is True
            expect(page.locator("#oap-bank-capture-watermark")).to_be_attached()
            expect(page.get_by_text("No authenticated account selected", exact=False)).to_be_visible()
            expect(page.locator('[aria-label="Quick actions"]')).to_be_visible()
            expect(page.get_by_text("My accounts", exact=True)).to_be_visible()
            expect(page.get_by_text("Recent activity", exact=True)).to_be_visible()
            more_panel = page.locator("#more")
            expect(more_panel).to_be_visible()
            page.get_by_text("More", exact=True).last.click()
            assert more_panel.get_attribute("open") is not None

            page.get_by_text("Accounts", exact=True).last.click()
            page.wait_for_url("**/pay/bank/accounts")
            expect(page.get_by_text("Accounts", exact=True).first).to_be_visible()
            expect(page.get_by_text("Action unavailable", exact=True)).to_be_visible()

            page.goto(BASE + "/pay/bank", wait_until="domcontentloaded")
            page.get_by_text("Transfers", exact=True).last.click()
            page.wait_for_url("**/pay/bank/transfers")
            expect(page.get_by_text("Transfers", exact=True).first).to_be_visible()

            page.goto(BASE + "/pay/bank", wait_until="domcontentloaded")
            page.get_by_text("Intelligence", exact=True).last.click()
            page.wait_for_url("**/pay/bank/intelligence")
            expect(page.get_by_text("All Bank Intelligence", exact=True)).to_be_visible()
            expect(page.get_by_text("21 first-party intelligence domains", exact=False)).to_be_visible()

            manifest_href = page.locator('link[rel="manifest"]').get_attribute("href")
            assert manifest_href == "/pay/bank/manifest.webmanifest"

            page.goto(BASE + "/pay/bank/cards", wait_until="domcontentloaded")
            nav = page.locator('[aria-label="OAP Bank navigation"]')
            expect(nav).to_be_visible()
            expect(nav.get_by_text("Home", exact=True)).to_be_visible()
            expect(nav.get_by_text("Accounts", exact=True)).to_be_visible()
            expect(nav.get_by_text("Transfers", exact=True)).to_be_visible()
            expect(nav.get_by_text("Activity", exact=True)).to_be_visible()
            expect(nav.get_by_text("More", exact=True)).to_be_visible()

            assert not errors, errors
            print("OAP_BANK_REAL_CHROMIUM_PASS")
            context.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
