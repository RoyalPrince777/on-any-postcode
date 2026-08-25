from flask import Blueprint, jsonify, request
import os, time

background_258 = Blueprint('background_258', __name__)

SAFE_JOB_TYPES = {
    'health_probe','readiness_refresh','provider_sync','education_refresh',
    'transport_refresh','weather_refresh','moderation_review','fraud_risk_review',
    'notification_prepare','intelligence_refresh','hrm_audit','data_quality_check'
}
SENSITIVE_JOB_TYPES = {
    'transfer_money','open_bank_account','issue_card','lend_money','publish_private_data',
    'real_world_action','delete_identity','change_founder_authority'
}


def register_background_258(app, db, uid):
    def now(): return int(time.time())

    with db() as c:
        c.execute("create table if not exists oap_258_jobs(id bigserial primary key,job_type text not null,payload text,status text not null default 'queued',requires_human boolean not null default false,attempts integer not null default 0,max_attempts integer not null default 3,created_by bigint,created_at bigint not null,updated_at bigint not null,last_error text)")
        c.execute("create table if not exists oap_258_worker_state(worker_name text primary key,status text not null,last_heartbeat bigint,protocol text not null,updated_at bigint not null)")
        c.execute("insert into oap_258_worker_state(worker_name,status,last_heartbeat,protocol,updated_at) values('oap-258-worker','configured',null,'25:8',%s) on conflict(worker_name) do nothing",(now(),))

    @background_258.get('/api/258')
    def protocol():
        return jsonify(
            name='25:8 Protocol',
            role='future_oriented_continuous_operations_protocol',
            runtime='24/7_background_worker',
            principles=['always_observing_not_always_executing','checkpoint_before_change','audit_every_material_action','adaptive_coherent','fail_closed_on_sensitive_actions','human_final_authority'],
            safe_job_types=sorted(SAFE_JOB_TYPES),
            sensitive_job_types=sorted(SENSITIVE_JOB_TYPES),
            autonomous_real_world_execution=False,
            authority='human_final'
        )

    @background_258.get('/api/258/health')
    def health():
        with db() as c:
            row=c.execute("select worker_name,status,last_heartbeat,protocol,updated_at from oap_258_worker_state where worker_name='oap-258-worker'").fetchone()
        heartbeat=row.get('last_heartbeat') if isinstance(row,dict) else (row[2] if row else None)
        age=(now()-heartbeat) if heartbeat else None
        live=bool(heartbeat and age <= 180)
        return jsonify(ok=True,service='oap-258-protocol',worker_live=live,heartbeat_age_seconds=age,state=row,authority='human_final')

    @background_258.post('/api/258/jobs')
    def enqueue():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        d=request.get_json(silent=True) or {}
        job_type=str(d.get('job_type','')).strip().lower()[:80]
        if not job_type:return jsonify(error='job_type_required'),400
        if job_type in SENSITIVE_JOB_TYPES:
            return jsonify(ok=False,status='blocked_human_approval_required',job_type=job_type,queued=False,authority='human_final'),403
        if job_type not in SAFE_JOB_TYPES:
            return jsonify(error='unsupported_job_type',allowed=sorted(SAFE_JOB_TYPES)),400
        payload=str(d.get('payload',''))[:4000]
        with db() as c:
            row=c.execute("insert into oap_258_jobs(job_type,payload,status,requires_human,attempts,max_attempts,created_by,created_at,updated_at) values(%s,%s,'queued',false,0,3,%s,%s,%s) returning id",(job_type,payload,u,now(),now())).fetchone()
        jid=row.get('id') if isinstance(row,dict) else row[0]
        return jsonify(ok=True,queued=True,job_id=jid,job_type=job_type,protocol='25:8'),202

    @background_258.get('/api/258/jobs')
    def jobs():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            rows=c.execute("select id,job_type,status,requires_human,attempts,max_attempts,created_at,updated_at,last_error from oap_258_jobs order by id desc limit 100").fetchall()
        return jsonify(jobs=rows,protocol='25:8')

    app.register_blueprint(background_258)
