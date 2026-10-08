CREATE TABLE IF NOT EXISTS oap_founder_private_pod_orders (
    private_order_id UUID PRIMARY KEY,
    owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    provider_id TEXT NOT NULL CHECK (provider_id IN ('prodigi','printful','tapstitch')),
    canonical_order JSONB NOT NULL,
    provider_payload JSONB NOT NULL,
    provider_reference TEXT NOT NULL DEFAULT '',
    provider_state TEXT NOT NULL DEFAULT 'PLANNED',
    canonical_state TEXT NOT NULL DEFAULT 'DRAFT',
    idempotency_key TEXT NOT NULL,
    recovery_required BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_identity_id,idempotency_key)
);

CREATE INDEX IF NOT EXISTS ix_founder_private_pod_orders_owner
    ON oap_founder_private_pod_orders(owner_identity_id,created_at DESC);

CREATE INDEX IF NOT EXISTS ix_founder_private_pod_orders_provider_reference
    ON oap_founder_private_pod_orders(provider_id,provider_reference)
    WHERE provider_reference <> '';
