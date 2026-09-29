from __future__ import annotations

import os
import threading
import time

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import neon_auth, smi_chat_runtime, web_security

AUTH_ID = "11111111-1111-4111-8111-111111111111"
AUTH_COOKIE = "better-auth.session_token"
AUTH_VALUE = "verified-browser-session"
CSRF_VALUE = "browser-proof-csrf-token-value-1234567890"


def _fake_auth_session(cookie_header: str):
    if f"{AUTH_COOKIE}={AUTH_VALUE}" not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "browser-proof-session"},
            "user": {
                "id": AUTH_ID,
                "name": "OAP Founder",
                "email": "founder@example.test",
                "emailVerified": True,
            },
        },
    )


def _failed_chat_events(*_args, **_kwargs):
    yield {"type": "stage", "label": "Understand"}
    yield {
        "type": "error",
        "code": "provider_unavailable",
        "diagnostic_code": "provider_runtime_error",
        "message": "Inference backend unavailable. No completion was recorded.",
    }


def _prepare_app():
    os.environ["OAP_AUTH_REQUIRED"] = "true"
    os.environ["OAP_HUMAN_AUTHORITY_EMAIL"] = "founder@example.test"
    os.environ["NEON_AUTH_BASE_URL"] = "https://example.neonauth.test/neondb/auth"

    app_module.app.config.update(
        TESTING=True,
        SESSION_COOKIE_SECURE=False,
        SECRET_KEY="smi-browser-proof-secret",
    )

    neon_auth.get_session = _fake_auth_session
    smi_chat_runtime.chat_events = _failed_chat_events
    smi_chat_runtime.list_conversations = lambda *_args, **_kwargs: []
    smi_chat_runtime.health = lambda: {
        "checks": {
            "provider_key": False,
            "conversation_memory": True,
            "human_authority": True,
            "execution_locked": True,
        }
    }

    web_security.CHAT_BURST_LIMITER.reset()
    web_security.AUTH_BURST_LIMITER.reset()
    web_security.PUBLIC_WRITE_LIMITER.reset()


def _session_cookies():
    session_name = app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    with app_module.app.test_client() as client:
        client.set_cookie(AUTH_COOKIE, AUTH_VALUE)
        with client.session_transaction() as current_session:
            current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [AUTH_COOKIE]
            current_session[web_security.CSRF_SESSION_KEY] = CSRF_VALUE

        response = client.get("/mission/ollama")
        assert response.status_code == 200, response.status_code
        session_cookie = client.get_cookie(session_name)
        assert session_cookie is not None
        return session_name, session_cookie.value


def main():
    _prepare_app()
    session_name, session_value = _session_cookies()

    server = make_server("127.0.0.1", 8765, app_module.app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = "http://127.0.0.1:8765"

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
            page.add_init_script(
                """
                (() => {
                  window.__smiLegacyPaintSamples = [];
                  const selectors = [
                    '.navs', '.smi-hero', '.chat-head',
                    '.smi-dashboard-layer', '.smi-command-centre', '.smi-status-backdrop'
                  ];
                  const visible = el => {
                    if (!el) return false;
                    const style = getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style.display !== 'none' &&
                           style.visibility !== 'hidden' &&
                           Number(style.opacity || '1') > 0 &&
                           rect.width > 0 && rect.height > 0;
                  };
                  const sample = () => {
                    const states = selectors.map(sel => [sel, visible(document.querySelector(sel))]);
                    window.__smiLegacyPaintSamples.push(states);
                    if (window.__smiLegacyPaintSamples.length < 180) requestAnimationFrame(sample);
                  };
                  requestAnimationFrame(sample);

                  class FakeRecognition {
                    constructor(){
                      this.lang='en-GB';
                      this.interimResults=true;
                      this.continuous=false;
                      this.onstart=null; this.onend=null; this.onerror=null; this.onresult=null;
                    }
                    start(){ setTimeout(() => this.onstart && this.onstart(), 0); }
                    stop(){ setTimeout(() => this.onend && this.onend(), 0); }
                  }
                  window.SpeechRecognition = FakeRecognition;
                  window.webkitSpeechRecognition = FakeRecognition;
                })();
                """
            )

            page.goto(base_url + "/mission/ollama", wait_until="domcontentloaded")
            page.wait_for_timeout(900)

            assert page.url.endswith("/mission/ollama"), page.url

            live = page.locator("#live-character-toggle")
            live.wait_for(state="visible")
            box = live.bounding_box()
            assert box and box["width"] > 0 and box["height"] > 0
            assert live.evaluate("el => el.parentElement === document.body")
            assert live.evaluate("el => getComputedStyle(el).pointerEvents") != "none"

            live.click()
            page.wait_for_timeout(100)
            assert live.get_attribute("aria-pressed") == "true"

            flash_seen = page.evaluate(
                """
                () => window.__smiLegacyPaintSamples.some(sample =>
                  sample.some(([, visible]) => visible)
                )
                """
            )
            assert flash_seen is False

            assistant_before = page.locator(".msg.assistant").count()
            prompt = "browser recovery proof request"
            page.locator("#message").fill(prompt)
            page.locator("#send").click()

            page.wait_for_function(
                """p => {
                    const input = document.querySelector('#message');
                    return input &&
                           input.value === p &&
                           document.body.innerText.includes('Your request is preserved for retry.');
                }""",
                prompt,
            )

            assert page.locator("#message").input_value() == prompt
            assert page.locator("#send").is_enabled()
            assert page.locator("#plus-button").is_enabled()
            assert page.locator("#pause-button").is_enabled()
            assert page.locator("#stop-button").is_enabled()

            assistant_after = page.locator(".msg.assistant").count()
            assert assistant_after == assistant_before

            system_text = page.locator(".msg.system").all_inner_texts()
            assert any("request is preserved for retry" in text for text in system_text)
            assert not any("sk-" in text.lower() for text in system_text)

            print("SMI_CHROMIUM_ACCEPTANCE=PASS")
            print("LIVE_VISIBLE_CLICKABLE=PASS")
            print("NO_LEGACY_FLASH_SAMPLES=PASS")
            print("FAILED_REQUEST_RECOVERY=PASS")

            context.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
