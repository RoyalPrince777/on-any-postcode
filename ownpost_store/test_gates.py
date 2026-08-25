import os, unittest, time
os.environ.setdefault('DATABASE_URL',os.environ.get('DATABASE_URL',''))
from gates import app

class Gates(unittest.TestCase):
 def setUp(self):
  self.c=app.test_client(); self.h={'X-Link-User':'1'}; self.h2={'X-Link-User':'2'}
 def test_health_all_gates_and_extras(self):
  r=self.c.get('/health');self.assertEqual(r.status_code,200);self.assertEqual(r.json['gates'],list(range(5,13)))
  for x in ['presence','whats_lit','business_link','notifications','safety','offline_idempotency']: self.assertIn(x,r.json['extras'])
 def test_location_requires_auth_and_validates(self):
  self.assertEqual(self.c.post('/api/location',json={'lat':51.5,'lon':-.1}).status_code,401)
  self.assertEqual(self.c.post('/api/location',headers=self.h,json={'lat':999,'lon':0}).status_code,400)
 def test_location_idempotency(self):
  h={**self.h,'Idempotency-Key':'ci-location-1'}
  a=self.c.post('/api/location',headers=h,json={'lat':51.5,'lon':-.1,'ttl':60});self.assertEqual(a.status_code,200)
  b=self.c.post('/api/location',headers=h,json={'lat':51.5,'lon':-.1,'ttl':60});self.assertEqual(b.status_code,200);self.assertTrue(b.json.get('duplicate'))
  self.c.delete('/api/location',headers=self.h)
 def test_presence_privacy_and_expiry_shape(self):
  r=self.c.post('/api/presence',headers=self.h,json={'status':'chilling','visibility':'nobody','ttl':60});self.assertEqual(r.status_code,200);self.assertEqual(r.json['presence']['status'],'chilling')
  r=self.c.get('/api/presence/1',headers=self.h2);self.assertEqual(r.status_code,200);self.assertFalse(r.json['visible'])
  r=self.c.delete('/api/presence',headers=self.h);self.assertEqual(r.json['presence']['status'],'offline')
 def test_presence_rejects_bad_status(self): self.assertEqual(self.c.post('/api/presence',headers=self.h,json={'status':'tracking_you'}).status_code,400)
 def test_people_requires_auth(self): self.assertEqual(self.c.get('/api/people').status_code,401)
 def test_block_and_unblock(self):
  self.assertEqual(self.c.post('/api/blocks/2',headers=self.h).status_code,200)
  self.assertEqual(self.c.delete('/api/blocks/2',headers=self.h).status_code,200)
 def test_report_requires_auth_and_creates(self):
  self.assertEqual(self.c.post('/api/reports',json={'kind':'spam'}).status_code,401)
  self.assertEqual(self.c.post('/api/reports',headers=self.h,json={'target_user_id':2,'kind':'spam','details':'ci'}).status_code,201)
 def test_notifications_auth_and_inbox(self):
  self.assertEqual(self.c.get('/api/notifications').status_code,401)
  self.assertEqual(self.c.post('/api/notifications',headers=self.h,json={'title':'CI','body':'hello'}).status_code,200)
  self.assertEqual(self.c.get('/api/notifications',headers=self.h).status_code,200)
 def test_android_manifest(self):
  r=self.c.get('/api/android');self.assertEqual(r.json['package'],'world.onanypostcode.link');self.assertTrue(r.json['core_free'])
 def test_release_write_requires_auth(self): self.assertEqual(self.c.post('/api/releases',json={'version':'x'}).status_code,401)
 def test_live_state_validation(self): self.assertEqual(self.c.post('/api/live/999999/state',headers=self.h,json={'status':'bad'}).status_code,400)
 def test_whats_lit_and_scope(self):
  r=self.c.post('/api/lit',headers=self.h,json={'title':'CI Trend','scope':'postcode','scope_value':'SE15','score':5});self.assertEqual(r.status_code,200)
  r=self.c.get('/api/lit?scope=postcode&scope_value=SE15');self.assertEqual(r.status_code,200);self.assertTrue(any(x['title']=='CI Trend' for x in r.json['trends']))
 def test_endz_alias_and_hierarchy(self):
  for p in ['/api/endz','/api/ends']:
   r=self.c.get(p);self.assertEqual(r.status_code,200);self.assertIn('global',r.json['hierarchy']);self.assertIn('universe',r.json['hierarchy'])
 def test_business_rule_and_creation(self):
  r=self.c.get('/api/businesses');self.assertEqual(r.status_code,200);self.assertIn('core is free',r.json['monetization_rule'])
  r=self.c.post('/api/businesses',headers=self.h,json={'name':'CI Business','category':'test','postcode':'SE15'});self.assertEqual(r.status_code,201);self.assertTrue(r.json['monetizable']);self.assertTrue(r.json['core_link_free'])
 def test_public_gate_reads(self):
  for p in ['/api/releases','/api/live','/api/poppin','/api/events','/api/endz','/api/lit','/api/businesses']: self.assertEqual(self.c.get(p).status_code,200,p)

if __name__=='__main__': unittest.main()
