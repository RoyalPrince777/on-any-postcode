import unittest, time
from gates import app

class YouthClub(unittest.TestCase):
    def setUp(self):
        self.c=app.test_client(); self.h={'X-Link-User':'1'}

    def test_health_and_policy(self):
        r=self.c.get('/api/youth-club/health'); self.assertEqual(r.status_code,200); self.assertTrue(r.json['ok'])
        for x in ['guardians','certified_adults','sessions','bookings','attendance','consent','safeguarding','audit']: self.assertIn(x,r.json['operations'])
        r=self.c.get('/api/youth-club'); self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['adult_content_allowed']); self.assertFalse(r.json['targeted_ads']); self.assertFalse(r.json['precise_location_public'])
        self.assertFalse(r.json['unrestricted_adult_minor_contact'])

    def test_safety_blocks_adult_content(self):
        r=self.c.post('/api/youth-club/content-check',json={'kind':'adult_sexual_content'})
        self.assertEqual(r.status_code,403); self.assertFalse(r.json['allowed'])

    def test_minor_join_requires_guardian(self):
        c=self.c.post('/api/youth-club/clubs',headers=self.h,json={'name':'SE15 Youth Club %s'%time.time_ns(),'postcode':'SE15','age_band':'youth'})
        self.assertEqual(c.status_code,201)
        r=self.c.post('/api/youth-club/clubs/%s/join'%c.json['club_id'],headers=self.h,json={'age_band':'youth'})
        self.assertEqual(r.status_code,200); self.assertTrue(r.json['guardian_required']); self.assertEqual(r.json['status'],'pending_guardian')

    def test_guardian_link_and_approval(self):
        member={'X-Link-User':'11'}; guardian={'X-Link-User':'12'}
        c=self.c.post('/api/youth-club/clubs',headers=member,json={'name':'Guardian CI %s'%time.time_ns(),'postcode':'CR4','age_band':'youth'})
        self.assertEqual(c.status_code,201)
        self.assertEqual(self.c.post('/api/youth-club/clubs/%s/join'%c.json['club_id'],headers=member,json={'age_band':'youth'}).status_code,200)
        r=self.c.post('/api/youth-club/guardians',headers=member,json={'guardian_user_id':12,'relationship':'parent'}); self.assertEqual(r.status_code,200); self.assertEqual(r.json['status'],'pending')
        r=self.c.post('/api/youth-club/guardians/11/approve',headers=guardian); self.assertEqual(r.status_code,200); self.assertEqual(r.json['status'],'approved')

    def test_uncleared_adult_cannot_lead_or_read_audit(self):
        adult={'X-Link-User':'21'}
        r=self.c.post('/api/youth-club/adults/me',headers=adult,json={'role':'mentor'}); self.assertEqual(r.status_code,200); self.assertFalse(r.json['can_lead'])
        c=self.c.post('/api/youth-club/clubs',headers=adult,json={'name':'Lead Check %s'%time.time_ns(),'postcode':'SE15','age_band':'youth'}); self.assertEqual(c.status_code,201)
        r=self.c.post('/api/youth-club/clubs/%s/sessions'%c.json['club_id'],headers=adult,json={'activity_kind':'coding','title':'Coding','starts_at':2000000000,'ends_at':2000003600}); self.assertEqual(r.status_code,403)
        self.assertEqual(self.c.get('/api/youth-club/audit',headers=adult).status_code,403)

    def test_safeguarding_incident_is_audited_for_human_review(self):
        r=self.c.post('/api/youth-club/safeguarding/incidents',headers=self.h,json={'kind':'safety_concern','details':'CI safeguarding test','severity':'high'})
        self.assertEqual(r.status_code,201); self.assertTrue(r.json['human_review']); self.assertTrue(r.json['guardian_or_trusted_escalation'])

if __name__=='__main__': unittest.main()
