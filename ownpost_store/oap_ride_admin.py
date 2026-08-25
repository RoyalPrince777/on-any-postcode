from flask import Blueprint, jsonify, request
import os, time

ride_admin = Blueprint('oap_ride_admin', __name__)


def register_oap_ride_admin(app, db, uid):
    def now(): return int(time.time())
    def founder_id():
        raw=os.environ.get('OAP_FOUNDER_USER_ID','').strip()
        return int(raw) if raw.isdigit() and int(raw)>0 else None
    def require_founder():
        u=uid(); f=founder_id()
        if not f:return None,(jsonify(error='founder_not_configured'),503)
        if not u:return None,(jsonify(error='auth_required'),401)
        if u!=f:return None,(jsonify(error='founder_only'),403)
        return u,None

    with db() as c:
        c.execute("create table if not exists oap_ride_vehicles(id bigserial primary key,driver_id bigint not null,make text,model text,registration text,colour text,vehicle_type text not null default 'car',active boolean not null default true,created_at bigint not null,updated_at bigint not null)")
        c.execute("create table if not exists oap_ride_driver_approvals(id bigserial primary key,driver_id bigint not null,approved_by bigint not null,certified boolean not null,licence_checked boolean not null,insurance_checked boolean not null,safeguarding_checked boolean not null,details text,created_at bigint not null)")

    @ride_admin.get('/api/ride/admin/health')
    def health():
        return jsonify(ok=True,service='oap-ride-admin',founder_configured=bool(founder_id()),authority='founder_human_final',commercial_execution=False)

    @ride_admin.get('/api/ride/admin/drivers')
    def drivers():
        _,err=require_founder()
        if err:return err
        with db() as c:
            rows=c.execute('select user_id,display_name,postcode,vehicle_type,certified,licence_checked,insurance_checked,safeguarding_checked,state from oap_ride_drivers order by user_id').fetchall()
        return jsonify(drivers=rows)

    @ride_admin.post('/api/ride/admin/drivers/<int:driver_id>/approval')
    def approve(driver_id):
        founder,err=require_founder()
        if err:return err
        d=request.get_json(silent=True) or {}
        values={k:bool(d.get(k,False)) for k in ['certified','licence_checked','insurance_checked','safeguarding_checked']}
        with db() as c:
            exists=c.execute('select 1 from oap_ride_drivers where user_id=%s',(driver_id,)).fetchone()
            if not exists:return jsonify(error='driver_not_found'),404
            c.execute('update oap_ride_drivers set certified=%s,licence_checked=%s,insurance_checked=%s,safeguarding_checked=%s,updated_at=%s where user_id=%s',(
                values['certified'],values['licence_checked'],values['insurance_checked'],values['safeguarding_checked'],now(),driver_id))
            r=c.execute('insert into oap_ride_driver_approvals(driver_id,approved_by,certified,licence_checked,insurance_checked,safeguarding_checked,details,created_at) values(%s,%s,%s,%s,%s,%s,%s,%s) returning id',(
                driver_id,founder,values['certified'],values['licence_checked'],values['insurance_checked'],values['safeguarding_checked'],str(d.get('details',''))[:1000],now())).fetchone()
        return jsonify(ok=True,approval_id=r['id'],driver_id=driver_id,checks=values,hrm_receipt=True,commercial_execution=False)

    @ride_admin.route('/api/ride/admin/drivers/<int:driver_id>/vehicles',methods=['GET','POST'])
    def vehicles(driver_id):
        _,err=require_founder()
        if err:return err
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}
                if not c.execute('select 1 from oap_ride_drivers where user_id=%s',(driver_id,)).fetchone():return jsonify(error='driver_not_found'),404
                r=c.execute('insert into oap_ride_vehicles(driver_id,make,model,registration,colour,vehicle_type,created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s,%s) returning id',(
                    driver_id,str(d.get('make',''))[:80],str(d.get('model',''))[:80],str(d.get('registration',''))[:30].upper(),str(d.get('colour',''))[:40],str(d.get('vehicle_type','car'))[:60],now(),now())).fetchone()
                return jsonify(ok=True,vehicle_id=r['id']),201
            rows=c.execute('select id,driver_id,make,model,registration,colour,vehicle_type,active from oap_ride_vehicles where driver_id=%s order by id desc',(driver_id,)).fetchall()
        return jsonify(vehicles=rows)

    @ride_admin.get('/api/ride/admin/drivers/<int:driver_id>/approvals')
    def approvals(driver_id):
        _,err=require_founder()
        if err:return err
        with db() as c:
            rows=c.execute('select id,driver_id,approved_by,certified,licence_checked,insurance_checked,safeguarding_checked,details,created_at from oap_ride_driver_approvals where driver_id=%s order by id desc limit 100',(driver_id,)).fetchall()
        return jsonify(approvals=rows)

    app.register_blueprint(ride_admin)
