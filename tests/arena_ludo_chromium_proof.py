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
    values = iter([5, 0, 1])
    original_randbelow = ludo.secrets.randbelow
    ludo.secrets.randbelow = lambda _: next(values)
    context = browser.new_context(viewport={"width": 393, "height": 852})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    try:
        page.goto(BASE + "/arena/ludo", wait_until="domcontentloaded")
        page.locator("[data-start]").press("Enter")
        expect(page.locator("[data-menu]")).to_be_hidden()
        expect(page.locator("[data-game]")).to_be_visible()
        expect(page.locator("[data-roll]")).to_be_focused()
        expect(page.locator("[data-turn]")).to_have_text("Player One")

        page.locator("[data-roll]").click()
        expect(page.locator("[data-roll-value]")).to_have_text("6")
        piece = page.locator('[data-board] [data-piece="p1-1"]')
        expect(piece).to_be_enabled()
        piece.click()
        expect(page.locator("[data-turn]")).to_have_text("Player One")
        expect(page.locator('[data-board] [data-piece="p1-1"]')).to_have_attribute("aria-label", "Player One, piece 1, Track 1")
        expect(page.locator("[data-roll]")).to_be_enabled()

        page.locator("[data-roll]").click()
        expect(page.locator("[data-roll-value]")).to_have_text("1")
        page.locator('[data-board] [data-piece="p1-1"]').click()
        expect(page.locator("[data-turn]")).to_have_text("Player Two")
        expect(page.locator('[data-board] [data-piece="p1-1"]')).to_have_attribute("aria-label", "Player One, piece 1, Track 2")

        page.locator("[data-roll]").click()
        expect(page.locator("[data-roll-value]")).to_have_text("2")
        expect(page.locator("[data-turn]")).to_have_text("Player One")
        expect(page.locator("[data-feedback]")).to_have_text("No legal move.")

        page.locator("[data-stop]").press("Enter")
        expect(page.locator("[data-status]")).to_have_text("stopped")
        expect(page.locator("[data-feedback]")).to_have_text("Match stopped.")
        expect(page.locator("[data-start]")).to_be_focused()
        assert not errors, errors
    finally:
        ludo.secrets.randbelow = original_randbelow
        context.close()


def prove_crowded_square(browser):
    context = browser.new_context(viewport={"width": 320, "height": 720})
    page = context.new_page()
    try:
        page.goto(BASE + "/arena/ludo", wait_until="domcontentloaded")
        page.evaluate("""() => {
            const root = document.querySelector("[data-game]");
            const board = root.querySelector("[data-board]");
            board.replaceChildren(root.querySelector("[data-roll]"));
            const renderBoard = window.OAPLudoBoard.mount(root);
            const players = ["Player One", "Player Two"].map((name, seat) => ({
                name,
                finished: 0,
                pieces: Array.from({length: 4}, (_, index) => ({
                    id: `p${seat + 1}-${index + 1}`,
                    zone: "track",
                    track_square: 0,
                })),
            }));
            renderBoard({
                players,
                pending_roll: 1,
                movable_piece_ids: players[1].pieces.map(piece => piece.id),
            }, undefined, true);
        }""")
        stack = page.get_by_role("group", name="8 pieces on this square")
        expect(stack).to_be_visible()
        expect(stack.get_by_role("button")).to_have_count(4)
        expect(stack.locator("button:enabled")).to_have_count(4)
        expect(page.locator("[data-legal] button:enabled")).to_have_count(4)
        assert stack.evaluate("""square => {
            const tile = square.getBoundingClientRect();
            return Array.from(square.querySelectorAll("button")).every(button => {
                const piece = button.getBoundingClientRect();
                return piece.width > 0 && piece.height > 0 &&
                    piece.left >= tile.left && piece.right <= tile.right + 1 &&
                    piece.top >= tile.top && piece.bottom <= tile.bottom + 1;
            });
        }""")
    finally:
        context.close()


def prove_ludo_agent(browser):
    web_security.PUBLIC_WRITE_LIMITER.reset()
    values = iter([0, 5, 0])
    original_randbelow = ludo.secrets.randbelow
    ludo.secrets.randbelow = lambda _: next(values)
    context = browser.new_context(viewport={"width": 393, "height": 852})
    page = context.new_page()
    requests = []

    def fail_first_agent_request(route):
        requests.append(route.request.post_data_json["request_id"])
        if len(requests) == 1:
            route.fulfill(status=503, json={"error": {"code": "temporary_test_failure"}})
        else:
            route.continue_()

    page.route("**/arena/ludo/agent-turn", fail_first_agent_request)
    try:
        page.goto(BASE + "/arena/ludo", wait_until="domcontentloaded")
        page.get_by_text("Settings", exact=True).click()
        page.get_by_label("Opponent", exact=True).select_option("agent")
        page.locator("[data-start]").click()
        expect(page.locator("[data-roll]")).to_be_enabled()
        page.locator("[data-roll]").click()
        retry = page.get_by_role("button", name="Retry agent turn")
        expect(retry).to_be_visible()
        expect(page.locator("[data-roll]")).to_be_disabled()
        retry.click()
        piece = page.locator('[data-board] [data-piece="p2-1"]')
        expect(piece).to_have_attribute("aria-label", "Ludo Agent, piece 1, Track 15")
        expect(page.locator("[data-turn]")).to_have_text("Player One")
        assert len(requests) == 3 and requests[0] == requests[1] != requests[2]

        page.locator("[data-stop]").click()
        expect(page.locator("[data-status]")).to_have_text("stopped")
        expect(page.locator("[data-roll]")).to_be_disabled()
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
            prove_crowded_square(browser)
            prove_ludo_agent(browser)
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)

    print("ARENA_LUDO_REAL_CHROMIUM_PASS")


if __name__ == "__main__":
    main()
