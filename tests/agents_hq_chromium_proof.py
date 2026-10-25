"""Authenticated, local Chromium proof for the read-only SMI Agents HQ.

A synthetic Founder session verifies browser wiring; it is NOT independent
production identity-provider certification or live agent participation.
"""
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
from mission_control import agents_hq, neon_auth, web_security

AUTH_ID = "11111111-1111-4111-8111-111111111111"
AUTH_COOKIE = "better-auth.session_token"
AUTH_VALUE = "agents-hq-browser-proof-session"


def _synthetic_auth(cookie_header: str):
    if f"{AUTH_COOKIE}={AUTH_VALUE}" not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "agents-hq-browser-proof"},
            "user": {
                "id": AUTH_ID,
                "name": "OAP Founder",
                "email": "founder@example.test",
                "emailVerified": True,
            },
        },
    )


def _founder_cookies() -> tuple[str, str]:
    session_name = app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    with app_module.app.test_client() as client:
        client.set_cookie(AUTH_COOKIE, AUTH_VALUE)
        with client.session_transaction() as current_session:
            current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [AUTH_COOKIE]
        response = client.get("/mission/smi/agents-hq")
        assert response.status_code == 200, response.status_code
        cookie = client.get_cookie(session_name)
        assert cookie is not None
        return session_name, cookie.value


def main() -> None:
    os.environ["OAP_AUTH_REQUIRED"] = "true"
    os.environ["OAP_HUMAN_AUTHORITY_EMAIL"] = "founder@example.test"
    os.environ["NEON_AUTH_BASE_URL"] = "https://example.neonauth.test/neondb/auth"
    app_module.app.config.update(
        TESTING=True,
        SESSION_COOKIE_SECURE=False,
        SECRET_KEY="agents-hq-local-browser-proof-only",
    )
    neon_auth.get_session = _synthetic_auth
    web_security.CHAT_BURST_LIMITER.reset()
    web_security.AUTH_BURST_LIMITER.reset()
    web_security.PUBLIC_WRITE_LIMITER.reset()
    session_name, session_value = _founder_cookies()
    directory = agents_hq.room_directory()
    individual = next(room for room in directory["rooms"] if room["kind"] == "individual")
    family = next(
        room for room in directory["rooms"]
        if room["kind"] == "family" and room["agent_ids"]
    )
    server = make_server("127.0.0.1", 8777, app_module.app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = "http://127.0.0.1:8777"

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                anonymous = browser.new_context(viewport={"width": 390, "height": 844})
                try:
                    denied = anonymous.request.get(url + "/mission/smi/agents-hq/rooms")
                    assert denied.status == 401, denied.status
                    assert denied.json()["error"]["code"] == "authentication_required"
                    assert denied.headers["cache-control"] == "no-store"
                finally:
                    anonymous.close()

                founder = browser.new_context(viewport={"width": 390, "height": 844})
                founder.add_cookies([
                    {"name": AUTH_COOKIE, "value": AUTH_VALUE, "url": url},
                    {"name": session_name, "value": session_value, "url": url},
                ])
                try:
                    page = founder.new_page()
                    errors: list[str] = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    response = page.goto(
                        url + "/mission/smi/agents-hq", wait_until="domcontentloaded"
                    )
                    assert response is not None and response.status == 200
                    assert response.headers["cache-control"] == "no-store"
                    expect(page.get_by_role("heading", name="SMI Agents HQ")).to_be_visible()
                    expect(page.get_by_text("No message history or autonomous agent chat", exact=False)).to_be_visible()
                    expect(page.locator("[data-kind='all_agents']")).to_have_attribute(
                        "aria-pressed", "true"
                    )

                    page.locator("[data-kind='individual']").click()
                    expect(page.locator("[data-kind='individual']")).to_have_attribute(
                        "aria-pressed", "true"
                    )
                    page.locator('[data-room-id="' + individual["id"] + '"]').click()
                    expect(page.locator("#room-status")).to_contain_text(
                        "registered members verified"
                    )
                    expect(page.locator("#room-members li")).to_have_count(1)
                    assert page.locator("#room-members li strong").all_text_contents() == [
                        agents_hq.room_context(individual["id"])["members"][0]["name"]
                    ]
                    assert page.locator("[data-room-id='" + individual["id"] + "']").get_attribute(
                        "aria-pressed"
                    ) == "true"

                    page.locator("[data-kind='family']").click()
                    expect(page.locator("#room-members li")).to_have_count(0)
                    page.locator('[data-room-id="' + family["id"] + '"]').click()
                    expect(page.locator("#room-status")).to_contain_text(
                        "registered members verified"
                    )
                    expected = agents_hq.room_context(family["id"])["members"]
                    expect(page.locator("#room-members li")).to_have_count(len(expected))
                    assert page.locator("#room-members li strong").all_text_contents() == [
                        member["name"] for member in expected
                    ]

                    unknown = founder.request.get(
                        url + "/mission/smi/agents-hq/rooms/guest:unregistered"
                    )
                    assert unknown.status == 404
                    assert unknown.json()["error"] == "unknown_room"
                    assert unknown.headers["cache-control"] == "no-store"
                    forbidden = founder.request.post(
                        url + "/mission/smi/agents-hq/rooms",
                        data={"message": "execute"},
                    )
                    assert forbidden.status == 405
                    assert errors == [], errors
                finally:
                    founder.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=2)
    print("AGENTS_HQ_CHROMIUM=PASS")
    print("FOUNDER_AUTH=MOCKED_CI_ONLY")
    print("REGISTERED_MEMBERS_API=PASS")
    print("ANONYMOUS_AND_UNKNOWN_ROOM_REJECTED=PASS")
    print("READ_ONLY_POST_BOUNDARY=PASS")
    print("LIVE_AGENT_CHAT=NOT_IMPLEMENTED")
    print("PRODUCTION_FOUNDER_AUTH=NOT_VERIFIED")


if __name__ == "__main__":
    main()
