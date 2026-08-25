from flask import Blueprint, jsonify
import os, time

finalization = Blueprint('oap_finalization', __name__)

CAPABILITIES = {
    'geographic_data': {'kind':'provider','required_env':'OAP_GEO_PROVIDER','live_when':'configured_and_probed'},
    'weather': {'kind':'provider','required_env':'OAP_WEATHER_PROVIDER','live_when':'configured_and_probed'},
    'maps_routing': {'kind':'provider','required_env':'OAP_ROUTING_PROVIDER','live_when':'configured_and_probed'},
    'transport_realtime': {'kind':'provider','required_env':'OAP_TRANSPORT_PROVIDER','live_when':'configured_and_probed'},
    'education_providers': {'kind':'provider','required_env':'OAP_EDUCATION_PROVIDER','live_when':'configured_and_verified'},
    'observability': {'kind':'provider','required_env':'OAP_OBSERVABILITY_PROVIDER','live_when':'configured_and_probed'},
    'sika_regulated_payments': {'kind':'legal','required_env':'OAP_SIKA_REGULATED_ENABLED','live_when':'authorised_and_explicitly_enabled'},
    'banking': {'kind':'legal','required_env':'OAP_BANKING_AUTHORISED','live_when':'licensed_and_explicitly_enabled'},
}

CORE_PROBES = [
    ('link','/health'),
    ('spot_family','/api/spot/me'),
    ('royal','/api/royal/health'),
    ('intelligence','/api/intelligence/health'),
    ('world_intelligence','/api/world-intelligence'),
    ('earth_intelligence','/api/earth-intelligence'),
    ('universe_intelligence','/api/universe-intelligence'),
    ('education','/api/education/health'),
]


def _env_on(name):
    return os.environ.get(name,'').strip().lower() in {'1','true','yes','enabled','authorised','authorized'}


def register_finalization(app, db, uid):
    def now(): return int(time.time())

    with db() as c:
        c.execute("create table if not exists oap_readiness_checks(name text primary key,status text not null,detail text not null,checked_at bigint not null)")

    @finalization.get('/api/readiness/capabilities')
    def capabilities():
        rows=[]
        for name,meta in CAPABILITIES.items():
            raw=os.environ.get(meta['required_env'],'').strip()
            if meta['kind']=='legal':
                status='enabled' if _env_on(meta['required_env']) else 'blocked_pending_authorisation'
            else:
                status='configured_unverified' if raw else 'not_connected'
            rows.append({'name':name,'kind':meta['kind'],'status':status,'live_claim':False if status!='enabled' else True,'requirement':meta['live_when']})
        return jsonify(capabilities=rows,no_fake_live_labels=True)

    @finalization.get('/api/readiness/core')
    def core_readiness():
        results=[]
        with app.test_client() as c:
            for name,path in CORE_PROBES:
                headers={'X-Link-User':'1'} if path=='/api/spot/me' else {}
                try:
                    r=c.get(path,headers=headers)
                    ok=r.status_code==200
                    detail='http_%s'%r.status_code
                except Exception as e:
                    ok=False; detail='exception_%s'%type(e).__name__
                status='green' if ok else 'red'
                results.append({'name':name,'path':path,'status':status,'detail':detail})
                with db() as conn:
                    conn.execute("insert into oap_readiness_checks(name,status,detail,checked_at) values(%s,%s,%s,%s) on conflict(name) do update set status=excluded.status,detail=excluded.detail,checked_at=excluded.checked_at",(name,status,detail,now()))
        overall='green' if all(x['status']=='green' for x in results) else 'red'
        return jsonify(overall=overall,checks=results,authority='human_final',checked_at=now())

    @finalization.get('/api/readiness')
    def readiness():
        with db() as c:
            checks=c.execute('select name,status,detail,checked_at from oap_readiness_checks order by name').fetchall()
        external=[]
        for name,meta in CAPABILITIES.items():
            raw=os.environ.get(meta['required_env'],'').strip()
            if meta['kind']=='legal':
                status='enabled' if _env_on(meta['required_env']) else 'blocked_pending_authorisation'
            else:
                status='configured_unverified' if raw else 'not_connected'
            external.append({'name':name,'status':status})
        return jsonify(
            core_checks=checks,
            external_dependencies=external,
            green_definition='tested_and_live',
            amber_definition='built_or_configured_but_not_fully_verified',
            red_definition='failed_or_unavailable',
            purple_definition='learning_until_verified',
            no_fake_green=True,
            authority='human_final'
        )

    app.register_blueprint(finalization)
