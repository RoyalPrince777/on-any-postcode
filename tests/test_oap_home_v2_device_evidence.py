"""Proof collector must preserve uncertainty and never change Android packages."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import oap_home_v2_device_evidence as probe


def _metadata(package, code, signer="a" * 64, label="OAP Home"):
    return {
        "package": package,
        "version_code": code,
        "signer_sha256": signer,
        "label": label,
    }


def _visible_v2(version=4, signer="a" * 64):
    return {
        "package": probe.V2_PACKAGE,
        "package_visible": True,
        "visibility": "visible",
        "version_code": version,
        "signer_sha256": signer,
    }


def _unknown_v2():
    return {
        "package": probe.V2_PACKAGE,
        "package_visible": False,
        "visibility": "unknown",
        "version_code": None,
        "signer_sha256": None,
    }


class ReadOnlyDeviceEvidenceTests(unittest.TestCase):
    def test_package_visibility_failure_is_unknown_not_not_installed(self):
        with mock.patch.object(probe, "_run", return_value=None):
            report = probe.installed_package(probe.V2_PACKAGE)
        assert report["visibility"] == "unknown"
        assert report["package_visible"] is False
        assert report["signer_sha256"] is None
        with mock.patch.object(probe, "_run", return_value=""):
            report = probe.installed_package(probe.LEGACY_PACKAGE)
        assert report["visibility"] == "unknown"
        assert report["version_code"] is None

    def test_unreadable_installed_apk_never_approves_signature(self):
        with mock.patch.object(
            probe, "_run", return_value="package:/data/app/x/base.apk\n"
        ), mock.patch.object(
            probe, "_apk_info", return_value=_metadata(None, None, None, None)
        ):
            report = probe.installed_package(probe.V2_PACKAGE)
        assert report["visibility"] == "visible"
        assert report["version_code"] is None
        assert report["signer_sha256"] is None

    def test_apk_info_uses_successful_package_and_signer_inspection_only(self):
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "base.apk"
            apk.write_bytes(b"fixture not a real apk")
            badging = (
                "package: name='com.onanypostcode.oaphome.v2' "
                "versionCode='21' versionName='2.1.0-founder-royal'\n"
                "application-label:'OAP Home'\n"
            )
            cert = "Signer #1 certificate SHA-256 digest: " + "a" * 64 + "\n"
            with mock.patch.object(probe, "_run", side_effect=[badging, cert]):
                actual = probe._apk_info(apk)
            assert actual == _metadata(probe.V2_PACKAGE, 21)
            with mock.patch.object(probe, "_run", side_effect=[None, None]):
                unreadable = probe._apk_info(apk)
            assert unreadable == _metadata(None, None, None, None)

    def test_fully_verified_candidate_only_proves_identity_not_install(self):
        with mock.patch.object(probe, "installed_package", side_effect=[
            _visible_v2(), _unknown_v2(), _unknown_v2(),
        ]), mock.patch.object(
            probe, "_apk_info", return_value=_metadata(probe.V2_PACKAGE, 21)
        ):
            result = probe.inspect(Path("candidate.apk"))
        assert result["candidate_update_verdict"] == "IDENTITY_COMPATIBLE_NOT_INSTALLED"
        assert result["koradaso_internet"]["visibility"] == "unknown"
        assert result["browser_launch_proven"] is False
        assert result["no_install_or_uninstall"] is True
        assert result["founder_final_required"] is True

    def test_new_candidate_rejected_on_signature_mismatch_or_version(self):
        cases = (
            (21, "b" * 64, "HOLD_SIGNER_MISMATCH"),
            (4, "a" * 64, "HOLD_NOT_NEWER"),
            (3, "a" * 64, "HOLD_NOT_NEWER"),
        )
        for code, signer, expected in cases:
            with mock.patch.object(probe, "installed_package", side_effect=[
                _visible_v2(), _unknown_v2(), _unknown_v2(),
            ]), mock.patch.object(
                probe, "_apk_info", return_value=_metadata(probe.V2_PACKAGE, code, signer)
            ):
                result = probe.inspect(Path("candidate.apk"))
            assert result["candidate_update_verdict"] == expected

    def test_wrong_package_or_label_or_unknown_installed_v2_blocks(self):
        candidates = (
            _metadata(probe.LEGACY_PACKAGE, 21),
            _metadata(probe.V2_PACKAGE, 21, label="OAP Home V2"),
        )
        for candidate in candidates:
            with mock.patch.object(probe, "installed_package", side_effect=[
                _visible_v2(), _unknown_v2(), _unknown_v2(),
            ]), mock.patch.object(probe, "_apk_info", return_value=candidate):
                result = probe.inspect(Path("candidate.apk"))
            assert result["candidate_update_verdict"] == "HOLD_MISSING_EVIDENCE"
        with mock.patch.object(probe, "installed_package", side_effect=[
            _unknown_v2(), _unknown_v2(), _unknown_v2(),
        ]), mock.patch.object(
            probe, "_apk_info", return_value=_metadata(probe.V2_PACKAGE, 21)
        ):
            result = probe.inspect(Path("candidate.apk"))
        assert result["candidate_update_verdict"] == "HOLD_MISSING_EVIDENCE"

    def test_no_candidate_is_read_only_and_old_home_never_automatically_removed(self):
        with mock.patch.object(probe, "installed_package", side_effect=[
            _visible_v2(), _unknown_v2(), _unknown_v2(),
        ]):
            result = probe.inspect()
        assert result["candidate"] is None
        assert result["candidate_update_verdict"] == "HOLD_MISSING_EVIDENCE"
        source = Path(probe.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "pm uninstall", "adb install", "adb uninstall", "pm install",
            "am start", "os.system(", "shutil.rmtree", "subprocess.Popen",
        ):
            assert forbidden not in source
