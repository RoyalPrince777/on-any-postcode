"""Opt-in schema definition for Global Movement associations.

No migration executes on import. Production rollout requires governed approval.
"""
from __future__ import annotations

import hashlib

MIGRATION_VERSION = "0001_oap_global_journey_associations"
STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_global_journey_associations (
        journey_id UUID PRIMARY KEY,
        booking_id UUID NOT NULL UNIQUE REFERENCES oap_movement_bookings(booking_id) ON DELETE RESTRICT,
        intent_id TEXT UNIQUE,
        version INTEGER NOT NULL CHECK (version = 1),
        owner_identity_id UUID NOT NULL REFERENCES oap_identities(identity_id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (intent_id IS NULL OR intent_id ~ '^oap-book-[0-9a-f]{16}$')
    )""",
)
CHECKSUM = hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()
