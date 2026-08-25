from flask import Blueprint, jsonify, request
import time

oap_intelligence = Blueprint('oap_intelligence', __name__)

WORLD_HIERARCHY = ['postcode','borough','county_region','country','continent','global','universe']
WORLD_DOMAINS = ['place','movement','culture','weather_environment','market','events','spot','safety','services']
SYSTEM_INTELLIGENCES = ['oap_world_intelligence','spot_intelligence','link_intelligence','sika_intelligence','movement_intelligence','market_intelligence','media_intelligence','guardian','hrm']


def register_oap_intelligence(app, db, uid):
    def now(): return int(time.time())

    with db() as c:
        c.execute("create table if not exists oap_intelligence_registry(name text primary key,parent text,status text not null,authority text not null,scope text not null,updated_at bigint not null)")
        rows = [
            ('on_any_postcode_intelligence', None, 'active', 'human_final', 'whole_oap_ecosystem'),
            ('oap_world_intelligence', 'on_any_postcode_intelligence', 'active', 'human_final', 'geography_and_world_context'),
            ('spot_intelligence', 'oap_world_intelligence', 'active', 'human_final', 'local_place_context'),
            ('movement_intelligence', 'oap_world_intelligence', 'active', 'human_final', 'people_goods_services_movement'),
        ]
        for row in rows:
            c.execute("insert into oap_intelligence_registry(name,parent,status,authority,scope,updated_at) values(%s,%s,%s,%s,%s,%s) on conflict(name) do update set parent=excluded.parent,status=excluded.status,authority=excluded.authority,scope=excluded.scope,updated_at=excluded.updated_at", (*row, now()))

    @oap_intelligence.get('/api/intelligence/health')
    def intelligence_health():
        return jsonify(ok=True, service='on-any-postcode-intelligence', authority='human_final', autonomous_real_world_execution=False, learning_state='purple_until_verified')

    @oap_intelligence.get('/api/intelligence')
    def intelligence_root():
        return jsonify(
            name='ON ANY POSTCODE Intelligence',
            role='whole_ecosystem_intelligence_coordinator',
            parent='SMI',
            authority='human_final',
            children=SYSTEM_INTELLIGENCES,
            law=['proof_before_execution','verification_before_sharing','audit_before_automation','human_approval_before_real_world_action'],
        )

    @oap_intelligence.get('/api/world-intelligence')
    def world_intelligence():
        return jsonify(
            name='OAP World Intelligence',
            parent='ON ANY POSTCODE Intelligence',
            role='geographic_and_world_intelligence',
            hierarchy=WORLD_HIERARCHY,
            domains=WORLD_DOMAINS,
            local_first=True,
            no_level_skipping=True,
            precise_location_default=False,
            authority='human_final',
        )

    @oap_intelligence.get('/api/world-intelligence/hierarchy')
    def world_hierarchy():
        return jsonify(hierarchy=WORLD_HIERARCHY, local_first=True, no_level_skipping=True)

    @oap_intelligence.get('/api/world-intelligence/context')
    def world_context():
        scope = str(request.args.get('scope','postcode')).strip().lower()
        value = str(request.args.get('value','')).strip()[:120]
        if scope not in WORLD_HIERARCHY:
            return jsonify(error='invalid_scope', allowed=WORLD_HIERARCHY), 400
        context = {'scope':scope,'value':value,'domains':WORLD_DOMAINS,'source_mode':'live_oap_records','prediction':False,'precise_location_used':False}
        with db() as c:
            if scope == 'postcode' and value:
                pc=value.upper()
                context['places']=c.execute('select postcode,borough,county,country,continent from link_ends where postcode=%s order by id desc limit 10',(pc,)).fetchall()
                context['trends']=c.execute("select title,score,source from link_trends where scope='postcode' and scope_value=%s order by score desc limit 10",(pc,)).fetchall()
                context['businesses']=c.execute('select name,category,postcode from link_businesses where active=true and postcode=%s order by id desc limit 10',(pc,)).fetchall()
                context['events']=c.execute('select title,postcode,starts_at from link_events where postcode=%s and starts_at>=%s order by starts_at limit 10',(pc,now()-86400)).fetchall()
            else:
                context['places']=[]; context['trends']=[]; context['businesses']=[]; context['events']=[]
        return jsonify(context=context)

    @oap_intelligence.get('/api/intelligence/registry')
    def intelligence_registry():
        with db() as c:
            rows=c.execute('select name,parent,status,authority,scope,updated_at from oap_intelligence_registry order by name').fetchall()
        return jsonify(intelligences=rows)

    app.register_blueprint(oap_intelligence)
