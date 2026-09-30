"""First-party OAP Arena agent registry and bounded opponent logic."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

AGENTS: dict[str, dict[str, Any]] = {
    "panther": {
        "name": "Panther",
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
        "name": "Elephant",
        "role": "Memory and pattern continuity",
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


def connect4_column(
    board: object,
    *,
    agent_piece: int = 2,
    human_piece: int = 1,
    difficulty: object = "standard",
) -> int:
    if not isinstance(board, list) or len(board) != 6 or any(not isinstance(r, list) or len(r) != 7 for r in board):
        raise ValueError("arena_agent_connect4_board_invalid")
    level = str(difficulty or "standard").strip().lower()
    if level not in {"easy", "standard", "strong", "a7"}:
        raise ValueError("arena_agent_difficulty_invalid")
    legal = [c for c in range(7) if _landing_row(board, c) is not None]
    if not legal:
        raise ValueError("arena_agent_no_legal_move")

    if level in {"strong", "a7"}:
        for c in legal:
            if _would_win(board, c, agent_piece):
                return c
        for c in legal:
            if _would_win(board, c, human_piece):
                return c

    preference = [3, 2, 4, 1, 5, 0, 6]
    if level == "easy":
        preference = [0, 6, 1, 5, 2, 4, 3]
    return next(c for c in preference if c in legal)
