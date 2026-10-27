"""Real PostgreSQL evidence race acceptance. Requires a dedicated TEST database.

Run with OAP_ESIM_TEST_DATABASE_URL; never point this at production.
A unique test schema is created and dropped after execution.
"""
import concurrent.futures
import datetime
import os
import uuid

import pytest

from mission_control.esim_persistence import EsimRepository, SCHEMA_STATEMENTS


@pytest.mark.skipif(
    not os.getenv("OAP_ESIM_TEST_DATABASE_URL"),
    reason="Dedicated PostgreSQL acceptance database not configured",
)
def test_two_independent_postgres_workers_cannot_claim_one_receipt():
    import psycopg

    dsn = os.environ["OAP_ESIM_TEST_DATABASE_URL"]
    schema = "esim_accept_" + uuid.uuid4().hex
    now = datetime.datetime.now(datetime.UTC).isoformat()
    def connect():
        connection = psycopg.connect(dsn, connect_timeout=5)
        connection.execute("SET search_path TO " + schema)
        return connection

    with psycopg.connect(dsn, connect_timeout=5) as root:
        root.execute("CREATE SCHEMA " + schema)
        root.commit()
    try:
        with connect() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)
            conn.commit()

        def item(request_id):
            return dict(
                request_id=request_id, subject_id="acceptance-only",
                purpose="replay-integrity", state="available",
                approved_by="test-authority", provider_name="test-provider",
                provider_profile_id=request_id, last_error=None,
                created_at=now, updated_at=now,
            )

        request_ids = ["esim_accept_" + uuid.uuid4().hex for _ in range(2)]
        for request_id in request_ids:
            EsimRepository(connect).save_request(item(request_id))

        def compete(request_id):
            record = item(request_id)
            record["state"] = "registered"
            event = dict(
                request_id=request_id, event="registered", state="registered",
                recorded_at=now, evidence_id="one-shared-receipt",
            )
            try:
                EsimRepository(connect).save_with_event(record, event)
                return "claimed"
            except RuntimeError as exc:
                if str(exc) == "network_evidence_already_used":
                    return "rejected"
                raise

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(compete, request_ids))
        assert sorted(outcomes) == ["claimed", "rejected"]

        with connect() as conn:
            assert conn.execute(
                "SELECT count(*) FROM oap_esim_evidence_claims"
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT count(*) FROM oap_esim_events WHERE event='registered'"
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT count(*) FROM oap_esim_requests WHERE state='registered'"
            ).fetchone()[0] == 1
    finally:
        with psycopg.connect(dsn, connect_timeout=5) as root:
            root.execute("DROP SCHEMA IF EXISTS " + schema + " CASCADE")
            root.commit()
