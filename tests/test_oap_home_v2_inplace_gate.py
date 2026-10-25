"""Offline read-only certificate/version gate tests for existing native V2 app."""
import unittest
from pathlib import Path
from unittest import mock

from scripts import oap_home_v2_inplace_apk_gate as gate


class HomeV2UpdateGateTests(unittest.TestCase):
    def test_existing_v2_same_signer_newer_and_renamed_to_home(self):
        with mock.patch.object(gate, "inspect_apk", side_effect=[
            (gate.EXPECTED_PACKAGE, 4, "2.0.0-founder", ("a" * 64,)),
            (gate.EXPECTED_PACKAGE, 21, "2.1.0-founder-royal", ("a" * 64,)),
        ]), mock.patch.object(gate, "command",
                             return_value="application-label:'OAP Home'\n"):
            result = gate.verify(Path("installed-v2.apk"), Path("candidate-v2.apk"))
        self.assertIn("V2_UPDATE_IDENTITY_PASSED (offline only)", result)
        self.assertIn("No installation", result)
        self.assertIn("old Home removal", result)

    def test_signing_mismatch_blocks_v2_update(self):
        with mock.patch.object(gate, "inspect_apk", side_effect=[
            (gate.EXPECTED_PACKAGE, 4, "2.0.0-founder", ("a" * 64,)),
            (gate.EXPECTED_PACKAGE, 21, "2.1.0-founder-royal", ("b" * 64,)),
        ]), self.assertRaisesRegex(gate.BlockedUpgrade, "certificates DIFFER"):
            gate.verify(Path("installed-v2.apk"), Path("candidate-v2.apk"))

    def test_existing_v2_cannot_be_downgraded_or_reinstalled_at_same_version(self):
        for code in (4, 3):
            with self.subTest(code=code), mock.patch.object(gate, "inspect_apk", side_effect=[
                (gate.EXPECTED_PACKAGE, 4, "2.0.0-founder", ("a" * 64,)),
                (gate.EXPECTED_PACKAGE, code, "2.1.0-founder-royal", ("a" * 64,)),
            ]), self.assertRaisesRegex(gate.BlockedUpgrade, "versionCode"):
                gate.verify(Path("installed-v2.apk"), Path("candidate-v2.apk"))

    def test_old_home_package_not_accepted_for_v2_update(self):
        for installed, candidate in (
            (gate.LEGACY_PACKAGE, gate.EXPECTED_PACKAGE),
            (gate.EXPECTED_PACKAGE, gate.LEGACY_PACKAGE),
        ):
            with self.subTest(installed=installed, candidate=candidate), mock.patch.object(
                gate, "inspect_apk", side_effect=[
                    (installed, 4, "2.0.0-founder", ("a" * 64,)),
                    (candidate, 21, "2.1.0-founder-royal", ("a" * 64,)),
                ]
            ), self.assertRaisesRegex(gate.BlockedUpgrade, "V2 package"):
                gate.verify(Path("installed-v2.apk"), Path("candidate-v2.apk"))

    def test_candidate_must_show_single_oap_home_name(self):
        with mock.patch.object(gate, "inspect_apk", side_effect=[
            (gate.EXPECTED_PACKAGE, 4, "2.0.0-founder", ("a" * 64,)),
            (gate.EXPECTED_PACKAGE, 21, "2.1.0-founder-royal", ("a" * 64,)),
        ]), mock.patch.object(
            gate, "command", return_value="application-label:'OAP Home V2'\n"
        ), self.assertRaisesRegex(gate.BlockedUpgrade, "display name"):
            gate.verify(Path("installed-v2.apk"), Path("candidate-v2.apk"))

    def test_missing_apk_inspection_tools_block(self):
        with mock.patch.object(gate.shutil, "which", return_value=None), self.assertRaisesRegex(
            gate.BlockedUpgrade, "unavailable"
        ):
            gate.command("apksigner", "verify", "example.apk")

    def test_never_installs_uninstalls_or_changes_home(self):
        source = Path(gate.__file__).read_text(encoding="utf-8")
        for forbidden in ("pm uninstall", "adb install", "pm install",
                          "rm -rf", "startActivity(", "OAP_HOME_KEYSTORE_"):
            self.assertNotIn(forbidden, source)
        self.assertIn('EXPECTED_PACKAGE = "com.onanypostcode.oaphome.v2"', source)
        self.assertIn('LEGACY_PACKAGE = "com.onanypostcode.oaphome"', source)
        self.assertIn("--installed-v2-apk", source)


if __name__ == "__main__":
    unittest.main()
