from __future__ import annotations


def test_three_new_arena_games_are_routed_and_local_only(client):
    cases = {
        "/arena/snakes-ladders": ("Snakes &amp; Ladders", 'data-oap-newgame="snakes"'),
        "/arena/scramble": ("OAP Word Scramble", 'data-oap-newgame="scramble"'),
        "/arena/postcode-empire": ("Postcode Empire", 'data-oap-newgame="empire"'),
    }
    hub = client.get("/arena").get_data(as_text=True)
    for path, (title, selector) in cases.items():
        response = client.get(path)
        assert response.status_code == 200, path
        page = response.get_data(as_text=True)
        assert selector in page, path
        assert title in page or title.replace("&amp;", "&") in page, path
        assert "/static/arena_new_games.js" in page
        assert "No betting, cash prizes, payments, ranked XP" in page
        assert path in hub
        assert response.headers["Cache-Control"] == "no-store"


def test_new_arena_games_have_real_free_play_rules_and_no_purchase_network(client):
    response = client.get("/static/arena_new_games.js")
    assert response.status_code == 200
    js = response.get_data(as_text=True)
    assert "function newSnakes()" in js
    assert "snake.positions[player]+dice" in js
    assert "function newScramble()" in js
    assert "guess===w.answer" in js
    assert "function newEmpire()" in js
    assert "empire.round>=12" in js
    assert "setInterval" not in js
    assert 'fetch(' not in js
    assert "localStorage" not in js
    assert "payment" not in js.lower()


def test_unknown_new_arena_game_route_is_not_mistaken_for_a_game(client):
    assert client.get("/arena/not-a-real-game").status_code == 404
