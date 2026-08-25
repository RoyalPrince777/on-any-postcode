from flask import Blueprint, jsonify, request
import os, time

signal_trust = Blueprint('oap_signal_trust', __name__)


def register_signal_trust(app, db, uid):
    def now(): return int(time.time())
    def founder_id():
        raw=str(os.getenv('OAP_FOUNDER_USER_ID','')).strip()
        return int(raw) if raw.isdigit() and int(raw)>0 else None
    def founder_only():
        fid=founder_id(); u=uid()
        if fid is None:return None,(jsonify(error='founder_identity_not_configured'),503)
        if u!=fid:return None,(jsonify(error='founder_only'),403)
        return u,None

    with db() as c:
        c.execute("create table if not exists oap_signal_trust(signal_id bigint primary key,trust_state text not null,evidence_ref text,certified_by bigint,checked_at bigint not null)")

    @signal_trust.get('/api/signal-trust/health')
    def health():
        return jsonify(ok=True,service='signal-trust',default_state='unverified',certification='founder_only',source_label_alone_grants_trust=False,authority='human_final')

    @signal_trust.get('/api/signal-trust/<int:signal_id>')
    def get_trust(signal_id):
        with db() as c:
            row=c.execute('select signal_id,trust_state,evidence_ref,certified_by,checked_at from oap_signal_trust where signal_id=%s',(signal_id,)).fetchone()
        return jsonify(signal_id=signal_id,trust=dict(row) if row else {'trust_state':'unverified'},authority='human_final')

    @signal_trust.post('/api/signal-trust/<int:signal_id>/certify')
    def certify(signal_id):
        u,error=founder_only()
        if error:return error
        d=request.get_json(silent=True) or {}
        evidence_ref=str(d.get('evidence_ref','')).strip()[:300]
        if not evidence_ref:return jsonify(error='evidence_ref_required'),400
        with db() as c:
            exists=c.execute('select id from link_trends where id=%s',(signal_id,)).fetchone()
            if not exists:return jsonify(error='signal_not_found'),404
            row=c.execute("insert into oap_signal_trust(signal_id,trust_state,evidence_ref,certified_by,checked_at) values(%s,'certified',%s,%s,%s) on conflict(signal_id) do update set trust_state='certified',evidence_ref=excluded.evidence_ref,certified_by=excluded.certified_by,checked_at=excluded.checked_at returning signal_id,trust_state,evidence_ref,certified_by,checked_at",(signal_id,evidence_ref,u,now())).fetchone()
        return jsonify(ok=True,trust=row,authority='human_final')

    @signal_trust.post('/api/signal-trust/<int:signal_id>/revoke')
    def revoke(signal_id):
        u,error=founder_only()
        if error:return error
        with db() as c:
            row=c.execute("insert into oap_signal_trust(signal_id,trust_state,evidence_ref,certified_by,checked_at) values(%s,'revoked','',%s,%s) on conflict(signal_id) do update set trust_state='revoked',evidence_ref='',certified_by=excluded.certified_by,checked_at=excluded.checked_at returning signal_id,trust_state,evidence_ref,certified_by,checked_at",(signal_id,u,now())).fetchone()
        return jsonify(ok=True,trust=row,authority='human_final')

    app.register_blueprint(signal_trust)
