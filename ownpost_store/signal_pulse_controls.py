from flask import Blueprint, jsonify, request
import time

controls = Blueprint('oap_signal_pulse_controls', __name__)

PULSE_CATEGORIES = ['safety','account','ride','replies','mentions','community','movement','weather','transport']
LOCKED_ON = {'safety','account'}
SIGNAL_SCOPES = {'postcode','borough','county','country','continent','global','universe'}


def register_signal_pulse_controls(app, db, uid):
    def now(): return int(time.time())

    with db() as c:
        c.execute("create table if not exists oap_pulse_preferences(user_id bigint not null,category text not null,enabled boolean not null,updated_at bigint not null,primary key(user_id,category))")
        c.execute("create table if not exists oap_signal_subscriptions(id bigserial primary key,user_id bigint not null,scope text not null,scope_value text not null,created_at bigint not null,unique(user_id,scope,scope_value))")
        c.execute("create index if not exists oap_signal_subscriptions_user_idx on oap_signal_subscriptions(user_id)")

    def prefs_for(c,u):
        stored={r['category']:bool(r['enabled']) for r in c.execute('select category,enabled from oap_pulse_preferences where user_id=%s',(u,)).fetchall()}
        return {cat:(True if cat in LOCKED_ON else stored.get(cat,True)) for cat in PULSE_CATEGORIES}

    @controls.get('/api/communications/health')
    def health():
        return jsonify(ok=True,service='signals-pulse-controls',canonical={'stream':'Signals','alerts':'Pulse'},pulse_categories=PULSE_CATEGORIES,locked_on=sorted(LOCKED_ON),signal_scopes=sorted(SIGNAL_SCOPES),precise_location_subscriptions=False,authority='human_final')

    @controls.route('/api/pulse/preferences',methods=['GET','POST'])
    def pulse_preferences():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}
                category=str(d.get('category','')).strip().lower()
                if category not in PULSE_CATEGORIES:return jsonify(error='invalid_category'),400
                if category in LOCKED_ON and d.get('enabled') is False:
                    return jsonify(error='protected_category_cannot_be_disabled',category=category),403
                enabled=bool(d.get('enabled',True))
                c.execute("insert into oap_pulse_preferences(user_id,category,enabled,updated_at) values(%s,%s,%s,%s) on conflict(user_id,category) do update set enabled=excluded.enabled,updated_at=excluded.updated_at",(u,category,enabled,now()))
            prefs=prefs_for(c,u)
        return jsonify(preferences=prefs,canonical_name='Pulse',protected=sorted(LOCKED_ON))

    @controls.route('/api/signals/subscriptions',methods=['GET','POST','DELETE'])
    def signal_subscriptions():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method in {'POST','DELETE'}:
                d=request.get_json(silent=True) or {}
                scope=str(d.get('scope','')).strip().lower(); value=str(d.get('scope_value','')).strip()[:100]
                if scope not in SIGNAL_SCOPES or not value:return jsonify(error='invalid_subscription'),400
                forbidden={'lat','latitude','lon','lng','longitude','address','exact_address','coordinates'}
                if any(k in d for k in forbidden):return jsonify(error='precise_location_not_allowed'),400
                if request.method=='POST':
                    c.execute("insert into oap_signal_subscriptions(user_id,scope,scope_value,created_at) values(%s,%s,%s,%s) on conflict(user_id,scope,scope_value) do nothing",(u,scope,value,now()))
                else:
                    c.execute('delete from oap_signal_subscriptions where user_id=%s and scope=%s and scope_value=%s',(u,scope,value))
            rows=c.execute('select id,scope,scope_value,created_at from oap_signal_subscriptions where user_id=%s order by scope,scope_value',(u,)).fetchall()
        return jsonify(subscriptions=rows,canonical_name='Signals',precise_location_subscriptions=False)

    app.register_blueprint(controls)
