import os, unittest
os.environ.setdefault('DATABASE_URL',os.environ.get('DATABASE_URL',''))
from flask import Flask, request
from psycopg import connect
from psycopg.rows import dict_row
from smi_resilience import register_smi_resilience

DB=os.environ['DATABASE_URL']
def db(): return connect(DB,autocommit=True,row_factory=dict_row)
def uid():
 v=request.headers.get('X-Link-User','')
 return int(v) if v.isdigit() and int(v)>0 else None

app=Flask(__name__);register_smi_resilience(app,db,uid)

class SMIResilience(unittest.TestCase):
 def setUp(self): self.c=app.test_client(); self.h={'X-Link-User':'1'}
 def test_health_and_priorities(self):
  h=self.c.get('/api/smi/resilience/health');self.assertEqual(h.status_code,200);self.assertEqual(len(h.json['controls']),7)
  p=self.c.get('/api/smi/priorities').json['priorities'];self.assertGreater(p['guardian'],p['studio']);self.assertGreater(p['active_journey'],p['background'])
 def test_bounded_queue_backpressure(self):
  self.c.post('/api/smi/queues/studio/drain',json={'count':999999})
  r=self.c.post('/api/smi/queues/studio',json={'enqueue':999999});self.assertEqual(r.status_code,200);self.assertTrue(r.json['queue']['backpressure']);self.assertGreater(r.json['queue']['dropped'],0);self.assertEqual(r.json['queue']['depth'],r.json['queue']['limit_depth'])
  self.c.post('/api/smi/queues/studio/drain',json={'count':999999})
 def test_spot_cache_version_and_freshness(self):
  a=self.c.post('/api/smi/spot-cache',json={'scope':'postcode','scope_value':'se15','payload':'one','ttl':60});self.assertEqual(a.status_code,200)
  b=self.c.post('/api/smi/spot-cache',json={'scope':'postcode','scope_value':'SE15','payload':'two','ttl':60});self.assertGreater(b.json['version'],a.json['version'])
  g=self.c.get('/api/smi/spot-cache?scope=postcode&scope_value=SE15');self.assertTrue(g.json['hit']);self.assertEqual(g.json['entry']['payload'],'two')
 def test_trend_integrity_quarantines_manipulation(self):
  q=self.c.post('/api/smi/trend-integrity',json={'volume':100,'independent_sources':1,'duplicate_ratio':.7,'freshness':1,'provenance_trust':.2});self.assertEqual(q.json['state'],'quarantine');self.assertFalse(q.json['pay_to_trend'])
  e=self.c.post('/api/smi/trend-integrity',json={'volume':30,'independent_sources':12,'duplicate_ratio':.05,'freshness':1,'provenance_trust':.9});self.assertEqual(e.json['state'],'eligible')
 def test_transport_circuit_breaker(self):
  name='ci-provider'
  self.c.post('/api/smi/circuits/'+name,json={'event':'success'})
  for _ in range(3):r=self.c.post('/api/smi/circuits/'+name,json={'event':'failure'})
  self.assertEqual(r.json['circuit']['state'],'open');self.assertFalse(r.json['provider_execution_allowed'])
  r=self.c.post('/api/smi/circuits/'+name,json={'event':'probe_pass'});self.assertEqual(r.json['circuit']['state'],'closed');self.assertTrue(r.json['provider_execution_allowed'])
 def test_cross_organ_private_edges_fail_closed(self):
  for source,target in [('studio','sovereign_private_core'),('market','private_link_messages'),('spot','precise_gps'),('ordinary_agent','sovereign_private_core')]:
   r=self.c.post('/api/smi/permission-check',json={'source':source,'target':target});self.assertFalse(r.json['allowed']);self.assertEqual(r.json['reason'],'explicit_capability_required')
 def test_recovery_requires_probe_to_earn_green(self):
  r=self.c.post('/api/smi/recovery',json={'component':'transport','state':'green','probe_passed':False});self.assertEqual(r.json['state'],'recovering');self.assertFalse(r.json['green_earned'])
  r=self.c.post('/api/smi/recovery',json={'component':'transport','state':'green','probe_passed':True});self.assertEqual(r.json['state'],'green');self.assertTrue(r.json['green_earned'])

if __name__=='__main__':unittest.main()
