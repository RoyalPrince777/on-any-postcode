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
    assert "opens its own installer surface" in body
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
    assert set(apps) == {"oap.world", "oap.linkup"}
    assert apps["oap.world"]["manifest_url"] == "/manifest.webmanifest"
    assert apps["oap.linkup"]["manifest_url"] == "/linkup/manifest.webmanifest"
    assert apps["oap.world"]["start_url"] != apps["oap.linkup"]["start_url"]
