ALTER TABLE link_voice_notes
ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'voice'
CHECK (kind IN ('voice','ptt'));
