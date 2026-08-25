from flask import Blueprint, jsonify, request
import os, time

obs = Blueprint('oap_observability', __name__)


def register_observability(app, db, uid):
    def now(): return int(time.time())
    with db() as c:
        c.execute("create table if not exists oap_observability_events(id bigserial primary key,kind text not null,component text not null,status text not null,detail text not null default '',created_at bigint not null)")

    @obs.get('/api/observability/health')
    def health():
        external=bool(os.environ.get('OAP_OBSERVABILITY_PROVIDER','').strip())
        return jsonify(ok=True,service='oap-observability',internal_metrics=True,external_provider_configured=external,privacy_default=True,secrets_logged=False,authority='human_final')

    @obs.route('/api/observability/events',methods=['GET','POST'])
    def events():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        if str(u)!=os.environ.get('OAP_FOUNDER_USER_ID',''):
            return jsonify(error='founder_only'),403
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}
                kind=str(d.get('kind','health'))[:60]; component=str(d.get('component','core'))[:80]; status=str(d.get('status','info'))[:40]; detail=str(d.get('detail',''))[:500]
                c.execute('insert into oap_observability_events(kind,component,status,detail,created_at) values(%s,%s,%s,%s,%s)',(kind,component,status,detail,now()))
            rows=c.execute('select id,kind,component,status,detail,created_at from oap_observability_events order by id desc limit 200').fetchall()
        return jsonify(events=rows,founder_only=True)

    app.register_blueprint(obs)
