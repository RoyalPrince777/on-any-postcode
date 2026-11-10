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

            # Two real controlled Chromium tabs must retain their old worker
            # and unsent text while a genuine newer worker waits.
            studio = context.new_page()
            studio_response = studio.goto(BASE + "/studio?source=koradaso")
            assert studio_response is not None and studio_response.status == 200
            studio.locator("#studio-input").fill("Unsent Founder draft")
            page.locator("#address").fill("Unsent search query")
            original_controller = page.evaluate("""() =>
                navigator.serviceWorker.controller?.state
            """)
            assert original_controller == "activated"
            current_cache = "oap-os-public-" + before
            next_cache = "oap-os-public-" + ("a" * 20 if before != "a" * 20 else "b" * 20)
            original_worker_view = app_module.app.view_functions["oap_os_service_worker"]

            def upgraded_worker():
                response = original_worker_view()
                source = response.get_data(as_text=True)
                assert current_cache in source
                response.set_data(source.replace(current_cache, next_cache))
                return response

            app_module.app.view_functions["oap_os_service_worker"] = upgraded_worker
            try:
                # Registration.update fetches a real changed service worker
                # from Flask. We do not mock Chromium's SW lifecycle.
                page.evaluate("""async () => {
                    const registration = await navigator.serviceWorker.getRegistration("/");
                    await registration.update();
                }""")
                page.wait_for_function("""async () => {
                    const registration = await navigator.serviceWorker.getRegistration("/");
                    return registration && registration.waiting?.state === "installed";
                }""")
                assert page.locator("#address").input_value() == "Unsent search query"
                assert studio.locator("#studio-input").input_value() == "Unsent Founder draft"
                assert page.evaluate("""async () => {
                    const registration = await navigator.serviceWorker.getRegistration("/");
                    return registration.active?.state === "activated" &&
                        registration.waiting?.state === "installed";
                }""")
                # The old controller and public shell remain usable.
                context.set_offline(True)
                offline_again = page.reload(wait_until="domcontentloaded")
                assert offline_again is not None and offline_again.status == 200
                context.set_offline(False)
                assert page.evaluate("""async () => {
                    const keys = await caches.keys();
                    return keys.some(key => key.startsWith("oap-os-public-"));
                }""")
            finally:
                app_module.app.view_functions["oap_os_service_worker"] = original_worker_view

            studio.close()
            page.close()
            context.close()
            browser.close()
        print("KORADASO_REAL_CHROMIUM_OFFLINE_SHELL_PASS")
    finally:
        server.shutdown()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
