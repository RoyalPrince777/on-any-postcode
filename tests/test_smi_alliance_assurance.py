"""Deterministic checks for the read-only SMI alliance assurance contract."""
import unittest

from oap.smi.alliance_assurance import ROLES, review_assurance


class AllianceAssuranceTests(unittest.TestCase):
    def test_pass_requires_every_observed_requirement(self):
        result = review_assurance(
            "routing", {"build": True, "real_route": True},
            {"build": True, "real_route": True},
        )
        self.assertEqual(result.verdict, "PASS")
        self.assertEqual(result.missing, ())
        self.assertEqual(result.contradictions, ())

    def test_missing_evidence_blocks(self):
        result = review_assurance("mail", {"inbound": True}, {})
        self.assertEqual(result.verdict, "BLOCKED")
        self.assertEqual(result.missing, ("inbound",))

    def test_explicit_failure_blocks(self):
        result = review_assurance("bank", {"ledger": True}, {"ledger": False})
        self.assertEqual(result.verdict, "BLOCKED")
        self.assertEqual(result.contradictions, ("ledger",))

    def test_mixed_evidence_cannot_pass(self):
        result = review_assurance(
            "cloud", {"a": True, "b": True, "c": True},
            {"a": True, "b": False},
        )
        self.assertEqual(result.verdict, "BLOCKED")
        self.assertEqual(result.missing, ("c",))
        self.assertEqual(result.contradictions, ("b",))

    def test_empty_requirements_never_pass(self):
        with self.assertRaises(ValueError):
            review_assurance("arena", {}, {})

    def test_expected_false_cannot_weaken_gate(self):
        with self.assertRaises(ValueError):
            review_assurance("arena", {"security": False}, {"security": True})

    def test_invalid_domain_rejected(self):
        with self.assertRaises(ValueError):
            review_assurance(" ", {"build": True}, {"build": True})

    def test_alliance_roles_preserved(self):
        names = {name for name, _ in ROLES}
        self.assertTrue({"gorilla", "tank", "dozer", "twin_one", "twin_two", "agent_smith", "brown", "jones", "johnson", "jackson", "thompson", "shere_khan"}.issubset(names))


if __name__ == "__main__":
    unittest.main()
