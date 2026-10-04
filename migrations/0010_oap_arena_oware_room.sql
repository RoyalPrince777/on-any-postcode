ALTER TABLE oap_arena_rooms
    DROP CONSTRAINT IF EXISTS oap_arena_rooms_game_key_check;

ALTER TABLE oap_arena_rooms
    ADD CONSTRAINT oap_arena_rooms_game_key_check
    CHECK (game_key IN ('iq','route-empire','connect4','ludo','chess','dot','oware'));
