"""Unit checks for offline, read-only OAP Home V2 original-package upgrade gate."""
import unittest
from pathlib import Path
from unittest import mock

from scripts import oap_home_v2_inplace_apk_gate as gate


class HomeInPlaceGateTests(unittest.TestCase):
    def test_exact_original_package_and_signer_allows_only_offline_proof(self):
        with mock.patch.object(gate, "inspect_apk", side_effect=[
            (gate.EXPECTED_PACKAGE, 3, "0.1-founder", ("a" * 64,)),
            (gate.EXPECTED_PACKAGE, 21, "2.0.0-founder-inplace", ("a" * 64,)),
        ]), mock.patch.object(gate, "command",
                            return_value="application-label:'OAP Home'\n"):
            result = gate.verify(Path("old.apk"), Path("candidate.apk"))
        self.assertIn("IDENTITY_GATE_PASSED (offline only)", result)
        self.assertIn("No installation", result)

    def test_signing_mismatch_blocks_old_home_overwrite(self):
        with mock.patch.object(gate, "inspect_apk", side_effect=[
            (gate.EXPECTED_PACKAGE, 3, "0.1-founder", ("a" * 64,)),
            (gate.EXPECTED_PACKAGE, 21, "2.0.0-founder-inplace", ("b" * 64,)),
        ]), self.assertRaisesRegex(gate.BlockedUpgrade, "certificates DIFFER"):
            gate.verify(Path("old.apk"), Path("candidate.apk"))

    def test_same_or_lower_version_cannot_install(self):
        for code in (3, 2):
            with self.subTest(code=code), mock.patch.object(gate, "inspect_apk", side_effect=[
                (gate.EXPECTED_PACKAGE, 3, "0.1-founder", ("a" * 64,)),
                (gate.EXPECTED_PACKAGE, code, "2.0.0-founder-inplace", ("a" * 64,)),
            ]), self.assertRaisesRegex(gate.BlockedUpgrade, "versionCode"):
                gate.verify(Path("old.apk"), Path("candidate.apk"))

    def test_no_duplicate_v2_package_allowed(self):
        with mock.patch.object(gate, "inspect_apk", side_effect=[
            (gate.EXPECTED_PACKAGE, 3, "0.1-founder", ("a" * 64,)),
            ("com.onanypostcode.oaphome.v2", 21, "2.0.0-founder", ("a" * 64,)),
        ]), self.assertRaisesRegex(gate.BlockedUpgrade, "ORIGINAL"):
            gate.verify(Path("old.apk"), Path("candidate.apk"))

    def test_unexpected_label_blocks(self):
        with mock.patch.object(gate, "inspect_apk", side_effect=[
            (gate.EXPECTED_PACKAGE, 3, "0.1-founder", ("a" * 64,)),
            (gate.EXPECTED_PACKAGE, 21, "2.0.0-founder-inplace", ("a" * 64,)),
        ]), mock.patch.object(gate, "command", return_value="application-label:'OAP Home OLD'\n"), self.assertRaisesRegex(gate.BlockedUpgrade, "display name"):
            gate.verify(Path("old.apk"), Path("candidate.apk"))

    def test_missing_tools_fail_closed(self):
        with mock.patch.object(gate.shutil, "which", return_value=None), self.assertRaisesRegex(gate.BlockedUpgrade, "unavailable"):
            gate.command("apksigner", "verify", "example.apk")

    def test_gate_never_installs_or_uninstalls_apps(self):
        source = Path(gate.__file__).read_text(encoding="utf-8")
        self.assertNotIn("pm uninstall", source)
        self.assertNotIn("adb install", source)
        self.assertNotIn("pm install", source)
        self.assertNotIn("rm -rf", source)
        self.assertNotIn("startActivity(", source)
        self.assertNotIn("OAP_HOME_KEYSTORE_", source)


if __name__ == "__main__":
    unittest.main()
