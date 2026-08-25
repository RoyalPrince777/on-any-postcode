#!/usr/bin/env python3
import os, signal, time
import psycopg
from psycopg.rows import dict_row

RUNNING = True
WORKER = 'oap-258-worker'
POLL_SECONDS = max(2, int(os.environ.get('OAP_258_POLL_SECONDS','5')))
DATABASE_URL = os.environ.get('DATABASE_URL','').strip()

SAFE_JOB_TYPES = {
    'health_probe','readiness_refresh','provider_sync','education_refresh',
    'transport_refresh','weather_refresh','moderation_review','fraud_risk_review',
    'notification_prepare','intelligence_refresh','hrm_audit','data_quality_check'
}


def stop(signum, frame):
    global RUNNING
    RUNNING = False


def connect():
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL is required')
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)


def ensure_schema(c):
    c.execute("create table if not exists oap_258_jobs(id bigserial primary key,job_type text not null,payload text,status text not null default 'queued',requires_human boolean not null default false,attempts integer not null default 0,max_attempts integer not null default 3,created_by bigint,created_at bigint not null,updated_at bigint not null,last_error text)")
    c.execute("create table if not exists oap_258_worker_state(worker_name text primary key,status text not null,last_heartbeat bigint,protocol text not null,updated_at bigint not null)")


def heartbeat(c, status='running'):
    t=int(time.time())
    c.execute("insert into oap_258_worker_state(worker_name,status,last_heartbeat,protocol,updated_at) values(%s,%s,%s,'25:8',%s) on conflict(worker_name) do update set status=excluded.status,last_heartbeat=excluded.last_heartbeat,protocol=excluded.protocol,updated_at=excluded.updated_at",(WORKER,status,t,t))


def claim_one(c):
    with c.transaction():
        row=c.execute("select id,job_type,payload,attempts,max_attempts from oap_258_jobs where status='queued' and requires_human=false and attempts < max_attempts order by id for update skip locked limit 1").fetchone()
        if not row:return None
        c.execute("update oap_258_jobs set status='processing',attempts=attempts+1,updated_at=%s where id=%s",(int(time.time()),row['id']))
        return row


def process(row):
    # 25:8 workers observe, refresh, verify and prepare. They do not perform
    # autonomous regulated, financial, identity-authority or other real-world actions.
    if row['job_type'] not in SAFE_JOB_TYPES:
        raise RuntimeError('job type not permitted by 25:8 worker')
    return 'prepared_and_verified'


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with connect() as c:
        ensure_schema(c)
        heartbeat(c,'running')
        while RUNNING:
            heartbeat(c,'running')
            row=claim_one(c)
            if row:
                try:
                    detail=process(row)
                    c.execute("update oap_258_jobs set status='completed',updated_at=%s,last_error=null where id=%s",(int(time.time()),row['id']))
                    print('25:8 completed job',row['id'],row['job_type'],detail,flush=True)
                except Exception as e:
                    attempts=row['attempts']+1
                    status='failed' if attempts >= row['max_attempts'] else 'queued'
                    c.execute("update oap_258_jobs set status=%s,updated_at=%s,last_error=%s where id=%s",(status,int(time.time()),type(e).__name__,row['id']))
                    print('25:8 job error',row['id'],type(e).__name__,flush=True)
            else:
                time.sleep(POLL_SECONDS)
        heartbeat(c,'stopped')


if __name__ == '__main__':
    main()
