from flask import Blueprint, jsonify, request
import os, time

ride = Blueprint('oap_ride', __name__)

TRIP_STATES = ['requested','matched','driver_coming','arrived','on_trip','completed','cancelled']
DRIVER_STATES = ['offline','available','busy']
RIDE_TYPES = ['local','standard','accessible','family','youth_safe','elder_safe','business','airport','scheduled','delivery']


def _enabled(name):
    return os.environ.get(name,'').strip().lower() in {'1','true','yes','enabled','authorised','authorized'}


def register_oap_ride(app, db, uid):
    def now(): return int(time.time())

    with db() as c:
        c.execute("create table if not exists oap_ride_drivers(user_id bigint primary key,display_name text not null,postcode text,vehicle_type text,certified boolean not null default false,licence_checked boolean not null default false,insurance_checked boolean not null default false,safeguarding_checked boolean not null default false,state text not null default 'offline',created_at bigint not null,updated_at bigint not null)")
        c.execute("create table if not exists oap_ride_requests(id bigserial primary key,rider_id bigint not null,ride_type text not null,origin text not null,destination text not null,postcode text,status text not null default 'requested',driver_id bigint,fare_estimate_minor bigint,currency text not null default 'GBP',scheduled_at bigint,guardian_required boolean not null default false,created_at bigint not null,updated_at bigint not null)")
        c.execute("create table if not exists oap_ride_events(id bigserial primary key,ride_id bigint not null,actor_id bigint,event_type text not null,from_state text,to_state text,details text,created_at bigint not null)")
        c.execute("create table if not exists oap_ride_safety(id bigserial primary key,ride_id bigint not null,reporter_id bigint not null,kind text not null,details text,status text not null default 'open',created_at bigint not null)")

    @ride.get('/api/ride/health')
    def health():
        commercial = _enabled('OAP_RIDE_COMMERCIAL_AUTHORISED')
        provider = bool(os.environ.get('OAP_ROUTING_PROVIDER','').strip())
        return jsonify(ok=True,service='oap-ride',parent='Movement',dispatch_software_live=True,commercial_ride_execution=commercial,routing_provider_connected=provider,payment_execution=False,authority='human_final',no_fake_green=True)

    @ride.get('/api/ride')
    def overview():
        return jsonify(
            name='OAP Ride',parent='Movement',intelligence='Ride Intelligence',captain='OAP Captain',
            ride_types=RIDE_TYPES,trip_states=TRIP_STATES,
            geography=['postcode','borough','county_region','country','continent','global'],
            connections=['movement','oap_captain','maps_routing','the_spot','guardian','hrm','bank_intelligence','sika'],
            principles=['local_first','certified_identity','transparent_created_value','privacy_default','safety_before_dispatch','human_final'],
            commercial_execution_requires=['transport_licensing','driver_checks','insurance','payment_provider','local_law_compliance'],
        )

    @ride.route('/api/ride/drivers/me',methods=['GET','POST'])
    def driver_me():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}
                name=str(d.get('display_name','')).strip()[:120]
                if not name:return jsonify(error='display_name_required'),400
                state=str(d.get('state','offline')).strip().lower()
                if state not in DRIVER_STATES:return jsonify(error='invalid_driver_state'),400
                c.execute("insert into oap_ride_drivers(user_id,display_name,postcode,vehicle_type,state,created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s) on conflict(user_id) do update set display_name=excluded.display_name,postcode=excluded.postcode,vehicle_type=excluded.vehicle_type,state=excluded.state,updated_at=excluded.updated_at",(u,name,str(d.get('postcode',''))[:20].upper(),str(d.get('vehicle_type','car'))[:60],state,now(),now()))
            row=c.execute('select user_id,display_name,postcode,vehicle_type,certified,licence_checked,insurance_checked,safeguarding_checked,state from oap_ride_drivers where user_id=%s',(u,)).fetchone()
        return jsonify(driver=row)

    @ride.post('/api/ride/estimate')
    def estimate():
        d=request.get_json(silent=True) or {}
        origin=str(d.get('origin','')).strip()[:200]; destination=str(d.get('destination','')).strip()[:200]
        if not origin or not destination:return jsonify(error='origin_destination_required'),400
        try: distance_km=max(0.0,min(2000.0,float(d.get('distance_km',0))))
        except:return jsonify(error='invalid_distance'),400
        # Planning estimate only: transparent illustrative formula, never a charged fare.
        base=300; per_km=150
        estimate=base+int(distance_km*per_km)
        return jsonify(ok=True,currency='GBP',estimate_minor=estimate,formula={'base_minor':base,'per_km_minor':per_km},planning_only=True,charged=False,dynamic_surge=False,provider_route_required=not bool(os.environ.get('OAP_ROUTING_PROVIDER','').strip()))

    @ride.route('/api/ride/requests',methods=['GET','POST'])
    def requests_route():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}
                rt=str(d.get('ride_type','standard')).strip().lower()
                if rt not in RIDE_TYPES:return jsonify(error='invalid_ride_type'),400
                origin=str(d.get('origin','')).strip()[:200]; destination=str(d.get('destination','')).strip()[:200]
                if not origin or not destination:return jsonify(error='origin_destination_required'),400
                scheduled=d.get('scheduled_at')
                try: scheduled=int(scheduled) if scheduled is not None else None
                except:return jsonify(error='invalid_schedule'),400
                guardian_required=rt=='youth_safe'
                r=c.execute("insert into oap_ride_requests(rider_id,ride_type,origin,destination,postcode,status,scheduled_at,guardian_required,created_at,updated_at) values(%s,%s,%s,%s,%s,'requested',%s,%s,%s,%s) returning id",(u,rt,origin,destination,str(d.get('postcode',''))[:20].upper(),scheduled,guardian_required,now(),now())).fetchone()
                c.execute("insert into oap_ride_events(ride_id,actor_id,event_type,to_state,details,created_at) values(%s,%s,'ride_requested','requested','HRM journey receipt',%s)",(r['id'],u,now()))
                return jsonify(ok=True,ride_id=r['id'],status='requested',dispatch_state='planning_only' if not _enabled('OAP_RIDE_COMMERCIAL_AUTHORISED') else 'eligible_for_dispatch',payment_state='not_charged',guardian_required=guardian_required),201
            rows=c.execute('select id,ride_type,origin,destination,postcode,status,driver_id,fare_estimate_minor,currency,scheduled_at,guardian_required from oap_ride_requests where rider_id=%s order by id desc limit 100',(u,)).fetchall()
        return jsonify(rides=rows)

    @ride.get('/api/ride/available')
    def available():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            d=c.execute('select certified,licence_checked,insurance_checked,safeguarding_checked,state,postcode from oap_ride_drivers where user_id=%s',(u,)).fetchone()
            if not d:return jsonify(error='driver_profile_required'),403
            if not (d['certified'] and d['licence_checked'] and d['insurance_checked']):return jsonify(error='driver_not_cleared'),403
            rows=c.execute("select id,ride_type,origin,destination,postcode,status,scheduled_at,guardian_required from oap_ride_requests where status='requested' and (postcode=%s or %s='') order by id limit 50",(d['postcode'],d['postcode'])).fetchall()
            rows=[r for r in rows if not r['guardian_required'] or d['safeguarding_checked']]
        return jsonify(rides=rows)

    @ride.post('/api/ride/<int:ride_id>/accept')
    def accept(ride_id):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        if not _enabled('OAP_RIDE_COMMERCIAL_AUTHORISED'):
            return jsonify(error='commercial_dispatch_blocked_pending_authorisation',execution=False,authority='human_final'),403
        with db() as c:
            d=c.execute('select certified,licence_checked,insurance_checked,safeguarding_checked from oap_ride_drivers where user_id=%s',(u,)).fetchone()
            if not d or not (d['certified'] and d['licence_checked'] and d['insurance_checked']):return jsonify(error='driver_not_cleared'),403
            trip=c.execute("select guardian_required,status from oap_ride_requests where id=%s for update",(ride_id,)).fetchone()
            if not trip:return jsonify(error='not_found'),404
            if trip['status']!='requested':return jsonify(error='ride_unavailable'),409
            if trip['guardian_required'] and not d['safeguarding_checked']:return jsonify(error='safeguarding_clearance_required'),403
            c.execute("update oap_ride_requests set driver_id=%s,status='matched',updated_at=%s where id=%s",(u,now(),ride_id))
            c.execute("update oap_ride_drivers set state='busy',updated_at=%s where user_id=%s",(now(),u))
            c.execute("insert into oap_ride_events(ride_id,actor_id,event_type,from_state,to_state,details,created_at) values(%s,%s,'driver_accept','requested','matched','Certified driver match',%s)",(ride_id,u,now()))
        return jsonify(ok=True,ride_id=ride_id,status='matched')

    @ride.post('/api/ride/<int:ride_id>/state')
    def state(ride_id):
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        target=str(d.get('status','')).strip().lower()
        if target not in TRIP_STATES:return jsonify(error='invalid_trip_state'),400
        transitions={'requested':{'cancelled'},'matched':{'driver_coming','cancelled'},'driver_coming':{'arrived','cancelled'},'arrived':{'on_trip','cancelled'},'on_trip':{'completed'},'completed':set(),'cancelled':set()}
        with db() as c:
            trip=c.execute('select rider_id,driver_id,status from oap_ride_requests where id=%s for update',(ride_id,)).fetchone()
            if not trip:return jsonify(error='not_found'),404
            if u not in {trip['rider_id'],trip['driver_id']}:return jsonify(error='forbidden'),403
            if target not in transitions.get(trip['status'],set()):return jsonify(error='invalid_transition',from_state=trip['status'],to_state=target),409
            old=trip['status']; c.execute('update oap_ride_requests set status=%s,updated_at=%s where id=%s',(target,now(),ride_id))
            if target in {'completed','cancelled'} and trip['driver_id']:
                c.execute("update oap_ride_drivers set state='available',updated_at=%s where user_id=%s",(now(),trip['driver_id']))
            c.execute("insert into oap_ride_events(ride_id,actor_id,event_type,from_state,to_state,details,created_at) values(%s,%s,'state_change',%s,%s,'HRM journey state receipt',%s)",(ride_id,u,old,target,now()))
        return jsonify(ok=True,ride_id=ride_id,status=target)

    @ride.post('/api/ride/<int:ride_id>/safety')
    def safety(ride_id):
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        kind=str(d.get('kind','')).strip().lower()[:60]
        if kind not in {'emergency','unsafe_driving','harassment','wrong_driver','wrong_rider','vehicle_issue','route_concern','other'}:return jsonify(error='invalid_safety_kind'),400
        with db() as c:
            trip=c.execute('select rider_id,driver_id from oap_ride_requests where id=%s',(ride_id,)).fetchone()
            if not trip:return jsonify(error='not_found'),404
            if u not in {trip['rider_id'],trip['driver_id']}:return jsonify(error='forbidden'),403
            r=c.execute('insert into oap_ride_safety(ride_id,reporter_id,kind,details,created_at) values(%s,%s,%s,%s,%s) returning id',(ride_id,u,kind,str(d.get('details',''))[:1000],now())).fetchone()
            c.execute("insert into oap_ride_events(ride_id,actor_id,event_type,details,created_at) values(%s,%s,'safety_report',%s,%s)",(ride_id,u,kind,now()))
        return jsonify(ok=True,report_id=r['id'],guardian_review=True,human_review=True),201

    @ride.get('/api/ride/<int:ride_id>/receipt')
    def receipt(ride_id):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            trip=c.execute('select id,rider_id,driver_id,ride_type,origin,destination,postcode,status,fare_estimate_minor,currency,scheduled_at,guardian_required,created_at,updated_at from oap_ride_requests where id=%s',(ride_id,)).fetchone()
            if not trip:return jsonify(error='not_found'),404
            if u not in {trip['rider_id'],trip['driver_id']}:return jsonify(error='forbidden'),403
            events=c.execute('select event_type,from_state,to_state,details,created_at from oap_ride_events where ride_id=%s order by id',(ride_id,)).fetchall()
        return jsonify(ride=trip,events=events,payment_state='not_charged',hrm_receipt=True)

    app.register_blueprint(ride)
