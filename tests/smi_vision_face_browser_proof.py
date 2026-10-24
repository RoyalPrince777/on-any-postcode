"""Real Chromium proof: an explicit still-image action cannot become covert capture.

Run via the existing SMI Chromium proof workflow. Browser data and fake identities
never reach public services. Server image decoding is separately unit-tested.
"""
from __future__ import annotations

import base64
import os
import sys
import threading
import time
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import (
    neon_auth,
    smi_chat_runtime,
    studio_face_detection,
    web_security,
)

AUTH_ID = "11111111-1111-4111-8111-111111111111"
AUTH_COOKIE = "better-auth.session_token"
AUTH_VALUE = "verified-vision-browser-session"
CSRF_VALUE = "vision-browser-csrf-token-value-1234567890"


def _fake_auth(cookie_header: str):
    if f"{AUTH_COOKIE}={AUTH_VALUE}" not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "vision-browser-session"},
            "user": {
                "id": AUTH_ID,
                "name": "OAP Founder",
                "email": "founder@example.test",
                "emailVerified": True,
            },
        },
    )


def _session_cookie():
    cookie_name = app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    with app_module.app.test_client() as client:
        client.set_cookie(AUTH_COOKIE, AUTH_VALUE)
        with client.session_transaction() as session:
            session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [AUTH_COOKIE]
            session[web_security.CSRF_SESSION_KEY] = CSRF_VALUE
        response = client.get("/mission/ollama")
        assert response.status_code == 200, response.status_code
        cookie = client.get_cookie(cookie_name)
        assert cookie is not None
        return cookie_name, cookie.value


def _png_bytes():
    stream = BytesIO()
    Image.new("RGB", (120, 100), (92, 122, 145)).save(stream, format="PNG")
    return stream.getvalue()


def main():
    os.environ.update(
        OAP_AUTH_REQUIRED="true",
        OAP_HUMAN_AUTHORITY_EMAIL="founder@example.test",
        NEON_AUTH_BASE_URL="https://example.neonauth.test/neondb/auth",
    )
    os.environ.pop("OAP_SMI_FACE_DETECTION_ENABLED", None)
    app_module.app.config.update(
        TESTING=True,
        SESSION_COOKIE_SECURE=False,
        SECRET_KEY="smi-private-vision-proof",
    )
    neon_auth.get_session = _fake_auth
    smi_chat_runtime.list_conversations = lambda *_a, **_kw: []
    smi_chat_runtime.health = lambda: {
        "checks": {"provider_key": False, "conversation_memory": True,
                   "human_authority": True, "execution_locked": True}
    }
    web_security.CHAT_BURST_LIMITER.reset()
    web_security.AUTH_BURST_LIMITER.reset()

    analysed = []
    delay_detection = [False]
    def bounded_detector(image_data):
        assert image_data.startswith("data:image/png;base64,")
        assert base64.b64decode(image_data.split(",", 1)[1])
        if delay_detection[0]:
            time.sleep(0.65)
        analysed.append(True)
        return {
            "state": "analysed",
            "image": {"width": 120, "height": 100},
            "face_count": 1,
            "faces": [{"x": 20, "y": 15, "width": 40, "height": 40}],
            "identity_verified": False,
            "raw_content_retained": False,
            "execution_granted": False,
        }

    studio_face_detection.detect_faces = bounded_detector
    cookie_name, cookie_value = _session_cookie()
    server = make_server("127.0.0.1", 8774, app_module.app)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    origin = "http://127.0.0.1:8774"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies([
                {"name": AUTH_COOKIE, "value": AUTH_VALUE, "url": origin},
                {"name": cookie_name, "value": cookie_value, "url": origin},
            ])
            page = context.new_page()
            posts = []
            page.on("request", lambda request: posts.append(request.url)
                    if request.url.endswith("/mission/studio/vision/faces") else None)
            page.goto(origin + "/mission/ollama", wait_until="domcontentloaded")
            button = page.locator("#smi-face-detect-button")
            button.wait_for(state="attached")
            assert button.is_hidden(), "No image should hide the preview action"

            page.locator("#image-input").set_input_files({
                "name": "private-still.png", "mimeType": "image/png", "buffer": _png_bytes()
            })
            page.locator("#image-preview").wait_for(state="visible")
            assert len(posts) == 0, "Image selection must never upload to face detector"
            assert len(analysed) == 0

            button.click()
            locked = page.locator("#smi-face-detect-status")
            page.wait_for_function(
                "() => document.querySelector('#smi-face-detect-status')?.textContent.includes('locked')"
            )
            assert len(posts) == 1
            assert len(analysed) == 0

            os.environ["OAP_SMI_FACE_DETECTION_ENABLED"] = "true"
            button.click()
            page.wait_for_function(
                "() => document.querySelector('#smi-face-detect-status')?.textContent.includes('1 face(s) detected')"
            )
            text = locked.inner_text()
            assert "20, 15, 40, 40" in text, text
            assert "not identity proof" in text
            assert len(posts) == 2
            assert len(analysed) == 1

            # The chat Stop control can be hidden while chat is idle; its
            # listener must still clear a completed face result.
            page.locator("#stop-button").dispatch_event("click")
            assert locked.inner_text() == ""
            assert len(posts) == 2

            # Unlike chat Stop, the face action exposes its own real, visible
            # cancellation affordance while the one-frame request is pending.
            delay_detection[0] = True
            button.click()
            page.wait_for_function(
                "() => document.querySelector('#smi-face-detect-button')?.textContent.includes('Cancel detection')"
            )
            button.click()
            assert "cancelled in this browser" in locked.inner_text()
            page.wait_for_timeout(850)
            assert "cancelled in this browser" in locked.inner_text()
            assert len(posts) <= 3

            page.locator("#remove-image").click()
            assert locked.inner_text() == ""
            assert button.is_hidden()

            print("SMI_VISION_BROWSER_EXPLICIT_CAPTURE=PASS")
            print("SMI_VISION_DEFAULT_LOCK=PASS")
            print("SMI_VISION_FOUNDER_SERVER_HANDOFF=PASS")
            print("SMI_VISION_STOP_REMOVE_CLEAR=PASS")
            context.close()
            browser.close()
    finally:
        os.environ.pop("OAP_SMI_FACE_DETECTION_ENABLED", None)
        server.shutdown()
        server_thread.join(timeout=2)


if __name__ == "__main__":
    main()
