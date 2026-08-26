CREATE TABLE IF NOT EXISTS oap_movement_worker_applications (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id UUID NOT NULL REFERENCES oap_identities(identity_id) ON DELETE CASCADE,
    role_type TEXT NOT NULL CHECK (role_type IN ('driver','rider','courier')),
    vehicle_type TEXT NOT NULL
        CHECK (vehicle_type IN ('car','van','ebike','bicycle','moped','motorcycle','none')),
    service_zone TEXT NOT NULL DEFAULT '',
    declaration_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    state TEXT NOT NULL DEFAULT 'SUBMITTED'
        CHECK (state IN ('SUBMITTED','UNDER_REVIEW','NEEDS_INFO',
                         'INTERNAL_APPROVED','REJECTED','CANCELLED')),
    external_compliance_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
        CHECK (external_compliance_state IN
               ('PROVIDER_REQUIRED','PENDING','VERIFIED','FAILED','NOT_APPLICABLE')),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_movement_active_worker_application
    ON oap_movement_worker_applications(identity_id, role_type)
    WHERE state NOT IN ('REJECTED','CANCELLED');

CREATE INDEX IF NOT EXISTS ix_movement_worker_application_review
    ON oap_movement_worker_applications(state, submitted_at);

CREATE TABLE IF NOT EXISTS oap_movement_vehicles (
    vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL
        REFERENCES oap_movement_worker_applications(application_id) ON DELETE CASCADE,
    identity_id UUID NOT NULL REFERENCES oap_identities(identity_id) ON DELETE CASCADE,
    vehicle_type TEXT NOT NULL
        CHECK (vehicle_type IN ('car','van','ebike','bicycle','moped','motorcycle','none')),
    display_label TEXT NOT NULL DEFAULT '',
    registration_last4 TEXT NOT NULL DEFAULT ''
        CHECK (char_length(registration_last4) <= 4),
    electric BOOLEAN NOT NULL DEFAULT FALSE,
    compliance_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
        CHECK (compliance_state IN
               ('PROVIDER_REQUIRED','PENDING','VERIFIED','FAILED','NOT_APPLICABLE')),
    active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(application_id)
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
    reason TEXT NOT NULL,
    role_granted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (NOT role_granted OR decision='INTERNAL_APPROVED')
);

CREATE INDEX IF NOT EXISTS ix_movement_certification_review_application
    ON oap_movement_certification_reviews(application_id, created_at DESC);

INSERT INTO oap_schema_migrations(version,checksum)
VALUES ('0006_movement_certification','b362e77e85358ce48a1ced0b8e55d62c7cc4367267ef54ac8749da80343e972f')
ON CONFLICT (version) DO NOTHING;
