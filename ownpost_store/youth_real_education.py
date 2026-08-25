from flask import Blueprint, jsonify, request
import time

youth_education = Blueprint('youth_real_education', __name__)

TRACKS = [
    ('money_basics','Money Basics','budgeting, saving, banking basics, debt, interest, fraud awareness'),
    ('work_careers','Work & Careers','CVs, interviews, workplace rights, payslips, pensions, apprenticeships'),
    ('trades','Trades & Practical Skills','electrical awareness, plumbing basics, carpentry, construction, mechanics, tool safety'),
    ('housing','Housing & Renting','renting, deposits, bills, utilities, tenancy basics, home safety'),
    ('food','Food & Cooking','shopping, nutrition basics, food hygiene, meal planning, cooking essentials'),
    ('first_aid','First Aid & Emergency Readiness','basic first aid awareness, emergency planning, when to seek professional help'),
    ('digital_safety','Digital Safety','privacy, scams, passwords, phishing, consent, image sharing, cyberbullying'),
    ('civics','Civics & Everyday Law','rights, responsibilities, voting basics, contracts, consumer rights, public services'),
    ('relationships','Relationships & Boundaries','respect, consent, communication, coercion awareness, healthy boundaries'),
    ('movement','Movement & Travel','public transport, route planning, road awareness, travel documents, accessibility'),
    ('entrepreneurship','Enterprise & Business','pricing, customers, bookkeeping basics, tax awareness, ethical selling'),
    ('tax_contracts','Tax, Pay & Contracts','gross/net pay, tax basics, National Insurance awareness, contracts and invoices'),
    ('home_maintenance','Home & Maintenance','cleaning systems, laundry, basic repairs, utilities, fire and electrical safety'),
    ('health_literacy','Health Literacy','how to use health services, reliable information, appointments, medication safety basics'),
    ('media_literacy','Media & Fact Checking','sources, evidence, misinformation, manipulated media, advertising literacy'),
]


def register_youth_real_education(app, db, uid):
    def now(): return int(time.time())

    with db() as c:
        c.execute("create table if not exists oap_education_tracks(slug text primary key,title text not null,summary text not null,status text not null default 'active',updated_at bigint not null)")
        c.execute("create table if not exists oap_education_progress(user_id bigint not null,track_slug text not null,state text not null default 'started',updated_at bigint not null,primary key(user_id,track_slug))")
        for slug,title,summary in TRACKS:
            c.execute("insert into oap_education_tracks(slug,title,summary,status,updated_at) values(%s,%s,%s,'active',%s) on conflict(slug) do update set title=excluded.title,summary=excluded.summary,updated_at=excluded.updated_at",(slug,title,summary,now()))

    @youth_education.get('/api/education/health')
    def education_health():
        return jsonify(ok=True,service='oap-real-education',purpose='practical_life_learning',replaces_school=False,authority='human_final')

    @youth_education.get('/api/education/tracks')
    def education_tracks():
        with db() as c:
            rows=c.execute("select slug,title,summary,status from oap_education_tracks where status='active' order by title").fetchall()
        return jsonify(tracks=rows,principles=['real_facts','practical_skills','qualified_sources_for_high_stakes_topics','learn_by_doing','local_context'])

    @youth_education.get('/api/youth-safety/policy')
    def youth_policy():
        return jsonify(
            ok=True,
            privacy_default=True,
            precise_location_public=False,
            targeted_ads=False,
            adult_public_discovery_of_minors=False,
            minor_financial_execution=False,
            report_block_tools=True,
            audit_required=True,
            age_appropriate_controls=True,
            guardian_controls_where_required=True,
            high_risk_contact_escalation='guardian_or_trusted_safety_flow',
            public_profile_fields='minimum_necessary',
            authority='human_final'
        )

    @youth_education.route('/api/education/progress/<slug>',methods=['GET','POST'])
    def progress(slug):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if not c.execute('select 1 from oap_education_tracks where slug=%s and status=\'active\'',(slug,)).fetchone():return jsonify(error='track_not_found'),404
            if request.method=='POST':
                d=request.get_json(silent=True) or {}; state=str(d.get('state','started')).lower()
                if state not in {'started','practising','completed'}:return jsonify(error='invalid_state'),400
                c.execute("insert into oap_education_progress(user_id,track_slug,state,updated_at) values(%s,%s,%s,%s) on conflict(user_id,track_slug) do update set state=excluded.state,updated_at=excluded.updated_at",(u,slug,state,now()))
            row=c.execute('select track_slug,state,updated_at from oap_education_progress where user_id=%s and track_slug=%s',(u,slug)).fetchone() or {'track_slug':slug,'state':'not_started','updated_at':None}
        return jsonify(progress=row)

    app.register_blueprint(youth_education)
