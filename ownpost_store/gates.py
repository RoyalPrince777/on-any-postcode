from flask import Flask, jsonify, request
import os, time
from psycopg import connect
from psycopg.rows import dict_row

app=Flask(__name__)
DB=os.environ['DATABASE_URL']
def db(): return connect(DB,autocommit=True,row_factory=dict_row)
def init():
 with db() as c:
  c.execute('create table if not exists link_locations(id bigserial primary key,user_id bigint not null,lat double precision not null,lon double precision not null,label text,expires_at bigint not null,created_at bigint not null)')
  c.execute('create table if not exists link_people(owner_id bigint not null,person_id bigint not null,alias text,created_at bigint not null,primary key(owner_id,person_id))')
  c.execute('create table if not exists platform_releases(id bigserial primary key,version text not null,channel text not null,notes text not null,created_at bigint not null)')
  c.execute('create table if not exists link_live(id bigserial primary key,owner_id bigint not null,title text not null,status text not null default \'ready\',created_at bigint not null)')
  c.execute('create table if not exists link_poppin(id bigserial primary key,title text not null,postcode text,score integer not null default 0,created_at bigint not null)')
  c.execute('create table if not exists link_events(id bigserial primary key,title text not null,postcode text,starts_at bigint not null,created_at bigint not null)')
  c.execute('create table if not exists link_ends(id bigserial primary key,postcode text not null,borough text,county text,country text not null,continent text not null,created_at bigint not null)')
init()

def uid():
 v=request.headers.get('X-Link-User','')
 return int(v) if v.isdigit() else None
@app.get('/health')
def health(): return jsonify(ok=True,service='the-link-gates',gates=list(range(5,13)))
@app.post('/api/location')
def location():
 u=uid(); d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 try: lat=float(d['lat']);lon=float(d['lon']);ttl=min(max(int(d.get('ttl',900)),60),86400)
 except:return jsonify(error='invalid_location'),400
 if not(-90<=lat<=90 and -180<=lon<=180):return jsonify(error='invalid_location'),400
 with db() as c:r=c.execute('insert into link_locations(user_id,lat,lon,label,expires_at,created_at) values(%s,%s,%s,%s,%s,%s) returning id,expires_at',(u,lat,lon,str(d.get('label',''))[:80],int(time.time())+ttl,int(time.time()))).fetchone()
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
   d=request.get_json(silent=True) or {}; p=int(d.get('person_id',0))
   if p<=0 or p==u:return jsonify(error='invalid_person'),400
   c.execute('insert into link_people(owner_id,person_id,alias,created_at) values(%s,%s,%s,%s) on conflict(owner_id,person_id) do update set alias=excluded.alias',(u,p,str(d.get('alias',''))[:80],int(time.time())))
  rows=c.execute('select person_id,alias from link_people where owner_id=%s order by created_at desc',(u,)).fetchall()
 return jsonify(people=rows)
@app.get('/api/android')
def android(): return jsonify(ok=True,gate=7,package='world.onanypostcode.link',distribution='ON ANY PLATFORM',install='PWA/APK pipeline ready')
@app.route('/api/releases',methods=['GET','POST'])
def releases():
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {}; c.execute('insert into platform_releases(version,channel,notes,created_at) values(%s,%s,%s,%s)',(str(d.get('version','dev'))[:30],str(d.get('channel','stable'))[:20],str(d.get('notes',''))[:500],int(time.time())))
  rows=c.execute('select version,channel,notes,created_at from platform_releases order by id desc limit 20').fetchall()
 return jsonify(releases=rows)
@app.route('/api/live',methods=['GET','POST'])
def live():
 with db() as c:
  if request.method=='POST':
   u=uid();d=request.get_json(silent=True) or {}
   if not u:return jsonify(error='auth_required'),401
   c.execute('insert into link_live(owner_id,title,status,created_at) values(%s,%s,%s,%s)',(u,str(d.get('title','Live & Direct'))[:120],'ready',int(time.time())))
  rows=c.execute('select id,owner_id,title,status from link_live order by id desc limit 50').fetchall()
 return jsonify(streams=rows)
@app.get('/api/poppin')
def poppin():
 with db() as c:r=c.execute('select id,title,postcode,score from link_poppin order by score desc,id desc limit 50').fetchall()
 return jsonify(items=r)
@app.route('/api/events',methods=['GET','POST'])
def events():
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {};c.execute('insert into link_events(title,postcode,starts_at,created_at) values(%s,%s,%s,%s)',(str(d.get('title',''))[:160],str(d.get('postcode',''))[:20],int(d.get('starts_at',time.time())),int(time.time())))
  r=c.execute('select id,title,postcode,starts_at from link_events where starts_at>=%s order by starts_at limit 100',(int(time.time())-86400,)).fetchall()
 return jsonify(events=r)
@app.route('/api/ends',methods=['GET','POST'])
def ends():
 with db() as c:
  if request.method=='POST':
   d=request.get_json(silent=True) or {};pc=str(d.get('postcode','')).strip().upper()
   if not pc:return jsonify(error='postcode_required'),400
   c.execute('insert into link_ends(postcode,borough,county,country,continent,created_at) values(%s,%s,%s,%s,%s,%s)',(pc,str(d.get('borough',''))[:100],str(d.get('county',''))[:100],str(d.get('country','United Kingdom'))[:100],str(d.get('continent','Europe'))[:100],int(time.time())))
  r=c.execute('select id,postcode,borough,county,country,continent from link_ends order by id desc limit 100').fetchall()
 return jsonify(ends=r)
