"""Boundary tests for the SMI civic review-only upgrade."""
import unittest

from mission_control import agents
from mission_control.civic_accountability_review import (
    BRANCHES,
    civic_accountability_snapshot,
    validate_review_entry,
)


class CivicAccountabilityReviewTests(unittest.TestCase):
    def test_registry_identity_and_permissions_unchanged(self):
        before = tuple((a["agent_id"], a["name"], a["role"], a.get("permissions"))
                       for a in agents.AGENT_REGISTRY)
        snapshot = civic_accountability_snapshot()
        after = tuple((a["agent_id"], a["name"], a["role"], a.get("permissions"))
                      for a in agents.AGENT_REGISTRY)
        self.assertEqual(before, after)
        self.assertEqual(snapshot["canonical_agent_ids"], tuple(row[0] for row in before))
        self.assertEqual(snapshot["canonical_agent_count"], agents.LOCKED_AGENT_COUNT)
        self.assertEqual(snapshot["activation"], "disabled")
        self.assertEqual(snapshot["green_gate"], "HOLD")

    def test_review_branches_have_no_identity_or_permissions(self):
        snapshot = civic_accountability_snapshot()
        self.assertEqual(len(snapshot["specialist_review_branches"]), len(BRANCHES))
        self.assertEqual(tuple(x["branch"] for x in snapshot["specialist_review_branches"]), BRANCHES)
        for candidate in snapshot["specialist_review_branches"]:
            self.assertIsNone(candidate["agent_id"])
            self.assertEqual(candidate["permissions"], ())
            self.assertEqual(candidate["status"], "supervised_candidate")

    def test_review_preserves_dissent_and_never_activates(self):
        entry = {"case_id": "review-1", "purpose": "evaluate a public claim",
                 "source_links": ["https://example.org/evidence"],
                 "dissent": "Evidence disputed.", "status": "reviewed_with_dissent"}
        output = validate_review_entry(entry)
        self.assertEqual(output["dissent"], "Evidence disputed.")
        self.assertEqual(output["status"], "reviewed_with_dissent")
        self.assertEqual(output["activation"], "disabled")

    def test_unauthorised_promotions_and_permissions_fail_closed(self):
        entry = {"case_id": "review-1", "purpose": "evaluate claim",
                 "source_links": ["https://example.org/source"],
                 "dissent": "", "status": "active"}
        with self.assertRaises(ValueError):
            validate_review_entry(entry)
        entry["status"] = "draft"
        entry["permissions"] = ("EXECUTE",)
        with self.assertRaises(ValueError):
            validate_review_entry(entry)
        del entry["permissions"]
        entry["agent_id"] = "FAKE-001"
        with self.assertRaises(ValueError):
            validate_review_entry(entry)

    def test_missing_evidence_fails_closed(self):
        with self.assertRaises(ValueError):
            validate_review_entry({"case_id": "no-evidence", "purpose": "claim",
                                   "source_links": [], "dissent": "", "status": "draft"})


if __name__ == "__main__":
    unittest.main()


def test_status_route_is_founder_only_and_no_store(monkeypatch):
    import app as app_module
    from mission_control import web_security

    monkeypatch.setattr(
        web_security,
        "current_authenticated_user",
        lambda: {"id": "founder-test", "name": "Founder", "email": "founder@example.test"},
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: False)
    client = app_module.app.test_client()
    route = "/mission/smi/civic-accountability/status"
    assert client.get(route).status_code == 403

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    response = client.get(route)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    payload = response.get_json()
    assert payload["activation"] == "disabled"
    assert payload["green_gate"] == "HOLD"
    assert all(item["agent_id"] is None for item in payload["specialist_review_branches"])
