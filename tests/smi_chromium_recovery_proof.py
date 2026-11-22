from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import expect, sync_playwright
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


def prove_governed_actions(context, base_url):
    """Real chat DOM + intercepted API boundaries; no live GitHub writes.

    The test certifies browser wiring and failure handling only. Signed-receipt
    validation, authority, CSRF and replay remain canonical backend test concerns.
    """
    plan = {
        "request_id": "22222222-2222-4222-8222-222222222222",
        "action_type": "github.file.write",
        "action_digest": "a" * 64,
        "payload": {
            "branch": "oap-mind/browser-proof",
            "path": "notes/change.md",
            "content": '<img src=x onerror="window.__unsafePlan=true">',
            "message": "Reviewed bounded change",
        },
        "requires_human_approval": True,
    }
    for scenario in (
        "approved", "rejected", "denied", "mismatch", "blocked",
        "lost-execution", "invalid-completion", "lost-approval",
    ):
        page = context.new_page()
        calls = []

        def boundary_for(scenario, calls):
            def boundary(route):
                request = route.request
                assert request.method == "POST"
                assert request.headers["x-oap-csrf"] == CSRF_VALUE
                payload = request.post_data_json
                path = request.url.split("/tools/github/", 1)[1]
                calls.append((path, payload))
                if path == "proposals/file":
                    route.fulfill(json={"proposal": plan, "executed": False})
                elif path == "approvals":
                    assert payload["request_id"] == plan["request_id"]
                    assert payload["action_digest"] == plan["action_digest"]
                    if scenario == "lost-approval":
                        route.abort("connectionreset")
                        return
                    if scenario == "denied":
                        route.fulfill(status=403, json={"error": {"message": "Founder gate blocked"}})
                        return
                    receipt = {
                        "receipt_id": "browser-receipt",
                        "request_id": plan["request_id"],
                        "action_type": plan["action_type"],
                        "action_digest": plan["action_digest"],
                        "decision": payload["decision"],
                        "signature_verified": True,
                        "expires_at": "2030-01-01T00:00:00Z",
                    }
                    if scenario == "mismatch":
                        receipt["action_digest"] = "b" * 64
                    route.fulfill(json={"approval": receipt, "executed": False})
                elif path == "execute":
                    assert payload == {"receipt_id": "browser-receipt", "plan": plan}
                    if scenario == "lost-execution":
                        route.abort("connectionreset")
                        return
                    result = {
                        "request_id": plan["request_id"],
                        "executed": scenario != "blocked",
                        "state": "EXECUTED" if scenario != "blocked" else "BLOCKED",
                        "reason": "Boundary result",
                        "audit_event_id": "browser-audit",
                    }
                    if scenario == "invalid-completion":
                        result["request_id"] = "wrong-request"
                    route.fulfill(json=result)
                else:
                    raise AssertionError(path)
            return boundary

        page.route("**/mission/tools/github/**", boundary_for(scenario, calls))
        page.goto(base_url + "/mission/ollama", wait_until="domcontentloaded")
        page.locator("#plus-button").click()
        entry = page.locator('[data-oap-action="github-governed"]')
        expect(entry).to_have_count(1)
        entry.click()
        card = page.locator(".action-card")
        expect(card).to_have_count(1)
        assert calls == []
        card.locator("[data-kind]").select_option("file")
        for name, value in plan["payload"].items():
            card.locator(f'[name="{name}"]').fill(value)
        card.get_by_role("button", name="Prepare exact plan", exact=True).click()
        approve = card.locator(".action-row .action-btn.primary")
        reject = card.get_by_role("button", name="Reject", exact=True)
        expect(approve).to_have_text("Approve & run")
        expect(approve).to_be_visible()
        assert json.loads(card.locator("pre").inner_text()) == plan["payload"]
        assert card.locator("pre img").count() == 0
        assert page.evaluate("() => window.__unsafePlan === true") is False
        for control in card.locator("select,input,textarea").all():
            expect(control).to_be_disabled()
        assert [path for path, _ in calls] == ["proposals/file"]
        target = reject if scenario == "rejected" else approve
        target.click()
        state = card.locator("[data-state]")
        expected = {
            "approved": "EXECUTED", "rejected": "REJECTED",
            "denied": "Approval outcome unconfirmed", "mismatch": "BLOCKED",
            "blocked": "BLOCKED", "lost-execution": "Execution outcome unconfirmed",
            "invalid-completion": "Execution outcome unconfirmed",
            "lost-approval": "Approval outcome unconfirmed",
        }[scenario]
        expect(state).to_contain_text(expected)
        assert plan["request_id"] in state.inner_text()
        expect(approve).to_be_disabled()
        expect(reject).to_be_disabled()
        expected_calls = ["proposals/file", "approvals"]
        if scenario in {"approved", "blocked", "lost-execution", "invalid-completion"}:
            expected_calls.append("execute")
        assert [path for path, _ in calls] == expected_calls
        # Even an additional DOM click cannot mint/replay an approval.
        target.evaluate("button => button.click()")
        assert [path for path, _ in calls] == expected_calls
        if scenario in {"lost-execution", "invalid-completion", "lost-approval"}:
            expect(state).to_contain_text("No automatic retry")
        page.close()
    print("SMI_EXACT_ACTION_BROWSER_WIRING=PASS (intercepted APIs; not live execution)")


