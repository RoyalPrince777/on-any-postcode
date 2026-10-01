"""Real Chromium acceptance for OAP Arena Ludo four-piece flow.

Uses the real Flask routes, session and Ludo engine. Only the local CI die source
is made deterministic so the browser path is repeatable. Never production.
"""
from __future__ import annotations

import threading

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import ludo, web_security

BASE = "http://127.0.0.1:8770"


def prepare():
    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="arena-ludo-browser-ci",
        SESSION_COOKIE_SECURE=False,
    )
    web_security.PUBLIC_WRITE_LIMITER.reset()


def prove_ludo(browser):
    values = iter([5, 0])
    original_randbelow = ludo.secrets.randbelow
    ludo.secrets.randbelow = lambda _: next(values)
    context = browser.new_context(viewport={"width": 393, "height": 852})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    try:
        page.goto(BASE + "/arena/ludo", wait_until="domcontentloaded")
        page.locator("[data-start]").click()
        expect(page.locator("[data-game]")).to_be_visible()
        expect(page.locator("[data-turn]")).to_have_text("Player One")

        page.locator("[data-roll]").click()
        expect(page.locator("[data-roll-value]")).to_have_text("6")
        piece = page.locator('[data-piece="p1-1"]')
        expect(piece).to_be_enabled()
        piece.click()
        expect(page.locator("[data-turn]")).to_have_text("Player One")
        expect(page.locator('[data-piece="p1-1"]')).to_contain_text("Track 1")
        expect(page.locator("[data-roll]")).to_be_enabled()

        page.locator("[data-roll]").click()
        expect(page.locator("[data-roll-value]")).to_have_text("1")
        page.locator('[data-piece="p1-1"]').click()
        expect(page.locator("[data-turn]")).to_have_text("Player Two")
        expect(page.locator('[data-piece="p1-1"]')).to_contain_text("Track 2")

        page.locator("[data-stop]").click()
        expect(page.locator("[data-status]")).to_have_text("stopped")
        expect(page.locator("[data-feedback]")).to_have_text("Match stopped.")
        assert not errors, errors
    finally:
        ludo.secrets.randbelow = original_randbelow
        context.close()


def main():
    prepare()
    server = make_server("127.0.0.1", 8770, app_module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            prove_ludo(browser)
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)

    print("ARENA_LUDO_REAL_CHROMIUM_PASS")


if __name__ == "__main__":
    main()
