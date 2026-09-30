"""Authenticated Chromium proof for the real ALL IN route and browser controls.

Uses a test auth session, not fabricated mission/database results. This is
software/browser acceptance, never a production-data certification.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import neon_auth, web_security

AUTH_COOKIE = "better-auth.session_token"
AUTH_VALUE = "all-in-browser-proof"
AUTH_ID = "11111111-1111-4111-8111-111111111111"
CSRF_VALUE = "all-in-browser-csrf-proof-token-1234567890123"


def _auth_session(cookie_header: str):
    if f"{AUTH_COOKIE}={AUTH_VALUE}" not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "all-in-browser-session"},
            "user": {
                "id": AUTH_ID, "name": "OAP Founder",
                "email": "founder@example.test", "emailVerified": True,
            },
        },
    )


def _setup():
    os.environ["OAP_AUTH_REQUIRED"] = "true"
    os.environ["OAP_HUMAN_AUTHORITY_EMAIL"] = "founder@example.test"
    os.environ["NEON_AUTH_BASE_URL"] = "https://example.neonauth.test/neondb/auth"
    app_module.app.config.update(
        TESTING=True, SESSION_COOKIE_SECURE=False,
        SECRET_KEY="all-in-browser-proof-secret",
    )
    neon_auth.get_session = _auth_session

    with app_module.app.test_client() as anonymous:
        response = anonymous.get("/mission/all-in-ai/app")
        assert response.status_code == 302, response.status_code

    session_name = app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    with app_module.app.test_client() as client:
        client.set_cookie(AUTH_COOKIE, AUTH_VALUE)
        with client.session_transaction() as state:
            state[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [AUTH_COOKIE]
            state[web_security.CSRF_SESSION_KEY] = CSRF_VALUE
        response = client.get("/mission/all-in-ai/app")
        assert response.status_code == 200, response.status_code
        cookie = client.get_cookie(session_name)
        assert cookie is not None
        return session_name, cookie.value


def main():
    session_name, session_value = _setup()
    server = make_server("127.0.0.1", 8766, app_module.app)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_url = "http://127.0.0.1:8766"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies([
                {"name": AUTH_COOKIE, "value": AUTH_VALUE, "url": base_url},
                {"name": session_name, "value": session_value, "url": base_url},
            ])
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            response = page.goto(base_url + "/mission/all-in-ai/app",
                                 wait_until="domcontentloaded")
            assert response is not None and response.status == 200
            assert page.locator("h1").inner_text() == "👑 ALL IN A.I."
            for name in ("start", "restore", "read", "stop", "recover",
                         "inference-inspect", "handoff-review",
                         "internal-execute", "internal-rollback"):
                assert page.locator("#" + name).count() == 1, name
            assert page.locator("#start").is_enabled()
            assert page.locator("#restore").is_enabled()
            for name in ("read", "stop", "recover", "inference-inspect",
                         "handoff-review", "internal-execute", "internal-rollback"):
                assert page.locator("#" + name).is_disabled(), name
            assert page.evaluate(
                "() => document.documentElement.scrollWidth <= innerWidth + 2"
            ), "ALL IN mobile horizontal overflow"
            assert not errors, errors

            # Use actual authenticated Flask CSRF middleware, but do not
            # fabricate or run a successful Mission/database transaction.
            csrf_status = page.evaluate(
                """async () => (await fetch('/mission/all-in-ai/mission', {
                  method: 'POST', credentials: 'same-origin',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({mission: 'unauthorised write'})
                })).status"""
            )
            assert csrf_status == 403, csrf_status

            # Forged browser state must not grant STOP or Recover.
            page.evaluate(
                """() => {
                  sessionStorage.setItem('oap_all_in_ai_mission_id',
                    '00000000-0000-4000-8000-000000000002');
                  sessionStorage.setItem('oap_all_in_ai_digest', 'a'.repeat(64));
                }"""
            )
            page.reload(wait_until="domcontentloaded")
            assert page.locator("#read").is_enabled()
            for name in ("stop", "recover", "inference-inspect",
                         "handoff-review", "internal-execute", "internal-rollback"):
                assert page.locator("#" + name).is_disabled(), name
            assert "Verify Read-back or Restore Latest" in page.locator(
                "#result"
            ).inner_text()
            assert not errors, errors

            print("ALL_IN_AUTHENTICATED_CHROMIUM=PASS")
            print("ALL_IN_PRIVATE_ROUTE_BOUNDARY=PASS")
            print("ALL_IN_NINE_BUTTONS_RENDERED=PASS")
            print("ALL_IN_NO_BROWSER_PROOF_FORGED=PASS")
            print("ALL_IN_REAL_CSRF_REJECTION=PASS")
            print("ALL_IN_MOBILE_LAYOUT_NO_OVERFLOW=PASS")
            print("ALL_IN_JS_PAGE_ERRORS=0")
            print("ALL_IN_PRODUCTION_DATABASE_PROOF=NOT_CLAIMED")
            context.close()
            browser.close()
    finally:
        server.shutdown()
        server_thread.join(timeout=2)


if __name__ == "__main__":
    main()
