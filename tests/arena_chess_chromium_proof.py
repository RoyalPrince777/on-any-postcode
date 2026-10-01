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


def move(page, source, target, *, next_turn=None, completed=False):
    page.locator("[data-source]").fill(source)
    page.locator("[data-target]").fill(target)
    page.locator("[data-move]").click()
    if completed:
        expect(page.locator("[data-status]")).to_have_text("completed")
    elif next_turn is not None:
        expect(page.locator("[data-turn]")).to_have_text(next_turn)


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
    move(page, "e2", "e3", next_turn="Black")
    move(page, "d7", "d5", next_turn="White")
    move(page, "f1", "b5", next_turn="Black")
    expect(page.locator("[data-feedback]")).to_have_text("Check. Black must respond.")
    assert not errors, errors
    context.close()


def prove_checkmate(browser):
    context, page, errors = open_game(browser)
    move(page, "f2", "f3", next_turn="Black")
    move(page, "e7", "e5", next_turn="White")
    move(page, "g2", "g4", next_turn="Black")
    move(page, "d8", "h4", completed=True)
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

    move(page, "b6", "c7", completed=True)
    expect(page.locator("[data-feedback]")).to_have_text("Stalemate.")
    expect(page.locator("[data-status]")).to_have_text("completed")
    assert not errors, errors
    context.close()



def seed_state(context, state):
    cookies = context.cookies(BASE)
    session_cookie = next(
        item for item in cookies
        if item["name"] == app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    )
    serializer = app_module.app.session_interface.get_signing_serializer(app_module.app)
    session_data = serializer.loads(session_cookie["value"])
    session_data[chess.SESSION_KEY] = chess._seal(state)
    context.add_cookies([{
        "name": session_cookie["name"],
        "value": serializer.dumps(session_data),
        "url": BASE,
    }])


def prove_castling(browser):
    context, page, errors = open_game(browser)
    state = chess.new_game()
    state["board"] = {"e1": "wK", "h1": "wR", "e8": "bK", "a8": "bR"}
    state["turn"] = "w"
    state["castling"] = {"wK": True, "wQ": False, "bK": False, "bQ": True}
    state["en_passant"] = None
    state["position_counts"] = {}
    seed_state(context, state)

    move(page, "e1", "g1", next_turn="Black")
    expect(page.locator('[data-square="g1"]')).to_have_text("♔")
    expect(page.locator('[data-square="f1"]')).to_have_text("♖")
    assert not errors, errors
    context.close()


def prove_promotion(browser):
    context, page, errors = open_game(browser)
    state = chess.new_game()
    state["board"] = {"h1": "wK", "h8": "bK", "a7": "wP", "g8": "bR"}
    state["turn"] = "w"
    state["castling"] = {"wK": False, "wQ": False, "bK": False, "bQ": False}
    state["en_passant"] = None
    state["position_counts"] = {}
    seed_state(context, state)

    page.locator("[data-source]").fill("a7")
    page.locator("[data-target]").fill("a8")
    page.locator("[data-promotion]").select_option("Q")
    page.locator("[data-move]").click()
    expect(page.locator('[data-square="a8"]')).to_have_text("♕")
    expect(page.locator("[data-turn]")).to_have_text("Black")
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
            prove_castling(browser)
            prove_promotion(browser)
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)

    print("ARENA_CHESS_REAL_CHROMIUM_PASS")


if __name__ == "__main__":
    main()
