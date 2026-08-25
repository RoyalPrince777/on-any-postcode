import os, unittest
os.environ.setdefault('DATABASE_URL',os.environ.get('DATABASE_URL',''))
from gates import app
class Gates(unittest.TestCase):
 def setUp(self): self.c=app.test_client(); self.h={'X-Link-User':'1'}
 def test_health_all_gates(self):
  r=self.c.get('/health');self.assertEqual(r.status_code,200);self.assertEqual(r.json['gates'],list(range(5,13)))
 def test_location_requires_auth(self): self.assertEqual(self.c.post('/api/location',json={'lat':51.5,'lon':-.1}).status_code,401)
 def test_location_validation(self): self.assertEqual(self.c.post('/api/location',headers=self.h,json={'lat':999,'lon':0}).status_code,400)
 def test_people_requires_auth(self): self.assertEqual(self.c.get('/api/people').status_code,401)
 def test_android_manifest(self): self.assertEqual(self.c.get('/api/android').json['package'],'world.onanypostcode.link')
 def test_public_gate_reads(self):
  for p in ['/api/releases','/api/live','/api/poppin','/api/events','/api/ends']: self.assertEqual(self.c.get(p).status_code,200,p)
if __name__=='__main__': unittest.main()
