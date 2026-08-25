from flask import Blueprint, jsonify, request
import time

bp=Blueprint('oap_smi_resilience',__name__)

PRIORITY={
 'guardian':100,'active_journey':95,'the_link':90,'bell_me':90,'booking':80,
 'spot':70,'tv':60,'entertainment':55,'studio':40,'background':20
}
QUEUE_LIMITS={
 'the_link':5000,'journeys':2500,'spot':4000,'studio':500,'background':1000
}
DENY_EDGES={
 ('studio','sovereign_private_core'),('market','private_link_messages'),
 ('spot','precise_gps'),('ordinary_agent','sovereign_private_core')
}

def register_smi_resilience(app,db,uid):
 def now(): return int(time.time())
 with db() as c:
  c.execute("create table if not exists smi_provider_circuits(provider text primary key,state text not null default 'closed',failures integer not null default 0,opened_at bigint,updated_at bigint not null)")
  c.execute("create table if not exists smi_queue_state(name text primary key,depth integer not null default 0,limit_depth integer not null,retry_limit integer not null default 3,dead_letter boolean not null default true,updated_at bigint not null)")
  c.execute("create table if not exists smi_spot_cache(scope text not null,scope_value text not null,payload text not null,version bigint not null,expires_at bigint not null,updated_at bigint not null,primary key(scope,scope_value))")
  c.execute("create table if not exists smi_recovery_events(id bigserial primary key,component text not null,state text not null,probe_passed boolean not null,reason text not null,created_at bigint not null)")
  for name,lim in QUEUE_LIMITS.items():
   c.execute("insert into smi_queue_state(name,depth,limit_depth,retry_limit,dead_letter,updated_at) values(%s,0,%s,3,true,%s) on conflict(name) do update set limit_depth=excluded.limit_depth,updated_at=excluded.updated_at",(name,lim,now()))

 @bp.get('/api/smi/resilience/health')
 def health():
  return jsonify(ok=True,service='smi-resilience',controls=['workload_isolation','bounded_queues','spot_cache','trend_integrity','transport_circuit_breakers','cross_organ_permissions','critical_service_priority'],learning='purple_until_verified')

 @bp.get('/api/smi/priorities')
 def priorities(): return jsonify(priorities=PRIORITY,rule='critical_human_services_first')

 @bp.route('/api/smi/queues/<name>',methods=['GET','POST'])
 def queue_state(name):
  if name not in QUEUE_LIMITS:return jsonify(error='unknown_queue'),404
  with db() as c:
   if request.method=='POST':
    d=request.get_json(silent=True) or {}
    try:delta=max(0,int(d.get('enqueue',0)))
    except:return jsonify(error='invalid_enqueue'),400
    row=c.execute('select depth,limit_depth from smi_queue_state where name=%s for update',(name,)).fetchone()
    accepted=min(delta,max(0,row['limit_depth']-row['depth'])); dropped=delta-accepted
    c.execute('update smi_queue_state set depth=depth+%s,updated_at=%s where name=%s',(accepted,now(),name))
   row=c.execute('select name,depth,limit_depth,retry_limit,dead_letter,updated_at from smi_queue_state where name=%s',(name,)).fetchone()
  out=dict(row);out['backpressure']=out['depth']>=out['limit_depth'];out['dropped']=dropped if request.method=='POST' else 0
  return jsonify(queue=out)

 @bp.post('/api/smi/queues/<name>/drain')
 def drain(name):
  if name not in QUEUE_LIMITS:return jsonify(error='unknown_queue'),404
  d=request.get_json(silent=True) or {}
  try:n=max(0,int(d.get('count',1)))
  except:return jsonify(error='invalid_count'),400
  with db() as c:c.execute('update smi_queue_state set depth=greatest(0,depth-%s),updated_at=%s where name=%s',(n,now(),name))
  return jsonify(ok=True)

 @bp.post('/api/smi/spot-cache')
 def spot_cache_put():
  d=request.get_json(silent=True) or {};scope=str(d.get('scope','postcode')).lower();value=str(d.get('scope_value','')).strip().upper();payload=str(d.get('payload',''))[:4000]
  if scope not in {'postcode','borough','county','country','continent','global','universe'} or not value:return jsonify(error='invalid_scope'),400
  ttl=min(max(int(d.get('ttl',120)),30),3600)
  with db() as c:
   r=c.execute("insert into smi_spot_cache(scope,scope_value,payload,version,expires_at,updated_at) values(%s,%s,%s,1,%s,%s) on conflict(scope,scope_value) do update set payload=excluded.payload,version=smi_spot_cache.version+1,expires_at=excluded.expires_at,updated_at=excluded.updated_at returning version",(scope,value,payload,now()+ttl,now())).fetchone()
  return jsonify(ok=True,scope=scope,scope_value=value,version=r['version'],fresh_for=ttl)

 @bp.get('/api/smi/spot-cache')
 def spot_cache_get():
  scope=request.args.get('scope','postcode').lower();value=request.args.get('scope_value','').strip().upper()
  with db() as c:r=c.execute('select scope,scope_value,payload,version,expires_at,updated_at from smi_spot_cache where scope=%s and scope_value=%s',(scope,value)).fetchone()
  if not r:return jsonify(hit=False),404
  fresh=r['expires_at']>=now();return jsonify(hit=fresh,stale=not fresh,entry=r)

 @bp.post('/api/smi/trend-integrity')
 def trend_integrity():
  d=request.get_json(silent=True) or {}
  try:volume=max(0,float(d.get('volume',0)));breadth=max(0,float(d.get('independent_sources',0)));dup=max(0,float(d.get('duplicate_ratio',0)));fresh=max(0,min(1,float(d.get('freshness',1))));trust=max(0,min(1,float(d.get('provenance_trust',0.5))))
  except:return jsonify(error='invalid_metrics'),400
  manipulation=min(1.0,dup + (0.35 if volume>50 and breadth<3 else 0))
  score=max(0.0,(min(volume,100)/100.0)*0.25 + min(breadth,20)/20.0*0.30 + fresh*0.20 + trust*0.25 - manipulation*0.50)
  state='quarantine' if manipulation>=0.6 else ('review' if manipulation>=0.3 else 'eligible')
  return jsonify(state=state,integrity_score=round(score,4),manipulation_risk=round(manipulation,4),pay_to_trend=False)

 @bp.route('/api/smi/circuits/<provider>',methods=['GET','POST'])
 def circuit(provider):
  provider=provider[:80].lower()
  with db() as c:
   row=c.execute('select provider,state,failures,opened_at,updated_at from smi_provider_circuits where provider=%s',(provider,)).fetchone()
   if not row:
    c.execute("insert into smi_provider_circuits(provider,state,failures,updated_at) values(%s,'closed',0,%s)",(provider,now()));row={'provider':provider,'state':'closed','failures':0,'opened_at':None,'updated_at':now()}
   if request.method=='POST':
    d=request.get_json(silent=True) or {};event=str(d.get('event','success'))
    if event not in {'success','failure','probe_pass'}:return jsonify(error='invalid_event'),400
    failures=0 if event in {'success','probe_pass'} else int(row['failures'])+1
    state='closed' if event in {'success','probe_pass'} else ('open' if failures>=3 else 'closed')
    opened=now() if state=='open' else None
    c.execute('update smi_provider_circuits set state=%s,failures=%s,opened_at=%s,updated_at=%s where provider=%s',(state,failures,opened,now(),provider))
    row=c.execute('select provider,state,failures,opened_at,updated_at from smi_provider_circuits where provider=%s',(provider,)).fetchone()
  return jsonify(circuit=row,provider_execution_allowed=row['state']=='closed')

 @bp.post('/api/smi/permission-check')
 def permission_check():
  d=request.get_json(silent=True) or {};source=str(d.get('source','')).lower();target=str(d.get('target','')).lower();explicit=bool(d.get('explicit_capability',False))
  denied=(source,target) in DENY_EDGES and not explicit
  return jsonify(allowed=not denied,source=source,target=target,reason='explicit_capability_required' if denied else 'allowed_by_policy')

 @bp.post('/api/smi/recovery')
 def recovery():
  d=request.get_json(silent=True) or {};component=str(d.get('component','')).strip()[:100];state=str(d.get('state','recovering'));probe=bool(d.get('probe_passed',False));reason=str(d.get('reason',''))[:500]
  if not component or state not in {'pressure','contained','degraded','recovering','green','red'}:return jsonify(error='invalid_recovery'),400
  effective='green' if state=='green' and probe else ('recovering' if state=='green' and not probe else state)
  with db() as c:c.execute('insert into smi_recovery_events(component,state,probe_passed,reason,created_at) values(%s,%s,%s,%s,%s)',(component,effective,probe,reason,now()))
  return jsonify(ok=True,component=component,state=effective,probe_passed=probe,green_earned=effective=='green' and probe)

 app.register_blueprint(bp)
