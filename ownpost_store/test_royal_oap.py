import os, unittest
os.environ.setdefault('OAP_FOUNDER_USER_ID','1')
from gates import app, db, uid
from royal_oap import register_royal_oap

if 'royal_oap' not in app.blueprints:
    register_royal_oap(app, db, uid)


class RoyalOAP(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()
        self.founder = {'X-Link-User':'1'}
        self.other = {'X-Link-User':'2'}

    def test_public_identity_is_additive(self):
        r = self.c.get('/api/royal')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json['replaces_oap'])
        self.assertTrue(r.json['public_private_separation'])
        self.assertFalse(r.json['government_claim'])
        self.assertFalse(r.json['legal_royalty_claim'])

    def test_founder_dashboard_is_private(self):
        self.assertEqual(self.c.get('/api/royal/founder').status_code, 403)
        self.assertEqual(self.c.get('/api/royal/founder', headers=self.other).status_code, 403)
        r = self.c.get('/api/royal/founder', headers=self.founder)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['access'], 'founder_only')
        self.assertEqual(r.json['profile_creation'], 'founder_only')

    def test_bank_remains_future_and_licensing_gated(self):
        r = self.c.get('/api/royal/institutions')
        self.assertEqual(r.status_code, 200)
        bank = next(x for x in r.json['institutions'] if x['layer']=='prince_sovereign_bank')
        self.assertEqual(bank['status'], 'future')
        self.assertEqual(bank['legal_state'], 'requires_licensing')

    def test_only_founder_can_change_registry_state(self):
        self.assertEqual(self.c.post('/api/royal/registry/royal_empire/state',headers=self.other,json={'status':'active'}).status_code,403)
        r = self.c.post('/api/royal/registry/royal_empire/state',headers=self.founder,json={'status':'active'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['institution']['status'],'active')

if __name__=='__main__':
    unittest.main()
