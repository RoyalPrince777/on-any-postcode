"""Shared, metadata-only Vision quota on the existing authoritative OAP store.

Schema is applied explicitly from migrations/0014_studio_vision_quota.sql, never
at import or request time. Missing schema/database must block hosted processing.
"""
from __future__ import annotations

import uuid

from . import postgres_db


def reserve_shared_quota(identity_id: str) -> bool:
    """Atomically reserve one of seven rolling-minute attempts across workers.

    This independent transaction commits before decoding/admission. Failed,
    cancelled and busy attempts cannot refund CPU budget by rolling back work.
    At most seven timestamps per Founder are retained; never media or hashes.
    """
    identity = str(uuid.UUID(str(identity_id)))
    with postgres_db.connect() as connection:
        connection.execute("SET LOCAL statement_timeout = '1500ms'")
        row = connection.execute(
            """INSERT INTO oap_studio_vision_quota AS quota(identity_id, attempts)
               VALUES (%s, ARRAY[statement_timestamp()])
               ON CONFLICT (identity_id) DO UPDATE
               SET attempts = ARRAY(
                   SELECT stamp FROM unnest(quota.attempts) AS stamp
                   WHERE stamp > statement_timestamp() - INTERVAL '60 seconds'
               ) || ARRAY[statement_timestamp()]
               WHERE cardinality(ARRAY(
                   SELECT stamp FROM unnest(quota.attempts) AS stamp
                   WHERE stamp > statement_timestamp() - INTERVAL '60 seconds'
               )) < 7
               RETURNING identity_id""",
            (identity,),
        ).fetchone()
    return row is not None
