from flask import Flask, jsonify, request
import os, time, re, urllib.parse
from psycopg import connect
from psycopg.rows import dict_row

app=Flask(__name__)
DB=os.environ['DATABASE_URL']
def db(): return connect(DB,autocommit=True,row_factory=dict_row)
def now(): return int(time.time())
def uid():
 v=request.headers.get('X-Link-User','')
 return int(v) if v.isdigit() and int(v)>0 else None

def init():
 with db() as c:
  c.execute("create table if not exists link_memory(id bigserial primary key,user_id bigint not null,kind text not null,content text not null,approved boolean not null default false,expires_at bigint,created_at bigint not null)")
  c.execute("create table if not exists link_hrm_receipts(id bigserial primary key,user_id bigint not null,action text not null,decision text not null,reason text not null,approved boolean not null default false,created_at bigint not null)")
  c.execute("create index if not exists link_memory_user_idx on link_memory(user_id,id desc)")
  c.execute("create index if not exists link_hrm_user_idx on link_hrm_receipts(user_id,id desc)")
init()

SOUTH_LONDON={
 'message':'Someone Said Suttin 💬','group':'The Lot’s Active 👥','call':'Man’s Bellin’ 📞','missed_call':'You Missed a Bell 📵',
 'video_call':'Face Card Incoming 🎥','voice':'They Dropped a Voice Note 🎙️','online':'They’re About 🟢','location':'Dropped Their Pin 📍',
 'poppin':'Suttin’s Poppin’ ⚡','lit':'Suttin’s Lit 🔥','event':'Suttin’s On 📅','live':'They’re Live & Direct 🔴',
 'crew':'Roll With Us? 🤝','linked':'You Lot Linked Up 🔗','business':'Business Is Bellin’ 💼','value':'Suttin Landed 💷',
 'warning':'Pattern Up — Check This ⚠️','reconnected':'We’re Back 🟢','offline':'Gone Quiet 🌙'
}

@app.get('/health')
def health():
 return jsonify(ok=True,service='the-link-intelligence',layers=['captain','find_suttin','guardian','catch_up','smart_notifications','memory','endz_intelligence','trend_intelligence','business_intelligence','hrm_receipts'])

@app.post('/api/captain')
def captain():
 u=uid();d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 q=str(d.get('query','')).strip().lower()
 routes=[('bell_me',('call','bell','video','ring')),('whats_lit',('trend','lit','viral')),('whats_on',('event','on tonight','what on')),('whats_poppin',('poppin','nearby','buzz')),('endz',('postcode','borough','endz','area')),('business',('business','shop','book','buy')),('my_people',('person','people','crew','lot'))]
 route='link_up'
 for name,words in routes:
  if any(w in q for w in words):route=name;break
 with db() as c:c.execute('insert into link_hrm_receipts(user_id,action,decision,reason,approved,created_at) values(%s,%s,%s,%s,false,%s)',(u,'captain_route',route,'Intent routing only; no consequential action executed',now()))
 return jsonify(route=route,confidence=.8 if route!='link_up' else .55,execute=False,human_authority=True)

@app.get('/api/find')
def find_suttin():
 u=uid();q=request.args.get('q','').strip();scope=request.args.get('scope','all')
 if not u:return jsonify(error='auth_required'),401
 if len(q)<2:return jsonify(results=[])
 like='%'+q+'%';out=[]
 with db() as c:
  if scope in {'all','endz'}:
   for r in c.execute('select id,postcode,borough,county,country,continent from link_ends where postcode ilike %s or borough ilike %s or county ilike %s or country ilike %s limit 20',(like,like,like,like)).fetchall():out.append({'type':'endz',**r})
  if scope in {'all','lit'}:
   for r in c.execute('select id,title,scope,scope_value,score from link_trends where title ilike %s order by score desc limit 20',(like,)).fetchall():out.append({'type':'lit',**r})
  if scope in {'all','events'}:
   for r in c.execute('select id,title,postcode,starts_at from link_events where title ilike %s and starts_at>=%s order by starts_at limit 20',(like,now()-86400)).fetchall():out.append({'type':'event',**r})
  if scope in {'all','business'}:
   for r in c.execute('select id,name,category,postcode from link_businesses where active=true and (name ilike %s or category ilike %s) limit 20',(like,like)).fetchall():out.append({'type':'business',**r})
 return jsonify(results=out[:50])

@app.post('/api/guardian/check')
def guardian():
 u=uid();d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 text=str(d.get('text',''))[:4000];lower=text.lower();flags=[]
 if len(text)>1800:flags.append('spam_length')
 if len(re.findall(r'https?://',lower))>4:flags.append('link_spam')
 if re.search(r'\b(password|seed phrase|one[- ]time code|otp)\b',lower):flags.append('sensitive_request')
 if re.search(r'\b(urgent|act now|guaranteed profit|double your money)\b',lower):flags.append('scam_pattern')
 for url in re.findall(r'https?://[^\s]+',text):
  host=(urllib.parse.urlparse(url).hostname or '').lower()
  if host.startswith('xn--'):flags.append('punycode_domain')
 risk='red' if 'sensitive_request' in flags and 'scam_pattern' in flags else ('yellow' if flags else 'green')
 return jsonify(risk=risk,flags=sorted(set(flags)),blocked=risk=='red',human_review=risk!='green')

