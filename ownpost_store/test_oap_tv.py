import os, unittest, time
os.environ.setdefault('DATABASE_URL',os.environ.get('DATABASE_URL',''))
from flask import Flask
from psycopg import connect
from psycopg.rows import dict_row
from oap_tv import register_tv

DB=os.environ['DATABASE_URL']
def db(): return connect(DB,autocommit=True,row_factory=dict_row)
def uid_from_header():
 v=__import__('flask').request.headers.get('X-Link-User','')
 return int(v) if v.isdigit() and int(v)>0 else None

app=Flask(__name__)
register_tv(app,db,uid_from_header)

class OAPTV(unittest.TestCase):
 def setUp(self): self.c=app.test_client(); self.h={'X-Link-User':'1'}
 def test_health(self):
  r=self.c.get('/api/tv/health');self.assertEqual(r.status_code,200);self.assertEqual(r.json['service'],'oap-tv');self.assertIn('schedule',r.json['layers'])
 def test_channel_auth_and_scope_validation(self):
  self.assertEqual(self.c.post('/api/tv/channels',json={'name':'x','slug':'x'}).status_code,401)
  self.assertEqual(self.c.post('/api/tv/channels',headers=self.h,json={'name':'Bad','slug':'bad','scope':'moon'}).status_code,400)
 def test_channel_show_episode_flow(self):
  slug='ci-tv-'+str(int(time.time()*1000))
  ch=self.c.post('/api/tv/channels',headers=self.h,json={'name':'CI TV','slug':slug,'scope':'postcode','scope_value':'SE15'});self.assertEqual(ch.status_code,201)
  cid=ch.json['channel_id']
  sh=self.c.post('/api/tv/shows',headers=self.h,json={'channel_id':cid,'title':'CI Show','category':'culture'});self.assertEqual(sh.status_code,201)
  ep=self.c.post('/api/tv/episodes',headers=self.h,json={'show_id':sh.json['show_id'],'title':'Pilot','duration_seconds':120,'published':True});self.assertEqual(ep.status_code,201)
  r=self.c.get('/api/tv/channels?scope=postcode&scope_value=SE15');self.assertTrue(any(x['id']==cid for x in r.json['channels']))
 def test_schedule_conflict(self):
  slug='ci-sched-'+str(int(time.time()*1000))
  cid=self.c.post('/api/tv/channels',headers=self.h,json={'name':'Schedule TV','slug':slug}).json['channel_id']; start=int(time.time())+5000
  a=self.c.post('/api/tv/schedule',headers=self.h,json={'channel_id':cid,'title':'One','starts_at':start,'ends_at':start+600});self.assertEqual(a.status_code,201)
  b=self.c.post('/api/tv/schedule',headers=self.h,json={'channel_id':cid,'title':'Clash','starts_at':start+100,'ends_at':start+700});self.assertEqual(b.status_code,409)
 def test_watchlist_requires_auth(self): self.assertEqual(self.c.get('/api/tv/watchlist').status_code,401)
 def test_reaction_validation(self):
  self.assertEqual(self.c.post('/api/tv/react/1',headers=self.h,json={'reaction':'toxic'}).status_code,400)
  self.assertEqual(self.c.post('/api/tv/react/1',headers=self.h,json={'reaction':'safe'}).status_code,200)
 def test_watch_progress(self):
  r=self.c.post('/api/tv/watch/1',headers=self.h,json={'progress_seconds':42});self.assertEqual(r.status_code,200);self.assertTrue(r.json['ok'])
 def test_hierarchy(self):
  r=self.c.get('/api/tv/channels');self.assertEqual(r.json['hierarchy'],['postcode','borough','county_region','country','continent','global','universe'])

if __name__=='__main__':unittest.main()
