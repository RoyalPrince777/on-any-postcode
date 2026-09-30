from mission_control import arena_agents


def test_catalogue_has_locked_first_party_agents_and_fair_play():
    data = arena_agents.catalogue()
    assert set(data["agents"]) == {"panther", "owl", "eagle", "falcon", "elephant", "bee", "gorilla"}
    assert data["defaults"]["connect4"] == "panther"
    assert data["agents"]["panther"]["name"] == "Bagheera"
    assert data["agents"]["panther"]["animal"] == "Panther"
    assert data["agents"]["elephant"]["name"] == "Colonel Hathi"
    assert data["agents"]["elephant"]["family"] == ["Colonel Hathi", "Hathi Jr"]
    assert "Control" in data["agents"]["elephant"]["role"]
    assert data["defaults"]["chess"] == "owl"
    assert data["fair_play"]["hidden_information_access"] is False
    assert data["fair_play"]["payments"] is False


def test_choose_agent_uses_game_default_and_fit():
    result = arena_agents.choose_agent("route-empire")
    assert result["key"] == "eagle"
    assert result["fit_stars"] == 7


def test_connect4_agent_wins_before_center_preference():
    board = [[0 for _ in range(7)] for _ in range(6)]
    board[5][0] = 2
    board[5][1] = 2
    board[5][2] = 2
    assert arena_agents.connect4_column(board, difficulty="strong") == 3


def test_connect4_agent_blocks_human_win():
    board = [[0 for _ in range(7)] for _ in range(6)]
    board[5][0] = 1
    board[5][1] = 1
    board[5][2] = 1
    assert arena_agents.connect4_column(board, difficulty="a7") == 3


def test_connect4_agent_easy_uses_bounded_legal_move():
    board = [[0 for _ in range(7)] for _ in range(6)]
    for row in range(6):
        board[row][0] = 1
    assert arena_agents.connect4_column(board, difficulty="easy") == 6
