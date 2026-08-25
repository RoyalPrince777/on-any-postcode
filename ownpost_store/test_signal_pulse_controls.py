import unittest
from gates import app

class SignalPulseControls(unittest.TestCase):
    def setUp(self):
        self.c=app.test_client(); self.h={'X-Link-User':'1'}

    def test_optional_pulse_can_be_suppressed(self):
        r=self.c.post('/api/pulse/preferences',headers=self.h,json={'category':'ride','enabled':False})
        self.assertEqual(r.status_code,200)
        e=self.c.post('/api/event-bridge',headers=self.h,json={'kind':'ride_state','title':'Driver arriving','target_user_id':1})
        self.assertEqual(e.status_code,201)
        self.assertFalse(e.json['delivered'])
        self.assertTrue(e.json['suppressed_by_preference'])

    def test_safety_pulse_cannot_be_suppressed(self):
        r=self.c.post('/api/pulse/preferences',headers=self.h,json={'category':'safety','enabled':False})
        self.assertEqual(r.status_code,403)
        e=self.c.post('/api/event-bridge',headers=self.h,json={'kind':'guardian_alert','title':'Safety review','target_user_id':1})
        self.assertEqual(e.status_code,201)
        self.assertTrue(e.json['delivered'])
        self.assertTrue(e.json['protected'])

    def test_signal_subscriptions_are_coarse_only(self):
        r=self.c.post('/api/signals/subscriptions',headers=self.h,json={'scope':'postcode','scope_value':'SE15'})
        self.assertEqual(r.status_code,200)
        e=self.c.post('/api/event-bridge',headers=self.h,json={'kind':'movement_disruption','title':'Road issue','scope':'postcode','scope_value':'SE15'})
        self.assertEqual(e.status_code,201)
        self.assertGreaterEqual(e.json['matching_subscribers'],1)
        bad=self.c.post('/api/signals/subscriptions',headers=self.h,json={'scope':'postcode','scope_value':'SE15','coordinates':[51.5,-0.1]})
        self.assertEqual(bad.status_code,400)

if __name__=='__main__': unittest.main()
