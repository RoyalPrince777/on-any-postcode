"""No-device tests for Redmi acceptance snapshot. No release claim."""
from scripts.koradaso_redmi_install_probe import inspect_redmi


def test_local_installed_debug_build_still_not_certified():
    def command(*args):
        if args[:1] == ("getprop",):
            return "25028RN03A"
        if args[:1] == ("pm",):
            return "package:/data/app/com.onanypostcode.oapworld/base.apk"
        raise AssertionError("unexpected command")
    result = inspect_redmi(command=command, local_page=lambda: 200)
    assert result["status"] == "device_probe_observed"
    assert result["android_package_detected"]
    assert result["signed_release_identity_verified"] is False
    assert result["production_certified"] is False


def test_missing_package_or_local_route_is_unknown():
    assert inspect_redmi(
        command=lambda *_args: "Redmi A5", local_page=lambda: 0
    )["status"] == "unknown"
    assert inspect_redmi(
        command=lambda *args: "Redmi A5" if args[0] == "getprop" else "",
        local_page=lambda: 200
    )["production_certified"] is False
