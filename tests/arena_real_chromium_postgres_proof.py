"""Real Chromium acceptance for OAP Arena rooms and local rule engines.

Connect4 and Dot use real Flask plus disposable PostgreSQL. Chess and Ludo then
run through their real local Flask/session/browser flows on the same CI runner.
Never connects to production; no game move endpoint or browser action is mocked.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import arena_chess_chromium_proof
import arena_ludo_chromium_proof
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import postgres_db, web_security

BASE = "http://127.0.0.1:8768"


def prepare():
    database = os.environ.get("OAP_PRIMARY_DATABASE_URL", "")
    assert database.startswith("postgresql://") and "127.0.0.1" in database, (
        "Only the disposable localhost CI database is authorized."
    )
    base = postgres_db.init_postgres(assume_yes=True)
    assert base["initialized"] is True, "Ephemeral base schema must be complete"
    migrations = (
        ROOT / "migrations/0008_oap_arena_multiplayer_rooms.sql",
        ROOT / "migrations/0010_oap_arena_oware_room.sql",
        ROOT / "migrations/0012_oap_civilization_events.sql",
    )
    with postgres_db.connect() as connection:
        for path in migrations:
            for sql in path.read_text().split(";"):
                if sql.strip():
                    connection.execute(sql)
        connection.commit()
    app_module.app.config.update(
        TESTING=True, SECRET_KEY="arena-disposable-chromium-ci",
        SESSION_COOKIE_SECURE=False,
    )
    web_security.PUBLIC_WRITE_LIMITER.reset()


def prove_civilization_event_transaction_atomicity():
    """Prove event rows obey the caller's real PostgreSQL commit boundary."""
    from mission_control import civilization_events

    room_id = "00000000-0000-0000-0000-000000000777"
    state = {
        "status": "completed",
        "result": "checkmate",
        "winner": "White",
        "checkpoint": "a" * 64,
    }
    with postgres_db.connect() as connection:
        civilization_events.append_match_finished(
            connection,
            room_id=room_id,
            request_id="rollback-proof",
            game_state=state,
            revision=7,
        )
        connection.rollback()
    with postgres_db.connect() as connection:
        row = connection.execute(
            "SELECT event_id FROM oap_civilization_events WHERE entity_id=%s",
            (room_id,),
        ).fetchone()
        assert row is None, "Rolled-back heartbeat must not survive"

    with postgres_db.connect() as connection:
        event_id = civilization_events.append_match_finished(
            connection,
            room_id=room_id,
            request_id="commit-proof",
            game_state=state,
            revision=7,
        )
        connection.commit()
    with postgres_db.connect() as connection:
        row = connection.execute(
            """SELECT event_id,event_type,causation_id,payload
               FROM oap_civilization_events WHERE entity_id=%s""",
            (room_id,),
        ).fetchone()
        assert row is not None
        assert str(row[0]) == event_id
        assert row[1] == "MATCH_FINISHED"
        assert row[2] == "commit-proof"
        assert row[3]["result"] == "checkmate"
        connection.execute(
            "DELETE FROM oap_civilization_events WHERE entity_id=%s",
            (room_id,),
        )
        connection.commit()
    print("ARENA_CIVILIZATION_EVENT_ATOMICITY_PASS")


def assert_layout(page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= window.innerWidth + 2"
    ), "Horizontal screen overflow"


