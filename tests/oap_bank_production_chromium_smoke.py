"""Live production Chromium proof for the OAP Bank/SIKA app.

No fixtures, request interception, set_content(), or mocked readiness state.
The target is the deployed public OAP Bank surface and its canonical status.
"""
from __future__ import annotations

import json
import os

from playwright.sync_api import expect, sync_playwright


BANK_URL = os.environ.get(
    "OAP_BANK_URL",
    "https://on-any-postcode.onrender.com/pay/bank",
)
STATUS_URL = os.environ.get(
    "OAP_BANK_STATUS_URL",
    "https://on-any-postcode.onrender.com/pay/bank/status",
)


def main() -> None:
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

        response = page.goto(BANK_URL, wait_until="domcontentloaded")
        assert response is not None and response.status == 200

        expect(page.get_by_text("OAP Bank", exact=True).first).to_be_visible()
        expect(page.locator('[aria-label="OAP Bank navigation"]')).to_be_visible()
        expect(page.get_by_text("Bank Home", exact=True)).to_be_visible()

        status_response = context.request.get(STATUS_URL)
        assert status_response.status == 200
        payload = json.loads(status_response.text())
        assert payload["software_scope"] == "software_only"
        assert payload["software_ready"] is True
        assert payload["software_percent"] == 100
        assert payload["software_checks"]
        assert all(payload["software_checks"].values())
        assert payload["software_external_execution_ready"] is False
        assert payload["money_movement_enabled"] is False

        assert not errors, errors
        print("OAP_BANK_PRODUCTION_CHROMIUM_PASS")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
