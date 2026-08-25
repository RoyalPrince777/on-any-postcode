import unittest, time
from gates import app

class OAPTV(unittest.TestCase):
 def setUp(self): self.c=app.test_client(); self.h={'X-Link-User':'1'}
 def test_health(self):
  r=self.c.get('/api/tv/health');self.assertEqual(r.status_code,200);self.assertEqual(r.json['service'],'oap-tv');self.assertEqual(r.json['product_language'],'My World');self.assertIn('my_world',r.json['layers']);self.assertIn('schedule',r.json['layers'])
 def test_my_world_auth_and_scope_validation(self):
  self.assertEqual(self.c.post('/api/tv/my-world',json={'name':'x','slug':'x'}).status_code,401)
  self.assertEqual(self.c.post('/api/tv/my-world',headers=self.h,json={'name':'Bad','slug':'bad','scope':'moon'}).status_code,400)
 def test_my_world_show_episode_flow(self):
  slug='ci-world-'+str(int(time.time()*1000))
  world=self.c.post('/api/tv/my-world',headers=self.h,json={'name':'CI World','slug':slug,'scope':'postcode','scope_value':'SE15'});self.assertEqual(world.status_code,201)
  wid=world.json['my_world_id']
  sh=self.c.post('/api/tv/shows',headers=self.h,json={'my_world_id':wid,'title':'CI Show','category':'culture'});self.assertEqual(sh.status_code,201);self.assertEqual(sh.json['my_world_id'],wid)
  ep=self.c.post('/api/tv/episodes',headers=self.h,json={'show_id':sh.json['show_id'],'title':'Pilot','duration_seconds':120,'published':True});self.assertEqual(ep.status_code,201)
  r=self.c.get('/api/tv/my-world?scope=postcode&scope_value=SE15');self.assertTrue(any(x['my_world_id']==wid for x in r.json['my_worlds']))
 def test_legacy_channel_route_is_compatibility_alias(self):
  r=self.c.get('/api/tv/channels');self.assertEqual(r.status_code,200);self.assertIn('my_worlds',r.json)
 def test_schedule_conflict(self):
  slug='ci-sched-'+str(int(time.time()*1000))
  wid=self.c.post('/api/tv/my-world',headers=self.h,json={'name':'Schedule World','slug':slug}).json['my_world_id']; start=int(time.time())+5000
  a=self.c.post('/api/tv/schedule',headers=self.h,json={'my_world_id':wid,'title':'One','starts_at':start,'ends_at':start+600});self.assertEqual(a.status_code,201)
  b=self.c.post('/api/tv/schedule',headers=self.h,json={'my_world_id':wid,'title':'Clash','starts_at':start+100,'ends_at':start+700});self.assertEqual(b.status_code,409)
 def test_watchlist_requires_auth(self): self.assertEqual(self.c.get('/api/tv/watchlist').status_code,401)
 def test_reaction_validation(self):
  self.assertEqual(self.c.post('/api/tv/react/1',headers=self.h,json={'reaction':'toxic'}).status_code,400)
  self.assertEqual(self.c.post('/api/tv/react/1',headers=self.h,json={'reaction':'safe'}).status_code,200)
 def test_watch_progress(self):
  r=self.c.post('/api/tv/watch/1',headers=self.h,json={'progress_seconds':42});self.assertEqual(r.status_code,200);self.assertTrue(r.json['ok'])
 def test_hierarchy(self):
  r=self.c.get('/api/tv/my-world');self.assertEqual(r.json['hierarchy'],['postcode','borough','county_region','country','continent','global','universe'])

if __name__=='__main__':unittest.main()
