from mission_control import arena_game_intelligence


def test_gaming_intelligence_registry_covers_all_arena_titles():
    validation = arena_game_intelligence.validate_registry()
    assert validation == {"passed": True, "errors": [], "games": 7}

    data = arena_game_intelligence.catalogue()
    assert set(data["games"]) == {
        "connect4", "dot", "ludo", "chess", "oware", "iq", "route-empire"
    }
    assert data["truth"]["agent_fit_is_not_agent_execution"] is True
    assert data["truth"]["training_is_advisory"] is True
    assert data["truth"]["payments"] is False


def test_capability_truth_does_not_fake_agent_or_ranked_support():
    data = arena_game_intelligence.catalogue()["games"]
    assert data["connect4"]["capabilities"]["agent_opponent"] is True
    for key in ("dot", "ludo", "chess", "oware", "iq", "route-empire"):
        assert data[key]["capabilities"]["agent_opponent"] is False
    assert all(not game["capabilities"]["ranked_results"] for game in data.values())
    assert all(not game["capabilities"]["tournaments"] for game in data.values())


def test_gaming_intelligence_summary_matches_real_capability_counts():
    assert arena_game_intelligence.summary() == {
        "games": 7,
        "local_play": 7,
        "online_rooms": 2,
        "agent_opponents": 1,
        "training": 7,
        "move_review": 7,
        "ranked_results": 0,
        "tournaments": 0,
    }


def test_gaming_intelligence_profile_fails_closed_for_unknown_game():
    profile = arena_game_intelligence.game_profile("chess")
    assert profile["key"] == "chess"
    assert profile["rules_status"] == "full_rules_local"

    try:
        arena_game_intelligence.game_profile("unknown")
    except ValueError as exc:
        assert str(exc) == "arena_game_intelligence_game_invalid"
    else:
        raise AssertionError("unknown game must fail closed")


def test_gaming_intelligence_http_and_arena_menu(client):
    catalog = client.get("/arena/intelligence")
    assert catalog.status_code == 200
    body = catalog.get_json()
    assert len(body["games"]) == 7
    assert body["games"]["connect4"]["capabilities"]["agent_opponent"] is True
    assert body["games"]["oware"]["capabilities"]["agent_opponent"] is False

    chess = client.get("/arena/intelligence/chess")
    assert chess.status_code == 200
    assert chess.get_json()["name"] == "Chess"

    unknown = client.get("/arena/intelligence/not-a-game")
    assert unknown.status_code == 400
    assert unknown.get_json()["error"]["code"] == "arena_game_intelligence_game_invalid"

    page = client.get("/arena").get_data(as_text=True)
    assert "🎮 Gaming Intelligence" in page
    assert "agent fit does not mean agent execution" in page
    assert "7 games" in page
