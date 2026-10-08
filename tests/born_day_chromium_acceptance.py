"""Real Chromium mobile acceptance for Born Day; run against a locally served OAP app.

Usage: OAP_BASE_URL=http://127.0.0.1:5000 python tests/born_day_chromium_acceptance.py
Requires: playwright and installed Chromium browser.
"""
import os

from playwright.sync_api import sync_playwright


def main():
    base = os.environ.get("OAP_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base + "/world", wait_until="domcontentloaded")
        page.locator('a[href="/born-day"]').first.click()
        assert page.url.split("?")[0].endswith("/born-day")
        assert page.locator('a[href="/born-day/play/oware"]').count()
        assert page.locator('a[href="/born-day/play/ludo"]').count()
        assert page.locator('a[href="/born-day/play/connect4"]').count()
        assert page.locator('a[href="/born-day/reaction-rush"]').count()
        for game in ("oware", "ludo", "connect4"):
            page.goto(base + "/born-day/play/" + game, wait_until="domcontentloaded")
            assert page.locator('nav[aria-label="Born Day navigation"] a[href="/born-day"]').count()
            page.locator('nav[aria-label="Born Day navigation"] a').click()
            assert page.url.split("?")[0].endswith("/born-day")
        page.goto(base + "/born-day/reaction-rush", wait_until="networkidle")
        pad = page.locator("#pad")
        pad.click()
        assert "WAIT" in pad.inner_text()
        pad.click()
        assert "False start" in page.locator("#result").inner_text()
        pad.click()
        assert "WAIT" in pad.inner_text()
        page.wait_for_function("document.querySelector('#pad').textContent.includes('GO!')", timeout=6500)
        pad.click()
        assert "reaction:" in page.locator("#result").inner_text()
        assert not errors, "Browser JavaScript errors: " + repr(errors)
        browser.close()
    print("Born Day mobile Chromium acceptance PASS")


if __name__ == "__main__":
    main()
