-- OAP civilization event outbox.
-- Authoritative organ state and its emitted fact are committed in one PostgreSQL transaction.
-- Consumers are separate; this table does not grant execution authority.

CREATE TABLE IF NOT EXISTS oap_civilization_events (
    event_id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    source_organ TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    causation_id TEXT NOT NULL,
    correlation_id UUID NOT NULL,
    payload JSONB NOT NULL,
    state TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (state IN ('PENDING','DISPATCHING','DISPATCHED','HELD')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dispatched_at TIMESTAMPTZ,
    UNIQUE (source_organ,event_type,entity_id)
);

CREATE INDEX IF NOT EXISTS ix_civilization_events_pending
    ON oap_civilization_events(state,created_at,event_id);
