import os, unittest
from gates import app

class OAPRideAdmin(unittest.TestCase):
    def setUp(self):
        self.c=app.test_client()
        self.h1={'X-Link-User':'1'}
        self.h2={'X-Link-User':'2'}

    def test_health_is_noncommercial(self):
        r=self.c.get('/api/ride/admin/health')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['commercial_execution'])

    def test_admin_requires_founder_configuration_or_founder_identity(self):
        r=self.c.get('/api/ride/admin/drivers',headers=self.h2)
        self.assertIn(r.status_code,{403,503})

    def test_non_founder_cannot_approve_driver(self):
        r=self.c.post('/api/ride/admin/drivers/1/approval',headers=self.h2,json={'certified':True,'licence_checked':True,'insurance_checked':True,'safeguarding_checked':True})
        self.assertIn(r.status_code,{403,503})

if __name__=='__main__': unittest.main()
