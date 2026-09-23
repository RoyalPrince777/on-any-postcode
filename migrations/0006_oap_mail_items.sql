-- Explicit migration only. No import-time or deployment-time schema mutation.
-- Distinct from existing Link Up messages. No transport and no implicit delivery.
CREATE TABLE IF NOT EXISTS oap_mail_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    folder TEXT NOT NULL CHECK (folder IN ('inbox','sent','draft','review')),
    subject TEXT NOT NULL DEFAULT '' CHECK (char_length(subject) <= 200),
    body TEXT NOT NULL DEFAULT '' CHECK (char_length(body) <= 20000),
    correspondent TEXT NOT NULL DEFAULT '' CHECK (char_length(correspondent) <= 320),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_oap_mail_owner_folder_created
    ON oap_mail_items(owner_id,folder,created_at DESC);
