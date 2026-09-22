"""Exercise the real SMI mask editor with LOCAL, test-only Founder identity.

No production credentials, no SMI inference, no real-mask claims and no
screenshots/private image artifacts. The binary source is the approved repo JPG.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import threading
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["NEON_AUTH_BASE_URL"] = "https://example.neonauth.test/neondb/auth"
os.environ["OAP_HUMAN_AUTHORITY_EMAIL"] = "founder@example.test"
os.environ["OAP_AUTH_REQUIRED"] = "true"

from PIL import Image
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

import app as oap
from mission_control import neon_auth
from oap.smi.character_rig_assets import APPROVED_SOURCE_SHA256, LAYERS

AUTH_COOKIE = "better-auth.session_token"
COOKIE_VALUE = "local-mask-test-fixture"


def mock_session(cookie_header):
    if AUTH_COOKIE + "=" + COOKIE_VALUE not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "local-fixture-only"},
            "user": {
                "id": "11111111-1111-4111-8111-111111111111",
                "email": "founder@example.test",
                "name": "Test Founder",
                "emailVerified": True,
            },
        },
    )


def run_workbench(page, origin, output):
    outside = []
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "request",
        lambda request: outside.append(request.url)
        if request.url.startswith("http") and not request.url.startswith(origin)
        else None,
    )
    response = page.goto(origin + "/mission/character-mask-workbench")
    assert response is not None and response.status == 200, (
        "Local Founder fixture did not enter private mask workbench"
    )
    page.locator("#source-art").wait_for(state="visible")
    page.get_by_text("Exact original verified.", exact=False).wait_for()
    original = ROOT / "static/oap/smi_live_chat_dashboard.jpg"
    assert hashlib.sha256(original.read_bytes()).hexdigest() == APPROVED_SOURCE_SHA256
    with Image.open(original) as img:
        dimensions = img.size
    assert page.locator("#source-art").evaluate(
        "(el) => [el.naturalWidth,el.naturalHeight]"
    ) == list(dimensions)
    assert page.locator("#save-all").is_enabled()
    preview = page.locator("#mask-only")
    assert preview.is_enabled()
    preview.click()
    assert preview.get_attribute("aria-pressed") == "true"
    assert page.locator("#art-stage").evaluate("(el) => el.classList.contains('mask-only')")
    assert page.locator("#source-art").is_visible() is False
    assert page.locator("#source-art").evaluate("(el) => el.naturalWidth") == dimensions[0]
    preview.click()
    assert preview.get_attribute("aria-pressed") == "false"
    assert page.locator("#source-art").is_visible()
    assert page.locator("#coverage").evaluate("(el) => el.value") == 0

    page.locator("#save-all").click()
    page.get_by_text("Finish all seven nonempty masks", exact=False).wait_for()
    assert page.locator("#coverage").evaluate("(el) => el.value") == 0

    names = list(LAYERS)
    for name in names:
        page.locator("#layers button[data-name='" + name + "']").click()
        canvas = page.locator("canvas[data-name='" + name + "']")
        assert canvas.is_visible()
        region = canvas.bounding_box()
        assert region and region["width"] > 0 and region["height"] > 0
        x = region["x"] + region["width"] * 0.5
        y = region["y"] + region["height"] * 0.5
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.up()
        assert canvas.evaluate(
            "(el) => [...el.getContext('2d').getImageData(0,0,"
            "el.width,el.height).data].some((v,i) => i%4===3 && v>0)"
        )
    assert page.locator("#coverage").evaluate("(el) => el.value") == 7

    with page.expect_download() as download_event:
        page.locator("#save-all").click()
    download = download_event.value
    assert download.suggested_filename == "smi-exact-character-draft-masks.zip"
    download.save_as(output)
    raw = output.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None, "ZIP CRCs must work in stdlib zipfile"
        names_in_zip = archive.namelist()
        assert set(names_in_zip) == {name + ".png" for name in names} | {
            "mask-bundle.json"
        }
        manifest = json.loads(archive.read("mask-bundle.json"))
        assert manifest["approval"] == "DRAFT_REQUIRES_FOUNDER_REVIEW"
        assert manifest["source_sha256"] == APPROVED_SOURCE_SHA256
        assert manifest["animation_active"] is False
        assert manifest["canvas"] == list(dimensions)
        for name in names:
            with Image.open(io.BytesIO(archive.read(name + ".png"))) as mask:
                mask.load()
                assert mask.mode == "RGBA"
                assert mask.size == dimensions
                assert mask.getchannel("A").getbbox() is not None
                # Every nontransparent painted pixel is white, not new art.
                middle = mask.getpixel(
                    (dimensions[0] // 2, dimensions[1] // 2)
                )
                assert middle[:3] == (255, 255, 255)
                assert middle[3] > 0

        draft = archive.read("eyes.png")
    with page.expect_download() as source_event:
        page.locator("#save-layers").click()
    source_download = source_event.value
    assert source_download.suggested_filename == (
        "smi-private-original-pixel-layers-DRAFT.zip"
    )
    source_output = output.with_name("original-pixel-source-draft.zip")
    source_download.save_as(source_output)
    with zipfile.ZipFile(source_output) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {
            name + ".png" for name in names
        } | {"source-package.json"}
        package = json.loads(archive.read("source-package.json"))
        assert package["approved_source_sha256"] == APPROVED_SOURCE_SHA256
        assert package["motion_proven"] is False
        assert package["speech_sync_proven"] is False
        assert package["human_authority_approved"] is False
        assert package["hidden_region_reconstruction"] is False
        with Image.open(original) as image:
            original_rgb = image.convert("RGB")
            for name in names:
                record = package["layers"][name]
                data = archive.read(name + ".png")
                assert hashlib.sha256(data).hexdigest() == record["sha256"]
                with Image.open(io.BytesIO(data)) as layer:
                    layer.load()
                    assert layer.mode == "RGBA"
                    x0, y0, x1, y1 = record["bbox_xyxy"]
                    assert layer.size == (x1 - x0, y1 - y0)
                    # The wholly selected source pixels stay the original RGB.
                    center = (dimensions[0] // 2, dimensions[1] // 2)
                    local = (center[0] - x0, center[1] - y0)
                    assert layer.getpixel(local) == (
                        *original_rgb.getpixel(center), 255
                    )
    print("SMI_PRIVATE_ORIGINAL_PIXEL_SOURCE_EXPORT_PASS")

    page.locator("#layers button[data-name='eyes']").click()
    page.locator("#clear").click()
    assert page.locator("#coverage").evaluate("(el) => el.value") == 6
    page.locator("#import-mask").set_input_files({
        "name": "eyes.png",
        "mimeType": "image/png",
        "buffer": draft,
    })
    page.get_by_text("Restored local eyes mask as draft.", exact=True).wait_for()
    assert page.locator("#coverage").evaluate("(el) => el.value") == 7

    assert not outside, "Mask workbench must not request external resources"
    assert not errors, "Browser exception during mask workflow"
    print("SMI_MASK_WORKBENCH_BROWSER_EXPORT_RESTORE_PASS")

    # A tampered source must keep the editor disabled; no substitute image.
    page.route(
        "**/static/oap/smi_live_chat_dashboard.jpg",
        lambda route: route.fulfill(body=b"not-approved-art", content_type="image/jpeg"),
    )
    page.reload()
    page.get_by_text("Original character identity mismatch", exact=False).wait_for()
    assert page.locator("#save-all").is_disabled()
    assert page.locator("#save-layers").is_disabled()
    assert page.locator("#source-art").is_hidden()
    assert not errors
    print("SMI_MASK_WORKBENCH_TAMPER_FAIL_CLOSED_PASS")


def main():
    neon_auth.get_session = mock_session
    oap.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    server = make_server("127.0.0.1", 0, oap.app, threaded=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    origin = "http://127.0.0.1:" + str(server.server_port)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    accept_downloads=True,
                    viewport={"width": 390, "height": 844},
                )
                # Auth's allowlisted cookie names live in Flask's signed
                # session, so a stand-alone provider cookie is insufficient.
                with oap.app.test_client() as test_client:
                    test_client.set_cookie(AUTH_COOKIE, COOKIE_VALUE)
                    with test_client.session_transaction() as flask_session:
                        flask_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [
                            AUTH_COOKIE
                        ]
                    signed_session = test_client.get_cookie("session")
                    assert signed_session is not None
                context.add_cookies([
                    {"name": AUTH_COOKIE, "value": COOKIE_VALUE, "url": origin},
                    {"name": "session", "value": signed_session.value, "url": origin},
                ])
                page = context.new_page()
                page.set_default_timeout(20_000)
                with tempfile.TemporaryDirectory(prefix="oap-mask-browser-") as folder:
                    run_workbench(page, origin, Path(folder) / "draft.zip")
            finally:
                browser.close()
    finally:
        server.shutdown()
        worker.join(timeout=4)


if __name__ == "__main__":
    main()
