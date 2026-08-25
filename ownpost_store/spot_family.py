from flask import Blueprint, jsonify, request
import time

spot_family=Blueprint('spot_family',__name__)
LEVELS=('postcode','borough','region','country','continent','global','universe')
STANDINGS=('member','founder','builder','steward','champion','ambassador','patron')

def register_spot_family(app,db,uid):
    def now(): return int(time.time())
    with db() as c:
        c.execute("create table if not exists oap_places(id bigserial primary key,level text not null,name text not null,code text,parent_id bigint,active boolean not null default true,created_at bigint not null,unique(level,code))")
        c.execute("create table if not exists oap_place_memberships(id bigserial primary key,user_id bigint not null,place_id bigint not null,standing text not null default 'member',certification text not null default 'claimed',is_primary boolean not null default false,created_at bigint not null,unique(user_id,place_id))")
        c.execute("create table if not exists oap_family_links(id bigserial primary key,parent_user_id bigint not null,child_user_id bigint not null,created_at bigint not null,unique(parent_user_id,child_user_id),check(parent_user_id<>child_user_id))")
        c.execute("create table if not exists oap_community_roles(id bigserial primary key,place_id bigint not null,user_id bigint not null,title text not null,status text not null default 'active',starts_at bigint not null,ends_at bigint,appointment_method text not null default 'oap',created_at bigint not null)")
        c.execute("create index if not exists oap_place_parent_idx on oap_places(parent_id)")
        c.execute("create index if not exists oap_place_member_idx on oap_place_memberships(place_id,user_id)")
        c.execute("create index if not exists oap_family_child_idx on oap_family_links(child_user_id)")

    def auth():
        u=uid()
        return u if u else None

    @spot_family.post('/api/spot/places')
    def create_place():
        u=auth(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        level=str(d.get('level','')).strip().lower(); name=str(d.get('name','')).strip()[:120]; code=str(d.get('code','')).strip().upper()[:30] or None
        if level not in LEVELS or not name:return jsonify(error='invalid_place'),400
        parent=d.get('parent_id')
        with db() as c:
            if parent and not c.execute('select 1 from oap_places where id=%s and active=true',(parent,)).fetchone():return jsonify(error='invalid_parent'),400
            r=c.execute('insert into oap_places(level,name,code,parent_id,created_at) values(%s,%s,%s,%s,%s) on conflict(level,code) do update set name=excluded.name returning id',(level,name,code,parent,now())).fetchone()
        return jsonify(ok=True,place_id=r['id']),201

    @spot_family.post('/api/spot/places/<int:place_id>/join')
    def join_place(place_id):
        u=auth(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        standing=str(d.get('standing','member')).lower()
        if standing not in STANDINGS:return jsonify(error='invalid_standing'),400
        with db() as c:
            if not c.execute('select 1 from oap_places where id=%s and active=true',(place_id,)).fetchone():return jsonify(error='not_found'),404
            if bool(d.get('is_primary')):c.execute('update oap_place_memberships set is_primary=false where user_id=%s',(u,))
            c.execute("insert into oap_place_memberships(user_id,place_id,standing,certification,is_primary,created_at) values(%s,%s,%s,'claimed',%s,%s) on conflict(user_id,place_id) do update set standing=excluded.standing,is_primary=excluded.is_primary",(u,place_id,standing,bool(d.get('is_primary')),now()))
        return jsonify(ok=True,standing=standing,certification='claimed')

    @spot_family.get('/api/spot/me')
    def my_spot():
        u=auth()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            rows=c.execute('select p.id,p.level,p.name,p.code,m.standing,m.certification,m.is_primary from oap_place_memberships m join oap_places p on p.id=m.place_id where m.user_id=%s and p.active=true order by m.is_primary desc,p.level,p.name',(u,)).fetchall()
        return jsonify(places=rows)

    @spot_family.get('/api/spot/places/<int:place_id>')
    def place_family(place_id):
        with db() as c:
            p=c.execute('select id,level,name,code,parent_id from oap_places where id=%s and active=true',(place_id,)).fetchone()
            if not p:return jsonify(error='not_found'),404
            counts=c.execute('select count(*) members,count(*) filter(where certification=%s) certified from oap_place_memberships where place_id=%s',('certified',place_id)).fetchone()
            roles=c.execute("select r.title,r.status,r.starts_at,r.ends_at,r.appointment_method,u.display_name from oap_community_roles r left join link_users u on u.id=r.user_id where r.place_id=%s and r.status='active' order by r.id desc",(place_id,)).fetchall()
            children=c.execute('select id,level,name,code from oap_places where parent_id=%s and active=true order by name',(place_id,)).fetchall()
        return jsonify(place=p,family=counts,roles=roles,children=children,language={'family':'OAP Family','standing':'Standing','certified':'Certified'})

    @spot_family.post('/api/family/link')
    def family_link():
        u=auth(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        try:child=int(d.get('child_user_id'))
        except:return jsonify(error='invalid_user'),400
        if child==u:return jsonify(error='invalid_link'),400
        with db() as c:
            if not c.execute('select 1 from link_users where id=%s',(child,)).fetchone():return jsonify(error='not_found'),404
            c.execute('insert into oap_family_links(parent_user_id,child_user_id,created_at) values(%s,%s,%s) on conflict do nothing',(u,child,now()))
        return jsonify(ok=True,relationship='oap_community_lineage',financial_reward=False)

    @spot_family.get('/api/family/me')
    def family_me():
        u=auth()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            parents=c.execute('select u.id,u.display_name from oap_family_links f join link_users u on u.id=f.parent_user_id where f.child_user_id=%s',(u,)).fetchall()
            children=c.execute('select u.id,u.display_name from oap_family_links f join link_users u on u.id=f.child_user_id where f.parent_user_id=%s',(u,)).fetchall()
        return jsonify(kind='OAP Family',biological=False,parents=parents,children=children)

    @spot_family.post('/api/spot/places/<int:place_id>/roles')
    def add_role(place_id):
        u=auth(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        title=str(d.get('title','')).strip()[:100]
        if not title.startswith('OAP '):return jsonify(error='role_must_be_oap_labelled'),400
        # Foundation gate: role writes are self-scoped until Founder authority service is connected.
        with db() as c:
            if not c.execute('select 1 from oap_places where id=%s and active=true',(place_id,)).fetchone():return jsonify(error='not_found'),404
            r=c.execute('insert into oap_community_roles(place_id,user_id,title,starts_at,appointment_method,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(place_id,u,title,now(),str(d.get('appointment_method','oap'))[:40],now())).fetchone()
        return jsonify(ok=True,role_id=r['id'],government_role=False),201

    @spot_family.get('/api/spot/intelligence/<int:place_id>')
    def spot_intelligence(place_id):
        with db() as c:
            p=c.execute('select id,level,name,code,parent_id from oap_places where id=%s and active=true',(place_id,)).fetchone()
            if not p:return jsonify(error='not_found'),404
            members=c.execute('select count(*) n from oap_place_memberships where place_id=%s',(place_id,)).fetchone()['n']
            businesses=c.execute("select count(*) n from oap_booking_providers where active=true and upper(postcode)=upper(coalesce(%s,''))",(p.get('code'),)).fetchone()['n'] if p['level']=='postcode' else 0
        pulse='quiet' if members<5 else ('warming_up' if members<25 else ('about' if members<100 else 'poppin'))
        return jsonify(ok=True,spot=p,pulse=pulse,evidence={'members':members,'booking_businesses':businesses},prediction=False,precise_location_used=False)

    app.register_blueprint(spot_family)
