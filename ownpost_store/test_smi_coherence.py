import os, unittest
os.environ.setdefault('DATABASE_URL',os.environ.get('DATABASE_URL',''))
from flask import Flask, request
from psycopg import connect
from psycopg.rows import dict_row
from smi_coherence import register_smi_coherence

DB=os.environ['DATABASE_URL']
def db():return connect(DB,autocommit=True,row_factory=dict_row)
def uid():
 v=request.headers.get('X-Link-User','');return int(v) if v.isdigit() and int(v)>0 else None
app=Flask(__name__);register_smi_coherence(app,db,uid)

class SMICoherence(unittest.TestCase):
 def setUp(self):self.c=app.test_client();self.h={'X-Link-User':'1'}
 def test_real_brain_regions_executable(self):
  r=self.c.get('/api/smi/brain/regions');self.assertEqual(r.status_code,200);self.assertTrue(r.json['executable_router']);self.assertEqual(r.json['brain_count'],1)
  for x in ['left_hemisphere','right_hemisphere','corpus_callosum','frontal_lobe','parietal_lobe','temporal_lobe','occipital_lobe','thalamus','hypothalamus','hippocampus','amygdala','cerebellum','brainstem']:self.assertIn(x,r.json['regions'])
 def test_attention_routes_modality_risk_memory_space(self):
  r=self.c.post('/api/smi/attention',json={'signal':'SE15 incident image','modality':'image','risk':'high','spatial':True,'memory_needed':True});routes=r.json['attention']['routes']
  for x in ['thalamus','amygdala','occipital_lobe','parietal_lobe','hippocampus','frontal_lobe','cerebellum','brainstem']:self.assertIn(x,routes)
 def test_shared_adaptive_loop_is_bounded(self):
  r=self.c.post('/api/smi/coherence/cycle',headers=self.h,json={'input':'improve route cache','evidence':'latency regression'});self.assertEqual(r.status_code,201);self.assertEqual(r.json['loop'],['observe','interpret','verify','adapt','test','remember','improve']);self.assertFalse(r.json['adapt']['auto_rewrite']);self.assertTrue(r.json['improve']['human_approval_required'])
 def test_conflict_cannot_be_silent(self):
  c=self.c.post('/api/smi/coherence/cycle',headers=self.h,json={'input':'choose plan','evidence':'test'}).json['cycle_id']
  r=self.c.post('/api/smi/coherence/resolve',headers=self.h,json={'cycle_id':c,'positions':[{'intelligence':'Matrix Intelligence','position':'A','confidence':.8,'evidence':'probe A'},{'intelligence':'Jungle Book Intelligence','position':'B','confidence':.9,'evidence':''}]});self.assertTrue(r.json['conflict']);self.assertFalse(r.json['silent_disagreement_allowed']);self.assertEqual(r.json['resolution'],'evidence_weighted_recommendation');self.assertEqual(r.json['recommendation']['position'],'A')
 def test_no_evidence_conflict_requires_human(self):
  c=self.c.post('/api/smi/coherence/cycle',headers=self.h,json={'input':'choose'}).json['cycle_id']
  r=self.c.post('/api/smi/coherence/resolve',headers=self.h,json={'cycle_id':c,'positions':[{'intelligence':'A','position':'x','confidence':1},{'intelligence':'B','position':'y','confidence':1}]});self.assertEqual(r.json['resolution'],'human_review_required');self.assertIsNone(r.json['recommendation'])
 def test_health(self):
  r=self.c.get('/api/smi/coherence/health');self.assertTrue(r.json['conflict_resolution']);self.assertEqual(r.json['learning'],'purple_until_verified')

if __name__=='__main__':unittest.main()
