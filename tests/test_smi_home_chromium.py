"""Real Chromium acceptance of the SMI homepage template and interactions."""
from pathlib import Path
from threading import Thread
from werkzeug.serving import make_server
from flask import Flask, render_template
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def test_smi_home_real_chromium_desktop_and_mobile():
    app = Flask(__name__, template_folder=str(ROOT / "templates"))

    @app.get("/smi-home")
    def home():
        return render_template("smi_command_home.html")

    server = make_server("127.0.0.1", 0, app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            for width, height in [(1440, 900), (390, 844)]:
                page = browser.new_page(viewport={"width": width, "height": height})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                response = page.goto(f"http://127.0.0.1:{server.server_port}/smi-home")
                assert response.status == 200
                assert page.get_by_role("heading", name="ONE WORLD. ONE FRONT DOOR.").is_visible()
                assert page.get_by_role("button", name="∞ Captain ALL IN").first.is_visible()
                page.get_by_role("button", name="Explore OAP World").click()
                assert page.get_by_role("dialog").is_visible()
                search = page.get_by_role("searchbox", name="Find OAP World destination")
                assert search.is_focused()
                search.fill("Link")
                assert page.get_by_role("navigation", name="World destinations").get_by_role("link", name="Link Up").is_visible()
                assert page.get_by_role("navigation", name="World destinations").get_by_role("link", name="SIKA").is_hidden()
                page.keyboard.press("Escape")
                assert page.get_by_role("dialog").is_hidden()
                page.get_by_role("button", name="∞ Captain ALL IN").first.click()
                assert page.get_by_role("dialog").is_visible()
                assert page.get_by_role("heading", name="Captain ALL IN").is_visible()
                page.get_by_role("button", name="Close").click()
                assert page.get_by_role("dialog").is_hidden()
                assert not errors, errors
                page.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
