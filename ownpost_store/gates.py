from flask import Flask, jsonify, request
import os, time, hashlib
from psycopg import connect
from psycopg.rows import dict_row

app=Flask(__name__)
DB=os.environ['DATABASE_URL']
def db(): return connect(DB,autocommit=True,row_factory=dict_row)
def now(): return int(time.time())

def init():
 with db() as c:
  c.execute('create table if not exists link_locations(id bigserial primary key,user_id bigint not null,lat double precision not null,lon double precision not null,label text,expires_at bigint not null,created_at bigint not null)')
  c.execute('create table if not exists link_people(owner_id bigint not null,person_id bigint not null,alias text,created_at bigint not null,primary key(owner_id,person_id))')
  c.execute('create table if not exists platform_releases(id bigserial primary key,version text not null,channel text not null,notes text not null,created_at bigint not null)')
  c.execute("create table if not exists link_live(id bigserial primary key,owner_id bigint not null,title text not null,status text not null default 'ready',created_at bigint not null)")
  c.execute('create table if not exists link_poppin(id bigserial primary key,title text not null,postcode text,score integer not null default 0,created_at bigint not null)')
  c.execute('create table if not exists link_events(id bigserial primary key,title text not null,postcode text,starts_at bigint not null,created_at bigint not null)')
  c.execute('create table if not exists link_ends(id bigserial primary key,postcode text not null,borough text,county text,country text not null,continent text not null,created_at bigint not null)')
  c.execute("create table if not exists link_presence(user_id bigint primary key,status text not null default 'offline',visibility text not null default 'my_people',expires_at bigint,updated_at bigint not null)")
  c.execute('create table if not exists link_blocks(owner_id bigint not null,blocked_id bigint not null,created_at bigint not null,primary key(owner_id,blocked_id))')
  c.execute('create table if not exists link_reports(id bigserial primary key,reporter_id bigint not null,target_user_id bigint,kind text not null,details text not null,created_at bigint not null)')
  c.execute('create table if not exists link_notifications(id bigserial primary key,user_id bigint not null,kind text not null,title text not null,body text not null,read_at bigint,created_at bigint not null)')
  c.execute('create table if not exists link_trends(id bigserial primary key,title text not null,scope text not null,scope_value text,score integer not null default 0,source text not null default \'community\',created_at bigint not null)')
  c.execute('create table if not exists link_businesses(id bigserial primary key,owner_id bigint not null,name text not null,category text not null,postcode text,description text not null,commercial boolean not null default true,active boolean not null default true,created_at bigint not null)')
  c.execute('create table if not exists link_business_links(id bigserial primary key,user_id bigint not null,business_id bigint not null,kind text not null,created_at bigint not null,unique(user_id,business_id,kind))')
  c.execute('create table if not exists link_idempotency(user_id bigint not null,op text not null,ikey text not null,result_hash text not null,created_at bigint not null,primary key(user_id,op,ikey))')
  c.execute('create index if not exists link_presence_exp_idx on link_presence(expires_at)')
  c.execute('create index if not exists link_notifications_user_idx on link_notifications(user_id,id desc)')
  c.execute('create index if not exists link_trends_scope_idx on link_trends(scope,scope_value,score desc)')
init()

def uid():
 v=request.headers.get('X-Link-User','')
 return int(v) if v.isdigit() and int(v)>0 else None

def require_uid():
 u=uid()
 return u,None if u else (None,(jsonify(error='auth_required'),401))

def blocked(c,a,b):
 return bool(c.execute('select 1 from link_blocks where (owner_id=%s and blocked_id=%s) or (owner_id=%s and blocked_id=%s)',(a,b,b,a)).fetchone())

def idem(c,u,op):
 key=request.headers.get('Idempotency-Key','').strip()[:120]
 if not key:return None
 return c.execute('select result_hash from link_idempotency where user_id=%s and op=%s and ikey=%s',(u,op,key)).fetchone()

def idem_save(c,u,op,payload):
 key=request.headers.get('Idempotency-Key','').strip()[:120]
 if key:
  h=hashlib.sha256(repr(payload).encode()).hexdigest()
  c.execute('insert into link_idempotency(user_id,op,ikey,result_hash,created_at) values(%s,%s,%s,%s,%s) on conflict do nothing',(u,op,key,h,now()))

