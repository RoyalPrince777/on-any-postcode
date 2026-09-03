from pathlib import Path

from mission_control import war_room


def _ratings(projection):
    return [item for category in projection["categories"] for item in category["items"]]


def test_oap_os_manifest_is_installable_and_public_only(client):
    response = client.get("/manifest.webmanifest")
    manifest = response.get_json()

    assert response.status_code == 200
    assert response.content_type == "application/manifest+json"
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert manifest["name"] == "ON ANY POSTCODE Operating System"
    assert manifest["short_name"] == "OAP OS"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"
    assert {icon["sizes"] for icon in manifest["icons"]} == {
        "192x192",
        "512x512",
    }
    shortcut_urls = {shortcut["url"].split("?", 1)[0] for shortcut in manifest["shortcuts"]}
    assert shortcut_urls == {"/the-spot", "/the-link", "/linkup", "/movement"}
    assert not any(
        route in str(manifest)
        for route in ("/mission", "/my-world", "/auth", "/infrastructure")
    )


def test_home_exposes_oap_os_install_contract(client):
    response = client.get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'rel="manifest" href="/manifest.webmanifest"' in page
    assert 'data-oap-install hidden' in page
    assert 'src="/assets/oap-os.js"' in page
    assert "OAP OPERATING SYSTEM · GENERATION 0" in page
    assert "Run OAP as its own app on this device." in page
    assert "protected records" not in page


def test_install_controller_has_cross_platform_guidance():
    controller = Path("static/oap-os.js").read_text()

    for platform in ("Android", "iPhone / iPad", "Windows", "macOS", "ChromeOS", "Linux"):
        assert platform in controller
    assert "Add to Home Screen" in controller
    assert "Add to Dock" in controller
    assert "beforeinstallprompt" in controller
    assert "navigator.standalone" in controller


def test_service_worker_is_root_scoped_and_never_runtime_caches_private_data(client):
    response = client.get("/service-worker.js")
    worker = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.content_type.startswith("application/javascript")
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["Service-Worker-Allowed"] == "/"
    assert 'request.method !== "GET"' in worker
    assert "isPrivatePath(url.pathname)" in worker
    assert 'caches.match("/offline")' in worker
    assert "cache.put" not in worker

    public_shell = worker.split("const PRIVATE_PREFIXES", 1)[0]
    for private_path in (
        "/auth",
        "/enter-my-world",
        "/my-world",
        "/mission",
        "/infrastructure",
    ):
        assert private_path not in public_shell


def test_offline_fallback_is_static_public_safe_mode(client):
    response = client.get("/offline")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert "Set-Cookie" not in response.headers
    assert "PUBLIC SAFE MODE" in page
    assert "never stored by this install shell" in page
    assert "<form" not in page.casefold()


def test_install_icons_are_bounded_reviewed_png_assets(client):
    for size in (192, 512):
        response = client.get(f"/assets/oap-os-icon-{size}.png")
        assert response.status_code == 200
        assert response.content_type == "image/png"
        assert response.data.startswith(b"\x89PNG\r\n\x1a\n")

    missing = client.get("/assets/oap-os-icon-1024.png")
    assert missing.status_code == 404
    assert missing.headers["Cache-Control"] == "no-store"


def test_os_boundary_and_war_room_rating_are_truthful():
    documentation = Path("docs/OAP_OPERATING_SYSTEM_V0.md").read_text()
    projection = war_room.get_war_room_dashboard()
    rating = next(
        item for item in _ratings(projection) if item["id"] == "oap_os_install_shell"
    )

    assert "Android/Linux host kernel" in documentation
    assert "OAP CORE" in documentation
    assert "Soul → Mind → Body" in documentation
    assert "Human Authority remains final" in documentation
    assert rating["stars"] == 3
    assert rating["first_missing_stage"] == "Runtime verified"
    assert "not a replacement kernel" in rating["truth_boundary"]
    assert any(
        boundary["components"] == "OAP OS / OAP CORE / Living Kernel / Android-Linux"
        for boundary in projection["conflict_audit"]["resolved_boundaries"]
    )
