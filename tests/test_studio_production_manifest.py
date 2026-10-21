"""Negative-boundary tests for the private Studio production manifest."""
import unittest
from uuid import uuid4

from mission_control.studio_production_manifest import validate_manifest


class StudioProductionManifestTests(unittest.TestCase):
    def setUp(self):
        self.owner = str(uuid4())
        self.manifest = {
            "owner_id": self.owner,
            "project_id": str(uuid4()),
            "episode_id": str(uuid4()),
            "duration_seconds": 600,
            "languages": ["en", "tw"],
            "assets": [{
                "asset_id": str(uuid4()),
                "owner_id": self.owner,
                "kind": "script",
                "sha256": "a" * 64,
            }],
        }

    def test_valid_is_private_and_blocked(self):
        result = validate_manifest(self.manifest, owner_id=self.owner)
        self.assertFalse(result["execution_authorised"])
        self.assertFalse(result["publish_authorised"])
        self.assertFalse(result["payment_authorised"])
        self.assertEqual(result["release_state"], "blocked")

    def test_reject_cross_owner(self):
        with self.assertRaisesRegex(ValueError, "owner_mismatch"):
            validate_manifest(self.manifest, owner_id=str(uuid4()))

    def test_reject_cross_owner_asset(self):
        self.manifest["assets"][0]["owner_id"] = str(uuid4())
        with self.assertRaisesRegex(ValueError, "asset_owner_mismatch"):
            validate_manifest(self.manifest, owner_id=self.owner)

    def test_reject_missing_hash(self):
        self.manifest["assets"][0].pop("sha256")
        with self.assertRaisesRegex(ValueError, "asset_evidence_invalid"):
            validate_manifest(self.manifest, owner_id=self.owner)

    def test_reject_invalid_duration(self):
        self.manifest["duration_seconds"] = True
        with self.assertRaisesRegex(ValueError, "duration_invalid"):
            validate_manifest(self.manifest, owner_id=self.owner)

    def test_reject_duplicate_assets(self):
        self.manifest["assets"].append(dict(self.manifest["assets"][0]))
        with self.assertRaisesRegex(ValueError, "asset_duplicate"):
            validate_manifest(self.manifest, owner_id=self.owner)


if __name__ == "__main__":
    unittest.main()
