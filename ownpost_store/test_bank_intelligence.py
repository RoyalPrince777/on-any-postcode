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
        self.assertTrue(r.json['education_before_action'])
        self.assertTrue(r.json['adaptive'])
        self.assertTrue(r.json['coherent'])

    def test_overview_blocks_regulated_claims(self):
        r=self.c.get('/api/bank-intelligence')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['can_move_money'])
        self.assertFalse(r.json['can_open_accounts'])
        self.assertFalse(r.json['can_issue_cards'])
        self.assertTrue(r.json['no_licence_claim'])
        self.assertFalse(r.json['sika_is_legal_tender'])
        self.assertIn('youth',r.json['account_modes'])
        self.assertIn('business',r.json['account_modes'])
        self.assertIn('elder_safe',r.json['account_modes'])

    def test_modern_feature_model(self):
        r=self.c.get('/api/bank-intelligence/features')
        self.assertEqual(r.status_code,200)
        names={x['slug']:x for x in r.json['features']}
        for slug in ['royal_pots','money_intelligence','salary_intelligence','card_intelligence','fraud_guardian','global_money_intelligence','credit_intelligence','business_intelligence','open_banking_intelligence','human_support','sika_bridge']:
            self.assertIn(slug,names)
        self.assertEqual(names['royal_pots']['mode'],'intelligence_now')
        self.assertEqual(names['card_intelligence']['mode'],'regulated_future')
        self.assertFalse(names['card_intelligence']['execution_enabled'])
        self.assertTrue(r.json['independent_oap_design'])

    def test_family_all_ages_protection(self):
        r=self.c.get('/api/bank-intelligence/family')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['rules']['targeted_credit_marketing'])
        self.assertFalse(r.json['rules']['autonomous_borrowing'])
        self.assertTrue(r.json['rules']['age_appropriate_financial_education'])
        self.assertTrue(r.json['rules']['guardian_controls_where_required'])
        self.assertFalse(r.json['precise_location_required'])

    def test_regulated_action_fails_closed(self):
        for action in ['transfer_money','open_account','issue_card','connect_open_banking_account']:
            r=self.c.post('/api/bank-intelligence/check',json={'action':action})
            self.assertEqual(r.status_code,403,action)
            self.assertEqual(r.json['status'],'blocked_pending_authorisation')
            self.assertFalse(r.json['execution'])

    def test_advisory_action_allowed_without_execution(self):
        r=self.c.post('/api/bank-intelligence/check',json={'action':'explain_budgeting'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['status'],'advisory_only')
        self.assertFalse(r.json['execution'])

    def test_planning_simulation_moves_no_money(self):
        r=self.c.post('/api/bank-intelligence/plan',json={'monthly_income':2500,'goals':['rent','emergency']})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['mode'],'simulation_only')
        self.assertFalse(r.json['execution'])
        self.assertIn('bills',r.json['suggested_buckets'])
        self.assertIn('savings',r.json['suggested_buckets'])

    def test_sika_boundary(self):
        r=self.c.get('/api/bank-intelligence/sika')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['legal_tender'])
        self.assertFalse(r.json['regulated_payments_enabled'])
        self.assertTrue(r.json['bank_separate'])

if __name__=='__main__': unittest.main()