@app.get('/health')
def health():
 return jsonify(ok=True,service='the-link-gates',gates=list(range(5,13)),extras=['presence','whats_lit','business_link','notifications','safety','offline_idempotency'])

@app.post('/api/location')
def location():
 u=uid(); d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 try: lat=float(d['lat']);lon=float(d['lon']);ttl=min(max(int(d.get('ttl',900)),60),86400)
 except:return jsonify(error='invalid_location'),400
 if not(-90<=lat<=90 and -180<=lon<=180):return jsonify(error='invalid_location'),400
 with db() as c:
  if idem(c,u,'location'):return jsonify(ok=True,duplicate=True)
  r=c.execute('insert into link_locations(user_id,lat,lon,label,expires_at,created_at) values(%s,%s,%s,%s,%s,%s) returning id,expires_at',(u,lat,lon,str(d.get('label',''))[:80],now()+ttl,now())).fetchone();idem_save(c,u,'location',r)
 return jsonify(ok=True,share=r)

@app.delete('/api/location')
def stop_location():
 u=uid()
 if not u:return jsonify(error='auth_required'),401
 with db() as c:c.execute('delete from link_locations where user_id=%s',(u,))
 return jsonify(ok=True)

@app.route('/api/people',methods=['GET','POST'])
def people():
 u=uid()
 if not u:return jsonify(error='auth_required'),401
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {}
   try:p=int(d.get('person_id',0))
   except:p=0
   if p<=0 or p==u:return jsonify(error='invalid_person'),400
   if blocked(c,u,p):return jsonify(error='blocked'),403
   c.execute('insert into link_people(owner_id,person_id,alias,created_at) values(%s,%s,%s,%s) on conflict(owner_id,person_id) do update set alias=excluded.alias',(u,p,str(d.get('alias',''))[:80],now()))
  rows=c.execute('select person_id,alias from link_people where owner_id=%s and not exists(select 1 from link_blocks b where b.owner_id=%s and b.blocked_id=link_people.person_id) order by created_at desc',(u,u)).fetchall()
 return jsonify(people=rows)

@app.route('/api/presence',methods=['GET','POST','DELETE'])
def presence():
 u=uid()
 if not u:return jsonify(error='auth_required'),401
 allowed={'online','in','chilling','free','about','out','out_tonight','lit_tonight','matchday','busy','dnd','invisible','offline'}
 vis={'everyone','my_people','selected','nobody'}
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {}; status=str(d.get('status','online')).lower(); visibility=str(d.get('visibility','my_people')).lower()
   if status not in allowed or visibility not in vis:return jsonify(error='invalid_presence'),400
   ttl=min(max(int(d.get('ttl',3600)),60),86400); exp=now()+ttl if status not in {'offline','invisible'} else None
   c.execute('insert into link_presence(user_id,status,visibility,expires_at,updated_at) values(%s,%s,%s,%s,%s) on conflict(user_id) do update set status=excluded.status,visibility=excluded.visibility,expires_at=excluded.expires_at,updated_at=excluded.updated_at',(u,status,visibility,exp,now()))
  elif request.method=='DELETE':
   c.execute("insert into link_presence(user_id,status,visibility,expires_at,updated_at) values(%s,'offline','nobody',null,%s) on conflict(user_id) do update set status='offline',visibility='nobody',expires_at=null,updated_at=excluded.updated_at",(u,now()))
  r=c.execute("select status,visibility,expires_at,updated_at from link_presence where user_id=%s",(u,)).fetchone() or {'status':'offline','visibility':'nobody','expires_at':None,'updated_at':None}
 return jsonify(presence=r)

@app.get('/api/presence/<int:person_id>')
def presence_of(person_id):
 viewer=uid()
 if not viewer:return jsonify(error='auth_required'),401
 with db() as c:
  if blocked(c,viewer,person_id):return jsonify(status='offline',visible=False)
  r=c.execute('select status,visibility,expires_at from link_presence where user_id=%s',(person_id,)).fetchone()
  if not r or (r['expires_at'] and r['expires_at']<now()) or r['status'] in {'offline','invisible'}:return jsonify(status='offline',visible=False)
  visible=r['visibility']=='everyone' or (r['visibility']=='my_people' and c.execute('select 1 from link_people where owner_id=%s and person_id=%s',(person_id,viewer)).fetchone())
  return jsonify(status=r['status'] if visible else 'offline',visible=bool(visible),expires_at=r['expires_at'] if visible else None)

