from flask import Blueprint, jsonify, request
import os, time

royal_oap = Blueprint('royal_oap', __name__)


def register_royal_oap(app, db, uid):
    def now():
        return int(time.time())

    def founder_id():
        raw = os.environ.get('OAP_FOUNDER_USER_ID', '').strip()
        return int(raw) if raw.isdigit() and int(raw) > 0 else None

    def founder_only():
        founder = founder_id()
        current = uid()
        if founder is None:
            return None, (jsonify(error='founder_identity_not_configured'), 503)
        if current != founder:
            return None, (jsonify(error='founder_only'), 403)
        return current, None

    with db() as c:
        c.execute("create table if not exists oap_royal_registry(id bigserial primary key,layer text not null unique,status text not null,legal_state text not null,public_description text not null,updated_at bigint not null)")
        entries = [
            ('royal_identity', 'active', 'brand_and_heritage', 'Royal ON ANY POSTCODE identity and heritage layer.'),
            ('prince_sovereign', 'active', 'brand_and_institutional', 'Prince Sovereign institutional direction under human authority.'),
            ('prince_sovereign_bank', 'future', 'requires_licensing', 'Future banking concept kept separate from OAP World until properly authorised.'),
            ('royal_empire', 'concept', 'brand_concept', 'Wider Royal ecosystem and store direction.'),
        ]
        for layer, status, legal_state, description in entries:
            c.execute(
                "insert into oap_royal_registry(layer,status,legal_state,public_description,updated_at) values(%s,%s,%s,%s,%s) on conflict(layer) do update set status=excluded.status,legal_state=excluded.legal_state,public_description=excluded.public_description,updated_at=excluded.updated_at",
                (layer, status, legal_state, description, now()),
            )

    @royal_oap.get('/api/royal/health')
    def royal_health():
        return jsonify(ok=True, service='royal-on-any-postcode', authority='human_final', founder_private=True)

    @royal_oap.get('/api/royal')
    def royal_identity():
        return jsonify(
            name='Royal ON ANY POSTCODE',
            parent='ON ANY POSTCODE LTD',
            motto='Born Local. Built Global. Earth is our turf.',
            role='heritage_and_institutional_layer',
            replaces_oap=False,
            public_private_separation=True,
            government_claim=False,
            legal_royalty_claim=False,
            hierarchy=['Royal / Prince Sovereign','ON ANY POSTCODE LTD','OAP ecosystem'],
        )

    @royal_oap.get('/api/royal/institutions')
    def royal_institutions():
        with db() as c:
            rows = c.execute('select layer,status,legal_state,public_description,updated_at from oap_royal_registry order by id').fetchall()
        return jsonify(institutions=rows, banking_rule='No banking service is represented as licensed until proper authorisation exists.')

    @royal_oap.get('/api/royal/founder')
    def royal_founder():
        current, error = founder_only()
        if error:
            return error
        return jsonify(
            ok=True,
            user_id=current,
            area='royal_founder_private',
            access='founder_only',
            authority='final_human_authority',
            profile_creation='founder_only',
        )

    @royal_oap.post('/api/royal/registry/<layer>/state')
    def royal_registry_state(layer):
        current, error = founder_only()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        status = str(payload.get('status','')).strip().lower()
        allowed = {'concept','future','active','paused','retired'}
        if status not in allowed:
            return jsonify(error='invalid_status'), 400
        with db() as c:
            row = c.execute('update oap_royal_registry set status=%s,updated_at=%s where layer=%s returning layer,status,legal_state',(status,now(),layer)).fetchone()
        if not row:
            return jsonify(error='not_found'), 404
        return jsonify(ok=True, institution=row, changed_by=current)

    app.register_blueprint(royal_oap)