def prove_reference_dashboard(context, base_url):
    """Check the real private dashboard across desktop, tablet and phone widths."""
    output = Path(os.environ.get("OAP_SMI_DASHBOARD_ARTIFACT_DIR", "/tmp/oap-smi-dashboard"))
    output.mkdir(parents=True, exist_ok=True)
    for width, height in ((1536, 1155), (1440, 900), (1280, 800), (1024, 768), (760, 852), (393, 852), (320, 740)):
        page = context.new_page()
        page.set_viewport_size({"width": width, "height": height})
        requested = []
        page.on("request", lambda request, sink=requested: sink.append(request.url))
        page.goto(base_url + "/mission/smi", wait_until="networkidle")
        expect(page.locator(".character-art img")).to_be_visible()
        assert page.locator(".character-art img").evaluate("img => img.complete && img.naturalWidth > 1000")
        expect(page.get_by_role("status", name="SMI welcome")).to_be_visible()
        assert "Welcome back to your world." in page.locator("[data-smi-welcome]").inner_text()
        # Automatic visual-only idle movement, never an audio or inference request.
        assert "smiCompanionIdle" in page.locator(".character-art img").evaluate(
            "img => getComputedStyle(img).animationName"
        )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        assert not any("/mission/ollama" in url or "/mission/smi/status" in url for url in requested)
        expect(page.locator(".smi-support-nav a")).to_have_count(5)
        assert page.locator(".status .unknown").count() == 5
        assert "All Systems Operational" not in page.locator("body").inner_text()
        assert "24,792" not in page.locator("body").inner_text()
        if width >= 1200:
            left = page.locator(".left").bounding_box()
            centre = page.locator(".centre").bounding_box()
            right = page.locator(".right").bounding_box()
            assert left["x"] < centre["x"] < right["x"]
            footer = page.locator(".footer-dock").bounding_box()
            assert footer["y"] + footer["height"] <= height + 1, (width, footer)
            assert page.locator(".smi-route-drawer").evaluate("node => node.open")
            expect(page.locator(".global-panel")).to_be_visible()
            talk = page.locator(".smi-talk-dock")
        elif width <= 760:
            assert not page.locator(".smi-route-drawer").evaluate("node => node.open")
            assert not page.locator(".right-details").evaluate("node => node.open")
            expect(page.locator(".global-panel")).not_to_be_visible()
            talk = page.locator(".smi-talk-primary")
            expect(talk).to_be_visible()
            page.locator(".smi-route-drawer > summary").click()
            expect(page.locator(".navlinks a")).to_have_count(15)
            expect(page.locator(".navlinks a").first).to_be_visible()
            page.locator(".smi-route-drawer > summary").click()
            page.locator(".right-details > summary").click()
            expect(page.get_by_role("heading", name="SYSTEM STATUS", exact=True)).to_be_visible()
            page.locator(".right-details > summary").click()
            page.evaluate("window.scrollTo(0, 0)")
        else:
            talk = page.locator(".smi-talk-dock")
        if width == 1536:
            page.screenshot(path=str(output / "smi-command-desktop.png"), full_page=True)
        if width == 393:
            page.screenshot(path=str(output / "smi-command-mobile.png"), full_page=True)
        talk.click()
        expect(page.locator("#smi-chat-panel")).to_be_visible()
        assert page.locator("body").get_attribute("data-smi-presence") == "chat"
        assert page.locator(".character-art img").evaluate(
            "img => getComputedStyle(img).animationPlayState"
        ) == "paused"
        expect(page.locator("#smi-chat-frame")).to_have_attribute("src", "/mission/ollama")
        if width in (1536, 393):
            # Browser-only bridge proof: canonical state events, never fake AI replies.
            child = page.frame_locator("#smi-chat-frame")
            expect(child.locator("body")).to_have_attribute("data-smi-presence", "ready")
            child.locator("body").evaluate("""() => window.dispatchEvent(
                new CustomEvent('oap-smi-character-state',
                    {detail:{state:'thinking',live:false,stopped:false}})
            )""")
            expect(page.locator("#smi-chat-panel")).to_have_attribute(
                "data-smi-visual-state", "thinking"
            )
            expect(page.locator("#smi-companion-state")).to_have_text("Visual · Thinking")
            child.locator("body").evaluate("""() => window.dispatchEvent(
                new CustomEvent('oap-smi-character-state',
                    {detail:{state:'stopped',live:false,stopped:true}})
            )""")
            expect(page.locator("#smi-chat-panel")).to_have_attribute(
                "data-smi-visual-state", "stopped"
            )
            expect(page.locator("#smi-companion-state")).to_have_text("Visual · Stopped")
        assert page.locator(".shell").evaluate("node => node.inert")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (width, "open chat")
        page.locator("#smi-chat-close").click()
        expect(page.locator("#smi-chat-panel")).not_to_be_visible()
        assert page.locator("#smi-chat-frame").get_attribute("src") is None
        assert page.locator("body").get_attribute("data-smi-presence") == "idle"
        expect(talk).to_be_focused()
        page.close()
    print("SMI_REFERENCE_DASHBOARD_RESPONSIVE=PASS (7 viewports; no device certification)")


