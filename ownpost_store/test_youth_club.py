import unittest
from gates import app

class YouthClub(unittest.TestCase):
    def setUp(self):
        self.c=app.test_client(); self.h={'X-Link-User':'1'}

    def test_health_and_policy(self):
        r=self.c.get('/api/youth-club/health'); self.assertEqual(r.status_code,200); self.assertTrue(r.json['ok'])
        r=self.c.get('/api/youth-club'); self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['adult_content_allowed']); self.assertFalse(r.json['targeted_ads']); self.assertFalse(r.json['precise_location_public'])
        self.assertFalse(r.json['unrestricted_adult_minor_contact'])

    def test_safety_blocks_adult_content(self):
        r=self.c.post('/api/youth-club/content-check',json={'kind':'adult_sexual_content'})
        self.assertEqual(r.status_code,403); self.assertFalse(r.json['allowed'])

    def test_minor_join_requires_guardian(self):
        c=self.c.post('/api/youth-club/clubs',headers=self.h,json={'name':'SE15 Youth Club','postcode':'SE15','age_band':'youth'})
        self.assertEqual(c.status_code,201)
        r=self.c.post('/api/youth-club/clubs/%s/join'%c.json['club_id'],headers=self.h,json={'age_band':'youth'})
        self.assertEqual(r.status_code,200); self.assertTrue(r.json['guardian_required']); self.assertEqual(r.json['status'],'pending_guardian')

if __name__=='__main__': unittest.main()
