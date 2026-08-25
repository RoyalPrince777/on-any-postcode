import os, unittest, uuid
from flask import Flask, request
from psycopg import connect
from psycopg.rows import dict_row
from spot_family import register_spot_family
from oap_core_systems import register_core_systems
DB=os.environ['DATABASE_URL']
def db(): return connect(DB,autocommit=True,row_factory=dict_row)
def uid():
 v=request.headers.get('X-Link-User','')
 return int(v) if v.isdigit() and int(v)>0 else None
app=Flask(__name__); register_core_systems(app,db,uid); register_spot_family(app,db,uid)

class SpotFamily(unittest.TestCase):
 def setUp(self):
  self.c=app.test_client(); self.h={'X-Link-User':'1'}; self.h2={'X-Link-User':'2'}
  with db() as c:
   for i in (1,2): c.execute("insert into link_users(id,username,display_name,password_hash,created_at) values(%s,%s,%s,'x',0) on conflict(id) do nothing",(i,f'ci{i}',f'CI {i}'))
 def test_postcode_to_borough_and_spot_intelligence(self):
  tag=uuid.uuid4().hex[:6].upper()
  b=self.c.post('/api/spot/places',headers=self.h,json={'level':'borough','name':'CI Borough '+tag,'code':'B'+tag}); self.assertEqual(b.status_code,201)
  p=self.c.post('/api/spot/places',headers=self.h,json={'level':'postcode','name':'CI Postcode '+tag,'code':'P'+tag,'parent_id':b.json['place_id']}); self.assertEqual(p.status_code,201)
  pid=p.json['place_id']
  j=self.c.post(f'/api/spot/places/{pid}/join',headers=self.h,json={'standing':'founder','is_primary':True}); self.assertEqual(j.status_code,200); self.assertEqual(j.json['certification'],'claimed')
  s=self.c.get(f'/api/spot/intelligence/{pid}'); self.assertEqual(s.status_code,200); self.assertFalse(s.json['prediction']); self.assertFalse(s.json['precise_location_used'])
  fam=self.c.get(f'/api/spot/places/{b.json["place_id"]}'); self.assertEqual(fam.status_code,200); self.assertTrue(any(x['id']==pid for x in fam.json['children']))
 def test_family_is_not_biological_or_paid(self):
  r=self.c.post('/api/family/link',headers=self.h,json={'child_user_id':2}); self.assertEqual(r.status_code,200); self.assertFalse(r.json['financial_reward'])
  me=self.c.get('/api/family/me',headers=self.h); self.assertEqual(me.status_code,200); self.assertFalse(me.json['biological'])
 def test_role_requires_oap_label(self):
  tag=uuid.uuid4().hex[:6].upper(); p=self.c.post('/api/spot/places',headers=self.h,json={'level':'postcode','name':'Role '+tag,'code':'R'+tag}).json['place_id']
  self.assertEqual(self.c.post(f'/api/spot/places/{p}/roles',headers=self.h,json={'title':'President'}).status_code,400)
  ok=self.c.post(f'/api/spot/places/{p}/roles',headers=self.h,json={'title':'OAP Postcode President'}); self.assertEqual(ok.status_code,201); self.assertFalse(ok.json['government_role'])
 def test_auth_and_invalid_standing(self):
  self.assertEqual(self.c.get('/api/spot/me').status_code,401)
  tag=uuid.uuid4().hex[:6].upper(); p=self.c.post('/api/spot/places',headers=self.h,json={'level':'postcode','name':'Stand '+tag,'code':'S'+tag}).json['place_id']
  self.assertEqual(self.c.post(f'/api/spot/places/{p}/join',headers=self.h,json={'standing':'king'}).status_code,400)

if __name__=='__main__': unittest.main()
