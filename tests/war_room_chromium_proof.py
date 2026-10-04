from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import neon_auth, web_security

AUTH_ID = "11111111-1111-4111-8111-111111111111"
AUTH_COOKIE = "better-auth.session_token"
AUTH_VALUE = "war-room-browser-proof-session"
CSRF_VALUE = "war-room-browser-proof-csrf-1234567890"


def _fake_auth_session(cookie_header: str):
    if f"{AUTH_COOKIE}={AUTH_VALUE}" not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "war-room-browser-proof"},
            "user": {
                "id": AUTH_ID,
                "name": "OAP Founder",
                "email": "founder@example.test",
                "emailVerified": True,
            },
        },
    )


def _prepare_app() -> None:
    os.environ["OAP_AUTH_REQUIRED"] = "true"
    os.environ["OAP_HUMAN_AUTHORITY_EMAIL"] = "founder@example.test"
    os.environ["NEON_AUTH_BASE_URL"] = "https://example.neonauth.test/neondb/auth"
    app_module.app.config.update(
        TESTING=True,
        SESSION_COOKIE_SECURE=False,
        SECRET_KEY="war-room-browser-proof-secret",
    )
    neon_auth.get_session = _fake_auth_session
    web_security.CHAT_BURST_LIMITER.reset()
    web_security.AUTH_BURST_LIMITER.reset()
    web_security.PUBLIC_WRITE_LIMITER.reset()


def _session_cookies() -> tuple[str, str]:
    session_name = app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    with app_module.app.test_client() as client:
        client.set_cookie(AUTH_COOKIE, AUTH_VALUE)
        with client.session_transaction() as current_session:
            current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [AUTH_COOKIE]
            current_session[web_security.CSRF_SESSION_KEY] = CSRF_VALUE

        response = client.get("/mission/war-room")
        assert response.status_code == 200, response.status_code
        session_cookie = client.get_cookie(session_name)
        assert session_cookie is not None
        return session_name, session_cookie.value


def main() -> None:
    _prepare_app()
    session_name, session_value = _session_cookies()

    server = make_server("127.0.0.1", 8776, app_module.app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = "http://127.0.0.1:8776"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {"name": AUTH_COOKIE, "value": AUTH_VALUE, "url": base_url},
                    {"name": session_name, "value": session_value, "url": base_url},
                ]
            )

            page = context.new_page()
            page_errors: list[str] = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            page.goto(base_url + "/mission/war-room", wait_until="domcontentloaded")
            expect(page.get_by_role("heading", name="WAR ROOM")).to_be_visible()
            expect(page.get_by_role("heading", name="UI · UX · Buttons · Functions · Proof · Authority")).to_be_visible()

            control_count = page.locator("[data-wr-control-count]")
            function_count = page.locator("[data-wr-function-count]")
            expect(control_count).not_to_have_text("—")
            expect(function_count).not_to_have_text("—")
            assert int(control_count.inner_text()) > 0
            assert int(function_count.inner_text()) > 0

            page.locator('button[data-depth="21"]').click()
            expect(page.locator("#war-action-result")).to_contain_text("MANUAL 21 selected")
            assert page.locator('button[data-depth="21"]').get_attribute("aria-pressed") == "true"

            page.locator("button.js-war-mode").click()
            expect(page.locator("#war-action-result")).to_contain_text("WAR ROOM selected")

            page.locator(".mission").fill("prove the upgraded War Room interaction path")
            page.locator('button[data-action="alignment-check"]').click()
            page.wait_for_function(
                """() => {
                    const node = document.querySelector('#war-action-result');
                    return node && !node.innerText.includes('Running bounded War Room review') &&
                           node.innerText.toLowerCase().includes('alignment');
                }"""
            )

            result_text = page.locator("#war-action-result").inner_text()
            assert "failed (" not in result_text.lower()
            assert "Founder Final" in page.locator("body").inner_text()
            assert page.locator("button.js-founder-final").is_visible()
            assert page.locator('button[data-proof="rollback-recovery"]').is_visible()
            assert page.locator('button[data-proof="runtime-guard"]').is_visible()
            assert page.locator('button[data-proof="isolation-recovery"]').is_visible()
            assert page_errors == [], page_errors

            print("WAR_ROOM_CHROMIUM_ACCEPTANCE=PASS")
            print("FOUNDER_AUTHENTICATED_ROUTE=PASS")
            print("STATUS_MATRIX_VISIBLE=PASS")
            print("CONTROL_COUNTS_RENDERED=PASS")
            print("MANUAL_21_INTERACTION=PASS")
            print("WAR_ROOM_MODE_INTERACTION=PASS")
            print("ALIGNMENT_POST_ACTION=PASS")
            print("RECOVERY_CONTROLS_VISIBLE=PASS")
            print("FOUNDER_FINAL_SEPARATE=PASS")
            print("PAGE_ERRORS=0")

            context.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