@app.route('/api/blocks/<int:person_id>',methods=['POST','DELETE'])
def block(person_id):
 u=uid()
 if not u:return jsonify(error='auth_required'),401
 if person_id==u:return jsonify(error='invalid_person'),400
 with db() as c:
  if request.method=='POST':
   c.execute('insert into link_blocks(owner_id,blocked_id,created_at) values(%s,%s,%s) on conflict do nothing',(u,person_id,now()));c.execute('delete from link_people where owner_id=%s and person_id=%s',(u,person_id))
  else:c.execute('delete from link_blocks where owner_id=%s and blocked_id=%s',(u,person_id))
 return jsonify(ok=True)

@app.post('/api/reports')
def report():
 u=uid();d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 kind=str(d.get('kind','other'))[:40]; details=str(d.get('details',''))[:1000]
 try:t=int(d.get('target_user_id')) if d.get('target_user_id') is not None else None
 except:t=None
 with db() as c:r=c.execute('insert into link_reports(reporter_id,target_user_id,kind,details,created_at) values(%s,%s,%s,%s,%s) returning id',(u,t,kind,details,now())).fetchone()
 return jsonify(ok=True,report_id=r['id']),201

@app.route('/api/notifications',methods=['GET','POST'])
def notifications():
 u=uid()
 if not u:return jsonify(error='auth_required'),401
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {}
   try:target=int(d.get('user_id',u))
   except:target=u
   if target!=u and blocked(c,u,target):return jsonify(error='blocked'),403
   c.execute('insert into link_notifications(user_id,kind,title,body,created_at) values(%s,%s,%s,%s,%s)',(target,str(d.get('kind','system'))[:40],str(d.get('title','THE LINK'))[:120],str(d.get('body',''))[:500],now()))
  rows=c.execute('select id,kind,title,body,read_at,created_at from link_notifications where user_id=%s order by id desc limit 100',(u,)).fetchall()
 return jsonify(notifications=rows)

@app.post('/api/notifications/<int:nid>/read')
def notification_read(nid):
 u=uid()
 if not u:return jsonify(error='auth_required'),401
 with db() as c:c.execute('update link_notifications set read_at=%s where id=%s and user_id=%s',(now(),nid,u))
 return jsonify(ok=True)

@app.get('/api/android')
def android(): return jsonify(ok=True,gate=7,package='world.onanypostcode.link',distribution='ON ANY PLATFORM',install='APK pipeline verified',core_free=True)

@app.route('/api/releases',methods=['GET','POST'])
def releases():
 u=uid();
 if request.method=='POST' and not u:return jsonify(error='auth_required'),401
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {}; c.execute('insert into platform_releases(version,channel,notes,created_at) values(%s,%s,%s,%s)',(str(d.get('version','dev'))[:30],str(d.get('channel','stable'))[:20],str(d.get('notes',''))[:500],now()))
  rows=c.execute('select version,channel,notes,created_at from platform_releases order by id desc limit 20').fetchall()
 return jsonify(releases=rows)

@app.route('/api/live',methods=['GET','POST'])
def live():
 with db() as c:
  if request.method=='POST':
   u=uid();d=request.get_json(silent=True) or {}
   if not u:return jsonify(error='auth_required'),401
   c.execute('insert into link_live(owner_id,title,status,created_at) values(%s,%s,%s,%s)',(u,str(d.get('title','Live & Direct'))[:120],'ready',now()))
  rows=c.execute('select id,owner_id,title,status from link_live order by id desc limit 50').fetchall()
 return jsonify(streams=rows)

@app.post('/api/live/<int:sid>/state')
def live_state(sid):
 u=uid();d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 state=str(d.get('status','ready'))
 if state not in {'ready','live','ended','reconnecting'}:return jsonify(error='invalid_state'),400
 with db() as c:
  r=c.execute('update link_live set status=%s where id=%s and owner_id=%s returning id,status',(state,sid,u)).fetchone()
 return (jsonify(ok=True,stream=r) if r else (jsonify(error='not_found'),404))

@app.get('/api/poppin')
def poppin():
 scope=request.args.get('postcode','').strip().upper()
 with db() as c:
  if scope:r=c.execute('select id,title,postcode,score from link_poppin where postcode=%s order by score desc,id desc limit 50',(scope,)).fetchall()
  else:r=c.execute('select id,title,postcode,score from link_poppin order by score desc,id desc limit 50').fetchall()
 return jsonify(items=r)

