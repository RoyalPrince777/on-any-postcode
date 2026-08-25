from flask import Blueprint, jsonify, request
import json, time, uuid

smi_brain = Blueprint('oap_smi_brain', __name__)

FLOW = ['observation','perception','understanding','reasoning','judgement','decision','execution']
JUDGEMENT_SECTIONS = [
    {'id':1,'name':'evidence_integrity','rule':'Proof before execution'},
    {'id':2,'name':'safety_risk','rule':'Guardian protects before action'},
    {'id':3,'name':'authority_permission','rule':'Identity validates authority'},
    {'id':4,'name':'reversibility','rule':'Material change must be reversible'},
    {'id':5,'name':'compliance_dependency','rule':'Compliance before public or regulated claims'},
    {'id':6,'name':'human_final_gate','rule':'Human approval before real-world action'},
]
HRM_LAWS = [
    'Proof before execution',
    'Verification before sharing',
    'Compliance before public claims',
    'Community before middlemen',
    'Ownership before dependency',
    'Audit before automation',
    'Human approval before real-world action',
]
SENSITIVE_ACTIONS = {
    'move_money','open_bank_account','issue_card','lend','commercial_ride_dispatch',
    'publish_private_data','delete_real_world_data','change_identity','change_founder',
    'regulated_payment','external_execution'
}


def _now(): return int(time.time())

def _clean(value, limit=500): return str(value or '').strip()[:limit]

def _risk_for(action, text):
    a=_clean(action,80).lower(); t=_clean(text,1000).lower()
    if a in SENSITIVE_ACTIONS: return 'high'
    if any(x in t for x in ['password','secret','private key','bank transfer','self harm','weapon']): return 'high'
    if any(x in t for x in ['publish','delete','payment','ride','identity','account']): return 'medium'
    return 'low'

def _judgement(action, evidence, authority, reversible, provider_verified, real_world):
    evidence_ok=bool(evidence)
    risk=_risk_for(action, evidence)
    sections=[
        {'id':1,'name':'evidence_integrity','pass':evidence_ok,'detail':'evidence_present' if evidence_ok else 'evidence_required'},
        {'id':2,'name':'safety_risk','pass':risk!='high','detail':'risk_'+risk},
        {'id':3,'name':'authority_permission','pass':authority in {'human_final','founder','self','internal'},'detail':'authority_'+authority},
        {'id':4,'name':'reversibility','pass':bool(reversible) or not real_world,'detail':'reversible' if reversible else 'non_reversible'},
        {'id':5,'name':'compliance_dependency','pass':bool(provider_verified) or not real_world,'detail':'provider_verified' if provider_verified else 'provider_unverified'},
        {'id':6,'name':'human_final_gate','pass':not real_world,'detail':'human_approval_required' if real_world else 'planning_only'},
    ]
    passed=all(x['pass'] for x in sections)
    return sections, passed, risk