def play_two_seats(browser, game, host_viewport, guest_viewport):
    web_security.PUBLIC_WRITE_LIMITER.reset()
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
    if game == "connect4":
        rejected = host.evaluate(
            """async () => {
                const csrf = document.querySelector('meta[name="oap-csrf-token"]').content;
                const response = await fetch('/arena/rooms/create', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-OAP-CSRF': csrf},
                    body: JSON.stringify({game_key:'unknown-game',host_name:'Rejected Room',capacity:2})
                });
                return {status:response.status, result:await response.json()};
            }"""
        )
        assert rejected["status"] == 400, rejected
        assert rejected["result"]["error"]["code"] == "arena_room_game_invalid"

    host.locator("[data-host]").fill("Alpha " + game)
    host.locator("[data-create]").click()
    match_selector = "[data-room]" if game == "connect4" else "[data-match]"
    expect(host.locator(match_selector)).to_be_visible()
    expect(host.locator("[data-create]")).to_be_hidden()
    room_code = host.locator("[data-code]").inner_text()
    assert len(room_code) == 6
    expect(host.locator("[data-token]")).not_to_be_empty()

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
    # The server commits a real move, but the browser loses the acknowledgement.
    # Also interrupt its first recovery read. No second move is allowed until
    # a subsequent explicit server read-back confirms the committed revision.
    action_url = "/arena/rooms/connect4/action" if game == "connect4" else "/arena/rooms/dot/action"
    def lost_ack(route):
        actual = route.fetch()
        assert actual.status == 200, actual.status
        route.fulfill(
            status=503, content_type="application/json",
            body='{"error":{"code":"test_ack_lost"}}',
        )
    host.route("**" + action_url, lost_ack, times=1)
    host.route(
        "**/arena/rooms/state",
        lambda route: route.fulfill(
            status=503, content_type="application/json",
            body='{"error":{"code":"test_refresh_unavailable"}}',
        ),
        times=1,
    )
    first_control = "[data-columns] button" if game == "connect4" else "[data-edges] button:not([disabled])"
    host.locator(first_control).first.click()
    expect(host.locator("[data-error]")).to_contain_text("test_refresh_unavailable")
    expect(host.locator("[data-stop]")).to_be_disabled()
    if game == "connect4":
        assert all(button.is_disabled() for button in host.locator("[data-columns] button").all())
    else:
        assert all(button.is_disabled() for button in host.locator("[data-edges] button").all())
    # The server committed exactly one move. Read-back restores the truthful
    # revision and confirms that the other player owns the next turn.
    host.locator("[data-refresh]").click()
    expect(host.locator("[data-revision]")).to_have_text("1")
    assert host.locator("[data-stop]").is_enabled()

    # Real authenticated browser CSRF/room membership requests from two sessions.
    if game == "connect4":
        second = "[data-columns] button"
        guest.locator("[data-refresh]").click()
        expect(guest.locator("[data-revision]")).to_have_text("1")
        guest.locator(second).nth(1).click()
        expect(guest.locator("[data-revision]")).to_have_text("2")
        host.locator("[data-refresh]").click()
        expect(host.locator("[data-revision]")).to_have_text("2")
    else:
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



def play_added_room(browser, game, host_viewport, guest_viewport):
    web_security.PUBLIC_WRITE_LIMITER.reset()
    host_context = browser.new_context(viewport=host_viewport)
    guest_context = browser.new_context(viewport=guest_viewport)
    host, guest = host_context.new_page(), guest_context.new_page()
    errors = []
    host.on("pageerror", lambda e: errors.append("host: " + str(e)))
    guest.on("pageerror", lambda e: errors.append("guest: " + str(e)))
    route = "/arena/ludo/room" if game == "ludo" else "/arena/oware/room"
    host.goto(BASE + route, wait_until="domcontentloaded")
    guest.goto(BASE + route, wait_until="domcontentloaded")
    assert_layout(host); assert_layout(guest)

    host.locator("[data-host]").fill("Alpha " + game)
    host.locator("[data-create]").click()
    expect(host.locator("[data-room]")).to_be_visible()
    room_code = host.locator("[data-code]").inner_text()
    assert len(room_code) == 6
    expect(host.locator("[data-token]")).not_to_be_empty()

    guest.locator("[data-join-code]").fill(room_code)
    guest.locator("[data-guest]").fill("Bravo " + game)
    guest.locator("[data-join]").click()
    expect(guest.locator("[data-room]")).to_be_visible()
    expect(guest.locator("[data-status]")).to_have_text("ACTIVE")

    host.locator("[data-refresh]").click()
    expect(host.locator("[data-status]")).to_have_text("ACTIVE")
    if game == "ludo":
        host.locator("[data-roll]").click()
    else:
        host.locator("[data-pits] button:not([disabled])").first.click()
    expect(host.locator("[data-revision]")).to_have_text("1")

    guest.locator("[data-refresh]").click()
    expect(guest.locator("[data-revision]")).to_have_text("1")
    host.locator("[data-stop]").click()
    expect(host.locator("[data-status]")).to_have_text("STOPPED")
    guest.locator("[data-refresh]").click()
    expect(guest.locator("[data-status]")).to_have_text("STOPPED")
    assert host.locator("[data-stop]").is_disabled()
    assert guest.locator("[data-stop]").is_disabled()
    assert not errors, errors
    print("ARENA_REAL_CHROMIUM_POSTGRES_PASS", game)
    host_context.close(); guest_context.close()