@app.get('/api/catch-up')
def catch_up():
 u=uid()
 if not u:return jsonify(error='auth_required'),401
 with db() as c:
  unread=c.execute('select count(*) n from link_notifications where user_id=%s and read_at is null',(u,)).fetchone()['n']
  events=c.execute('select count(*) n from link_events where starts_at between %s and %s',(now(),now()+86400)).fetchone()['n']
  trends=c.execute('select count(*) n from link_trends where created_at>=%s',(now()-86400,)).fetchone()['n']
  live=c.execute("select count(*) n from link_live where status='live'").fetchone()['n']
 return jsonify(summary={'unread_notifications':unread,'whats_on_next_24h':events,'whats_lit_last_24h':trends,'live_direct_now':live},private_message_content_used=False)

@app.post('/api/notifications/render')
def render_notification():
 u=uid();d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 kind=str(d.get('kind','message'));pack=str(d.get('pack','south_london'))
 if pack=='south_london':title=SOUTH_LONDON.get(kind,'THE LINK')
 else:title={'message':'New message','call':'Incoming call','lit':'Trending now','event':'New event','live':'Live now'}.get(kind,'THE LINK')
 return jsonify(kind=kind,title=title,pack=pack,protocol_event=kind)

@app.route('/api/memory',methods=['GET','POST','DELETE'])
def memory():
 u=uid();d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 with db() as c:
  if request.method=='POST':
   kind=str(d.get('kind','preference'))[:40];content=str(d.get('content','')).strip()[:2000];approved=bool(d.get('approved',False));ttl=int(d.get('ttl',0) or 0)
   if not content:return jsonify(error='content_required'),400
   if kind=='long_term' and not approved:return jsonify(error='approval_required'),403
   exp=now()+min(ttl,31536000) if ttl>0 else None
   r=c.execute('insert into link_memory(user_id,kind,content,approved,expires_at,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(u,kind,content,approved,exp,now())).fetchone();return jsonify(ok=True,memory_id=r['id']),201
  if request.method=='DELETE':
   c.execute('delete from link_memory where user_id=%s',(u,));return jsonify(ok=True,forgotten=True)
  rows=c.execute('select id,kind,content,approved,expires_at,created_at from link_memory where user_id=%s and (expires_at is null or expires_at>%s) order by id desc limit 100',(u,now())).fetchall()
 return jsonify(memory=rows,controls=['approve','forget','delete'],private_by_default=True)

@app.get('/api/endz/intelligence')
def endz_intelligence():
 level=request.args.get('level','postcode');value=request.args.get('value','').strip()
 if level not in {'postcode','borough','county','country','continent'}:return jsonify(error='invalid_level'),400
 col={'postcode':'postcode','borough':'borough','county':'county','country':'country','continent':'continent'}[level]
 with db() as c:
  rows=c.execute(f'select postcode,borough,county,country,continent from link_ends where {col} ilike %s limit 100',('%'+value+'%',)).fetchall()
 return jsonify(level=level,value=value,endz=rows,hierarchy=['postcode','borough','county_region','country','continent','global','universe'])

@app.get('/api/lit/intelligence')
def lit_intelligence():
 scope=request.args.get('scope','postcode');value=request.args.get('scope_value','')
 if scope not in {'postcode','borough','county','country','continent','global','universe'}:return jsonify(error='invalid_scope'),400
 with db() as c:
  if value:rows=c.execute('select id,title,scope,scope_value,score,source,created_at from link_trends where scope=%s and scope_value=%s order by (score*1000000 + created_at) desc limit 50',(scope,value)).fetchall()
  else:rows=c.execute('select id,title,scope,scope_value,score,source,created_at from link_trends where scope=%s order by (score*1000000 + created_at) desc limit 50',(scope,)).fetchall()
 return jsonify(trends=rows,ranking=['score','freshness','geography'],private_messages_used=False)

@app.get('/api/business/intelligence')
def business_intelligence():
 q=request.args.get('q','').strip();pc=request.args.get('postcode','').strip().upper();like='%'+q+'%'
 with db() as c:
  if pc:rows=c.execute('select id,name,category,postcode,description from link_businesses where active=true and postcode=%s and (name ilike %s or category ilike %s) order by id desc limit 50',(pc,like,like)).fetchall()
  else:rows=c.execute('select id,name,category,postcode,description from link_businesses where active=true and (name ilike %s or category ilike %s) order by id desc limit 50',(like,like)).fetchall()
 return jsonify(businesses=rows,core_link_free=True,commercial_layer_only=True,private_data_monetized=False)

@app.route('/api/hrm/receipts',methods=['GET','POST'])
def hrm_receipts():
 u=uid();d=request.get_json(silent=True) or {}
 if not u:return jsonify(error='auth_required'),401
 with db() as c:
  if request.method=='POST':
   action=str(d.get('action',''))[:80];decision=str(d.get('decision',''))[:120];reason=str(d.get('reason',''))[:1000];approved=bool(d.get('approved',False))
   if not action or not decision:return jsonify(error='action_and_decision_required'),400
   r=c.execute('insert into link_hrm_receipts(user_id,action,decision,reason,approved,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(u,action,decision,reason,approved,now())).fetchone();return jsonify(ok=True,receipt_id=r['id']),201
  rows=c.execute('select id,action,decision,reason,approved,created_at from link_hrm_receipts where user_id=%s order by id desc limit 100',(u,)).fetchall()
 return jsonify(receipts=rows)
