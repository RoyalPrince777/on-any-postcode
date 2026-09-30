-- Property advertising authority in the EXISTING OAP PostgreSQL database.
-- Explicit migration only; authoring this file neither applies it nor publishes listings.
-- Rows require independently reviewed documentary authority, not publisher self-attestation.
CREATE TABLE IF NOT EXISTS oap_property_advertising_authority (
    evidence_id UUID PRIMARY KEY,
    publisher_id UUID NOT NULL REFERENCES oap_identities(identity_id),
    advertiser_id UUID NOT NULL REFERENCES oap_identities(identity_id),
    property_ref TEXT NOT NULL CHECK (length(trim(property_ref)) BETWEEN 1 AND 160),
    country TEXT NOT NULL CHECK (length(trim(country)) BETWEEN 1 AND 120),
    grantor_reference TEXT NOT NULL CHECK (length(trim(grantor_reference)) BETWEEN 1 AND 240),
    evidence_sha256 TEXT NOT NULL CHECK (evidence_sha256 ~ '^[0-9a-f]{64}$'),
    activity TEXT NOT NULL CHECK (activity = 'ADVERTISE'),
    reviewed_by UUID NOT NULL REFERENCES oap_identities(identity_id),
    reviewed_at TIMESTAMPTZ NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'REVIEW_REQUIRED'
        CHECK (status IN ('REVIEW_REQUIRED','ACTIVE','REVOKED')),
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (publisher_id <> reviewed_by),
    CHECK (valid_from < valid_until),
    CHECK ((status='REVOKED') = (revoked_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS ix_property_authority_publisher_property
    ON oap_property_advertising_authority
       (publisher_id, advertiser_id, property_ref, country, status);
-- No grant-issuing endpoint or automatic ACTIVE transition is installed here.
