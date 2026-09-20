"""Chromium evidence of actual Founder UI/browser wiring with LOCAL fake identity/provider.

This is NOT a test of the real Founder password, production AI, DB or Android
physical device. Run separately: python tests/browser_founder_e2e.py
"""
from __future__ import annotations

import os
import threading

os.environ["NEON_AUTH_BASE_URL"] = "https://example.neonauth.test/neondb/auth"
os.environ["OAP_HUMAN_AUTHORITY_EMAIL"] = "founder@example.test"
os.environ["OAP_AUTH_REQUIRED"] = "true"

import app as oap  # noqa: E402
from mission_control import neon_auth, smi_chat_runtime, status  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

AUTH_COOKIE = "better-auth.session_token"
TEST_PASSWORD = "local-test-password-not-a-founder-secret"
received: list[dict] = []
stop_release = threading.Event()


def mock_sign_in(email: str, password: str) -> neon_auth.AuthResult:
    if email != "founder@example.test" or password != TEST_PASSWORD:
        return neon_auth.AuthResult(status_code=401, payload={"error": "invalid"})
    return neon_auth.AuthResult(
        status_code=200,
        payload={"user": {"id": "11111111-1111-4111-8111-111111111111"}},
        set_cookie_headers=(
            AUTH_COOKIE + "=local-browser-fixture; Path=/; Secure; HttpOnly; SameSite=Lax",
        ),
    )


def mock_get_session(cookie_header: str) -> neon_auth.AuthResult:
    if AUTH_COOKIE + "=local-browser-fixture" not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "local-browser-test"},
            "user": {
                "id": "11111111-1111-4111-8111-111111111111",
                "name": "Browser test Founder",
                "email": "founder@example.test",
                "emailVerified": True,
            },
        },
    )


def mock_chat_events(
    message, identity_id, display_name, conversation_id, image_data, attachment,
    **kwargs,
):
    received.append({"message": message, "identity": identity_id,
                     "attachment": attachment, "image": image_data})
    if message == "Stop stream":
        yield {"type": "delta", "delta": "partial fixture text"}
        stop_release.wait(8)
        yield {"type": "complete", "result": {
            "response": "THIS STOPPED COMPLETION MUST NEVER SHOW",
            "conversation_id": "stopped-test",
        }}
    else:
        yield {"type": "delta", "delta": "Fixture processed attachment"}
        yield {"type": "complete", "result": {
            "response": "Fixture processed attachment",
            "conversation_id": "browser-test",
            "task_type": "mocked-browser-stream",
            "signal_level": "test-only",
        }}


def assert_in_viewport(page, selector: str):
    element = page.locator(selector)
    assert element.count() == 1
    box = element.bounding_box()
    assert box is not None, selector + " is hidden"
    width = page.evaluate("window.innerWidth")
    assert box["x"] >= -2 and box["x"] + box["width"] <= width + 2, (
        selector, box, width
    )


def test_founder_browser(page, origin):
    page.goto(origin + "/auth?next=/mission/ollama")
    password = page.locator('input[name="password"]')
    assert password.count() == 1
    assert password.get_attribute("type") == "password"
    assert page.locator('input[name="email"]').count() == 0
    assert "enter_my_world_wallpaper.png" in page.locator(".grid").evaluate(
        "(el) => getComputedStyle(el).backgroundImage"
    )
    assert_in_viewport(page, 'button[type="submit"]')

    password.fill("not-the-test-password")
    page.locator('button[type="submit"]').click()
    assert "Private password not recognised" in page.locator("body").inner_text()
    assert page.locator("#plus-button").count() == 0

    page.locator('input[name="password"]').fill(TEST_PASSWORD)
    page.locator('button[type="submit"]').click()
    page.wait_for_url("**/mission/ollama")
    page.locator("#plus-button").wait_for(state="visible")
    assert not page.locator("body").evaluate(
        "(el) => el.classList.contains('smi-command-open')"
    ), "Command Centre must not cover the chat on entry"
    assert page.locator("#send").is_visible()

    page.goto(origin + "/mission/oap-lab")
    page.locator("h1").get_by_text("OAP Lab").wait_for()
    assert page.locator("body").get_attribute("class") != "public"
    page.goto(origin + "/mission/ollama")

    plus = page.locator("#plus-button")
    plus.click()
    assert plus.get_attribute("aria-expanded") == "true"
    assert page.locator("#attach-menu").is_visible()
    page.keyboard.press("Escape")
    assert plus.get_attribute("aria-expanded") == "false"
    assert plus.evaluate("(el) => document.activeElement===el")

    plus.click()
    with page.expect_file_chooser() as picked:
        page.locator("#file-button").click()
    picked.value.set_files({
        "name": "local-fixture.txt",
        "mimeType": "text/plain",
        "buffer": b"fixture file content",
    })
    page.locator("#media-preview.show").wait_for(state="visible")
    assert "local-fixture.txt" in page.locator("#media-preview").inner_text()
    assert plus.get_attribute("aria-expanded") == "false"
    page.locator("#message").fill("Examine attached note")
    page.locator("#send").click()
    page.locator(".msg.assistant").filter(
        has_text="Fixture processed attachment"
    ).wait_for(state="visible")
    assert any(
        x["message"] == "Examine attached note"
        and x["attachment"] and x["attachment"]["name"] == "local-fixture.txt"
        and x["attachment"]["kind"] == "document"
        and "Zml4dHVyZSBmaWxlIGNvbnRlbnQ=" in x["attachment"]["data"]
        for x in received
    ), "A browser-chosen file must reach the real Flask stream route"

    page.locator("#message").fill("Stop stream")
    page.locator("#send").click()
    page.locator(".msg.assistant").filter(
        has_text="partial fixture text"
    ).wait_for(state="visible")
    page.locator("#stop-button").click()
    assert "Response stopped by Human Authority" in page.locator("#status").inner_text()
    stop_release.set()
    page.wait_for_timeout(250)
    assert "THIS STOPPED COMPLETION MUST NEVER SHOW" not in page.locator(
        "#messages"
    ).inner_text()
    print("FOUNDER_CHROMIUM_UI_FLOW_PASS")


def test_mobile_browser(context, origin):
    page = context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(origin + "/auth?next=/mission/ollama")
    assert_in_viewport(page, ".card.private")
    assert_in_viewport(page, 'button[type="submit"]')
    assert page.locator(".grid").evaluate(
        "(el) => getComputedStyle(el).backgroundImage.includes('enter_my_world_wallpaper.png')"
    )
    page.set_viewport_size({"width": 390, "height": 480})
    page.locator('input[name="password"]').focus()
    assert_in_viewport(page, ".card.private")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2")
    assert page.locator("button[type=submit]").evaluate(
        "(el) => getComputedStyle(el).minHeight !== '0px'"
    )
    print("FOUNDER_CHROMIUM_NARROW_VIEW_PASS")
    page.close()


def main():
    oap.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    neon_auth.sign_in = mock_sign_in
    neon_auth.get_session = mock_get_session
    smi_chat_runtime.chat_events = mock_chat_events
    smi_chat_runtime.list_conversations = lambda _identity: []
    status._probe_ollama = lambda: False
    server = make_server("127.0.0.1", 0, oap.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = "http://127.0.0.1:" + str(server.server_port)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()
                page.set_default_timeout(12000)
                test_founder_browser(page, origin)
                test_mobile_browser(context, origin)
            finally:
                browser.close()
    finally:
        stop_release.set()
        server.shutdown()
        thread.join(timeout=4)


if __name__ == "__main__":
    main()
