from flask import Blueprint, jsonify, request
import time

youth_club = Blueprint('oap_youth_club', __name__)

AGE_BANDS = [
    {'slug':'junior','label':'Junior Club','min_age':6,'max_age':11},
    {'slug':'youth','label':'Youth Club','min_age':12,'max_age':17},
    {'slug':'young_adult','label':'Young Adults','min_age':18,'max_age':24},
]

ACTIVITIES = [
    'after_school','sports','music','media','gaming','coding','trades','cooking',
    'first_aid','money_basics','careers','apprenticeships','mentoring','homework_support',
    'confidence','leadership','entrepreneurship','local_history_culture','trips',
    'volunteering','fitness','wellbeing','digital_safety','anti_bullying','scam_awareness',
    'life_skills'
]

PROHIBITED = [
    'adult_sexual_content','gambling_mechanics','targeted_ads_to_minors','public_precise_location',
    'unrestricted_adult_minor_discovery','unsolicited_adult_minor_dm','dark_patterns',
    'infinite_scroll_engagement_targeting','rage_bait_ranking','streak_pressure',
    'debt_push','speculative_finance_pressure','sale_of_youth_data'
]


def register_youth_club(app, db, uid):
    def now(): return int(time.time())
    with db() as c:
        c.execute("create table if not exists oap_youth_clubs(id bigserial primary key,name text not null,postcode text not null,borough text,age_band text not null,status text not null default 'active',created_at bigint not null)")
        c.execute("create table if not exists oap_youth_memberships(id bigserial primary key,club_id bigint not null,user_id bigint not null,age_band text not null,status text not null default 'pending',guardian_required boolean not null default true,guardian_approved boolean not null default false,created_at bigint not null,unique(club_id,user_id))")
        c.execute("create table if not exists oap_youth_activities(id bigserial primary key,club_id bigint not null,kind text not null,title text not null,starts_at bigint,status text not null default 'planned',adult_supervision_required boolean not null default true,created_at bigint not null)")
        c.execute("create table if not exists oap_youth_guardians(id bigserial primary key,member_user_id bigint not null,guardian_user_id bigint not null,relationship text not null,status text not null default 'pending',created_at bigint not null,unique(member_user_id,guardian_user_id))")
        c.execute("create table if not exists oap_youth_adults(user_id bigint primary key,role text not null,certified boolean not null default false,safeguarding_checked boolean not null default false,active boolean not null default true,created_at bigint not null,updated_at bigint not null)")
        c.execute("create table if not exists oap_youth_sessions(id bigserial primary key,club_id bigint not null,activity_kind text not null,title text not null,starts_at bigint not null,ends_at bigint not null,capacity integer not null default 20,status text not null default 'planned',lead_adult_id bigint,created_at bigint not null)")
        c.execute("create table if not exists oap_youth_session_bookings(id bigserial primary key,session_id bigint not null,user_id bigint not null,status text not null default 'booked',guardian_consent boolean not null default false,created_at bigint not null,unique(session_id,user_id))")
        c.execute("create table if not exists oap_youth_attendance(id bigserial primary key,session_id bigint not null,user_id bigint not null,state text not null,checked_by bigint not null,created_at bigint not null,unique(session_id,user_id))")
        c.execute("create table if not exists oap_youth_incidents(id bigserial primary key,club_id bigint,session_id bigint,reporter_id bigint not null,kind text not null,details text not null,status text not null default 'open',severity text not null default 'standard',created_at bigint not null,updated_at bigint not null)")
        c.execute("create table if not exists oap_youth_audit(id bigserial primary key,actor_id bigint,action text not null,subject_type text not null,subject_id bigint,detail text not null,created_at bigint not null)")

    def audit(c, actor, action, subject_type, subject_id, detail):
        c.execute('insert into oap_youth_audit(actor_id,action,subject_type,subject_id,detail,created_at) values(%s,%s,%s,%s,%s,%s)',(actor,action,subject_type,subject_id,str(detail)[:1000],now()))

    def cleared_adult(c, user_id):
        row=c.execute('select certified,safeguarding_checked,active,role from oap_youth_adults where user_id=%s',(user_id,)).fetchone()
        return row if row and row['certified'] and row['safeguarding_checked'] and row['active'] else None

    @youth_club.get('/api/youth-club/health')
    def health():
        return jsonify(ok=True,service='oap-youth-club',parent='The Spot',safety='protected_by_default',operations=['guardians','certified_adults','sessions','bookings','attendance','consent','safeguarding','audit'],authority='human_final')

    @youth_club.get('/api/youth-club')
    def overview():
        return jsonify(name='Royal Prince ON ANY POSTCODE Youth Club',hierarchy=['postcode','borough','county_region','country','continent','world'],age_bands=AGE_BANDS,activities=ACTIVITIES,principles=['benefit_over_attention','learning_over_engagement','privacy_by_default','local_first','certified_adults_only','no_ads'],prohibited=PROHIBITED,adult_content_allowed=False,precise_location_public=False,targeted_ads=False,unrestricted_adult_minor_contact=False,authority='human_final')

    @youth_club.get('/api/youth-club/safety')
    def safety():
        return jsonify(certified_adults_required=True,safeguarding_checks_required=True,report_block=True,audit_required=True,guardian_controls_where_required=True,trusted_contact_escalation=True,public_profile='minimum_necessary',recommendation_goal='safety_skill_opportunity',engagement_goal='not_screen_time',prohibited=PROHIBITED,authority='human_final')

    @youth_club.route('/api/youth-club/clubs', methods=['GET','POST'])
    def clubs():
        with db() as c:
            if request.method == 'POST':
                u=uid(); d=request.get_json(silent=True) or {}
                if not u:return jsonify(error='auth_required'),401
                name=str(d.get('name','')).strip()[:160]; postcode=str(d.get('postcode','')).strip().upper()[:20]; age_band=str(d.get('age_band','youth')).strip().lower()
                if not name or not postcode or age_band not in {x['slug'] for x in AGE_BANDS}:return jsonify(error='invalid_club'),400
                r=c.execute('insert into oap_youth_clubs(name,postcode,borough,age_band,created_at) values(%s,%s,%s,%s,%s) returning id',(name,postcode,str(d.get('borough',''))[:120],age_band,now())).fetchone();audit(c,u,'club_created','club',r['id'],name)
                return jsonify(ok=True,club_id=r['id'],status='active'),201
            rows=c.execute("select id,name,postcode,borough,age_band,status from oap_youth_clubs where status='active' order by id desc limit 100").fetchall()
        return jsonify(clubs=rows)

    @youth_club.post('/api/youth-club/clubs/<int:club_id>/join')
    def join(club_id):
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        age_band=str(d.get('age_band','youth')).strip().lower()
        if age_band not in {x['slug'] for x in AGE_BANDS}:return jsonify(error='invalid_age_band'),400
        guardian_required=age_band in {'junior','youth'}
        with db() as c:
            if not c.execute("select 1 from oap_youth_clubs where id=%s and status='active'",(club_id,)).fetchone():return jsonify(error='not_found'),404
            c.execute("insert into oap_youth_memberships(club_id,user_id,age_band,status,guardian_required,guardian_approved,created_at) values(%s,%s,%s,%s,%s,%s,%s) on conflict(club_id,user_id) do update set age_band=excluded.age_band,guardian_required=excluded.guardian_required",(club_id,u,age_band,'pending_guardian' if guardian_required else 'pending',guardian_required,False,now()));audit(c,u,'membership_requested','club',club_id,age_band)
        return jsonify(ok=True,status='pending_guardian' if guardian_required else 'pending',guardian_required=guardian_required)

    @youth_club.post('/api/youth-club/guardians')
    def guardian_link():
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        try: guardian_id=int(d.get('guardian_user_id',0))
        except: guardian_id=0
        if guardian_id<=0 or guardian_id==u:return jsonify(error='invalid_guardian'),400
        rel=str(d.get('relationship','guardian')).strip()[:60] or 'guardian'
        with db() as c:
            c.execute("insert into oap_youth_guardians(member_user_id,guardian_user_id,relationship,status,created_at) values(%s,%s,%s,'pending',%s) on conflict(member_user_id,guardian_user_id) do update set relationship=excluded.relationship",(u,guardian_id,rel,now()));audit(c,u,'guardian_link_requested','user',guardian_id,rel)
        return jsonify(ok=True,status='pending',guardian_user_id=guardian_id)

    @youth_club.post('/api/youth-club/guardians/<int:member_user_id>/approve')
    def guardian_approve(member_user_id):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            link=c.execute("update oap_youth_guardians set status='approved' where member_user_id=%s and guardian_user_id=%s returning id",(member_user_id,u)).fetchone()
            if not link:return jsonify(error='guardian_link_not_found'),404
            c.execute("update oap_youth_memberships set guardian_approved=true,status='pending' where user_id=%s and guardian_required=true",(member_user_id,));audit(c,u,'guardian_approved','user',member_user_id,'guardian consent link approved')
        return jsonify(ok=True,status='approved')

    @youth_club.route('/api/youth-club/adults/me',methods=['GET','POST'])
    def adult_me():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}; role=str(d.get('role','mentor')).strip().lower()
                if role not in {'mentor','coach','tutor','activity_lead','safeguarding_lead'}:return jsonify(error='invalid_role'),400
                c.execute("insert into oap_youth_adults(user_id,role,created_at,updated_at) values(%s,%s,%s,%s) on conflict(user_id) do update set role=excluded.role,updated_at=excluded.updated_at",(u,role,now(),now()));audit(c,u,'adult_role_requested','user',u,role)
            row=c.execute('select user_id,role,certified,safeguarding_checked,active from oap_youth_adults where user_id=%s',(u,)).fetchone()
        return jsonify(adult=row,can_lead=bool(row and row['certified'] and row['safeguarding_checked'] and row['active']))

    @youth_club.post('/api/youth-club/clubs/<int:club_id>/sessions')
    def create_session(club_id):
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        try: starts=int(d.get('starts_at')); ends=int(d.get('ends_at')); capacity=max(1,min(200,int(d.get('capacity',20))))
        except:return jsonify(error='invalid_session'),400
        kind=str(d.get('activity_kind','')).strip().lower(); title=str(d.get('title','')).strip()[:160]
        if ends<=starts or kind not in ACTIVITIES or not title:return jsonify(error='invalid_session'),400
        with db() as c:
            if not cleared_adult(c,u):return jsonify(error='certified_safeguarding_checked_adult_required'),403
            if not c.execute("select 1 from oap_youth_clubs where id=%s and status='active'",(club_id,)).fetchone():return jsonify(error='not_found'),404
            r=c.execute("insert into oap_youth_sessions(club_id,activity_kind,title,starts_at,ends_at,capacity,status,lead_adult_id,created_at) values(%s,%s,%s,%s,%s,%s,'planned',%s,%s) returning id",(club_id,kind,title,starts,ends,capacity,u,now())).fetchone();audit(c,u,'session_created','session',r['id'],title)
        return jsonify(ok=True,session_id=r['id'],status='planned'),201

    @youth_club.post('/api/youth-club/sessions/<int:session_id>/book')
    def book_session(session_id):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            s=c.execute("select id,capacity,status from oap_youth_sessions where id=%s",(session_id,)).fetchone()
            if not s:return jsonify(error='not_found'),404
            if s['status'] not in {'planned','open'}:return jsonify(error='session_unavailable'),409
            m=c.execute("select guardian_required,guardian_approved,status from oap_youth_memberships where user_id=%s order by id desc limit 1",(u,)).fetchone()
            if not m:return jsonify(error='active_membership_required'),403
            if m['guardian_required'] and not m['guardian_approved']:return jsonify(error='guardian_consent_required'),403
            count=c.execute("select count(*) as n from oap_youth_session_bookings where session_id=%s and status='booked'",(session_id,)).fetchone()['n']
            if count>=s['capacity']:return jsonify(error='session_full'),409
            c.execute("insert into oap_youth_session_bookings(session_id,user_id,status,guardian_consent,created_at) values(%s,%s,'booked',%s,%s) on conflict(session_id,user_id) do update set status='booked',guardian_consent=excluded.guardian_consent",(session_id,u,bool(m['guardian_approved']),now()));audit(c,u,'session_booked','session',session_id,'guardian consent enforced')
        return jsonify(ok=True,status='booked')

    @youth_club.post('/api/youth-club/sessions/<int:session_id>/attendance/<int:member_user_id>')
    def attendance(session_id,member_user_id):
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        state=str(d.get('state','present')).strip().lower()
        if state not in {'present','absent','left_early','collected'}:return jsonify(error='invalid_attendance_state'),400
        with db() as c:
            if not cleared_adult(c,u):return jsonify(error='certified_safeguarding_checked_adult_required'),403
            if not c.execute('select 1 from oap_youth_session_bookings where session_id=%s and user_id=%s',(session_id,member_user_id)).fetchone():return jsonify(error='booking_required'),404
            c.execute("insert into oap_youth_attendance(session_id,user_id,state,checked_by,created_at) values(%s,%s,%s,%s,%s) on conflict(session_id,user_id) do update set state=excluded.state,checked_by=excluded.checked_by,created_at=excluded.created_at",(session_id,member_user_id,state,u,now()));audit(c,u,'attendance_updated','session',session_id,'%s:%s'%(member_user_id,state))
        return jsonify(ok=True,state=state)

    @youth_club.post('/api/youth-club/safeguarding/incidents')
    def incident():
        u=uid(); d=request.get_json(silent=True) or {}
        if not u:return jsonify(error='auth_required'),401
        kind=str(d.get('kind','other')).strip().lower()[:80]; details=str(d.get('details','')).strip()[:2000]; severity=str(d.get('severity','standard')).strip().lower()
        if not details or severity not in {'standard','high','emergency'}:return jsonify(error='invalid_incident'),400
        try: club_id=int(d.get('club_id')) if d.get('club_id') is not None else None; session_id=int(d.get('session_id')) if d.get('session_id') is not None else None
        except:return jsonify(error='invalid_incident'),400
        with db() as c:
            r=c.execute("insert into oap_youth_incidents(club_id,session_id,reporter_id,kind,details,severity,created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s,%s) returning id",(club_id,session_id,u,kind,details,severity,now(),now())).fetchone();audit(c,u,'safeguarding_incident','incident',r['id'],severity+':'+kind)
        return jsonify(ok=True,incident_id=r['id'],status='open',human_review=True,guardian_or_trusted_escalation=severity in {'high','emergency'}),201

    @youth_club.get('/api/youth-club/audit')
    def audit_log():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if not cleared_adult(c,u):return jsonify(error='certified_safeguarding_checked_adult_required'),403
            rows=c.execute('select id,actor_id,action,subject_type,subject_id,detail,created_at from oap_youth_audit order by id desc limit 200').fetchall()
        return jsonify(audit=rows)

    @youth_club.post('/api/youth-club/content-check')
    def content_check():
        d=request.get_json(silent=True) or {}; kind=str(d.get('kind','')).strip().lower()[:80]
        if not kind:return jsonify(error='kind_required'),400
        if kind in PROHIBITED:return jsonify(ok=False,allowed=False,reason='youth_safety_block',authority='human_final'),403
        return jsonify(ok=True,allowed=True,reason='age_appropriate_review_still_required',authority='human_final')

    app.register_blueprint(youth_club)