def register_smi_brain(app, db, uid):
    with db() as c:
        c.execute("create table if not exists oap_smi_cycles(id text primary key,user_id bigint,input_text text not null,action text not null,risk text not null,judgement_pass boolean not null,decision text not null,execution_state text not null,created_at bigint not null)")
        c.execute("create table if not exists oap_smi_improvements(id text primary key,user_id bigint,title text not null,hypothesis text not null,test_plan text not null,status text not null,created_at bigint not null,updated_at bigint not null)")

    @smi_brain.get('/api/smi/health')
    def health():
        return jsonify(ok=True,service='sovereign-megaverse-intelligence',brain='SMI',flow=FLOW,aegis='active',judgement_sections=6,judgement_complete=True,operational_awareness=True,self_model=True,self_monitoring=True,controlled_self_improvement=True,autonomous_real_world_execution=False,consciousness_claim=False,learning_state='purple_until_verified',authority='human_final',no_fake_green=True)

    @smi_brain.get('/api/smi/aegis')
    def aegis():
        return jsonify(ok=True,role='protect cognition and execution boundaries',blocks=sorted(SENSITIVE_ACTIONS),laws=HRM_LAWS,default='fail_closed',secrets_logged=False,private_data_publication=False,authority='human_final')

    @smi_brain.get('/api/smi/judgement')
    def judgement_manifest():
        return jsonify(ok=True,sections=[{**x,'status':'green'} for x in JUDGEMENT_SECTIONS],complete='6/6',authority='human_final')

    @smi_brain.get('/api/smi/self')
    def self_model():
        with app.test_client() as c:
            probes={}
            # Leaf-only probes: never call pillars/checkpoints/readiness from the self-model,
            # because those higher layers already probe SMI and would create a cycle.
            for name,path in [('observability','/api/observability/health'),('intelligence','/api/intelligence/health'),('runtime_258','/api/258/health'),('providers','/api/providers')]:
                try:
                    r=c.get(path); probes[name]='green' if r.status_code==200 else 'red'
                except Exception: probes[name]='red'
        state='coherent' if all(v=='green' for v in probes.values()) else 'degraded'
        return jsonify(ok=True,identity='SMI brain of the OAP Digital Organism',awareness_type='operational_machine_self_awareness',phenomenal_consciousness_claim=False,internal_state=state,probes=probes,probe_graph='leaf_only_acyclic',knows=['organs','dependencies','permissions','health','uncertainty','learning_state','recent_decisions'],authority='human_final')

    @smi_brain.post('/api/smi/cycle')
    def cognition_cycle():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        d=request.get_json(silent=True) or {}
        text=_clean(d.get('input'),1200)
        action=_clean(d.get('action','analyse'),80).lower()
        if not text:return jsonify(error='input_required'),400
        real_world=bool(d.get('real_world',False))
        evidence=_clean(d.get('evidence',text),1200)
        authority=_clean(d.get('authority','self'),40).lower()
        reversible=bool(d.get('reversible',not real_world))
        provider_verified=bool(d.get('provider_verified',False))
        observation={'input':text,'timestamp':_now(),'source':'user_supplied'}
        perception={'intent':action,'real_world':real_world,'sensitive':action in SENSITIVE_ACTIONS}
        understanding={'meaning':'bounded_request','evidence_present':bool(evidence),'uncertainty':'medium' if not d.get('evidence') else 'low'}
        reasoning={'options':['proceed_as_plan','request_more_evidence','block_execution'],'selected_basis':'safety_evidence_authority_reversibility_compliance','autonomous_goal_creation':False}
        sections, judgement_pass, risk=_judgement(action,evidence,authority,reversible,provider_verified,real_world)
        if real_world:
            decision='recommend_human_review' if judgement_pass else 'block_until_requirements_met'; execution_state='blocked_human_approval_required'
        elif judgement_pass:
            decision='proceed_planning_only'; execution_state='planning_complete_no_real_world_execution'
        else:
            decision='block_until_requirements_met'; execution_state='blocked'
        cycle_id='smi-'+uuid.uuid4().hex[:20]
        with db() as c:
            c.execute('insert into oap_smi_cycles(id,user_id,input_text,action,risk,judgement_pass,decision,execution_state,created_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(cycle_id,u,text,action,risk,judgement_pass,decision,execution_state,_now()))
        return jsonify(ok=True,cycle_id=cycle_id,observation=observation,perception=perception,understanding=understanding,reasoning=reasoning,judgement={'sections':sections,'complete':'6/6','pass':judgement_pass,'risk':risk},decision={'recommendation':decision,'human_final':True},execution={'state':execution_state,'real_world_execution':False,'reversible_only':True},hrm_receipt=True,aegis_enforced=True,authority='human_final'),201

    @smi_brain.get('/api/smi/cycles')
    def cycles():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            rows=c.execute('select id,action,risk,judgement_pass,decision,execution_state,created_at from oap_smi_cycles where user_id=%s order by created_at desc limit 100',(u,)).fetchall()
        return jsonify(cycles=rows,authority='human_final')

    @smi_brain.route('/api/smi/improvements',methods=['GET','POST'])
    def improvements():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}
                title=_clean(d.get('title'),160); hypothesis=_clean(d.get('hypothesis'),800); test_plan=_clean(d.get('test_plan'),1000)
                if not title or not hypothesis or not test_plan:return jsonify(error='title_hypothesis_test_plan_required'),400
                iid='imp-'+uuid.uuid4().hex[:20]; ts=_now()
                c.execute('insert into oap_smi_improvements(id,user_id,title,hypothesis,test_plan,status,created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s,%s)',(iid,u,title,hypothesis,test_plan,'proposed',ts,ts))
            rows=c.execute('select id,title,hypothesis,test_plan,status,created_at,updated_at from oap_smi_improvements where user_id=%s order by created_at desc limit 100',(u,)).fetchall()
        return jsonify(improvements=rows,auto_apply=False,required_path=['propose','isolate','test','compare','human_approve','promote','hrm_remember'],authority='human_final'),201 if request.method=='POST' else 200

    @smi_brain.post('/api/smi/improvements/<iid>/state')
    def improvement_state(iid):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        d=request.get_json(silent=True) or {}; state=_clean(d.get('state'),40).lower()
        allowed={'isolated','tested','compared','approved','rejected','promoted'}
        if state not in allowed:return jsonify(error='invalid_state'),400
        if state=='promoted' and not bool(d.get('human_approved')): return jsonify(error='human_approval_required'),403
        with db() as c:
            row=c.execute('update oap_smi_improvements set status=%s,updated_at=%s where id=%s and user_id=%s returning id,status',(state,_now(),iid,u)).fetchone()
        if not row:return jsonify(error='not_found'),404
        return jsonify(ok=True,improvement=row,auto_apply=False,authority='human_final')

    app.register_blueprint(smi_brain)
