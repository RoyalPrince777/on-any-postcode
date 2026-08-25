from flask import Blueprint, jsonify
import os, time

checkpoints = Blueprint('oap_checkpoints', __name__)

INTERNAL = [
    ('link','/health'),
    ('signals','/api/signals'),
    ('language','/api/language'),
    ('communications','/api/communications/health'),
    ('signal_intelligence','/api/signal-intelligence/health'),
    ('spot','/api/spot/me'),
    ('location_bridge','/api/location-bridge/health'),
    ('event_bridge','/api/event-bridge/health'),
    ('providers','/api/providers'),
    ('provider_adapters','/api/adapters/health'),
    ('observability','/api/observability/health'),
    ('royal','/api/royal/health'),
    ('intelligence','/api/intelligence/health'),
    ('adaptive_coherence','/api/intelligence/adaptive-coherence'),
    ('world','/api/world-intelligence'),
    ('earth','/api/earth-intelligence'),
    ('continent','/api/continent-intelligence?continent=Africa'),
    ('country','/api/country-intelligence?continent=Africa&country=Ghana'),
    ('universe','/api/universe-intelligence'),
    ('education','/api/education/health'),
    ('youth_club','/api/youth-club/health'),
    ('bank_intelligence','/api/bank-intelligence/health'),
    ('regulated_rails','/api/regulated'),
    ('258','/api/258/health'),
    ('movement','/api/movement/health'),
    ('ride','/api/ride/health'),
    ('ride_admin','/api/ride/admin/health'),
]

EXTERNAL = [
    ('geographic_data','OAP_GEO_PROVIDER','provider'),
    ('weather','OAP_WEATHER_PROVIDER','provider'),
    ('maps_routing','OAP_ROUTING_PROVIDER','provider'),
    ('transport_realtime','OAP_TRANSPORT_PROVIDER','provider'),
    ('education_providers','OAP_EDUCATION_PROVIDER','provider'),
    ('observability_provider','OAP_OBSERVABILITY_PROVIDER','provider'),
    ('background_worker_247','OAP_258_WORKER_ENABLED','infrastructure'),
    ('ride_commercial','OAP_RIDE_COMMERCIAL_AUTHORISED','legal'),
    ('sika_regulated_payments','OAP_SIKA_REGULATED_ENABLED','legal'),
    ('banking','OAP_BANKING_AUTHORISED','legal'),
    ('open_banking','OAP_OPEN_BANKING_AUTHORISED','legal'),
]


def _on(name):
    return os.environ.get(name,'').strip().lower() in {'1','true','yes','enabled','authorised','authorized'}


def register_checkpoints(app, db, uid):
    def now(): return int(time.time())

    @checkpoints.get('/api/checkpoints')
    def all_checkpoints():
        internal=[]
        with app.test_client() as c:
            for name,path in INTERNAL:
                headers={'X-Link-User':'1'} if path=='/api/spot/me' else {}
                try:
                    r=c.get(path,headers=headers)
                    status='green' if r.status_code==200 else 'red'
                    detail='http_%s'%r.status_code
                except Exception as e:
                    status='red'
                    detail='exception_%s'%type(e).__name__
                internal.append({'name':name,'status':status,'detail':detail,'path':path})
        external=[]
        for name,env,kind in EXTERNAL:
            raw=os.environ.get(env,'').strip()
            if kind=='legal':
                status='enabled_unverified' if _on(env) else 'blocked_pending_authorisation'
            elif kind=='infrastructure':
                status='configured_unverified' if _on(env) else 'not_connected'
            else:
                status='configured_unverified' if raw else 'not_connected'
            external.append({'name':name,'kind':kind,'status':status})
        return jsonify(
            ok=True,
            checkpoint_model=['built','automated_tests','security_privacy_tests','integration_tests','deployed','live_probe','green'],
            internal=internal,
            external=external,
            internal_overall='green' if all(x['status']=='green' for x in internal) else 'red',
            external_overall='amber' if any(x['status']!='enabled_verified' for x in external) else 'green',
            canonical_language={'feed':'Signals','notifications':'Pulse','verified':'Certified','contribution':'Created Value'},
            learning_state='purple_until_verified',
            no_fake_green=True,
            authority='human_final',
            checked_at=now()
        )

    app.register_blueprint(checkpoints)
