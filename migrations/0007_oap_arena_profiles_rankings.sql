-- OAP Arena durable player profiles and completed-match history.
-- Explicit migration only. No import-time or deployment-time schema mutation.

CREATE TABLE IF NOT EXISTS oap_arena_player_profiles (
    identity_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    matches_played INTEGER NOT NULL DEFAULT 0 CHECK (matches_played >= 0),
    wins INTEGER NOT NULL DEFAULT 0 CHECK (wins >= 0),
    losses INTEGER NOT NULL DEFAULT 0 CHECK (losses >= 0),
    draws INTEGER NOT NULL DEFAULT 0 CHECK (draws >= 0),
    points INTEGER NOT NULL DEFAULT 0 CHECK (points >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (wins + losses + draws = matches_played)
);

CREATE TABLE IF NOT EXISTS oap_arena_matches (
    match_id UUID PRIMARY KEY,
    player_a_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    player_b_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    player_a_score SMALLINT NOT NULL CHECK (player_a_score BETWEEN 0 AND 7),
    player_b_score SMALLINT NOT NULL CHECK (player_b_score BETWEEN 0 AND 7),
    receipt_hash TEXT NOT NULL UNIQUE CHECK (char_length(receipt_hash) = 64),
    status TEXT NOT NULL CHECK (status IN ('COMPLETED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (player_a_id <> player_b_id)
);

CREATE INDEX IF NOT EXISTS ix_arena_profiles_ranking
    ON oap_arena_player_profiles(points DESC,wins DESC,matches_played ASC,identity_id);

CREATE INDEX IF NOT EXISTS ix_arena_matches_player_a_created
    ON oap_arena_matches(player_a_id,created_at DESC);

CREATE INDEX IF NOT EXISTS ix_arena_matches_player_b_created
    ON oap_arena_matches(player_b_id,created_at DESC);
