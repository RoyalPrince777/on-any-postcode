from flask import Blueprint, jsonify, request
import time

event_bridge = Blueprint('oap_event_bridge', __name__)

PUBLIC_KINDS = {'movement_disruption','transport_update','road_closure','weather_advisory','community_safety','event_update'}
PRIVATE_KINDS = {'ride_match','ride_arrival','ride_state','ride_safety','guardian_alert','account_alert','mention','reply'}
ALLOWED_SCOPES = {'postcode','borough','county','country','continent','global','universe'}
LOCKED_PULSE = {'safety','account'}
PRIVATE_CATEGORY = {
    'ride_match':'ride','ride_arrival':'ride','ride_state':'ride','ride_safety':'safety',
    'guardian_alert':'safety','account_alert':'account','mention':'mentions','reply':'replies'
}


def register_event_bridge(app, db, uid):
    def now(): return int(time.time())

    with db() as c:
        c.execute("create table if not exists oap_event_bridge_events(id bigserial primary key,actor_id bigint,kind text not null,channel text not null,scope text,scope_value text,target_user_id bigint,title text not null,body text,created_at bigint not null)")

    def pulse_enabled(c,user_id,category):
        if category in LOCKED_PULSE:return True
        r=c.execute('select enabled from oap_pulse_preferences where user_id=%s and category=%s',(user_id,category)).fetchone()
        return True if not r else bool(r['enabled'])

    @event_bridge.get('/api/event-bridge/health')
    def health():
        return jsonify(ok=True,service='signals-pulse-event-bridge',public_channel='Signals',private_channel='Pulse',precise_public_location=False,preference_aware=True,protected_pulse_categories=sorted(LOCKED_PULSE),authority='human_final')

    @event_bridge.post('/api/event-bridge')
    def emit():
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        kind=str(d.get('kind','')).strip().lower()[:60]
        title=str(d.get('title','')).strip()[:160]
        body=str(d.get('body','')).strip()[:500]
        if not kind or not title:return jsonify(error='kind_title_required'),400

        if kind in PUBLIC_KINDS:
            scope=str(d.get('scope','postcode')).strip().lower()
            scope_value=str(d.get('scope_value','')).strip()[:100]
            if scope not in ALLOWED_SCOPES:return jsonify(error='invalid_scope'),400
            forbidden = any(k in d for k in ('lat','lon','latitude','longitude','exact_address','precise_location','coordinates'))
            if forbidden:return jsonify(error='precise_public_location_blocked'),403
            with db() as c:
                c.execute('insert into link_trends(title,scope,scope_value,score,source,created_at) values(%s,%s,%s,%s,%s,%s)',(title,scope,scope_value,int(d.get('score',1)),kind,now()))
                r=c.execute("insert into oap_event_bridge_events(actor_id,kind,channel,scope,scope_value,title,body,created_at) values(%s,%s,'Signals',%s,%s,%s,%s,%s) returning id",(u,kind,scope,scope_value,title,body,now())).fetchone()
                subscribers=c.execute('select count(*) as n from oap_signal_subscriptions where scope=%s and scope_value=%s',(scope,scope_value)).fetchone()
            return jsonify(ok=True,event_id=r['id'],channel='Signals',public=True,precise_location=False,matching_subscribers=int(subscribers['n']) if subscribers else 0),201

        if kind in PRIVATE_KINDS:
            try: target=int(d.get('target_user_id',u))
            except:return jsonify(error='invalid_target'),400
            category=PRIVATE_CATEGORY[kind]
            with db() as c:
                blocked=c.execute('select 1 from link_blocks where (owner_id=%s and blocked_id=%s) or (owner_id=%s and blocked_id=%s)',(u,target,target,u)).fetchone()
                if target!=u and blocked:return jsonify(error='blocked'),403
                enabled=pulse_enabled(c,target,category)
                r=c.execute("insert into oap_event_bridge_events(actor_id,kind,channel,target_user_id,title,body,created_at) values(%s,%s,'Pulse',%s,%s,%s,%s) returning id",(u,kind,target,title,body,now())).fetchone()
                if enabled:
                    c.execute('insert into link_notifications(user_id,kind,title,body,created_at) values(%s,%s,%s,%s,%s)',(target,kind,title,body,now()))
            return jsonify(ok=True,event_id=r['id'],channel='Pulse',public=False,target_user_id=target,category=category,delivered=enabled,suppressed_by_preference=not enabled,protected=category in LOCKED_PULSE),201

        return jsonify(error='unsupported_event_kind'),400

    app.register_blueprint(event_bridge)
