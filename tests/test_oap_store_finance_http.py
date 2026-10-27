"""HTTP acceptance of guarded OAP Store finance discovery.

This is not evidence of device installation, signed APK registration, or
bank authorisation.
"""


def test_finance_discovery_in_oap_store_without_install_buttons(client):
    response = client.get("/store")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    text = response.get_data(as_text=True)
    for app_id, name, path in (
        ("oap.sika", "SIKA Finance", "/sika"),
        ("oap.pay", "OAP Pay", "/pay"),
        ("oap.bank", "OAP Bank", "/pay/bank"),
    ):
        assert f'data-oap-store-app="{app_id}"' in text
        section = text.split(f'data-oap-store-app="{app_id}"', 1)[1].split("</section>", 1)[0]
        assert f'href="{path}"' in section
        assert f"Open {name}" in section
        assert "INSTALL NOT YET PROVEN" in section
        assert f"Install {name}" not in section


def test_finance_catalogue_http_fails_closed_for_downloads(client):
    response = client.get("/oap-store/apps")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    apps = {a["app_id"]: a for a in response.get_json()["apps"]}
    for app_id in ("oap.sika", "oap.pay", "oap.bank"):
        app = apps[app_id]
        assert app["install_enabled"] is False
        assert app["install_url"] is None
        assert app["manifest_url"] is None
        assert app["native_package_available"] is False
        assert app["physical_device_certified"] is False
