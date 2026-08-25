import os, unittest
os.environ.setdefault('DATABASE_URL',os.environ.get('DATABASE_URL',''))
from link_intelligence import app

class LinkIntelligenceTests(unittest.TestCase):
 def setUp(self):
  self.c=app.test_client(); self.h={'X-Link-User':'1'}
 def test_health_layers(self):
  r=self.c.get('/health');self.assertEqual(r.status_code,200);self.assertIn('captain',r.json['layers']);self.assertIn('hrm_receipts',r.json['layers'])
 def test_captain_requires_auth(self): self.assertEqual(self.c.post('/api/captain',json={'query':'bell me'}).status_code,401)
 def test_captain_routes(self): self.assertEqual(self.c.post('/api/captain',headers=self.h,json={'query':'bell my people'}).json['route'],'bell_me')
 def test_guardian_sensitive_scam(self):
  r=self.c.post('/api/guardian/check',headers=self.h,json={'text':'URGENT send your OTP now guaranteed profit'});self.assertEqual(r.json['risk'],'red');self.assertTrue(r.json['blocked'])
 def test_notification_language_pack(self): self.assertIn('Bellin',self.c.post('/api/notifications/render',headers=self.h,json={'kind':'call','pack':'south_london'}).json['title'])
 def test_long_term_memory_requires_approval(self): self.assertEqual(self.c.post('/api/memory',headers=self.h,json={'kind':'long_term','content':'remember this'}).status_code,403)
 def test_approved_memory_and_forget(self):
  self.assertEqual(self.c.post('/api/memory',headers=self.h,json={'kind':'long_term','content':'approved memory','approved':True}).status_code,201)
  self.assertEqual(self.c.delete('/api/memory',headers=self.h).status_code,200)
 def test_endz_invalid_level(self): self.assertEqual(self.c.get('/api/endz/intelligence?level=street').status_code,400)
 def test_lit_invalid_scope(self): self.assertEqual(self.c.get('/api/lit/intelligence?scope=street').status_code,400)
 def test_business_policy(self):
  r=self.c.get('/api/business/intelligence?q=');self.assertTrue(r.json['core_link_free']);self.assertTrue(r.json['commercial_layer_only']);self.assertFalse(r.json['private_data_monetized'])
 def test_hrm_requires_auth(self): self.assertEqual(self.c.get('/api/hrm/receipts').status_code,401)
 def test_hrm_receipt(self): self.assertEqual(self.c.post('/api/hrm/receipts',headers=self.h,json={'action':'test','decision':'allow','reason':'regression','approved':True}).status_code,201)
 def test_catch_up_privacy(self): self.assertFalse(self.c.get('/api/catch-up',headers=self.h).json['private_message_content_used'])
 def test_find_short_query(self): self.assertEqual(self.c.get('/api/find?q=x',headers=self.h).json['results'],[])

if __name__=='__main__': unittest.main()
