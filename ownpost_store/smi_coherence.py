from flask import Blueprint, jsonify, request
import json, time, uuid

bp=Blueprint('oap_smi_coherence',__name__)

REGIONS={
 'left_hemisphere':{'role':'logic_rules_code_math','routes':['frontal_lobe','parietal_lobe']},
 'right_hemisphere':{'role':'creativity_culture_scenarios_meaning','routes':['temporal_lobe','occipital_lobe']},
 'corpus_callosum':{'role':'merge_hemisphere_outputs','routes':['frontal_lobe']},
 'frontal_lobe':{'role':'planning_strategy_judgement_metacognition','routes':['cerebellum']},
 'parietal_lobe':{'role':'space_postcode_maps_navigation','routes':['frontal_lobe']},
 'temporal_lobe':{'role':'language_audio_conversation_context','routes':['hippocampus','frontal_lobe']},
 'occipital_lobe':{'role':'vision_video_design_interpretation','routes':['frontal_lobe']},
 'thalamus':{'role':'attention_filter_signal_router','routes':['left_hemisphere','right_hemisphere']},
 'hypothalamus':{'role':'priority_resource_urgency_homeostasis','routes':['brainstem','frontal_lobe']},
 'hippocampus':{'role':'memory_route_form_retrieve_context','routes':['frontal_lobe']},
 'amygdala':{'role':'rapid_risk_threat_signal','routes':['frontal_lobe','brainstem']},
 'cerebellum':{'role':'timing_accuracy_test_correction','routes':['brainstem']},
 'brainstem':{'role':'continuity_health_body_bridge','routes':['nexus_kernel']},
}
LOOP=['observe','interpret','verify','adapt','test','remember','improve']

def _now():return int(time.time())
def _clean(v,n=500):return str(v or '').strip()[:n]

def register_smi_coherence(app,db,uid):
 with db() as c:
  c.execute("create table if not exists smi_coherence_cycles(id text primary key,user_id bigint,input_text text not null,attention text not null,routes text not null,verification text not null,adaptation text not null,test_state text not null,memory_state text not null,improvement_state text not null,created_at bigint not null)")
  c.execute("create table if not exists smi_intelligence_positions(id bigserial primary key,cycle_id text not null,intelligence text not null,position text not null,confidence double precision not null,evidence text not null,created_at bigint not null)")
  c.execute("create table if not exists smi_conflicts(id text primary key,cycle_id text not null,left_intelligence text not null,right_intelligence text not null,resolution text not null,state text not null,created_at bigint not null)")

 @bp.get('/api/smi/brain/regions')
 def regions():return jsonify(ok=True,regions=REGIONS,executable_router=True,brain_count=1,synthetic_mind='internal_not_second_brain')

 @bp.post('/api/smi/attention')
 def attention():
  d=request.get_json(silent=True) or {};signal=_clean(d.get('signal'),1200);modality=_clean(d.get('modality','text'),30).lower();risk=_clean(d.get('risk','low'),20).lower();place=bool(d.get('spatial',False));memory=bool(d.get('memory_needed',False))
  if not signal:return jsonify(error='signal_required'),400
  routes=['thalamus'];
  if risk in {'high','critical'}:routes+=['amygdala']
  if modality in {'image','video','vision'}:routes+=['right_hemisphere','occipital_lobe']
  elif modality in {'audio','speech','conversation'}:routes+=['right_hemisphere','temporal_lobe']
  else:routes+=['left_hemisphere','right_hemisphere']
  if place:routes+=['parietal_lobe']
  if memory:routes+=['hippocampus']
  routes+=['corpus_callosum','frontal_lobe','cerebellum','brainstem']
  return jsonify(ok=True,attention={'signal':signal,'priority':'critical' if risk=='critical' else ('high' if risk=='high' else 'normal'),'routes':list(dict.fromkeys(routes)),'filtered':False},authority='human_final')

 @bp.post('/api/smi/coherence/cycle')
 def cycle():
  u=uid()
  if not u:return jsonify(error='auth_required'),401
  d=request.get_json(silent=True) or {};text=_clean(d.get('input'),1200)
  if not text:return jsonify(error='input_required'),400
  attention='focused';routes=['thalamus','left_hemisphere','right_hemisphere','corpus_callosum','frontal_lobe','cerebellum','brainstem']
  verification='verified' if d.get('evidence') else 'needs_evidence';adaptation='bounded_candidate' if verification=='verified' else 'hold';test_state='required';memory_state='hrm_candidate';improvement_state='purple_until_verified'
  cid='coh-'+uuid.uuid4().hex[:20]
  with db() as c:c.execute('insert into smi_coherence_cycles(id,user_id,input_text,attention,routes,verification,adaptation,test_state,memory_state,improvement_state,created_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(cid,u,text,attention,json.dumps(routes),verification,adaptation,test_state,memory_state,improvement_state,_now()))
  return jsonify(ok=True,cycle_id=cid,loop=LOOP,observe={'input':text},interpret={'routes':routes},verify={'state':verification},adapt={'state':adaptation,'auto_rewrite':False},test={'state':test_state,'isolation_required':True},remember={'state':memory_state},improve={'state':improvement_state,'human_approval_required':True},authority='human_final'),201

 @bp.post('/api/smi/coherence/resolve')
 def resolve():
  u=uid()
  if not u:return jsonify(error='auth_required'),401
  d=request.get_json(silent=True) or {};cid=_clean(d.get('cycle_id'),80);positions=d.get('positions') or []
  if not cid or len(positions)<2:return jsonify(error='cycle_id_and_two_positions_required'),400
  norm=[]
  for p in positions[:20]:
   name=_clean(p.get('intelligence'),100);pos=_clean(p.get('position'),500);ev=_clean(p.get('evidence'),800)
   try:conf=max(0.0,min(1.0,float(p.get('confidence',0))))
   except:return jsonify(error='invalid_confidence'),400
   if not name or not pos:return jsonify(error='invalid_position'),400
   norm.append({'intelligence':name,'position':pos,'confidence':conf,'evidence':ev})
  unique={x['position'] for x in norm};conflict=len(unique)>1
  ranked=sorted(norm,key=lambda x:(bool(x['evidence']),x['confidence']),reverse=True);winner=ranked[0]
  resolution='consensus' if not conflict else ('evidence_weighted_recommendation' if winner['evidence'] else 'human_review_required')
  conflict_id=None
  with db() as c:
   for x in norm:c.execute('insert into smi_intelligence_positions(cycle_id,intelligence,position,confidence,evidence,created_at) values(%s,%s,%s,%s,%s,%s)',(cid,x['intelligence'],x['position'],x['confidence'],x['evidence'],_now()))
   if conflict:
    conflict_id='conf-'+uuid.uuid4().hex[:20];c.execute('insert into smi_conflicts(id,cycle_id,left_intelligence,right_intelligence,resolution,state,created_at) values(%s,%s,%s,%s,%s,%s,%s)',(conflict_id,cid,norm[0]['intelligence'],norm[1]['intelligence'],resolution,'resolved_recommendation' if winner['evidence'] else 'open_human_review',_now()))
  return jsonify(ok=True,conflict=conflict,conflict_id=conflict_id,resolution=resolution,recommendation=winner if resolution!='human_review_required' else None,silent_disagreement_allowed=False,human_final=True)

 @bp.get('/api/smi/coherence/health')
 def health():return jsonify(ok=True,loop=LOOP,conflict_resolution=True,silent_disagreement_allowed=False,brain_regions=len(REGIONS),controlled_adaptation=True,learning='purple_until_verified',authority='human_final')

 app.register_blueprint(bp)
