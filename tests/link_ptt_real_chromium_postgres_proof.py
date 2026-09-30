"""Real Chromium + real Flask + disposable PostgreSQL proof for private live PTT.

The proof uses two authenticated browser contexts and real local WebRTC media.
It never connects to production. External TURN relay is intentionally substituted
with localhost ICE for this bounded browser/media acceptance; TURN certification
remains owned by the existing independent relay gate.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Response
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module
from mission_control import (
    link_call_audit,
    link_ptt_floor,
    link_relationships,
    link_signalling,
    link_turn,
    linkup_safety,
    neon_auth,
    postgres_db,
    web_security,
)

BASE = "http://127.0.0.1:8779"
AUTH_COOKIE = "better-auth.session_token"
CSRF_A = "ptt-browser-csrf-a-12345678901234567890"
CSRF_B = "ptt-browser-csrf-b-12345678901234567890"
USER_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
USER_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
AUTH_VALUES = {
    "ptt-browser-a": (USER_A, "Alpha PTT"),
    "ptt-browser-b": (USER_B, "Bravo PTT"),
}


def _auth(cookie_header: str):
    value = next((key for key in AUTH_VALUES if f"{AUTH_COOKIE}={key}" in cookie_header), None)
    if not value:
        return neon_auth.AuthResult(status_code=200, payload=None)
    identity, name = AUTH_VALUES[value]
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "ptt-" + identity[:8]},
            "user": {
                "id": identity,
                "name": name,
                "email": f"{identity[:8]}@example.test",
                "emailVerified": True,
            },
        },
    )


def _proof_page() -> Response:
    csrf = web_security.csrf_token()
    peer = USER_B if web_security.authenticated_identity() == USER_A else USER_A
    html = f"""<!doctype html>
<html><head>
<meta name="oap-csrf-token" content="{csrf}">
<title>OAP Private Live PTT Chromium Proof</title>
</head><body>
<p data-oap-call-status role="status">Call</p>
<div data-oap-incoming-calls hidden></div>
<div data-oap-call-stage hidden>
  <p data-oap-call-stage-label>Call</p>
  <video data-oap-remote-video autoplay playsinline hidden></video>
  <video data-oap-local-video autoplay muted playsinline hidden></video>
  <audio data-oap-remote-audio autoplay hidden></audio>
  <button type="button" disabled data-oap-live-ptt-hold hidden aria-pressed="false">Hold to Speak</button>
  <button type="button" disabled data-oap-live-ptt-stop hidden>STOP PTT</button>
  <button type="button" data-oap-hangup>End</button>
</div>
<button type="button" disabled data-oap-call-control data-call-mode="ptt"
        data-recipient-id="{peer}">Live PTT</button>
