"""Negative tests for the design-only agent passport contract."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "mission_control" / "agent_passport_contract.py"
spec = importlib.util.spec_from_file_location("agent_passport_contract", MODULE)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class PassportNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = json.loads((ROOT / "mission_control" / "agent_passports.json").read_text(encoding="utf-8"))

    def assert_rejected(self, mutation):
        data = copy.deepcopy(self.good)
        mutation(data)
        with self.assertRaises(contract.PassportContractError):
            contract.validate_registry(data)

    def test_valid_registry(self):
        self.assertTrue(contract.validate_registry(self.good))
        self.assertEqual(len(contract.load_registry()["entries"]), 48)

    def test_missing_field(self):
        self.assert_rejected(lambda d: d["entries"][0].pop("authority"))

    def test_extra_field(self):
        self.assert_rejected(lambda d: d["entries"][0].update({"execute": True}))

    def test_duplicate_id(self):
        self.assert_rejected(lambda d: d["entries"][1].update({"agent_id": d["entries"][0]["agent_id"]}))

    def test_duplicate_name(self):
        self.assert_rejected(lambda d: d["entries"][1].update({"official_name": d["entries"][0]["official_name"].upper()}))

    def test_permission_elevation(self):
        self.assert_rejected(lambda d: d["entries"][0].update({"authority": "admin"}))

    def test_tool_grant(self):
        self.assert_rejected(lambda d: d["entries"][0].update({"tools": ["deploy"]}))

    def test_production_promotion(self):
        self.assert_rejected(lambda d: d["entries"][0].update({"environment": "production"}))

    def test_status_promotion(self):
        self.assert_rejected(lambda d: d["entries"][0].update({"status": "verified"}))

    def test_unknown_family(self):
        self.assert_rejected(lambda d: d["entries"][0].update({"family": "unknown"}))

    def test_malformed_field_types(self):
        self.assert_rejected(lambda d: d["entries"][0].update({"capabilities": "execute"}))

    def test_missing_registry(self):
        with self.assertRaises(contract.PassportContractError):
            contract.load_registry(ROOT / "nonexistent-passports.json")


if __name__ == "__main__":
    unittest.main()