@app.route('/api/lit',methods=['GET','POST'])
def lit():
 with db() as c:
  if request.method=='POST':
   u=uid();d=request.get_json(silent=True) or {}
   if not u:return jsonify(error='auth_required'),401
   scope=str(d.get('scope','postcode')).lower(); val=str(d.get('scope_value',''))[:100]; title=str(d.get('title',''))[:160]
   if scope not in {'postcode','borough','county','country','continent','global','universe'} or not title:return jsonify(error='invalid_trend'),400
   c.execute('insert into link_trends(title,scope,scope_value,score,source,created_at) values(%s,%s,%s,%s,%s,%s)',(title,scope,val,int(d.get('score',1)),str(d.get('source','community'))[:40],now()))
  scope=request.args.get('scope','postcode');val=request.args.get('scope_value','')
  if val:r=c.execute('select id,title,scope,scope_value,score,source,created_at from link_trends where scope=%s and scope_value=%s order by score desc,created_at desc limit 50',(scope,val)).fetchall()
  else:r=c.execute('select id,title,scope,scope_value,score,source,created_at from link_trends where scope=%s order by score desc,created_at desc limit 50',(scope,)).fetchall()
 return jsonify(trends=r)

@app.route('/api/events',methods=['GET','POST'])
def events():
 if request.method=='POST' and not uid():return jsonify(error='auth_required'),401
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {};c.execute('insert into link_events(title,postcode,starts_at,created_at) values(%s,%s,%s,%s)',(str(d.get('title',''))[:160],str(d.get('postcode',''))[:20].upper(),int(d.get('starts_at',now())),now()))
  r=c.execute('select id,title,postcode,starts_at from link_events where starts_at>=%s order by starts_at limit 100',(now()-86400,)).fetchall()
 return jsonify(events=r)

@app.route('/api/endz',methods=['GET','POST'])
@app.route('/api/ends',methods=['GET','POST'])
def endz():
 if request.method=='POST' and not uid():return jsonify(error='auth_required'),401
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {};pc=str(d.get('postcode','')).strip().upper()
   if not pc:return jsonify(error='postcode_required'),400
   c.execute('insert into link_ends(postcode,borough,county,country,continent,created_at) values(%s,%s,%s,%s,%s,%s)',(pc,str(d.get('borough',''))[:100],str(d.get('county',''))[:100],str(d.get('country','United Kingdom'))[:100],str(d.get('continent','Europe'))[:100],now()))
  r=c.execute('select id,postcode,borough,county,country,continent from link_ends order by id desc limit 100').fetchall()
 return jsonify(endz=r, hierarchy=['postcode','borough','county_region','country','continent','global','universe'])

@app.route('/api/businesses',methods=['GET','POST'])
def businesses():
 with db() as c:
  if request.method=='POST':
   u=uid();d=request.get_json(silent=True) or {}
   if not u:return jsonify(error='auth_required'),401
   name=str(d.get('name','')).strip()[:160];cat=str(d.get('category','other'))[:80]
   if not name:return jsonify(error='name_required'),400
   r=c.execute('insert into link_businesses(owner_id,name,category,postcode,description,commercial,created_at) values(%s,%s,%s,%s,%s,true,%s) returning id',(u,name,cat,str(d.get('postcode',''))[:20].upper(),str(d.get('description',''))[:1000],now())).fetchone();return jsonify(ok=True,business_id=r['id'],monetizable=True,core_link_free=True),201
  rows=c.execute('select id,name,category,postcode,description,commercial from link_businesses where active=true order by id desc limit 100').fetchall()
 return jsonify(businesses=rows,monetization_rule='THE LINK core is free; commercial business links may monetize')

@app.post('/api/businesses/<int:bid>/link')
def business_link(bid):
 u=uid();d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 kind=str(d.get('kind','follow'))[:40]
 if kind not in {'follow','enquire','book','buy','merchant'}:return jsonify(error='invalid_kind'),400
 with db() as c:
  if not c.execute('select 1 from link_businesses where id=%s and active=true',(bid,)).fetchone():return jsonify(error='not_found'),404
  c.execute('insert into link_business_links(user_id,business_id,kind,created_at) values(%s,%s,%s,%s) on conflict do nothing',(u,bid,kind,now()))
 return jsonify(ok=True,commercial=kind in {'book','buy','merchant'})
