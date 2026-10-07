"""Authenticated Chromium acceptance for standalone OAP PTT.

This proves browser/auth/CSRF/hold-release/microphone-boundary behavior against
the real Flask routes with a deterministic in-process persistence seam.
It does NOT claim production identity, physical microphone hardware, radio,
network transport, or device-to-device audible delivery.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import app as app_module
from mission_control import link_relationships, link_voice, neon_auth, product_store, web_security

AUTH_ID = "11111111-1111-4111-8111-111111111111"
PEER_ID = "22222222-2222-4222-8222-222222222222"
AUTH_COOKIE = "better-auth.session_token"
AUTH_VALUE = "ptt-browser-proof-session"
CSRF_VALUE = "ptt-browser-proof-csrf-1234567890123456"
RECEIPTS: list[dict[str, object]] = []


def _fake_auth_session(cookie_header: str):
    if f"{AUTH_COOKIE}={AUTH_VALUE}" not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "ptt-browser-proof"},
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
        SECRET_KEY="ptt-browser-proof-secret",
    )
    neon_auth.get_session = _fake_auth_session
    web_security.PUBLIC_WRITE_LIMITER.reset()
    web_security.AUTH_BURST_LIMITER.reset()
    web_security.CHAT_BURST_LIMITER.reset()

    product_store.linkup_dashboard = lambda _identity: {
        "directory": [
            {
                "identity_id": PEER_ID,
                "display_name": "PTT Peer",
                "card_id": product_store.member_card_id(PEER_ID),
            }
        ]
    }
    link_relationships.list_for_identity = lambda _identity: [
        {
            "status": "accepted",
            "requester_id": AUTH_ID,
            "recipient_id": PEER_ID,
        }
    ]
    link_voice.status = lambda: {
        "configured": True,
        "schema_ready": True,
        "ready": True,
        "ptt_ready": True,
        "first_party": True,
        "max_voice_bytes": 5 * 1024 * 1024,
        "max_voice_duration_ms": 120000,
    }
    link_voice.list_voice = lambda _identity, _peer: []

    def _capture(sender_id, recipient_id, *, media, mime_type, duration_ms=None, kind="voice"):
        assert sender_id == AUTH_ID
        assert recipient_id == PEER_ID
        assert kind == "ptt"
        assert isinstance(media, bytes) and len(media) > 0
        assert str(mime_type).split(";", 1)[0] in link_voice.ALLOWED_MIME_TYPES
        RECEIPTS.append(
            {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "byte_size": len(media),
                "mime_type": str(mime_type),
                "duration_ms": duration_ms,
                "kind": kind,
            }
        )
        return {
            "voice_id": "33333333-3333-4333-8333-333333333333",
            "mime_type": str(mime_type).split(";", 1)[0],
            "byte_size": len(media),
            "duration_ms": int(duration_ms or 0),
            "sha256": "a" * 64,
            "created_at": "2026-10-07T00:00:00+00:00",
            "kind": "ptt",
        }

    link_voice.create_voice = _capture


def _session_cookies() -> tuple[str, str]:
    session_name = app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    with app_module.app.test_client() as anonymous:
        response = anonymous.get("/ptt")
        assert response.status_code == 302, response.status_code

    with app_module.app.test_client() as client:
        client.set_cookie(AUTH_COOKIE, AUTH_VALUE)
        with client.session_transaction() as current_session:
            current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [AUTH_COOKIE]
            current_session[web_security.CSRF_SESSION_KEY] = CSRF_VALUE
        response = client.get("/ptt")
        assert response.status_code == 200, response.status_code
        session_cookie = client.get_cookie(session_name)
        assert session_cookie is not None
        return session_name, session_cookie.value


def main() -> None:
    RECEIPTS.clear()
    _prepare_app()
    session_name, session_value = _session_cookies()

    server = make_server("127.0.0.1", 8787, app_module.app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = "http://127.0.0.1:8787"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--use-fake-device-for-media-stream",
                    "--use-fake-ui-for-media-stream",
                ],
            )
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.grant_permissions(["microphone"], origin=base_url)
            context.add_cookies(
                [
                    {"name": AUTH_COOKIE, "value": AUTH_VALUE, "url": base_url},
                    {"name": session_name, "value": session_value, "url": base_url},
                ]
            )
            page = context.new_page()
            page_errors: list[str] = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.add_init_script(
                """
                (() => {
                  window.__oapPttMicRequests = 0;
                  const mediaDevices = navigator.mediaDevices;
                  if (!mediaDevices || !mediaDevices.getUserMedia) return;
                  const original = mediaDevices.getUserMedia.bind(mediaDevices);
                  mediaDevices.getUserMedia = (...args) => {
                    window.__oapPttMicRequests += 1;
                    return original(...args);
                  };
                })();
                """
            )

            response = page.goto(base_url + "/ptt", wait_until="domcontentloaded")
            assert response is not None and response.status == 200
            expect(page.get_by_role("heading", name="🎙️ PTT")).to_be_visible()
            expect(page.locator("#ptt-contact")).to_have_value("")
            assert page.evaluate("() => window.__oapPttMicRequests") == 0
            expect(page.locator("[data-oap-voice-status]")).to_contain_text("PTT")

            page.locator("#ptt-contact").select_option(PEER_ID)
            control = page.locator("[data-oap-ptt-control]")
            expect(control).to_be_enabled()

            box = control.bounding_box()
            assert box is not None
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down()
            page.wait_for_function("() => window.__oapPttMicRequests === 1")
            expect(page.locator("[data-oap-voice-status]")).to_contain_text("PTT transmitting")
            page.wait_for_timeout(500)
            page.mouse.up()

            page.wait_for_function(
                """() => document.querySelector('[data-oap-voice-status]')?.innerText.includes('PTT landed.')"""
            )
            assert len(RECEIPTS) == 1, RECEIPTS
            receipt = RECEIPTS[0]
            assert receipt["kind"] == "ptt"
            assert int(receipt["byte_size"]) > 0
            assert page.evaluate("() => window.__oapPttMicRequests") == 1
            assert page_errors == [], page_errors
            assert page.evaluate(
                "() => document.documentElement.scrollWidth <= innerWidth + 2"
            )

            print("PTT_AUTHENTICATED_CHROMIUM=PASS")
            print("PTT_PRIVATE_ROUTE_BOUNDARY=PASS")
            print("PTT_MIC_OFF_BEFORE_USER_ACTION=PASS")
            print("PTT_HOLD_REQUESTS_MIC=PASS")
            print("PTT_RELEASE_STOPS_AND_POSTS=PASS")
            print("PTT_AUTH_CSRF_POST_ROUTE=PASS")
            print("PTT_BROWSER_MEDIA_BYTES_CAPTURED=PASS")
            print("PTT_PAGE_ERRORS=0")
            print("PTT_REAL_DEVICE_TO_DEVICE_AUDIO=NOT_CLAIMED")

            context.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