<script src="/static/linkup_realtime.js"></script>
</body></html>"""
    return Response(html, content_type="text/html; charset=utf-8")


def _session_cookie(auth_value: str, csrf: str):
    session_name = app_module.app.config.get("SESSION_COOKIE_NAME", "session")
    with app_module.app.test_client() as client:
        client.set_cookie(AUTH_COOKIE, auth_value)
        with client.session_transaction() as current_session:
            current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [AUTH_COOKIE]
            current_session[web_security.CSRF_SESSION_KEY] = csrf
        response = client.get("/__ptt_chromium_proof")
        assert response.status_code == 200
        session_cookie = client.get_cookie(session_name)
        assert session_cookie is not None
        return session_name, session_cookie.value


def _prepare():
    database = os.environ.get("OAP_PRIMARY_DATABASE_URL", "")
    assert database.startswith("postgresql://") and "127.0.0.1" in database
    os.environ["OAP_AUTH_REQUIRED"] = "true"
    os.environ["OAP_LINK_CALL_AUDIT_RETENTION_DAYS"] = "7"
    os.environ["NEON_AUTH_BASE_URL"] = "https://example.neonauth.test/neondb/auth"

    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="ptt-real-chromium-disposable-ci",
        SESSION_COOKIE_SECURE=False,
    )
    neon_auth.get_session = _auth
    link_call_audit._youth_guard = lambda *_args: None

    # Real local WebRTC needs no external relay. Keep this substitution explicit:
    # it proves browser/media/controller behaviour, not production TURN reachability.
    link_turn.status = lambda: {
        "configured": True,
        "owned": True,
        "credential_ready": True,
        "relay_verified": True,
        "ready": True,
        "url_count": 0,
        "ttl_seconds": 300,
    }
    link_turn.issue_credentials = lambda *_args, **_kwargs: {
        "ice_servers": [],
        "expires_at": 0,
        "ttl_seconds": 300,
        "relay_verified": True,
    }

    postgres_db.init_postgres(assume_yes=True)
    linkup_safety.init_schema(assume_yes=True)
    link_relationships.init_schema(assume_yes=True)
    link_call_audit.init_schema(assume_yes=True)
    link_call_audit.upgrade_ptt_mode(assume_yes=True)
    link_signalling.init_schema(assume_yes=True)
    link_ptt_floor.init_schema(assume_yes=True)

    with postgres_db.connect() as connection:
        for identity, label in ((USER_A, "Alpha"), (USER_B, "Bravo")):
            connection.execute(
                """INSERT INTO users(id,email,username,display_name,status)
                   VALUES (%s,%s,%s,%s,'active')
                   ON CONFLICT(id) DO UPDATE SET status='active'""",
                (identity, f"{identity[:8]}@example.invalid", f"ptt-{label.lower()}", label),
            )
        connection.execute(
            """INSERT INTO link_relationships(
                   requester_id,recipient_id,status,link_kind,accepted_at,resolved_at)
               VALUES (%s,%s,'accepted','permanent',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
               ON CONFLICT DO NOTHING""",
            (USER_A, USER_B),
        )
        connection.commit()

    if "__ptt_chromium_proof" not in app_module.app.view_functions:
        app_module.app.add_url_rule(
            "/__ptt_chromium_proof",
            "__ptt_chromium_proof",
            web_security.login_required(api=False)(_proof_page),
        )


def _instrument(page):
    page.add_init_script(
        """(() => {
          window.__oapPttStreams = [];
          const original = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
          navigator.mediaDevices.getUserMedia = async constraints => {
            const stream = await original(constraints);
            window.__oapPttStreams.push(stream);
            return stream;
          };
        })();"""
    )


def _audio_enabled(page):
    return page.evaluate(
        """() => {
          const stream = window.__oapPttStreams.at(-1);
          const track = stream?.getAudioTracks?.()[0];
          return track ? track.enabled : null;
        }"""
    )


def main():
    _prepare()
    session_name_a, session_a = _session_cookie("ptt-browser-a", CSRF_A)
    session_name_b, session_b = _session_cookie("ptt-browser-b", CSRF_B)
    assert session_name_a == session_name_b
    session_name = session_name_a

    server = make_server("127.0.0.1", 8779, app_module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--use-fake-device-for-media-stream",
                    "--use-fake-ui-for-media-stream",
                    "--disable-features=WebRtcHideLocalIpsWithMdns",
                    "--autoplay-policy=no-user-gesture-required",
                ],
            )
            a = browser.new_context(viewport={"width": 390, "height": 844})
            b = browser.new_context(viewport={"width": 1280, "height": 800})
            for context, auth_value, session_value in (
                (a, "ptt-browser-a", session_a),
                (b, "ptt-browser-b", session_b),
            ):
                context.grant_permissions(["microphone"], origin=BASE)
                context.add_cookies(
                    [
                        {"name": AUTH_COOKIE, "value": auth_value, "url": BASE},
                        {"name": session_name, "value": session_value, "url": BASE},
                    ]
                )
            page_a, page_b = a.new_page(), b.new_page()
            _instrument(page_a)
            _instrument(page_b)
            errors = []
            page_a.on("pageerror", lambda e: errors.append("A: " + str(e)))
            page_b.on("pageerror", lambda e: errors.append("B: " + str(e)))

            page_a.goto(BASE + "/__ptt_chromium_proof", wait_until="domcontentloaded")
            page_b.goto(BASE + "/__ptt_chromium_proof", wait_until="domcontentloaded")
            ptt_a = page_a.locator('[data-call-mode="ptt"]')
            expect(ptt_a).to_be_enabled(timeout=10000)
            ptt_a.click()

            incoming = page_b.locator("[data-oap-incoming-calls] button", has_text="Answer")
            expect(incoming).to_be_visible(timeout=10000)
            incoming.click()

            page_a.wait_for_function(
                """() => document.querySelector('[data-oap-call-status]')
                    ?.textContent.includes('Private PTT connected')""",
                timeout=15000,
            )
            page_b.wait_for_function(
                """() => document.querySelector('[data-oap-call-stage-label]')
                    ?.textContent.includes('Private Live PTT')""",
                timeout=15000,
            )
            assert _audio_enabled(page_a) is False
            assert _audio_enabled(page_b) is False

            hold_a = page_a.locator("[data-oap-live-ptt-hold]")
            stop_b = page_b.locator("[data-oap-live-ptt-stop]")
            expect(hold_a).to_be_enabled()
            expect(stop_b).to_be_enabled()
            hold_a.dispatch_event("pointerdown", {"button": 0, "pointerId": 9})
            page_a.wait_for_function(
                """() => document.querySelector('[data-oap-live-ptt-hold]')
                    ?.getAttribute('aria-pressed') === 'true'""",
                timeout=5000,
            )
            assert _audio_enabled(page_a) is True

            with postgres_db.connect(readonly=True) as connection:
                row = connection.execute(
                    """SELECT holder_id,stopped FROM link_ptt_floor
                       WHERE holder_id=%s AND stopped=FALSE""",
                    (USER_A,),
                ).fetchone()
                assert row and str(row[0]) == USER_A and row[1] is False

            # The other participant can authoritatively STOP the lease. The holder
            # polls the real floor endpoint and must mute without a local release.
            stop_b.click()
            page_a.wait_for_function(
                """() => window.__oapPttStreams.at(-1)
                    ?.getAudioTracks?.()[0]?.enabled === false""",
                timeout=5000,
            )
            assert _audio_enabled(page_a) is False

            with postgres_db.connect(readonly=True) as connection:
                row = connection.execute(
                    "SELECT holder_id,stopped FROM link_ptt_floor WHERE stopped=TRUE"
                ).fetchone()
                assert row and row[0] is None and row[1] is True

            # A stopped call cannot reopen its floor.
            hold_a.dispatch_event("pointerdown", {"button": 0, "pointerId": 10})
            page_a.wait_for_timeout(500)
            assert _audio_enabled(page_a) is False
            assert "PTT floor denied" in page_a.locator("[data-oap-call-status]").inner_text()

            assert not errors, errors
            print("PTT_REAL_CHROMIUM_POSTGRES=PASS")
            print("TWO_AUTHENTICATED_BROWSERS=PASS")
            print("REAL_LOCAL_WEBRTC_CONNECTED=PASS")
            print("REAL_POSTGRES_FLOOR=PASS")
            print("REMOTE_STOP_MUTES_HOLDER=PASS")
            print("STOP_TOMBSTONE_BLOCKS_REOPEN=PASS")
            print("EXTERNAL_TURN_RELAY=EXCLUDED_FROM_THIS_PROOF")

            a.close()
            b.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=3)
        with postgres_db.connect() as connection:
            connection.execute(
                "DELETE FROM link_relationships WHERE requester_id IN (%s,%s) OR recipient_id IN (%s,%s)",
                (USER_A, USER_B, USER_A, USER_B),
            )
            connection.execute("DELETE FROM users WHERE id IN (%s,%s)", (USER_A, USER_B))
            connection.commit()


if __name__ == "__main__":
    main()
