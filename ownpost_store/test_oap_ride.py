import os, unittest
os.environ.setdefault('OAP_RIDE_COMMERCIAL_AUTHORISED','false')
from gates import app

class OAPRide(unittest.TestCase):
    def setUp(self):
        self.c=app.test_client(); self.h={'X-Link-User':'1'}

    def test_health_and_parent(self):
        r=self.c.get('/api/ride/health'); self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['dispatch_software_live']); self.assertFalse(r.json['commercial_ride_execution'])
        self.assertEqual(r.json['parent'],'Movement'); self.assertEqual(r.json['authority'],'human_final')

    def test_overview_has_oap_language_and_safety(self):
        r=self.c.get('/api/ride'); self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['name'],'OAP Ride'); self.assertEqual(r.json['intelligence'],'Ride Intelligence')
        self.assertIn('local_first',r.json['principles']); self.assertIn('youth_safe',r.json['ride_types'])

    def test_estimate_is_planning_only(self):
        r=self.c.post('/api/ride/estimate',json={'origin':'CR4','destination':'SW11','distance_km':10})
        self.assertEqual(r.status_code,200); self.assertTrue(r.json['planning_only']); self.assertFalse(r.json['charged'])
        self.assertFalse(r.json['dynamic_surge'])

    def test_request_requires_auth(self):
        self.assertEqual(self.c.post('/api/ride/requests',json={'origin':'A','destination':'B'}).status_code,401)

    def test_youth_safe_request_requires_guardian(self):
        r=self.c.post('/api/ride/requests',headers=self.h,json={'origin':'CR4','destination':'SW11','postcode':'CR4','ride_type':'youth_safe'})
        self.assertEqual(r.status_code,201); self.assertTrue(r.json['guardian_required'])
        self.assertEqual(r.json['dispatch_state'],'planning_only'); self.assertEqual(r.json['payment_state'],'not_charged')

    def test_commercial_accept_fails_closed(self):
        r=self.c.post('/api/ride/999/accept',headers=self.h)
        self.assertEqual(r.status_code,403); self.assertFalse(r.json['execution'])
        self.assertEqual(r.json['authority'],'human_final')

if __name__=='__main__': unittest.main()
