"""First-party OAP Arena agent registry and bounded opponent logic."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

AGENTS: dict[str, dict[str, Any]] = {
    "fox": {
        "name": "Fox",
        "role": "Cheeky traps, tactical blocks and counterplay",
        "overall_stars": 7,
        "fits": {"iq": 6, "route-empire": 6, "connect4": 7, "ludo": 6, "chess": 6, "dot": 7},
    },
    "tiger": {
        "name": "Shere Khan",
        "role": "Aggressive centre pressure and tactical forks",
        "overall_stars": 7,
        "fits": {"iq": 5, "route-empire": 6, "connect4": 7, "ludo": 7, "chess": 5, "dot": 6},
    },
    "neo": {
        "name": "Neo",
        "role": "Predictive combination strategy",
        "overall_stars": 7,
        "fits": {"iq": 7, "route-empire": 6, "connect4": 7, "ludo": 5, "chess": 7, "dot": 6},
    },
    "octopus": {
        "name": "Octopus",
        "role": "Adaptive threats and flexible counterplay",
        "overall_stars": 7,
        "fits": {"iq": 7, "route-empire": 6, "connect4": 7, "ludo": 6, "chess": 6, "dot": 6},
    },
    "queen-bee": {
        "name": "Queen Bee",
        "role": "Pattern coordination and multi-threat attacks",
        "overall_stars": 7,
        "fits": {"iq": 6, "route-empire": 6, "connect4": 7, "ludo": 7, "chess": 5, "dot": 6},
    },
    "panther": {
        "name": "Bagheera",
        "animal": "Panther",
        "role": "Adaptive opponent",
        "overall_stars": 7,
        "fits": {"iq": 6, "route-empire": 7, "connect4": 7, "ludo": 6, "chess": 6, "dot": 7},
    },
    "owl": {
        "name": "Owl",
        "role": "Wisdom and deep reasoning",
        "overall_stars": 7,
        "fits": {"iq": 7, "route-empire": 6, "connect4": 6, "ludo": 5, "chess": 7, "dot": 6},
    },
    "eagle": {
        "name": "Eagle",
        "role": "Long-range vision",
        "overall_stars": 6,
        "fits": {"iq": 5, "route-empire": 7, "connect4": 5, "ludo": 5, "chess": 6, "dot": 5},
    },
    "falcon": {
        "name": "Falcon",
        "role": "Fast tactical decisions",
        "overall_stars": 6,
        "fits": {"iq": 5, "route-empire": 5, "connect4": 7, "ludo": 6, "chess": 6, "dot": 7},
    },
    "elephant": {
        "name": "Colonel Hathi",
        "animal": "Elephant",
        "family": ["Colonel Hathi", "Hathi Jr"],
        "role": "Control, memory and pattern continuity",
        "overall_stars": 6,
        "fits": {"iq": 7, "route-empire": 6, "connect4": 5, "ludo": 5, "chess": 6, "dot": 5},
    },
    "bee": {
        "name": "Bee",
        "role": "Coordination and team play",
        "overall_stars": 5,
        "fits": {"iq": 5, "route-empire": 5, "connect4": 5, "ludo": 7, "chess": 4, "dot": 6},
    },
    "gorilla": {
        "name": "Gorilla",
        "role": "Defensive play and protection",
        "overall_stars": 5,
        "fits": {"iq": 4, "route-empire": 6, "connect4": 6, "ludo": 5, "chess": 6, "dot": 5},
    },
}
DEFAULT_BY_GAME = {
    "iq": "owl",
    "route-empire": "eagle",
    "connect4": "panther",
    "ludo": "bee",
    "chess": "owl",
    "dot": "falcon",
}


def catalogue() -> dict[str, Any]:
    return {
        "agents": deepcopy(AGENTS),
        "defaults": dict(DEFAULT_BY_GAME),
        "difficulty": ["easy", "standard", "strong", "a7"],
        "fair_play": {
            "same_visible_state_as_human": True,
            "hidden_information_access": False,
            "payments": False,
            "human_authority_final": True,
        },
    }


def choose_agent(game_key: object, agent_key: object | None = None) -> dict[str, Any]:
    game = str(game_key or "").strip().lower()
    if game not in DEFAULT_BY_GAME:
        raise ValueError("arena_agent_game_invalid")
    key = str(agent_key or DEFAULT_BY_GAME[game]).strip().lower()
    if key not in AGENTS:
        raise ValueError("arena_agent_invalid")
    return {
        "key": key,
        **deepcopy(AGENTS[key]),
        "game_key": game,
        "fit_stars": int(AGENTS[key]["fits"][game]),
    }


def _windows(board: list[list[int]]) -> list[list[tuple[int, int]]]:
    rows, cols = 6, 7
    out: list[list[tuple[int, int]]] = []
    for r in range(rows):
        for c in range(cols - 3):
            out.append([(r, c + i) for i in range(4)])
    for r in range(rows - 3):
        for c in range(cols):
            out.append([(r + i, c) for i in range(4)])
    for r in range(rows - 3):
        for c in range(cols - 3):
            out.append([(r + i, c + i) for i in range(4)])
    for r in range(rows - 3):
        for c in range(3, cols):
            out.append([(r + i, c - i) for i in range(4)])
    return out


def _landing_row(board: list[list[int]], column: int) -> int | None:
    for row in range(5, -1, -1):
        if board[row][column] == 0:
            return row
    return None


def _would_win(board: list[list[int]], column: int, piece: int) -> bool:
    row = _landing_row(board, column)
    if row is None:
        return False
    test = [list(r) for r in board]
    test[row][column] = piece
    for window in _windows(test):
        if all(test[r][c] == piece for r, c in window):
            return True
    return False


def _board_score(board: list[list[int]], agent_piece: int, human_piece: int, agent_key: str) -> int:
    """Bounded visible-board heuristic, with agent-specific centre and threat weights."""
    score = 0
    attack = 10 if agent_key == "tiger" else 7
    defend = 10 if agent_key in {"fox", "panther"} else 7
    for window in _windows(board):
        cells = [board[r][c] for r, c in window]
        ours, theirs = cells.count(agent_piece), cells.count(human_piece)
        if ours and theirs:
            continue
        if ours:
            score += (0, 2, attack, attack * 10, 100_000)[ours]
        if theirs:
            score -= (0, 2, defend, defend * 12, 100_000)[theirs]
    centre = [board[r][3] for r in range(6)]
    score += (8 if agent_key == "tiger" else 4) * (
        centre.count(agent_piece) - centre.count(human_piece)
    )
    return score


def connect4_column(
    board: object,
    *,
    agent_piece: int = 2,
    human_piece: int = 1,
    difficulty: object = "standard",
    agent_key: str = "panther",
) -> int:
    if not isinstance(board, list) or len(board) != 6 or any(
        not isinstance(r, list) or len(r) != 7 or any(x not in {0, 1, 2} for x in r)
        for r in board
    ):
        raise ValueError("arena_agent_connect4_board_invalid")
    level = str(difficulty or "standard").strip().lower()
    if level not in {"easy", "standard", "strong", "a7"}:
        raise ValueError("arena_agent_difficulty_invalid")
    if agent_key not in AGENTS:
        raise ValueError("arena_agent_invalid")
    order = [3, 2, 4, 1, 5, 0, 6]
    legal = [c for c in order if _landing_row(board, c) is not None]
    if not legal:
        raise ValueError("arena_agent_no_legal_move")

    # Winning is always legal and must never be skipped.
    for column in legal:
        if _would_win(board, column, agent_piece):
            return column
    threats = [c for c in legal if _would_win(board, c, human_piece)]
    if threats:
        return threats[0]

    if level == "easy":
        # A beginner still makes legal moves but sees no further than this turn.
        beginner_order = [0, 6, 1, 5, 2, 4, 3] if agent_key == "fox" else order
        return next(c for c in beginner_order if c in legal)

    depths = {"standard": 2, "strong": 4, "a7": 5}
    depth = depths[level]
    nodes = [0]
    budget = 18_000

    def drop_piece(current: list[list[int]], col: int, piece: int) -> list[list[int]]:
        nxt = [row[:] for row in current]
        row = _landing_row(nxt, col)
        if row is not None:
            nxt[row][col] = piece
        return nxt

    def evaluate(current: list[list[int]], remaining: int, ai_turn: bool, alpha: int, beta: int) -> int:
        nodes[0] += 1
        if nodes[0] >= budget or remaining <= 0:
            return _board_score(current, agent_piece, human_piece, agent_key)
        possible = [c for c in order if _landing_row(current, c) is not None]
        if not possible:
            return 0
        best = -1_000_000 if ai_turn else 1_000_000
        piece = agent_piece if ai_turn else human_piece
        for col in possible:
            nxt = drop_piece(current, col, piece)
            if _would_win(current, col, piece):
                value = (500_000 + remaining) if ai_turn else (-500_000 - remaining)
            else:
                value = evaluate(nxt, remaining - 1, not ai_turn, alpha, beta)
            if ai_turn:
                best = max(best, value)
                alpha = max(alpha, best)
            else:
                best = min(best, value)
                beta = min(beta, best)
            if alpha >= beta:
                break
        return best

    winner = legal[0]
    best_score = -1_000_000
    for col in legal:
        played = drop_piece(board, col, agent_piece)
        score = evaluate(played, depth - 1, False, -1_000_000, 1_000_000)
        if score > best_score:
            winner, best_score = col, score
    return winner
