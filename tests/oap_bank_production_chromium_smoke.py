"""Live production Chromium proof for the OAP Bank/SIKA app.

No fixtures, request interception, set_content(), or mocked readiness state.
The target is the deployed public OAP Bank surface and its canonical status.
"""
from playwright.sync_api import expect, sync_playwright

BASE_URL = "https://on-any-postcode.onrender.com"
BANK_URL = BASE_URL + "/pay/bank"
STATUS_URL = BASE_URL + "/pay/bank/status"

CUSTOMER_ROUTES = (
    "/pay/bank/accounts",
    "/pay/bank/transfers",
    "/pay/bank/activity",
    "/pay/bank/cards",
    "/pay/bank/rights",
    "/pay/bank/guardian",
    "/pay/bank/settings",
    "/pay/bank/intelligence",
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
        payload = status_response.json()
        assert payload["software_scope"] == "software_only"
        assert payload["software_ready"] is True
        assert payload["software_percent"] == 100
        assert payload["software_checks"]
        assert all(payload["software_checks"].values())
        for required_check in (
            "account_owner_resolution",
            "canonical_balance_engine",
            "payment_reservations",
            "atomic_payment_creation",
            "terminal_hold_lifecycle",
            "authenticated_customer_view",
        ):
            assert payload["software_checks"][required_check] is True
        assert payload["software_external_execution_ready"] is False
        assert payload["money_movement_enabled"] is False
        assert payload["authenticated_customer_view"] is True
        assert payload["personal_balance_public"] is False

        private_response = context.request.get(
            BASE_URL + "/pay/bank/me/status"
        )
        assert private_response.status == 401
        assert (
            private_response.json()["error"]["code"]
            == "authentication_required"
        )

        for route in CUSTOMER_ROUTES:
            route_response = context.request.get(BASE_URL + route)
            assert route_response.status == 200, route

        manifest_response = context.request.get(
            BASE_URL + "/pay/bank/manifest.webmanifest"
        )
        assert manifest_response.status == 200
        manifest = manifest_response.json()
        assert manifest["id"] == "/pay/bank"
        assert manifest["start_url"] == "/pay/bank"
        assert manifest["scope"] == "/pay/bank"
        assert manifest["display"] == "standalone"

        assert not errors, errors
        print("OAP_BANK_PRODUCTION_CHROMIUM_PASS")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
