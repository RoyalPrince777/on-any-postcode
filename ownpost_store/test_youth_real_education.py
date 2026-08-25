import unittest
from gates import app, db, uid
from youth_real_education import register_youth_real_education

if 'youth_real_education' not in app.blueprints:
    register_youth_real_education(app, db, uid)


class YouthRealEducation(unittest.TestCase):
    def setUp(self):
        self.c=app.test_client(); self.h={'X-Link-User':'1'}

    def test_health_does_not_replace_school(self):
        r=self.c.get('/api/education/health')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['replaces_school'])
        self.assertEqual(r.json['purpose'],'practical_life_learning')

    def test_practical_tracks_exist(self):
        r=self.c.get('/api/education/tracks')
        self.assertEqual(r.status_code,200)
        slugs={x['slug'] for x in r.json['tracks']}
        for slug in ['money_basics','trades','housing','food','digital_safety','civics','tax_contracts','home_maintenance']:
            self.assertIn(slug,slugs)

    def test_youth_policy_is_private_by_default(self):
        r=self.c.get('/api/youth-safety/policy')
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['privacy_default'])
        self.assertFalse(r.json['precise_location_public'])
        self.assertFalse(r.json['targeted_ads'])
        self.assertFalse(r.json['adult_public_discovery_of_minors'])
        self.assertFalse(r.json['minor_financial_execution'])
        self.assertTrue(r.json['report_block_tools'])

    def test_progress_requires_auth_and_valid_state(self):
        self.assertEqual(self.c.get('/api/education/progress/trades').status_code,401)
        self.assertEqual(self.c.post('/api/education/progress/trades',headers=self.h,json={'state':'fake'}).status_code,400)
        r=self.c.post('/api/education/progress/trades',headers=self.h,json={'state':'practising'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['progress']['state'],'practising')

if __name__=='__main__': unittest.main()
