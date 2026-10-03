"""OAP Store install surface truth-mode regression coverage."""
from mission_control import oap_store


def test_oap_world_is_first_installable_store_entry():
    app = oap_store.OAP_WORLD
    assert app["app_id"] == "oap.world"
    assert app["publisher"] == "ON ANY POSTCODE LTD"
    assert app["first_party"] is True
    assert app["install_enabled"] is True
    assert app["install_mode"] == "PWA"
    assert app["manifest_url"] == "/manifest.webmanifest"
    assert app["service_worker_url"] == "/service-worker.js"
    assert app["native_apk"] is False
    assert app["physical_device_certified"] is False


def test_link_up_is_a_separate_installable_store_entry():
    app = oap_store.LINK_UP
    assert app["app_id"] == "oap.linkup"
    assert app["publisher"] == "ON ANY POSTCODE LTD"
    assert app["first_party"] is True
    assert app["install_enabled"] is True
    assert app["install_mode"] == "PWA"
    assert app["manifest_url"] == "/linkup/manifest.webmanifest"
    assert app["start_url"].startswith("/linkup")
    assert app["install_url"].startswith("/linkup")
    assert app["service_worker_url"] == "/service-worker.js"
    assert app["native_apk"] is False
    assert app["physical_device_certified"] is False


def test_store_routes_expose_installable_pwa_without_native_claim(client):
    page = client.get("/store")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "OAP Store" in body
    assert "Install OAP World" in body
    assert "Install Link Up" in body
    assert "data-oap-install" not in body
    assert "Open OAP Arena" in body
    assert "Open OAP Library" in body
    assert "Open OAP Music" in body
    assert "OPEN READY · INSTALL NOT YET PROVEN" in body
    assert "signed native Android APK" in body

    entry = client.get("/oap-store/apps/oap.world")
    assert entry.status_code == 200
    payload = entry.get_json()
    assert payload["install_enabled"] is True
    assert payload["install_mode"] == "PWA"
    assert payload["native_apk"] is False
    assert payload["native_package_available"] is False


def test_link_up_store_entry_and_manifest_are_dedicated(client):
    entry = client.get("/oap-store/apps/oap.linkup")
    assert entry.status_code == 200
    payload = entry.get_json()
    assert payload["app_id"] == "oap.linkup"
    assert payload["manifest_url"] == "/linkup/manifest.webmanifest"
    assert payload["install_url"].startswith("/linkup")
    assert payload["native_apk"] is False

    manifest_response = client.get("/linkup/manifest.webmanifest")
    assert manifest_response.status_code == 200
    assert manifest_response.content_type == "application/manifest+json"
    manifest = manifest_response.get_json()
    assert manifest["name"] == "Link Up · ON ANY POSTCODE"
    assert manifest["short_name"] == "Link Up"
    assert manifest["id"] == "/linkup"
    assert manifest["start_url"].startswith("/linkup")
    assert manifest["scope"] == "/linkup"
    assert manifest["display"] == "standalone"


def test_store_catalogue_keeps_app_install_identities_separate():
    apps = {app["app_id"]: app for app in oap_store.catalogue()}
    assert {"oap.world", "oap.linkup", "oap.music", "oap.arena", "oap.library"} <= set(apps)
    assert len(apps) == len(oap_store.catalogue())
    assert apps["oap.world"]["manifest_url"] == "/manifest.webmanifest"
    assert apps["oap.linkup"]["manifest_url"] == "/linkup/manifest.webmanifest"
    assert apps["oap.music"]["manifest_url"] == "/music/manifest.webmanifest"
    assert apps["oap.world"]["start_url"] != apps["oap.linkup"]["start_url"]
    assert apps["oap.linkup"]["start_url"] != apps["oap.music"]["start_url"]


def test_store_lists_every_public_spot_app_without_faking_installability():
    apps = {app["app_id"]: app for app in oap_store.catalogue()}
    for capability in oap_store.products.PUBLIC_SPOT_CAPABILITIES:
        app_id = f'oap.{capability["source_id"]}'
        if capability["source_id"] == "music":
            assert "oap.music" in apps
            continue
        if capability["source_id"] == "arena":
            assert "oap.arena" in apps
            continue
        assert app_id in apps
        assert apps[app_id]["first_party"] is True
        assert apps[app_id]["open_url"].startswith("/")


