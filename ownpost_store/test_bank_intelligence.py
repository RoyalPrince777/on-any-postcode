import os, unittest
os.environ.setdefault('OAP_BANKING_AUTHORISED','false')
os.environ.setdefault('OAP_SIKA_REGULATED_ENABLED','false')
from gates import app, db, uid
from bank_intelligence import register_bank_intelligence

if 'bank_intelligence' not in app.blueprints:
    register_bank_intelligence(app, db, uid)


class BankIntelligence(unittest.TestCase):
    def setUp(self): self.c=app.test_client()

    def test_health_is_intelligence_not_fake_bank(self):
        r=self.c.get('/api/bank-intelligence/health')
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['intelligence_live'])
        self.assertFalse(r.json['banking_service_live'])
        self.assertFalse(r.json['autonomous_financial_execution'])

    def test_overview_blocks_regulated_claims(self):
        r=self.c.get('/api/bank-intelligence')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['can_move_money'])
        self.assertFalse(r.json['can_open_accounts'])
        self.assertFalse(r.json['can_issue_cards'])
        self.assertTrue(r.json['no_licence_claim'])
        self.assertFalse(r.json['sika_is_legal_tender'])

    def test_regulated_action_fails_closed(self):
        r=self.c.post('/api/bank-intelligence/check',json={'action':'transfer_money'})
        self.assertEqual(r.status_code,403)
        self.assertEqual(r.json['status'],'blocked_pending_authorisation')
        self.assertFalse(r.json['execution'])

    def test_advisory_action_allowed_without_execution(self):
        r=self.c.post('/api/bank-intelligence/check',json={'action':'explain_budgeting'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['status'],'advisory_only')
        self.assertFalse(r.json['execution'])

    def test_sika_boundary(self):
        r=self.c.get('/api/bank-intelligence/sika')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['legal_tender'])
        self.assertFalse(r.json['regulated_payments_enabled'])
        self.assertTrue(r.json['bank_separate'])

if __name__=='__main__': unittest.main()