def play_final_room(browser, game, host_viewport, guest_viewport):
    web_security.PUBLIC_WRITE_LIMITER.reset()
    host_context = browser.new_context(viewport=host_viewport)
    guest_context = browser.new_context(viewport=guest_viewport)
    host, guest = host_context.new_page(), guest_context.new_page()
    errors = []
    host.on("pageerror", lambda e: errors.append("host: " + str(e)))
    guest.on("pageerror", lambda e: errors.append("guest: " + str(e)))
    route = "/arena/iq/room" if game == "iq" else "/arena/route-empire/room"
    host.goto(BASE + route, wait_until="domcontentloaded")
    guest.goto(BASE + route, wait_until="domcontentloaded")
    assert_layout(host); assert_layout(guest)

    host.locator("[data-host]").fill("Alpha " + game)
    host.locator("[data-create]").click()
    expect(host.locator("[data-room]")).to_be_visible()
    room_code = host.locator("[data-code]").inner_text()
    assert len(room_code) == 6

    guest.locator("[data-join-code]").fill(room_code)
    guest.locator("[data-guest]").fill("Bravo " + game)
    guest.locator("[data-join]").click()
    expect(guest.locator("[data-room]")).to_be_visible()
    expect(guest.locator("[data-status]")).to_have_text("ACTIVE")
    host.locator("[data-refresh]").click()
    expect(host.locator("[data-status]")).to_have_text("ACTIVE")

    if game == "iq":
        expect(host.locator("[data-choices] button").first).to_be_enabled()
        host.locator("[data-choices] button").first.click()
        expect(host.locator("[data-revision]")).to_have_text("1")
        expect(host.locator("[data-wait]")).to_contain_text("Answer locked")
        guest.locator("[data-refresh]").click()
        expect(guest.locator("[data-revision]")).to_have_text("1")
        expect(guest.locator("[data-choices] button").first).to_be_enabled()
        guest.locator("[data-choices] button").nth(1).click()
        expect(guest.locator("[data-revision]")).to_have_text("2")
        host.locator("[data-refresh]").click()
        expect(host.locator("[data-revision]")).to_have_text("2")
        expect(host.locator("[data-progress]")).to_contain_text("Question 2")
    else:
        expect(host.locator("[data-nodes] button").first).to_be_enabled()
        host.locator("[data-nodes] button").first.click()
        expect(host.locator("[data-revision]")).to_have_text("1")
        host.locator("[data-end-turn]").click()
        expect(host.locator("[data-revision]")).to_have_text("2")
        guest.locator("[data-refresh]").click()
        expect(guest.locator("[data-revision]")).to_have_text("2")
        expect(guest.locator("[data-nodes] button").filter(has_text="Claim").nth(1)).to_be_enabled()
        guest.locator("[data-nodes] button").filter(has_text="Claim").nth(1).click()
        expect(guest.locator("[data-revision]")).to_have_text("3")
        host.locator("[data-refresh]").click()
        expect(host.locator("[data-revision]")).to_have_text("3")

    host.locator("[data-stop]").click()
    expect(host.locator("[data-status]")).to_have_text("STOPPED")
    guest.locator("[data-refresh]").click()
    expect(guest.locator("[data-status]")).to_have_text("STOPPED")
    assert not errors, errors
    print("ARENA_REAL_CHROMIUM_POSTGRES_PASS", game)
    host_context.close(); guest_context.close()

def main():
    prepare()
    prove_civilization_event_transaction_atomicity()
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
            play_added_room(browser, "ludo", mobile, desktop)
            play_added_room(browser, "oware", desktop, mobile)
            play_final_room(browser, "iq", mobile, desktop)
            play_final_room(browser, "route-empire", desktop, mobile)
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
    arena_chess_chromium_proof.main()
    arena_ludo_chromium_proof.main()
