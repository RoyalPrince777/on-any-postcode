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


def _png_bytes(color=(92, 122, 145)):
    stream = BytesIO()
    Image.new("RGB", (120, 100), color).save(stream, format="PNG")
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

    studio_face_detection.detect_faces_bounded = bounded_detector
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

            # A new image from the legacy camera picker (not #image-input)
            # invalidates previously completed face coordinates.
            delay_detection[0] = False
            button.click()
            page.wait_for_function(
                "() => document.querySelector('#smi-face-detect-status')?.textContent.includes('1 face(s) detected')"
            )
            camera_posts = len(posts)
            page.locator("#camera-input").set_input_files({
                "name": "second-camera.png", "mimeType": "image/png",
                "buffer": _png_bytes((44, 73, 112)),
            })
            page.wait_for_function(
                "() => document.querySelector('#preview-name')?.textContent === 'second-camera.png'"
            )
            page.wait_for_function(
                "() => document.querySelector('#smi-face-detect-status')?.textContent === ''"
            )
            assert len(posts) == camera_posts, "Camera file selection cannot upload to detector"

            # Studio's character-reference control writes previewImg.src
            # directly and does not fire a file input change. The actual
            # media controls must still clear results and not auto-post.
            button.click()
            page.wait_for_function(
                "() => document.querySelector('#smi-face-detect-status')?.textContent.includes('1 face(s) detected')"
            )
            reference_bytes = _png_bytes((116, 80, 65))
            reference_url = "data:image/png;base64," + base64.b64encode(
                reference_bytes
            ).decode("ascii")
            page.evaluate(
                """(source) => {
                    const card = document.createElement('article');
                    card.className = 'smi-studio-artifact';
                    const image = document.createElement('img');
                    image.className = 'smi-studio-image';
                    image.src = source;
                    card.append(image);
                    document.getElementById('messages').append(card);
                }""",
                reference_url,
            )
            reference = page.locator(".smi-use-character-reference").last
            reference.wait_for(state="attached")
            before_reference = len(posts)
            reference.click()
            page.wait_for_function(
                "() => document.querySelector('#preview-name')?.textContent === 'Studio character reference'"
            )
            page.wait_for_function(
                "() => document.querySelector('#smi-face-detect-status')?.textContent === ''"
            )
            assert len(posts) == before_reference, "Studio reference must never silently upload"

            # Replacing a frame while its remote request is pending must
            # invalidate the late result even if the server already started.
            delay_detection[0] = True
            button.click()
            page.wait_for_function(
                "() => document.querySelector('#smi-face-detect-button')?.textContent.includes('Cancel detection')"
            )
            page.locator("#camera-input").set_input_files({
                "name": "third-camera.png", "mimeType": "image/png",
                "buffer": _png_bytes((17, 126, 91)),
            })
            page.wait_for_function(
                "() => document.querySelector('#preview-name')?.textContent === 'third-camera.png'"
            )
            page.wait_for_timeout(850)
            assert locked.inner_text() == "", "A superseded request exposed a stale result"
            assert "Cancel detection" not in button.inner_text()
            print("SMI_VISION_CAMERA_REFERENCE_STALE_CLEAR=PASS")
            print("SMI_VISION_LATE_RESULT_SUPPRESSED=PASS")

            page.locator("#remove-image").click()
            assert locked.inner_text() == ""
            assert button.is_hidden()

            # Browser-backed synthetic permission timing only: verify that
            # End, Human STOP and pagehide release camera+mic tracks. This
            # intentionally does NOT claim physical Android hardware proof.
            page.evaluate("""
            () => {
              const proof = {stopped: 0, requests: []};
              proof.makeStream = () => {
                const stream = new MediaStream();
                const tracks = ["video", "audio"].map(kind => ({
                  kind, enabled: true, stop: () => { proof.stopped += 1; }
                }));
                stream.getTracks = () => tracks;
                stream.getVideoTracks = () => [tracks[0]];
                stream.getAudioTracks = () => [tracks[1]];
                return stream;
              };
              window.__visionPermissionProof = proof;
              const devices = navigator.mediaDevices || {};
              devices.getUserMedia = () => new Promise(resolve => proof.requests.push(resolve));
              if (!navigator.mediaDevices) {
                Object.defineProperty(navigator, "mediaDevices", {configurable: true, value: devices});
              }
              document.querySelector("#faceup-video").play = () => Promise.resolve();
            }
            """)

            # Permission is granted *after* closing the still-pending drawer:
            # both tracks must be immediately stopped, never exposed as active.
            page.locator("#faceup-button").click()
            page.wait_for_function("() => window.__visionPermissionProof.requests.length === 1")
            page.locator("#faceup-close").click()
            page.evaluate(
                "() => window.__visionPermissionProof.requests.shift()(window.__visionPermissionProof.makeStream())"
            )
            page.wait_for_function("() => window.__visionPermissionProof.stopped === 2")
            assert page.locator("#faceup-panel").is_hidden()
            assert page.locator("#faceup-video").evaluate("(v) => v.srcObject === null")

            # When a valid session is running, SMI's single canonical Stop
            # must terminate camera and microphone, not merely chat output.
            page.locator("#faceup-button").click()
            page.wait_for_function("() => window.__visionPermissionProof.requests.length === 1")
            page.evaluate(
                "() => window.__visionPermissionProof.requests.shift()(window.__visionPermissionProof.makeStream())"
            )
            page.wait_for_function(
                "() => document.querySelector('#faceup-status')?.textContent.includes('session active')"
            )
            page.locator("#stop-button").dispatch_event("click")
            page.wait_for_function("() => window.__visionPermissionProof.stopped === 4")
            assert page.locator("#faceup-panel").is_hidden()
            assert page.locator("#faceup-video").evaluate("(v) => v.srcObject === null")

            # Closing the browser while a permission prompt is pending must
            # also invalidate and stop a late-resolved camera/mic stream.
            page.locator("#faceup-button").click()
            page.wait_for_function("() => window.__visionPermissionProof.requests.length === 1")
            page.evaluate("() => window.dispatchEvent(new Event('pagehide'))")
            page.evaluate(
                "() => window.__visionPermissionProof.requests.shift()(window.__visionPermissionProof.makeStream())"
            )
            page.wait_for_function("() => window.__visionPermissionProof.stopped === 6")
            assert page.locator("#faceup-panel").is_hidden()
            # Repeat after back-cache restoration: cleanup must not be one-shot.
            page.evaluate("() => window.dispatchEvent(new Event('pageshow'))")
            page.locator("#faceup-button").click()
            page.wait_for_function("() => window.__visionPermissionProof.requests.length === 1")
            page.evaluate("() => window.dispatchEvent(new Event('pagehide'))")
            page.evaluate(
                "() => window.__visionPermissionProof.requests.shift()(window.__visionPermissionProof.makeStream())"
            )
            page.wait_for_function("() => window.__visionPermissionProof.stopped === 8")
            assert page.locator("#faceup-panel").is_hidden()
            print("SMI_FACEUP_REPEAT_PAGEHIDE_RELEASED=PASS")
            page.locator("#faceup-button").click()
            page.wait_for_function("() => window.__visionPermissionProof.requests.length === 1")
            page.evaluate("""() => {
                Object.defineProperty(document, 'hidden', {configurable: true, value: true});
                document.dispatchEvent(new Event('visibilitychange'));
                delete document.hidden;
                window.__visionPermissionProof.requests.shift()(window.__visionPermissionProof.makeStream());
            }""")
            page.wait_for_function("() => window.__visionPermissionProof.stopped === 10")
            assert page.locator("#faceup-panel").is_hidden()
            print("SMI_FACEUP_HIDDEN_PERMISSION_REVOKED=PASS")
            print("SMI_FACEUP_PERMISSION_RACE_CLOSED=PASS")
            print("SMI_FACEUP_CAMERA_MIC_STOP_RELEASED=PASS")

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
