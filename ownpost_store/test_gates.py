import os, unittest, time
os.environ.setdefault('DATABASE_URL',os.environ.get('DATABASE_URL',''))
from gates import app
from test_link_intelligence import LinkIntelligenceTests
from test_oap_tv import OAPTV
from test_oap_core_systems import OAPCoreSystems
from test_spot_family import SpotFamily
from test_royal_oap import RoyalOAP
from test_oap_intelligence import OAPIntelligence
from test_youth_real_education import YouthRealEducation
from test_youth_club import YouthClub
from test_bank_intelligence import BankIntelligence
from test_background_258 import Background258
from test_oap_ride import OAPRide
from test_oap_ride_admin import OAPRideAdmin
from test_movement_hub import MovementHub

class Gates(unittest.TestCase):
 def setUp(self):
  self.c=app.test_client(); self.h={'X-Link-User':'1'}; self.h2={'X-Link-User':'2'}
 def test_health_all_gates_and_extras(self):
  r=self.c.get('/health');self.assertEqual(r.status_code,200);self.assertEqual(r.json['gates'],list(range(5,13)))
  for x in ['presence','whats_lit','business_link','notifications','safety','offline_idempotency','oap_tv','booking','careers','market','global_transport','ai_studio','organ_registry']: self.assertIn(x,r.json['extras'])
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
 def test_signals_and_pulse_are_canonical(self):
  r=self.c.get('/api/language'); self.assertEqual(r.status_code,200); self.assertEqual(r.json['canonical']['feed'],'Signals'); self.assertEqual(r.json['canonical']['notifications'],'Pulse')
  self.assertEqual(self.c.get('/api/pulse').status_code,401)
  p=self.c.post('/api/pulse',headers=self.h,json={'title':'Pulse CI','body':'hello'}); self.assertEqual(p.status_code,200); self.assertIn('pulse',p.json)
  s=self.c.post('/api/signals',headers=self.h,json={'title':'Signal CI','scope':'postcode','scope_value':'SE15'}); self.assertEqual(s.status_code,200); self.assertIn('signals',s.json)
 def test_master_checkpoints(self):
  r=self.c.get('/api/checkpoints'); self.assertEqual(r.status_code,200); self.assertTrue(r.json['no_fake_green']); self.assertEqual(r.json['canonical_language']['feed'],'Signals'); self.assertEqual(r.json['canonical_language']['notifications'],'Pulse'); self.assertIn('internal',r.json); self.assertIn('external',r.json)
 def test_provider_contracts_are_honest(self):
  r=self.c.get('/api/providers'); self.assertEqual(r.status_code,200); self.assertTrue(r.json['no_fake_live']); self.assertTrue(all(not x['live_claim'] for x in r.json['providers']))
 def test_provider_adapters_fail_safe(self):
  r=self.c.get('/api/adapters/health'); self.assertEqual(r.status_code,200); self.assertTrue(r.json['no_fake_live'])
  g=self.c.get('/api/adapters/geography?postcode=SE15'); self.assertEqual(g.status_code,200); self.assertFalse(g.json['live_provider'])
  rt=self.c.post('/api/adapters/route',json={'origin':'SE15','destination':'CR4'}); self.assertEqual(rt.status_code,200); self.assertTrue(rt.json['planning_only']); self.assertIsNone(rt.json['route'])
 def test_shared_location_bridge(self):
  h=self.c.get('/api/location-bridge/health'); self.assertEqual(h.status_code,200); self.assertTrue(h.json['local_first']); self.assertTrue(h.json['no_fake_live'])
  c=self.c.get('/api/location-bridge/context?postcode=SE15'); self.assertEqual(c.status_code,200); self.assertEqual(c.json['postcode'],'SE15'); self.assertFalse(c.json['public_precise_location'])
  r=self.c.post('/api/location-bridge/route',json={'origin':'SE15','destination':'CR4'}); self.assertEqual(r.status_code,200); self.assertTrue(r.json['planning_only']); self.assertFalse(r.json['execution']); self.assertIn('OAP Ride',r.json['consumers'])
 def test_regulated_rails_fail_closed(self):
  r=self.c.get('/api/regulated'); self.assertEqual(r.status_code,200); self.assertEqual(r.json['default'],'fail_closed')
  x=self.c.post('/api/regulated/banking/execute',json={'action':'open_account'}); self.assertIn(x.status_code,{202,403}); self.assertFalse(x.json.get('provider_execution',False))
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
  for p in ['/api/releases','/api/live','/api/poppin','/api/events','/api/endz','/api/lit','/api/signals','/api/language','/api/checkpoints','/api/providers','/api/adapters/health','/api/location-bridge/health','/api/regulated','/api/observability/health','/api/ride/admin/health','/api/businesses','/api/tv/health','/api/core/health','/api/organism/self','/api/spot/me','/api/royal/health','/api/royal','/api/royal/institutions','/api/intelligence/health','/api/intelligence','/api/world-intelligence','/api/earth-intelligence','/api/continent-intelligence?continent=Africa','/api/country-intelligence?continent=Africa&country=Ghana','/api/universe-intelligence','/api/intelligence/adaptive-coherence','/api/education/health','/api/education/tracks','/api/youth-safety/policy','/api/youth-club/health','/api/youth-club','/api/youth-club/safety','/api/bank-intelligence/health','/api/bank-intelligence','/api/bank-intelligence/sika','/api/258','/api/258/health','/api/movement/health','/api/movement','/api/movement/safety','/api/ride/health','/api/ride','/api/readiness/capabilities','/api/readiness/core']:
   r=self.c.get(p,headers=self.h if p=='/api/spot/me' else {}); self.assertEqual(r.status_code,200,p)

if __name__=='__main__': unittest.main()
