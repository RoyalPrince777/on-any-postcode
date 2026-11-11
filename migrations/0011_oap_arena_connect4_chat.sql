-- Explicit, opt-in migration. Never run automatically on import.
CREATE TABLE IF NOT EXISTS oap_arena_connect4_chat (
  message_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  room_id UUID NOT NULL REFERENCES oap_arena_rooms(room_id) ON DELETE CASCADE,
  seat SMALLINT NOT NULL CHECK (seat IN (1,2)),
  request_id TEXT NOT NULL CHECK (char_length(request_id) BETWEEN 8 AND 127),
  message TEXT NOT NULL CHECK (char_length(message) BETWEEN 1 AND 280),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (room_id,seat,request_id)
);
CREATE INDEX IF NOT EXISTS ix_arena_connect4_chat_room_order
  ON oap_arena_connect4_chat(room_id,message_id DESC);
