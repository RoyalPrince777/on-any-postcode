"""The OAP Store is the single truthful front door for finance app discovery."""
from mission_control import oap_store


def test_finance_apps_are_in_single_catalogue_without_false_install_claims():
    apps = {app["app_id"]: app for app in oap_store.catalogue()}
    for app_id, url in (("oap.pay", "/pay"), ("oap.bank", "/pay/bank")):
        item = apps[app_id]
        assert item["distribution"] == "OAP Store"
        assert item["publisher"] == "ON ANY POSTCODE LTD"
        assert item["first_party"] is True
        assert item["open_url"] == url
        assert item["release_state"] == "open_ready"
        assert item["install_enabled"] is False
        assert item["native_package_available"] is False
        assert item["native_apk"] is False
        assert item["physical_device_certified"] is False


def test_finance_apps_have_unique_store_ids():
    apps = oap_store.catalogue()
    ids = [app["app_id"] for app in apps]
    assert len(ids) == len(set(ids))
