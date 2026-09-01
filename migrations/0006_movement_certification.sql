CREATE TABLE IF NOT EXISTS oap_movement_worker_applications (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id UUID NOT NULL REFERENCES oap_identities(identity_id) ON DELETE CASCADE,
    role_type TEXT NOT NULL CHECK (role_type IN ('driver','rider','courier')),
    vehicle_type TEXT NOT NULL
        CHECK (vehicle_type IN ('car','van','ebike','bicycle','moped','motorcycle','none')),
    service_zone TEXT NOT NULL DEFAULT '',
    declaration_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    terms_version TEXT NOT NULL,
    terms_digest TEXT NOT NULL CHECK (char_length(terms_digest) = 64),
    applicant_response TEXT NOT NULL DEFAULT ''
        CHECK (char_length(applicant_response) <= 500),
    state TEXT NOT NULL DEFAULT 'SUBMITTED'
        CHECK (state IN ('SUBMITTED','UNDER_REVIEW','NEEDS_INFO',
                         'INTERNAL_APPROVED','REJECTED','CANCELLED')),
    external_compliance_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
        CHECK (external_compliance_state IN
               ('PROVIDER_REQUIRED','PENDING','VERIFIED','FAILED','NOT_APPLICABLE')),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    retention_expires_at TIMESTAMPTZ NOT NULL
        DEFAULT (CURRENT_TIMESTAMP + INTERVAL '90 days'),
    UNIQUE(application_id, identity_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_movement_active_worker_application
    ON oap_movement_worker_applications(identity_id, role_type)
    WHERE state NOT IN ('REJECTED','CANCELLED');

CREATE INDEX IF NOT EXISTS ix_movement_worker_application_review
    ON oap_movement_worker_applications(state, submitted_at);

CREATE TABLE IF NOT EXISTS oap_movement_vehicles (
    vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL,
    identity_id UUID NOT NULL REFERENCES oap_identities(identity_id) ON DELETE CASCADE,
    vehicle_type TEXT NOT NULL
        CHECK (vehicle_type IN ('car','van','ebike','bicycle','moped','motorcycle','none')),
    display_label TEXT NOT NULL DEFAULT '',
    registration_last4 TEXT NOT NULL DEFAULT ''
        CHECK (registration_last4 ~ '^[A-Z0-9]{0,4}$'),
    electric BOOLEAN NOT NULL DEFAULT FALSE,
    compliance_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
        CHECK (compliance_state IN
               ('PROVIDER_REQUIRED','PENDING','VERIFIED','FAILED','NOT_APPLICABLE')),
    active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(application_id),
    FOREIGN KEY (application_id, identity_id)
        REFERENCES oap_movement_worker_applications(application_id, identity_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_movement_vehicle_identity
    ON oap_movement_vehicles(identity_id, active, updated_at DESC);

CREATE TABLE IF NOT EXISTS oap_movement_certification_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL
        REFERENCES oap_movement_worker_applications(application_id) ON DELETE CASCADE,
    reviewer_identity_id UUID NOT NULL REFERENCES oap_identities(identity_id),
    decision TEXT NOT NULL
        CHECK (decision IN ('UNDER_REVIEW','NEEDS_INFO','INTERNAL_APPROVED','REJECTED')),
    reason TEXT NOT NULL CHECK (char_length(reason) BETWEEN 3 AND 500),
    applicant_message TEXT NOT NULL DEFAULT ''
        CHECK (char_length(applicant_message) <= 500),
    role_granted BOOLEAN NOT NULL DEFAULT FALSE CHECK (role_granted = FALSE),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (decision <> 'NEEDS_INFO' OR char_length(applicant_message) >= 3)
);

CREATE INDEX IF NOT EXISTS ix_movement_certification_review_application
    ON oap_movement_certification_reviews(application_id, created_at DESC);

INSERT INTO oap_schema_migrations(version,checksum)
VALUES ('0006_movement_certification','444ba01632473bc3d8fea794d2bd3cf799e327cbb2a32b73606e9729daa102c9')
ON CONFLICT (version) DO NOTHING;
