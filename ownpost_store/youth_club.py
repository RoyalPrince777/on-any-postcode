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

    @youth_club.get('/api/youth-club/health')
    def health():
        return jsonify(ok=True,service='oap-youth-club',parent='The Spot',safety='protected_by_default',authority='human_final')

    @youth_club.get('/api/youth-club')
    def overview():
        return jsonify(
            name='Royal Prince ON ANY POSTCODE Youth Club',
            hierarchy=['postcode','borough','county_region','country','continent','world'],
            age_bands=AGE_BANDS,
            activities=ACTIVITIES,
            principles=['benefit_over_attention','learning_over_engagement','privacy_by_default','local_first','certified_adults_only','no_ads'],
            prohibited=PROHIBITED,
            adult_content_allowed=False,
            precise_location_public=False,
            targeted_ads=False,
            unrestricted_adult_minor_contact=False,
            authority='human_final'
        )

    @youth_club.get('/api/youth-club/safety')
    def safety():
        return jsonify(
            certified_adults_required=True,
            safeguarding_checks_required=True,
            report_block=True,
            audit_required=True,
            guardian_controls_where_required=True,
            trusted_contact_escalation=True,
            public_profile='minimum_necessary',
            recommendation_goal='safety_skill_opportunity',
            engagement_goal='not_screen_time',
            prohibited=PROHIBITED,
            authority='human_final'
        )

    @youth_club.route('/api/youth-club/clubs', methods=['GET','POST'])
    def clubs():
        with db() as c:
            if request.method == 'POST':
                u=uid(); d=request.get_json(silent=True) or {}
                if not u:return jsonify(error='auth_required'),401
                name=str(d.get('name','')).strip()[:160]
                postcode=str(d.get('postcode','')).strip().upper()[:20]
                age_band=str(d.get('age_band','youth')).strip().lower()
                if not name or not postcode or age_band not in {x['slug'] for x in AGE_BANDS}:
                    return jsonify(error='invalid_club'),400
                r=c.execute('insert into oap_youth_clubs(name,postcode,borough,age_band,created_at) values(%s,%s,%s,%s,%s) returning id',(name,postcode,str(d.get('borough',''))[:120],age_band,now())).fetchone()
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
            c.execute("insert into oap_youth_memberships(club_id,user_id,age_band,status,guardian_required,guardian_approved,created_at) values(%s,%s,%s,%s,%s,%s,%s) on conflict(club_id,user_id) do update set age_band=excluded.age_band,guardian_required=excluded.guardian_required",(club_id,u,age_band,'pending_guardian' if guardian_required else 'pending',guardian_required,False,now()))
        return jsonify(ok=True,status='pending_guardian' if guardian_required else 'pending',guardian_required=guardian_required)

    @youth_club.post('/api/youth-club/content-check')
    def content_check():
        d=request.get_json(silent=True) or {}
        kind=str(d.get('kind','')).strip().lower()[:80]
        if not kind:return jsonify(error='kind_required'),400
        if kind in PROHIBITED:return jsonify(ok=False,allowed=False,reason='youth_safety_block',authority='human_final'),403
        return jsonify(ok=True,allowed=True,reason='age_appropriate_review_still_required',authority='human_final')

    app.register_blueprint(youth_club)
