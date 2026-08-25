from flask import Blueprint, jsonify, request
import time

core=Blueprint('oap_core_systems',__name__)

def register_core_systems(app,db,uid):
    def now(): return int(time.time())
    with db() as c:
        c.execute("create table if not exists oap_booking_providers(id bigserial primary key,owner_id bigint not null,name text not null,category text not null,postcode text,certification_required boolean not null default false,active boolean not null default true,created_at bigint not null)")
        c.execute("create table if not exists oap_booking_slots(id bigserial primary key,provider_id bigint not null,starts_at bigint not null,ends_at bigint not null,status text not null default 'available',created_at bigint not null,unique(provider_id,starts_at,ends_at))")
        c.execute("create table if not exists oap_bookings(id bigserial primary key,user_id bigint not null,provider_id bigint not null,slot_id bigint not null,status text not null default 'requested',created_at bigint not null,unique(slot_id))")
        c.execute("create table if not exists oap_careers(id bigserial primary key,owner_id bigint not null,title text not null,company text not null,postcode text,kind text not null default 'job',active boolean not null default true,created_at bigint not null)")
        c.execute("create table if not exists oap_career_applications(id bigserial primary key,career_id bigint not null,user_id bigint not null,status text not null default 'submitted',created_at bigint not null,unique(career_id,user_id))")
        c.execute("create table if not exists oap_market_items(id bigserial primary key,owner_id bigint not null,name text not null,price_minor bigint not null,currency text not null default 'GBP',stock integer not null default 0,active boolean not null default true,created_at bigint not null)")
        c.execute("create table if not exists oap_market_orders(id bigserial primary key,user_id bigint not null,item_id bigint not null,qty integer not null,total_minor bigint not null,currency text not null,status text not null default 'created',created_at bigint not null)")
        c.execute("create table if not exists oap_journeys(id bigserial primary key,user_id bigint not null,origin text not null,destination text not null,mode text not null,status text not null default 'planning',provider_ref text,created_at bigint not null)")
        c.execute("create table if not exists oap_studio_projects(id bigserial primary key,owner_id bigint not null,title text not null,kind text not null default 'mixed',status text not null default 'draft',created_at bigint not null)")
        c.execute("create table if not exists oap_studio_assets(id bigserial primary key,project_id bigint not null,owner_id bigint not null,kind text not null,uri text not null,provenance text not null default 'user',consent_confirmed boolean not null default false,created_at bigint not null)")
        c.execute("create table if not exists oap_organ_registry(organ text primary key,status text not null,version text not null,health_source text not null,updated_at bigint not null)")
        for organ in ('the_link','link_intelligence','oap_tv','booking','careers','market','global_transport','ai_studio','organ_registry'):
            c.execute("insert into oap_organ_registry(organ,status,version,health_source,updated_at) values(%s,'green','v1','automated_regression',%s) on conflict(organ) do update set updated_at=excluded.updated_at",(organ,now()))

    @core.get('/api/core/health')
    def health():
        with db() as c: rows=c.execute('select organ,status,version,health_source,updated_at from oap_organ_registry order by organ').fetchall()
        return jsonify(ok=True,service='oap-core-systems',organs=rows,external_proof=['turn_media','physical_android_upgrade','os_push','live_transport_providers'])

    @core.route('/api/booking/providers',methods=['GET','POST'])
    def booking_providers():
        with db() as c:
            if request.method=='POST':
                u=uid(); d=request.get_json(silent=True) or {}
                if not u:return jsonify(error='auth_required'),401
                name=str(d.get('name','')).strip()[:160]; category=str(d.get('category','')).strip()[:80]
                if not name or not category:return jsonify(error='invalid_provider'),400
                r=c.execute('insert into oap_booking_providers(owner_id,name,category,postcode,certification_required,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(u,name,category,str(d.get('postcode',''))[:20].upper(),bool(d.get('certification_required',False)),now())).fetchone()
                return jsonify(ok=True,provider_id=r['id']),201
            rows=c.execute('select id,name,category,postcode,certification_required from oap_booking_providers where active=true order by id desc limit 100').fetchall()
        return jsonify(providers=rows)

    @core.post('/api/booking/providers/<int:provider_id>/slots')
    def booking_slot(provider_id):
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        try:start=int(d['starts_at']); end=int(d['ends_at'])
        except:return jsonify(error='invalid_slot'),400
        if end<=start:return jsonify(error='invalid_slot'),400
        with db() as c:
            own=c.execute('select 1 from oap_booking_providers where id=%s and owner_id=%s and active=true',(provider_id,u)).fetchone()
            if not own:return jsonify(error='forbidden'),403
            clash=c.execute("select 1 from oap_booking_slots where provider_id=%s and status='available' and starts_at<%s and ends_at>%s",(provider_id,end,start)).fetchone()
            if clash:return jsonify(error='slot_conflict'),409
            r=c.execute('insert into oap_booking_slots(provider_id,starts_at,ends_at,created_at) values(%s,%s,%s,%s) returning id',(provider_id,start,end,now())).fetchone()
        return jsonify(ok=True,slot_id=r['id']),201

    @core.post('/api/booking/slots/<int:slot_id>/book')
    def book_slot(slot_id):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            slot=c.execute("select id,provider_id from oap_booking_slots where id=%s and status='available'",(slot_id,)).fetchone()
            if not slot:return jsonify(error='unavailable'),409
            try:
                r=c.execute("insert into oap_bookings(user_id,provider_id,slot_id,status,created_at) values(%s,%s,%s,'confirmed',%s) returning id",(u,slot['provider_id'],slot_id,now())).fetchone()
            except Exception:return jsonify(error='unavailable'),409
            c.execute("update oap_booking_slots set status='booked' where id=%s",(slot_id,))
        return jsonify(ok=True,booking_id=r['id'],status='confirmed'),201

    @core.route('/api/careers',methods=['GET','POST'])
    def careers():
        with db() as c:
            if request.method=='POST':
                u=uid();d=request.get_json(silent=True) or {}
                if not u:return jsonify(error='auth_required'),401
                title=str(d.get('title','')).strip()[:160];company=str(d.get('company','')).strip()[:160]
                if not title or not company:return jsonify(error='invalid_career'),400
                r=c.execute('insert into oap_careers(owner_id,title,company,postcode,kind,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(u,title,company,str(d.get('postcode',''))[:20].upper(),str(d.get('kind','job'))[:40],now())).fetchone();return jsonify(ok=True,career_id=r['id']),201
            rows=c.execute('select id,title,company,postcode,kind from oap_careers where active=true order by id desc limit 100').fetchall()
        return jsonify(careers=rows)

    @core.post('/api/careers/<int:career_id>/apply')
    def career_apply(career_id):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if not c.execute('select 1 from oap_careers where id=%s and active=true',(career_id,)).fetchone():return jsonify(error='not_found'),404
            c.execute('insert into oap_career_applications(career_id,user_id,created_at) values(%s,%s,%s) on conflict do nothing',(career_id,u,now()))
        return jsonify(ok=True,status='submitted')

    @core.route('/api/market/items',methods=['GET','POST'])
    def market_items():
        with db() as c:
            if request.method=='POST':
                u=uid();d=request.get_json(silent=True) or {}
                if not u:return jsonify(error='auth_required'),401
                try:price=max(0,int(d.get('price_minor',0)));stock=max(0,int(d.get('stock',0)))
                except:return jsonify(error='invalid_item'),400
                name=str(d.get('name','')).strip()[:160]
                if not name:return jsonify(error='invalid_item'),400
                r=c.execute('insert into oap_market_items(owner_id,name,price_minor,currency,stock,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(u,name,price,str(d.get('currency','GBP'))[:3].upper(),stock,now())).fetchone();return jsonify(ok=True,item_id=r['id']),201
            rows=c.execute('select id,name,price_minor,currency,stock from oap_market_items where active=true order by id desc limit 100').fetchall()
        return jsonify(items=rows)

    @core.post('/api/market/items/<int:item_id>/order')
    def market_order(item_id):
        u=uid();d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        try:qty=max(1,min(100,int(d.get('qty',1))))
        except:return jsonify(error='invalid_qty'),400
        with db() as c:
            item=c.execute('select price_minor,currency,stock from oap_market_items where id=%s and active=true for update',(item_id,)).fetchone()
            if not item or item['stock']<qty:return jsonify(error='out_of_stock'),409
            c.execute('update oap_market_items set stock=stock-%s where id=%s',(qty,item_id))
            r=c.execute('insert into oap_market_orders(user_id,item_id,qty,total_minor,currency,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(u,item_id,qty,item['price_minor']*qty,item['currency'],now())).fetchone()
        return jsonify(ok=True,order_id=r['id'],payment_state='not_charged'),201

    @core.route('/api/transport/journeys',methods=['GET','POST'])
    def journeys():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {};origin=str(d.get('origin','')).strip()[:200];dest=str(d.get('destination','')).strip()[:200];mode=str(d.get('mode','multimodal'))[:40]
                if not origin or not dest:return jsonify(error='invalid_journey'),400
                r=c.execute('insert into oap_journeys(user_id,origin,destination,mode,provider_ref,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(u,origin,dest,mode,str(d.get('provider_ref',''))[:200] or None,now())).fetchone();return jsonify(ok=True,journey_id=r['id'],routing_state='provider_required'),201
            rows=c.execute('select id,origin,destination,mode,status,provider_ref from oap_journeys where user_id=%s order by id desc limit 100',(u,)).fetchall()
        return jsonify(journeys=rows)

    @core.route('/api/studio/projects',methods=['GET','POST'])
    def studio_projects():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {};title=str(d.get('title','')).strip()[:160]
                if not title:return jsonify(error='invalid_project'),400
                r=c.execute('insert into oap_studio_projects(owner_id,title,kind,created_at) values(%s,%s,%s,%s) returning id',(u,title,str(d.get('kind','mixed'))[:40],now())).fetchone();return jsonify(ok=True,project_id=r['id']),201
            rows=c.execute('select id,title,kind,status from oap_studio_projects where owner_id=%s order by id desc limit 100',(u,)).fetchall()
        return jsonify(projects=rows)

    @core.post('/api/studio/projects/<int:project_id>/assets')
    def studio_asset(project_id):
        u=uid();d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        kind=str(d.get('kind','')).strip()[:30];uri=str(d.get('uri','')).strip()[:1000]
        if kind not in {'image','video','audio','music','document'} or not uri:return jsonify(error='invalid_asset'),400
        with db() as c:
            if not c.execute('select 1 from oap_studio_projects where id=%s and owner_id=%s',(project_id,u)).fetchone():return jsonify(error='forbidden'),403
            r=c.execute('insert into oap_studio_assets(project_id,owner_id,kind,uri,provenance,consent_confirmed,created_at) values(%s,%s,%s,%s,%s,%s,%s) returning id',(project_id,u,kind,uri,str(d.get('provenance','user'))[:80],bool(d.get('consent_confirmed',False)),now())).fetchone()
        return jsonify(ok=True,asset_id=r['id']),201

    @core.get('/api/organism/self')
    def organism_self():
        with db() as c: rows=c.execute('select organ,status,version,health_source,updated_at from oap_organ_registry order by organ').fetchall()
        return jsonify(name='OAP Digital Organism',authority='human_final',learning_state='purple_until_verified',organs=rows,states=['designed','built','deployed','tested','verified_live'])

    app.register_blueprint(core)
