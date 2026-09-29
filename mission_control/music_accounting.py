"""OAP Music accounting evidence layer.

Records creator allocation and refund/reconciliation state. It never captures
payment, transfers money, or executes SIKA.
"""
from __future__ import annotations

MUSIC_ACCOUNTING_MIGRATION_VERSION = "0018_oap_music_accounting"

SCHEMA_STATEMENTS = (
    """ALTER TABLE oap_music_purchase_intents
       ADD COLUMN IF NOT EXISTS refund_reference TEXT,
       ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ""",
    """CREATE TABLE IF NOT EXISTS oap_music_creator_allocations (
        allocation_id UUID PRIMARY KEY,
        purchase_id UUID NOT NULL UNIQUE REFERENCES oap_music_purchase_intents(purchase_id)
            ON DELETE RESTRICT,
        beneficiary_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        gross_amount_minor BIGINT NOT NULL CHECK (gross_amount_minor >= 0),
        currency TEXT NOT NULL DEFAULT 'GBP',
        state TEXT NOT NULL DEFAULT 'PENDING_RECONCILIATION'
            CHECK (state IN ('PENDING_RECONCILIATION','RECONCILED','REVERSED')),
        settlement_reference TEXT NOT NULL,
        reconciliation_reference TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        reconciled_at TIMESTAMPTZ,
        reversed_at TIMESTAMPTZ
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_creator_allocation_beneficiary
       ON oap_music_creator_allocations(beneficiary_identity_id,created_at DESC)""",
)
