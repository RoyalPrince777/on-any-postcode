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
 def test_pulse_intelligence_is_human_first(self):
  h=self.c.get('/api/pulse/intelligence/health'); self.assertEqual(h.status_code,200); self.assertIn('clicks',h.json['excluded_inputs']); self.assertEqual(h.json['protected_priority'],['safety','account'])
  stamp=str(int(time.time()*1000)); general='Pulse General '+stamp; safety='Pulse Safety '+stamp
  a=self.c.post('/api/pulse',headers=self.h,json={'kind':'system','title':general,'body':'general'}); self.assertEqual(a.status_code,200)
  b=self.c.post('/api/pulse',headers=self.h,json={'kind':'guardian_alert','title':safety,'body':'safety'}); self.assertEqual(b.status_code,200); self.assertEqual(b.json['ranking_policy'],'human_first_personal_priority_not_engagement_maximisation')
  rows=b.json['pulse']; titles=[x['title'] for x in rows]; self.assertLess(titles.index(safety),titles.index(general)); sr=next(x for x in rows if x['title']==safety); self.assertEqual(sr['category'],'safety')
  self.assertEqual(self.c.post(f"/api/pulse/{sr['id']}/read",headers=self.h).status_code,200)
  r=self.c.get('/api/pulse',headers=self.h); titles=[x['title'] for x in r.json['pulse']]; self.assertLess(titles.index(safety),titles.index(general))
 def test_protected_event_bridge_authority(self):
  h=self.c.get('/api/event-bridge/health'); self.assertEqual(h.status_code,200); self.assertEqual(h.json['protected_cross_user_policy'],'founder_authority_only')
  bad=self.c.post('/api/event-bridge',headers=self.h2,json={'kind':'guardian_alert','title':'Spoofed safety','target_user_id':1}); self.assertEqual(bad.status_code,403); self.assertEqual(bad.json['error'],'protected_event_authority_required')
  own=self.c.post('/api/event-bridge',headers=self.h2,json={'kind':'guardian_alert','title':'Own safety','target_user_id':2}); self.assertEqual(own.status_code,201); self.assertTrue(own.json['protected']); self.assertTrue(own.json['delivered'])
 def test_signal_trust_defaults_unverified(self):
  h=self.c.get('/api/signal-trust/health'); self.assertEqual(h.status_code,200); self.assertFalse(h.json['source_label_alone_grants_trust'])
  stamp=str(int(time.time()*1000)); title='Untrusted Safety '+stamp
  self.c.post('/api/signals',headers=self.h,json={'title':title,'scope':'postcode','scope_value':'SE15','source':'community_safety','score':1})
  r=self.c.get('/api/signals/ranked?scope=postcode&scope_value=SE15'); row=next(x for x in r.json['signals'] if x['title']==title); self.assertEqual(row['evidence_state'],'unverified_source'); self.assertEqual(row['rank_factors']['safety_importance'],0.0); self.assertFalse(row['source_label_grants_trust'])
 def test_smi_health_and_judgement_are_complete(self):
  h=self.c.get('/api/smi/health'); self.assertEqual(h.status_code,200); self.assertEqual(h.json['flow'],['observation','perception','understanding','reasoning','judgement','decision','execution']); self.assertEqual(h.json['judgement_sections'],6); self.assertTrue(h.json['judgement_complete']); self.assertTrue(h.json['operational_awareness']); self.assertFalse(h.json['consciousness_claim']); self.assertFalse(h.json['autonomous_real_world_execution'])
  j=self.c.get('/api/smi/judgement'); self.assertEqual(j.status_code,200); self.assertEqual(j.json['complete'],'6/6'); self.assertEqual(len(j.json['sections']),6); self.assertTrue(all(x['status']=='green' for x in j.json['sections']))
  a=self.c.get('/api/smi/aegis'); self.assertEqual(a.status_code,200); self.assertEqual(a.json['default'],'fail_closed'); self.assertFalse(a.json['secrets_logged'])
 def test_smi_full_cognition_cycle_is_bounded(self):
  r=self.c.post('/api/smi/cycle',headers=self.h,json={'input':'Compare two safe internal options','action':'analyse','evidence':'user supplied evidence','real_world':False}); self.assertEqual(r.status_code,201)
  for k in ['observation','perception','understanding','reasoning','judgement','decision','execution']: self.assertIn(k,r.json)
  self.assertEqual(r.json['judgement']['complete'],'6/6'); self.assertTrue(r.json['judgement']['pass']); self.assertFalse(r.json['execution']['real_world_execution']); self.assertTrue(r.json['hrm_receipt']); self.assertTrue(r.json['aegis_enforced'])
 def test_smi_real_world_execution_fails_closed(self):
  r=self.c.post('/api/smi/cycle',headers=self.h,json={'input':'Move money externally','action':'move_money','evidence':'request only','real_world':True,'provider_verified':False}); self.assertEqual(r.status_code,201); self.assertFalse(r.json['judgement']['pass']); self.assertFalse(r.json['execution']['real_world_execution']); self.assertIn('blocked',r.json['execution']['state']); self.assertEqual(r.json['judgement']['sections'][-1]['name'],'human_final_gate'); self.assertFalse(r.json['judgement']['sections'][-1]['pass'])
 def test_smi_awareness_and_controlled_self_improvement(self):
  s=self.c.get('/api/smi/self'); self.assertEqual(s.status_code,200); self.assertEqual(s.json['awareness_type'],'operational_machine_self_awareness'); self.assertFalse(s.json['phenomenal_consciousness_claim']); self.assertEqual(s.json['authority'],'human_final')
  p=self.c.post('/api/smi/improvements',headers=self.h,json={'title':'Improve route cache','hypothesis':'Cache reduces latency','test_plan':'Isolate, benchmark, compare, review'}); self.assertEqual(p.status_code,201); iid=p.json['improvements'][0]['id']; self.assertFalse(p.json['auto_apply'])
  blocked=self.c.post(f'/api/smi/improvements/{iid}/state',headers=self.h,json={'state':'promoted'}); self.assertEqual(blocked.status_code,403); self.assertEqual(blocked.json['error'],'human_approval_required')
  approved=self.c.post(f'/api/smi/improvements/{iid}/state',headers=self.h,json={'state':'promoted','human_approved':True}); self.assertEqual(approved.status_code,200); self.assertFalse(approved.json['auto_apply'])
 def test_internal_pillars_are_green(self):
  r=self.c.get('/api/pillars'); self.assertEqual(r.status_code,200); self.assertEqual(r.json['internal_overall'],'green'); self.assertTrue(r.json['external_dependencies_separate']); self.assertTrue(r.json['acyclic']); self.assertTrue(all(x['status']=='green' for x in r.json['pillars'])); self.assertTrue(any(x['name']=='smi_brain_cognition' for x in r.json['pillars']))
 def test_release_seal_is_truthful(self):
  r=self.c.get('/api/readiness/release-seal'); self.assertEqual(r.status_code,200); self.assertEqual(r.json['internal_state'],'green'); self.assertTrue(r.json['no_fake_green']); self.assertIn(r.json['release_state'],{'internal_green_external_amber','fully_green'})
 def test_auth_boundaries(self):
  for path in ['/api/transport/journeys','/api/studio/projects']:
   self.assertEqual(self.c.get(path).status_code,401)
  self.assertEqual(self.c.post('/api/booking/providers',json={'name':'x','category':'x'}).status_code,401)

if __name__=='__main__': unittest.main()
