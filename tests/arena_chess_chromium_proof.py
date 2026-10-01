"""Real Chromium acceptance for bounded OAP Arena Chess feedback.

Uses the real Flask routes and chess engine. The stalemate case seeds only the
server-side session position; the decisive move and UI response are real.
Never connects to production.
"""
from __future__ import annotations

import threading

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import chess, web_security

BASE = "http://127.0.0.1:8769"


def prepare():
    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="arena-chess-browser-ci",
        SESSION_COOKIE_SECURE=False,
    )
    web_security.PUBLIC_WRITE_LIMITER.reset()


def move(page, source, target):
    page.locator("[data-source]").fill(source)
    page.locator("[data-target]").fill(target)
    page.locator("[data-move]").click()


def open_game(browser):
    context = browser.new_context(viewport={"width": 393, "height": 852})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(BASE + "/arena/chess", wait_until="domcontentloaded")
    page.locator("[data-start]").click()
    expect(page.locator("[data-game]")).to_be_visible()
    return context, page, errors


def prove_check(browser):
    context, page, errors = open_game(browser)
    move(page, "e2", "e3")
    move(page, "d7", "d5")
    move(page, "f1", "b5")
    expect(page.locator("[data-feedback]")).to_have_text("Check. Black must respond.")
    assert not errors, errors
    context.close()


def prove_checkmate(browser):
    context, page, errors = open_game(browser)
    move(page, "f2", "f3")
    move(page, "e7", "e5")
    move(page, "g2", "g4")
    move(page, "d8", "h4")
    expect(page.locator("[data-feedback]")).to_have_text("Checkmate. Winner: Black")
    expect(page.locator("[data-status]")).to_have_text("completed")
    assert not errors, errors
    context.close()


def prove_stalemate(browser):
    context, page, errors = open_game(browser)

    cookies = context.cookies(BASE)
    session_cookie = next(
        item for item in cookies
        if item["name"] == app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    )
    serializer = app_module.app.session_interface.get_signing_serializer(app_module.app)
    session_data = serializer.loads(session_cookie["value"])

    state = chess.new_game()
    state["board"] = {"a8": "bK", "c6": "wK", "b6": "wQ"}
    state["turn"] = "w"
    state["winner"] = None
    state["result"] = None
    state["check"] = False
    session_data[chess.SESSION_KEY] = chess._seal(state)

    context.add_cookies([{
        "name": session_cookie["name"],
        "value": serializer.dumps(session_data),
        "url": BASE,
    }])

    move(page, "b6", "c7")
    expect(page.locator("[data-feedback]")).to_have_text("Stalemate.")
    expect(page.locator("[data-status]")).to_have_text("completed")
    assert not errors, errors
    context.close()


def main():
    prepare()
    server = make_server("127.0.0.1", 8769, app_module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            prove_check(browser)
            prove_checkmate(browser)
            prove_stalemate(browser)
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)

    print("ARENA_CHESS_REAL_CHROMIUM_PASS")


if __name__ == "__main__":
    main()
