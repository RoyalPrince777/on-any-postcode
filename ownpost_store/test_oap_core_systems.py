import unittest, time
from gates import app

class OAPCoreSystems(unittest.TestCase):
 def setUp(self): self.c=app.test_client(); self.h={'X-Link-User':'1'}; self.h2={'X-Link-User':'2'}
 def test_health_and_self_model(self):
  r=self.c.get('/api/core/health'); self.assertEqual(r.status_code,200); self.assertTrue(r.json['ok']); self.assertGreaterEqual(len(r.json['organs']),9)
  s=self.c.get('/api/organism/self'); self.assertEqual(s.status_code,200); self.assertEqual(s.json['authority'],'human_final')
 def test_booking_atomic_slot(self):
  p=self.c.post('/api/booking/providers',headers=self.h,json={'name':'CI Cleaner','category':'cleaner','postcode':'SE15'}); self.assertEqual(p.status_code,201)
  pid=p.json['provider_id']; start=int(time.time())+10000
  sl=self.c.post(f'/api/booking/providers/{pid}/slots',headers=self.h,json={'starts_at':start,'ends_at':start+3600}); self.assertEqual(sl.status_code,201)
  sid=sl.json['slot_id']; a=self.c.post(f'/api/booking/slots/{sid}/book',headers=self.h2); self.assertEqual(a.status_code,201)
  b=self.c.post(f'/api/booking/slots/{sid}/book',headers=self.h); self.assertEqual(b.status_code,409)
 def test_booking_owner_controls_slots(self):
  p=self.c.post('/api/booking/providers',headers=self.h,json={'name':'CI Handyman','category':'handyman'}).json['provider_id']; start=int(time.time())+12000
  self.assertEqual(self.c.post(f'/api/booking/providers/{p}/slots',headers=self.h2,json={'starts_at':start,'ends_at':start+900}).status_code,403)
 def test_careers_flow(self):
  r=self.c.post('/api/careers',headers=self.h,json={'title':'Cleaner','company':'OAP CI','postcode':'SE15'}); self.assertEqual(r.status_code,201)
  self.assertEqual(self.c.post(f"/api/careers/{r.json['career_id']}/apply",headers=self.h2).status_code,200)
 def test_market_stock_protection(self):
  r=self.c.post('/api/market/items',headers=self.h,json={'name':'CI Item','price_minor':500,'stock':1}); self.assertEqual(r.status_code,201); iid=r.json['item_id']
  self.assertEqual(self.c.post(f'/api/market/items/{iid}/order',headers=self.h2,json={'qty':1}).status_code,201)
  self.assertEqual(self.c.post(f'/api/market/items/{iid}/order',headers=self.h,json={'qty':1}).status_code,409)
 def test_transport_is_provider_honest(self):
  r=self.c.post('/api/transport/journeys',headers=self.h,json={'origin':'SE15','destination':'SW1','mode':'multimodal'}); self.assertEqual(r.status_code,201); self.assertEqual(r.json['routing_state'],'provider_required')
 def test_studio_asset_permission(self):
  p=self.c.post('/api/studio/projects',headers=self.h,json={'title':'CI Studio'}); self.assertEqual(p.status_code,201); pid=p.json['project_id']
  self.assertEqual(self.c.post(f'/api/studio/projects/{pid}/assets',headers=self.h2,json={'kind':'image','uri':'asset://x'}).status_code,403)
  self.assertEqual(self.c.post(f'/api/studio/projects/{pid}/assets',headers=self.h,json={'kind':'image','uri':'asset://x','provenance':'user','consent_confirmed':True}).status_code,201)
 def test_auth_boundaries(self):
  for path in ['/api/transport/journeys','/api/studio/projects']:
   self.assertEqual(self.c.get(path).status_code,401)
  self.assertEqual(self.c.post('/api/booking/providers',json={'name':'x','category':'x'}).status_code,401)

if __name__=='__main__': unittest.main()
