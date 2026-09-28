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


def test_store_routes_expose_installable_pwa_without_native_claim(client):
    page = client.get("/store")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "OAP Store" in body
    assert "Install OAP World" in body
    assert "data-oap-install" in body
    assert "signed native Android APK" in body

    entry = client.get("/oap-store/apps/oap.world")
    assert entry.status_code == 200
    payload = entry.get_json()
    assert payload["install_enabled"] is True
    assert payload["install_mode"] == "PWA"
    assert payload["native_apk"] is False
    assert payload["native_package_available"] is False