def test_only_apps_with_dedicated_install_proof_expose_install_buttons():
    apps = {app["app_id"]: app for app in oap_store.catalogue()}
    installable = {app_id for app_id, app in apps.items() if app["install_enabled"]}
    assert installable == {"oap.world", "oap.linkup", "oap.music", "oap.transport"}
    for app_id, app in apps.items():
        if app_id not in installable:
            assert app["manifest_url"] is None
            assert app["install_url"] is None
            assert app["release_state"] in {"open_ready", "planned"}
            if app["release_state"] == "planned":
                assert app["open_url"] is None
            else:
                assert app["open_url"]


def test_public_store_does_not_expose_founder_private_command_surfaces(client):
    body = client.get("/store").get_data(as_text=True)
    for private_route in ("/mission", "/infrastructure", "/my-world", "/global-affairs"):
        assert f'href="{private_route}"' not in body


def test_generic_store_entry_returns_catalogue_record(client):
    response = client.get("/oap-store/apps/oap.arena")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["app_id"] == "oap.arena"
    assert payload["open_url"] == "/arena"
    assert payload["install_enabled"] is False

    missing = client.get("/oap-store/apps/oap.not-real")
    assert missing.status_code == 404


def test_planned_infrastructure_apps_are_listed_without_fake_routes():
    apps = {app["app_id"]: app for app in oap_store.catalogue()}
    for app_id in ("oap.mail", "oap.vpn", "oap.cyber-security"):
        assert app_id in apps
        assert apps[app_id]["release_state"] == "planned"
        assert apps[app_id]["open_url"] is None
        assert apps[app_id]["install_url"] is None
        assert apps[app_id]["install_enabled"] is False

    cyber = apps["oap.cyber-security"]
    assert cyber["internal_intelligence"] == (
        "Neo", "Trinity", "Morpheus", "Oracle",
        "Architect", "Keymaker", "Seraph", "Agent Smith",
    )


def test_store_renders_planned_apps_without_open_or_install_claim(client):
    body = client.get("/store").get_data(as_text=True)
    assert "OAP Mail" in body
    assert "OAP Search" in body
    assert 'href="/search"' in body
    assert "OAP VPN" in body
    assert "OAP Cyber Security" in body
    assert "PLANNED · SURFACE NOT YET PROVEN" in body
    assert 'href="/mail"' not in body
    assert 'href="/vpn"' not in body
    assert 'href="/cyber-security"' not in body


def test_oap_search_is_open_ready_and_public_catalogue_only(client):
    apps = {app["app_id"]: app for app in oap_store.catalogue()}
    search = apps["oap.search"]
    assert search["release_state"] == "open_ready"
    assert search["open_url"] == "/search"
    assert search["install_enabled"] is False

    page = client.get("/search?q=music")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "OAP Search" in body
    assert "OAP Music" in body
    assert "OAP TV &amp; Media" in body
    assert "Private Link Up messages" in body
    assert "/mission" not in body
    assert "/infrastructure" not in body


def test_oap_search_does_not_return_planned_apps_without_open_routes(client):
    page = client.get("/search?q=vpn")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "No public OAP app matched." in body
    assert "Open OAP VPN" not in body


def test_oap_transport_is_a_separate_installable_os_entry(client):
    app = oap_store.OAP_TRANSPORT
    assert app["app_id"] == "oap.transport"
    assert app["install_enabled"] is True
    assert app["install_mode"] == "PWA"
    assert app["manifest_url"] == "/transport/manifest.webmanifest"
    assert app["start_url"].startswith("/transport")
    assert app["bundles"] == ("Rider", "Driver", "Travel")
    assert app["native_apk"] is False
    assert app["physical_device_certified"] is False

    entry = client.get("/oap-store/apps/oap.transport")
    assert entry.status_code == 200
    payload = entry.get_json()
    assert payload["install_enabled"] is True
    assert payload["manifest_url"] == "/transport/manifest.webmanifest"

    manifest_response = client.get("/transport/manifest.webmanifest")
    assert manifest_response.status_code == 200
    assert manifest_response.content_type == "application/manifest+json"
    manifest = manifest_response.get_json()
    assert manifest["name"] == "OAP Transport · ON ANY POSTCODE"
    assert manifest["id"] == "/transport"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"
    shortcuts = {item["name"]: item["url"].split("?", 1)[0] for item in manifest["shortcuts"]}
    assert shortcuts == {
        "Rider": "/transport/ride/rider",
        "Driver": "/transport/ride/driver",
        "Travel": "/travel",
    }


def test_transport_home_exposes_install_contract(client):
    response = client.get("/transport")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'rel="manifest" href="/transport/manifest.webmanifest"' in body
    assert "Install OAP Transport" in body
    assert "data-oap-install hidden" in body
    assert 'src="/assets/oap-os.js"' in body
