from flask import Blueprint, jsonify
import time

pillars = Blueprint('oap_pillars', __name__)

PILLARS = {
 'identity_privacy':['/api/royal/health','/api/organism/self','/api/communications/health'],
 'signals_pulse_trust':['/api/language','/api/signal-intelligence/health','/api/signal-trust/health','/api/event-bridge/health'],
 'smi_brain_cognition':['/api/smi/health','/api/smi/aegis','/api/smi/judgement','/api/smi/self','/api/smi/architecture'],
 'intelligence_governance':['/api/intelligence/health','/api/intelligence/adaptive-coherence','/api/world-intelligence','/api/earth-intelligence'],
 'place_movement':['/api/location-bridge/health','/api/movement/health','/api/ride/health','/api/ride/admin/health'],
 'youth_education':['/api/education/health','/api/youth-club/health','/api/youth-safety/policy'],
 'economy_boundaries':['/api/bank-intelligence/health','/api/regulated'],
 'runtime_observability':['/api/258/health','/api/observability/health','/api/providers','/api/adapters/health'],
 'readiness_audit':['/api/readiness/capabilities'],
}


def register_pillars(app):
 @pillars.get('/api/pillars')
 def pillar_status():
  rows=[]
  with app.test_client() as c:
   for name,paths in PILLARS.items():
    checks=[]
    for path in paths:
     try:
      r=c.get(path); status='green' if r.status_code==200 else 'red'; detail='http_%s'%r.status_code
     except Exception as e:
      status='red'; detail='exception_%s'%type(e).__name__
     checks.append({'path':path,'status':status,'detail':detail})
    rows.append({'name':name,'status':'green' if all(x['status']=='green' for x in checks) else 'red','checks':checks})
  return jsonify(ok=True,pillars=rows,internal_overall='green' if all(x['status']=='green' for x in rows) else 'red',green_definition='all_internal_pillar_probes_pass',external_dependencies_separate=True,acyclic=True,no_fake_green=True,authority='human_final',checked_at=int(time.time()))
 app.register_blueprint(pillars)
