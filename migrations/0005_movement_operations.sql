INSERT INTO oap_roles(role_id,name,authority_level) VALUES
        ('MOVEMENT_DRIVER','Certified Movement Driver',5),
        ('MOVEMENT_RIDER','Certified Movement Rider',5),
        ('MOVEMENT_COURIER','Certified Movement Courier',5),
        ('MOVEMENT_MERCHANT','Certified Movement Merchant',5)
        ON CONFLICT (role_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS oap_movement_bookings (
        booking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        member_identity_id UUID NOT NULL,
        service_type TEXT NOT NULL
            CHECK (service_type IN ('ride','ebike','delivery')),
        pickup JSONB NOT NULL,
        destination JSONB,
        scheduled_for TIMESTAMPTZ,
        state TEXT NOT NULL DEFAULT 'REQUESTED'
            CHECK (state IN ('DRAFT','REQUESTED','MATCH_PROPOSED','ACCEPTED',
                             'IN_PROGRESS','COMPLETED','CANCELLED')),
        route_snapshot JSONB,
        idempotency_key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE INDEX IF NOT EXISTS ix_movement_booking_member_created
        ON oap_movement_bookings(member_identity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_movement_booking_state_scheduled
        ON oap_movement_bookings(state, scheduled_for);

CREATE TABLE IF NOT EXISTS oap_movement_availability (
        identity_id UUID NOT NULL,
        role_type TEXT NOT NULL
            CHECK (role_type IN ('driver','rider','courier')),
        availability_state TEXT NOT NULL
            CHECK (availability_state IN ('ONLINE','BUSY','OFFLINE')),
        zone TEXT NOT NULL DEFAULT '',
        available_until TIMESTAMPTZ,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (identity_id, role_type));

CREATE INDEX IF NOT EXISTS ix_movement_availability_match
        ON oap_movement_availability(
            role_type, availability_state, zone, updated_at DESC);

CREATE TABLE IF NOT EXISTS oap_movement_match_proposals (
        proposal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        worker_identity_id UUID NOT NULL,
        worker_role TEXT NOT NULL
            CHECK (worker_role IN ('driver','rider','courier')),
        state TEXT NOT NULL DEFAULT 'PROPOSED'
            CHECK (state IN ('PROPOSED','ACCEPTED','DECLINED','EXPIRED')),
        score DOUBLE PRECISION NOT NULL CHECK (score >= 0 AND score <= 1),
        reason TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(booking_id, worker_identity_id, worker_role));

CREATE UNIQUE INDEX IF NOT EXISTS ux_movement_one_accepted_match
        ON oap_movement_match_proposals(booking_id)
        WHERE state='ACCEPTED';

CREATE TABLE IF NOT EXISTS oap_movement_tracking_consents (
        booking_id UUID NOT NULL
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        identity_id UUID NOT NULL,
        state TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (state IN ('ACTIVE','REVOKED','EXPIRED')),
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (booking_id, identity_id));

CREATE TABLE IF NOT EXISTS oap_movement_tracking_points (
        point_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        identity_id UUID NOT NULL,
        latitude DOUBLE PRECISION NOT NULL
            CHECK (latitude >= -90 AND latitude <= 90),
        longitude DOUBLE PRECISION NOT NULL
            CHECK (longitude >= -180 AND longitude <= 180),
        recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL);

CREATE INDEX IF NOT EXISTS ix_movement_tracking_booking_recorded
        ON oap_movement_tracking_points(booking_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS oap_movement_esim_requests (
        request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID
            REFERENCES oap_movement_bookings(booking_id) ON DELETE SET NULL,
        identity_id UUID NOT NULL,
        purpose TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (state IN ('PROVIDER_REQUIRED','REQUESTED','APPROVED',
                             'PROVISIONED','REJECTED','CANCELLED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE INDEX IF NOT EXISTS ix_movement_esim_identity_created
        ON oap_movement_esim_requests(identity_id, created_at DESC);

CREATE TABLE IF NOT EXISTS oap_movement_payment_intents (
        intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        member_identity_id UUID NOT NULL,
        amount_minor BIGINT NOT NULL CHECK (amount_minor >= 0),
        currency TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (state IN ('PROVIDER_REQUIRED','CREATED','AUTHORIZED',
                             'CAPTURED','CANCELLED','FAILED')),
        provider_reference TEXT,
        idempotency_key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE INDEX IF NOT EXISTS ix_movement_payment_booking_created
        ON oap_movement_payment_intents(booking_id, created_at DESC);

CREATE TABLE IF NOT EXISTS oap_movement_trip_channels (
        channel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL UNIQUE
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        state TEXT NOT NULL DEFAULT 'PENDING_LINK_UP'
            CHECK (state IN ('PENDING_LINK_UP','READY','CLOSED')),
        linkup_conversation_id UUID,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);

INSERT INTO oap_schema_migrations(version,checksum) VALUES ('0005_movement_operations','85fe8a2ec33543f87d2534f2ef072203ebc1fa2aa032a9e4d5ef06ea177a8d47') ON CONFLICT (version) DO NOTHING;
