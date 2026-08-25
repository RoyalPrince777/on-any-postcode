import unittest
from gates import app, db, uid
from oap_finalization import register_finalization

if 'oap_finalization' not in app.blueprints:
    register_finalization(app, db, uid)


class OAPFinalization(unittest.TestCase):
    def setUp(self): self.c=app.test_client()

    def test_capabilities_do_not_fake_live(self):
        r=self.c.get('/api/readiness/capabilities')
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['no_fake_live_labels'])
        for x in r.json['capabilities']:
            if x['status']!='enabled': self.assertFalse(x['live_claim'])

    def test_core_readiness_probes_mounted_organs(self):
        r=self.c.get('/api/readiness/core')
        self.assertEqual(r.status_code,200)
        names={x['name'] for x in r.json['checks']}
        for name in {'link','spot_family','royal','intelligence','world_intelligence','earth_intelligence','universe_intelligence','education'}:
            self.assertIn(name,names)
        self.assertEqual(r.json['authority'],'human_final')

    def test_readiness_contract(self):
        self.c.get('/api/readiness/core')
        r=self.c.get('/api/readiness')
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['no_fake_green'])
        self.assertEqual(r.json['green_definition'],'tested_and_live')
        self.assertEqual(r.json['purple_definition'],'learning_until_verified')

if __name__=='__main__': unittest.main()
