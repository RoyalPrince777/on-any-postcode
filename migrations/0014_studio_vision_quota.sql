-- Explicit opt-in migration. No application-startup or request-time DDL.
-- Rolling quota metadata only: no image, image hash, identity inference or boxes.
CREATE TABLE IF NOT EXISTS oap_studio_vision_quota (
 identity_id UUID PRIMARY KEY,
 attempts TIMESTAMPTZ[] NOT NULL,
 CHECK (cardinality(attempts) BETWEEN 1 AND 7)
);
