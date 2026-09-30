-- OAP Arena shared multiplayer rooms.
-- Explicit migration only. No import-time schema mutation.

CREATE TABLE IF NOT EXISTS oap_arena_rooms (
    room_id UUID PRIMARY KEY,
    room_code TEXT NOT NULL UNIQUE CHECK (room_code ~ '^[A-Z2-9]{6}$'),
    game_key TEXT NOT NULL CHECK (game_key IN ('iq','route-empire','connect4','ludo','chess','dot')),
    status TEXT NOT NULL CHECK (status IN ('WAITING','ACTIVE','COMPLETED','STOPPED')),
    capacity SMALLINT NOT NULL CHECK (capacity BETWEEN 2 AND 4),
    revision BIGINT NOT NULL DEFAULT 0 CHECK (revision >= 0),
    game_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS oap_arena_room_players (
    room_id UUID NOT NULL REFERENCES oap_arena_rooms(room_id) ON DELETE CASCADE,
    player_id UUID NOT NULL,
    display_name TEXT NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 40),
    seat SMALLINT NOT NULL CHECK (seat BETWEEN 1 AND 4),
    reconnect_token_hash TEXT NOT NULL CHECK (char_length(reconnect_token_hash) = 64),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (room_id, player_id),
    UNIQUE (room_id, seat),
    UNIQUE (room_id, reconnect_token_hash)
);

CREATE INDEX IF NOT EXISTS ix_arena_rooms_code ON oap_arena_rooms(room_code);
CREATE INDEX IF NOT EXISTS ix_arena_room_players_room ON oap_arena_room_players(room_id,seat);

CREATE TABLE IF NOT EXISTS oap_arena_room_updates (
    room_id UUID NOT NULL REFERENCES oap_arena_rooms(room_id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    revision BIGINT NOT NULL CHECK (revision > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (room_id, request_id)
);

CREATE INDEX IF NOT EXISTS ix_arena_room_updates_room_revision
    ON oap_arena_room_updates(room_id,revision DESC);
