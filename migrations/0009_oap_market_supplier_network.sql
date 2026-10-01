-- OAP Market Supplier Network
-- Durable product-to-manufacturer mappings. External execution remains disabled.

CREATE TABLE IF NOT EXISTS oap_market_supplier_bindings (
    binding_id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    supplier_slug TEXT NOT NULL,
    supplier_label TEXT NOT NULL,
    supplier_product_ref TEXT NOT NULL,
    supplier_variant_ref TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL CHECK (state IN ('DRAFT','READY','STOPPED','RECOVERY_REQUIRED')),
    stop_reason TEXT NOT NULL DEFAULT '',
    evidence_reference TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id)
);

CREATE INDEX IF NOT EXISTS idx_market_supplier_bindings_seller
    ON oap_market_supplier_bindings(seller_identity_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_market_supplier_bindings_state
    ON oap_market_supplier_bindings(state);
