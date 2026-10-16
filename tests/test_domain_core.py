import tempfile
import unittest
from mission_control.domain_core import DomainCore, ExecutionDisabled, normalize

class DomainCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.core=DomainCore(self.tmp.name+"/domains.db")
    def tearDown(self):
        self.core.db.close()
        self.tmp.cleanup()
    def test_canonical_record_and_owner_ledger(self):
        record=self.core.create("EXAMPLE.COM","founder")
        self.assertEqual(record["name"],"example.com")
        self.assertEqual(len(self.core.mine("founder")),1)
        self.assertEqual(self.core.mine("other"),[])
        self.assertEqual(self.core.market(),[])
        self.assertEqual(self.core.db.execute("SELECT count(*) FROM ownership_ledger").fetchone()[0],1)
    def test_execution_locked(self):
        record=self.core.create("example.org","founder")
        price=self.core.evidence(record["id"],"exact_price","fixture",{"amount":"10","currency":"GBP"})
        self.core.transition(record["id"],"quoted",price)
        checkout=self.core.evidence(record["id"],"checkout","fixture",{"authorized":False})
        with self.assertRaises(ExecutionDisabled):
            self.core.transition(record["id"],"checkout_authorized",checkout)
        with self.assertRaises(ExecutionDisabled):
            self.core.transition(record["id"],"registration_pending",checkout)
        self.assertEqual(self.core.get(record["id"])["state"],"quoted")
        with self.assertRaises(ExecutionDisabled): self.core.register(record["id"],{})
    def test_cannot_force_owned_even_if_flag_requested(self):
        core=DomainCore(self.tmp.name+"/second.db",execution_enabled=True)
        try:
            record=core.create("example.co.uk","founder")
            with self.assertRaises(ValueError): core.transition(record["id"],"owned",None)
            with self.assertRaises(ExecutionDisabled): core.register(record["id"],{"authorized":True})
        finally: core.db.close()
    def test_evidence_cannot_cross_domains(self):
        a=self.core.create("example.net","founder")
        b=self.core.create("example.info","founder")
        evidence=self.core.evidence(a["id"],"exact_price","fixture",{"amount":"5"})
        with self.assertRaises(ValueError): self.core.transition(b["id"],"quoted",evidence)
    def test_invalid_names(self):
        for name in ("https://example.com","bad domain","example"):
            with self.assertRaises(ValueError): normalize(name)
if __name__=="__main__": unittest.main()
