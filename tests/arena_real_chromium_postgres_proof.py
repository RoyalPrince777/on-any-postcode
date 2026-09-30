"""Real Chromium + real Flask + disposable PostgreSQL acceptance for Arena rooms.

Never connects to production. The workflow supplies an ephemeral localhost CI DB.
No game endpoint, board state or browser action is mocked.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import postgres_db, web_security

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8768"


def prepare():
    database = os.environ.get("OAP_PRIMARY_DATABASE_URL", "")
    assert database.startswith("postgresql://") and "127.0.0.1" in database, (
        "Only the disposable localhost CI database is authorized."
    )
    migration = (ROOT / "migrations/0008_oap_arena_multiplayer_rooms.sql").read_text()
    with postgres_db.connect() as connection:
        for sql in migration.split(";"):
            if sql.strip():
                connection.execute(sql)
        connection.commit()
    app_module.app.config.update(
        TESTING=True, SECRET_KEY="arena-disposable-chromium-ci",
        SESSION_COOKIE_SECURE=False,
    )
    web_security.PUBLIC_WRITE_LIMITER.reset()


def assert_layout(page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= window.innerWidth + 2"
    ), "Horizontal screen overflow"


def play_two_seats(browser, game, host_viewport, guest_viewport):
    host_context = browser.new_context(viewport=host_viewport)
    guest_context = browser.new_context(viewport=guest_viewport)
    host, guest = host_context.new_page(), guest_context.new_page()
    errors = []
    host.on("pageerror", lambda e: errors.append("host: " + str(e)))
    guest.on("pageerror", lambda e: errors.append("guest: " + str(e)))
    route = "/arena/connect4/room" if game == "connect4" else "/arena/dot/room"
    host.goto(BASE + route, wait_until="domcontentloaded")
    guest.goto(BASE + route, wait_until="domcontentloaded")
    assert_layout(host)
    assert_layout(guest)

    host.locator("[data-host]").fill("Alpha " + game)
    host.locator("[data-create]").click()
    match_selector = "[data-room]" if game == "connect4" else "[data-match]"
    expect(host.locator(match_selector)).to_be_visible()
    expect(host.locator("[data-create]")).to_be_hidden()
    room_code = host.locator("[data-code]").inner_text()
    assert len(room_code) == 6
    assert host.locator("[data-token]").inner_text().strip()

    guest_code = "[data-join-code]" if game == "connect4" else "[data-code-input]"
    guest.locator(guest_code).fill(room_code)
    guest.locator("[data-guest]").fill("Bravo " + game)
    guest.locator("[data-join]").click()
    expect(guest.locator(match_selector)).to_be_visible()
    expect(guest.locator("[data-status]")).to_have_text("ACTIVE")

    host.locator("[data-refresh]").click()
    expect(host.locator("[data-status]")).to_have_text("ACTIVE")
    assert_layout(host)
    assert_layout(guest)
    # Real authenticated browser CSRF/room membership requests from two sessions.
    if game == "connect4":
        first, second = "[data-columns] button", "[data-columns] button"
        host.locator(first).first.click()
        expect(host.locator("[data-revision]")).to_have_text("1")
        guest.locator("[data-refresh]").click()
        expect(guest.locator("[data-revision]")).to_have_text("1")
        guest.locator(second).nth(1).click()
        expect(guest.locator("[data-revision]")).to_have_text("2")
        host.locator("[data-refresh]").click()
        expect(host.locator("[data-revision]")).to_have_text("2")
    else:
        host.locator("[data-edges] button:not([disabled])").first.click()
        expect(host.locator("[data-revision]")).to_have_text("1")
        guest.locator("[data-refresh]").click()
        expect(guest.locator("[data-revision]")).to_have_text("1")
        guest.locator("[data-edges] button:not([disabled])").first.click()
        expect(guest.locator("[data-revision]")).to_have_text("2")
        host.locator("[data-refresh]").click()
        expect(host.locator("[data-revision]")).to_have_text("2")

    host.locator("[data-stop]").click()
    expect(host.locator("[data-status]")).to_have_text("STOPPED")
    guest.locator("[data-refresh]").click()
    expect(guest.locator("[data-status]")).to_have_text("STOPPED")
    assert host.locator("[data-stop]").is_disabled()
    assert guest.locator("[data-stop]").is_disabled()
    assert not errors, errors
    print("ARENA_REAL_CHROMIUM_POSTGRES_PASS", game)
    host_context.close()
    guest_context.close()


def main():
    prepare()
    server = make_server("127.0.0.1", 8768, app_module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            mobile = {"width": 393, "height": 852}
            desktop = {"width": 1280, "height": 800}
            play_two_seats(browser, "connect4", mobile, desktop)
            play_two_seats(browser, "dot", desktop, mobile)
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
