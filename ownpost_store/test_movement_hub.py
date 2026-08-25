import unittest
from gates import app

class MovementHub(unittest.TestCase):
    def setUp(self): self.c=app.test_client()

    def test_health_and_structure(self):
        r=self.c.get('/api/movement/health'); self.assertEqual(r.status_code,200); self.assertTrue(r.json['ok'])
        r=self.c.get('/api/movement'); self.assertEqual(r.status_code,200)
        self.assertIn('ride',r.json['modes']); self.assertTrue(r.json['local_first']); self.assertFalse(r.json['autonomous_real_world_execution'])

    def test_safety_boundaries(self):
        r=self.c.get('/api/movement/safety'); self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['certified_commercial_drivers_required']); self.assertTrue(r.json['insurance_required_for_commercial_ride'])
        self.assertFalse(r.json['precise_location_public']); self.assertFalse(r.json['trip_data_for_ads'])

if __name__=='__main__': unittest.main()
