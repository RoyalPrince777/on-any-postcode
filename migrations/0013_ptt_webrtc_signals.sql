-- Transient WebRTC SDP/ICE negotiation; no audio is stored.
CREATE TABLE IF NOT EXISTS oap_ptt_signals (
 signal_id UUID PRIMARY KEY,
 sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 kind TEXT NOT NULL CHECK (kind IN ('offer','answer','candidate','hangup')),
 payload JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '2 minutes')
);
CREATE INDEX IF NOT EXISTS ix_oap_ptt_signals_recipient ON oap_ptt_signals(recipient_id,created_at);
