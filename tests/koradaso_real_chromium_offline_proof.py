"""Actual Chromium acceptance for the public KORADASO offline shell.

Uses the real Flask server, service worker and Chromium CacheStorage.
Does not certify offline SMI inference, device boot, or production rollout.
"""
from __future__ import annotations

import threading

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

import app as app_module

BASE = "http://127.0.0.1:8787"


def main() -> None:
    app_module.app.config.update(
        TESTING=True, SECRET_KEY="koradaso-browser-acceptance",
        SESSION_COOKIE_SECURE=False,
    )
    server = make_server("127.0.0.1", 8787, app_module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 393, "height": 852})
            page = context.new_page()
            response = page.goto(BASE + "/koradaso")
            assert response is not None and response.status == 200
            page.evaluate("""async () => {
                if (!("serviceWorker" in navigator)) throw Error("worker_unsupported");
                await navigator.serviceWorker.ready;
            }""")
            # The first navigation may precede the worker taking control.
            page.reload()
            page.wait_for_function("navigator.serviceWorker.controller !== null")
            before = page.locator("html").get_attribute("data-koradaso-release")
            assert before and len(before) == 20

            context.set_offline(True)
            offline = page.reload(wait_until="domcontentloaded")
            assert offline is not None and offline.status == 200
            expect(page.locator("html")).to_have_attribute(
                "data-koradaso-release", before
            )
            assert "KORADASO" in page.title().upper()
            assert page.evaluate("navigator.serviceWorker.controller !== null")
            context.set_offline(False)
            context.close()
            browser.close()
        print("KORADASO_REAL_CHROMIUM_OFFLINE_SHELL_PASS")
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
