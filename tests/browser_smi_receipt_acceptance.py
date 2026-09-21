"""Chromium DOM check of the *actual* Live SMI receipt listener.

Local fixture only: does not claim hosted, Android or backend HRM proof.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "mission_control/static/smi_chat_final.js"


def main():
    source = JS.read_text(encoding="utf-8")
    start = source.index("const seenReceiptIds=new Set();")
    end = source.index("const composer=q('#chat-form');", start)
    listener = source[start:end]
    assert "response.clone().text()" not in source
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content(
                '<main id="messages"><div class="msg assistant"><span class="msg-text">Accepted reply</span></div></main>'
            )
            page.evaluate(
                """source => {
                  const messages=document.querySelector('#messages');
                  (new Function('messages',source))(messages);
                }""",
                listener,
            )
            def emit(request_id, conversation_id="conversation-1"):
                page.evaluate(
                    """detail => window.dispatchEvent(
                        new CustomEvent('oap-smi-complete',{detail}))""",
                    {"request_id": request_id, "conversation_id": conversation_id,
                     "guardian": "PASSED", "can_execute": False},
                )
            emit("request-1")
            emit("request-1")  # replay must not create a second card
            assert page.locator(".receipt-card").count() == 1
            assert page.locator(".msg.assistant").get_attribute("data-request-id") == "request-1"
            emit("")  # malformed receipt must fail closed
            assert page.locator(".receipt-card").count() == 1
            page.locator("#messages").evaluate(
                """el => el.insertAdjacentHTML('beforeend',
                    '<div class="msg assistant"><span class="msg-text">Next</span></div>')"""
            )
            emit("request-2")
            assert page.locator(".receipt-card").count() == 2
            assert page.locator(".msg.assistant").last.get_attribute("data-request-id") == "request-2"
            assert not errors, errors
            print("SMI_CANONICAL_RECEIPT_CHROMIUM_IDEMPOTENCY_PASS")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
