"""Contract checks for design-only OAP agent passports."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "mission_control" / "agent_passports.json"


class AgentPassportContractTests(unittest.TestCase):
    def test_registry_has_unique_complete_passports(self):
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        fields = data["fields"]
        self.assertEqual(len(fields), 21)
        self.assertEqual(len(set(fields)), 21)
        ids = set()
        for entry in data["entries"]:
            self.assertEqual(set(entry), set(fields))
            self.assertTrue(all(entry[key] is not None and entry[key] != "" for key in fields))
            self.assertNotIn(entry["agent_id"], ids)
            ids.add(entry["agent_id"])
            self.assertEqual(entry["authority"], "advisory-only")
            self.assertEqual(entry["environment"], "design-only")
            self.assertEqual(entry["status"], "proposed")
            self.assertEqual(entry["tools"], [])
        self.assertGreater(len(ids), 0)

    def test_named_families_present(self):
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        names = {entry["official_name"] for entry in data["entries"]}
        for name in ("Neo", "Agent Smith", "Colonel Hathi", "Hathi Jr.",
                     "Winifred", "Akela", "King Louie", "Bandar-log",
                     "AKAN", "MANSA", "Queen Bee"):
            self.assertIn(name, names)


if __name__ == "__main__":
    unittest.main()