def main():
    _prepare_app()
    session_name, session_value = _session_cookies()

    server = make_server("127.0.0.1", 8765, app_module.app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = "http://127.0.0.1:8765"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=os.environ.get("OAP_TEST_CHROMIUM_EXECUTABLE"),
            )
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
                    '.navs', '.smi-hero', '.status-row',
                    '.smi-dashboard-layer', '.smi-status-backdrop'
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
                    const body = document.body;
                    if (body && body.classList.contains('smi-booting')) {
                      const visibleSelectors = selectors.filter(sel => visible(document.querySelector(sel)));
                      window.__smiLegacyPaintSamples.push(visibleSelectors);
                      requestAnimationFrame(sample);
                    }
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
            page.wait_for_timeout(250)
            assert live.get_attribute("aria-pressed") == "true"

            page.wait_for_function(
                "() => Boolean(window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION?.snapshot?.())"
            )
            motion_before = page.evaluate(
                "() => window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION.snapshot()"
            )
            canvas = page.locator("#smi-source-pixel-motion")
            canvas.wait_for(state="visible")
            page.wait_for_timeout(350)
            motion_after = page.evaluate(
                "() => window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION.snapshot()"
            )
            assert motion_after["live"] is True
            assert motion_after["frames"] > motion_before["frames"]
            assert motion_after["fullSceneSourcePixelMotion"] is True
            assert motion_after["rigLayerFrames"]["head"] > 0
            assert motion_after["rigLayerFrames"]["eyes"] > 0
            assert motion_after["rigLayerFrames"]["breathing"] > 0
            assert motion_after["rigLayerFrames"]["hands"] > 0

            # Software-only browser proof: a real browser speech-boundary event must
            # produce visible mouth-region pixel motion. This deliberately does NOT
            # claim decoded-audio or phoneme-accurate lip sync.
            page.evaluate(
                """() => window.dispatchEvent(new CustomEvent(
                    'oap-smi-character-state',
                    {detail:{state:'speaking',live:true,stopped:false,epoch:777}}
                ))"""
            )
            page.wait_for_timeout(80)
            mouth_before = page.evaluate(
                """() => {
                    const canvas=document.querySelector('#smi-source-pixel-motion');
                    const ctx=canvas.getContext('2d');
                    const d=ctx.getImageData(738,253,66,33).data;
                    return Array.from(d);
                }"""
            )
            mouth_frames_before = page.evaluate(
                "() => window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION.snapshot().rigLayerFrames.mouth_visemes"
            )
            page.evaluate(
                """() => window.dispatchEvent(new CustomEvent(
                    'oap-smi-speech-boundary',
                    {detail:{
                        source:'browser-speech-synthesis',
                        decodedAudio:false,
                        phonemeAligned:false,
                        elapsedMs:120,
                        epoch:777
                    }}
                ))"""
            )
            page.wait_for_timeout(70)
            mouth_after = page.evaluate(
                """() => {
                    const canvas=document.querySelector('#smi-source-pixel-motion');
                    const ctx=canvas.getContext('2d');
                    const d=ctx.getImageData(738,253,66,33).data;
                    return Array.from(d);
                }"""
            )
            mouth_frames_after = page.evaluate(
                "() => window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION.snapshot().rigLayerFrames.mouth_visemes"
            )
            assert mouth_frames_after > mouth_frames_before
            assert mouth_after != mouth_before
            speech_snapshot = page.evaluate(
                "() => window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION.snapshot()"
            )
            assert speech_snapshot["accurateHumanLipSyncProven"] is False

            visible_legacy_during_boot = page.evaluate(
                "() => window.__smiLegacyPaintSamples.flat()"
            )
            assert visible_legacy_during_boot == [], visible_legacy_during_boot

            assistant_before = page.locator(".msg.assistant").count()
            prompt = "browser recovery proof request"
            page.locator("#message").fill(prompt)
            page.locator("#send").click()

            page.wait_for_function(
                """p => {
                    const input = document.querySelector('#message');
                    const liveCaption = document.querySelector('#smi-live-reply-caption');
                    return input &&
                           input.value === p &&
                           liveCaption &&
                           !liveCaption.hidden &&
                           liveCaption.innerText.includes('your request is preserved for retry.');
                }""",
                arg=prompt,
            )

            assert page.locator("#message").input_value() == prompt
            assert page.locator("#send").is_enabled()
            assert page.locator("#plus-button").is_enabled()
            assert page.locator("#pause-button").is_enabled()
            assert page.locator("#stop-button").is_enabled()

            page.locator("#stop-button").click()
            page.wait_for_timeout(120)
            stopped_snapshot = page.evaluate(
                "() => window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION.snapshot()"
            )
            assert stopped_snapshot["phase"] == "stopped"
            assert stopped_snapshot["live"] is False
            frozen_frames = stopped_snapshot["frames"]
            page.wait_for_timeout(220)
            stopped_after = page.evaluate(
                "() => window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION.snapshot()"
            )
            assert stopped_after["frames"] == frozen_frames

            assistant_after = page.locator(".msg.assistant").count()
            assert assistant_after == assistant_before

            system_text = page.locator(".msg.system").all_inner_texts()
            assert any("request is preserved for retry" in text for text in system_text)
            assert not any("sk-" in text.lower() for text in system_text)

            print("SMI_CHROMIUM_ACCEPTANCE=PASS")
            print("LIVE_VISIBLE_CLICKABLE=PASS")
            print("NO_LEGACY_FLASH_SAMPLES=PASS")
            print("FAILED_REQUEST_RECOVERY=PASS")
            print("SOURCE_PIXEL_MOTION=PASS")
            print("STOP_FREEZES_MOTION=PASS")

            prove_governed_actions(context, base_url)
            prove_reference_dashboard(context, base_url)
            context.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()

