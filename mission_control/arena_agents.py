"""First-party OAP Arena agent registry and bounded opponent logic."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any

from . import chess

AGENTS: dict[str, dict[str, Any]] = {
    "panther": {
        "name": "Bagheera",
        "animal": "Panther",
        "role": "Adaptive opponent",
        "overall_stars": 7,
        "fits": {"iq": 6, "route-empire": 7, "connect4": 7, "ludo": 6, "chess": 6, "dot": 7, "oware": 6},
    },
    "owl": {
        "name": "Owl",
        "role": "Wisdom and deep reasoning",
        "overall_stars": 7,
        "fits": {"iq": 7, "route-empire": 6, "connect4": 6, "ludo": 5, "chess": 7, "dot": 6, "oware": 6},
    },
    "eagle": {
        "name": "Eagle",
        "role": "Long-range vision",
        "overall_stars": 6,
        "fits": {"iq": 5, "route-empire": 7, "connect4": 5, "ludo": 5, "chess": 6, "dot": 5, "oware": 6},
    },
    "falcon": {
        "name": "Falcon",
        "role": "Fast tactical decisions",
        "overall_stars": 6,
        "fits": {"iq": 5, "route-empire": 5, "connect4": 7, "ludo": 6, "chess": 6, "dot": 7, "oware": 6},
    },
    "elephant": {
        "name": "Colonel Hathi",
        "animal": "Elephant",
        "family": ["Colonel Hathi", "Hathi Jr"],
        "role": "Control, memory and pattern continuity",
        "overall_stars": 6,
        "fits": {"iq": 7, "route-empire": 6, "connect4": 5, "ludo": 5, "chess": 6, "dot": 5, "oware": 6},
    },
    "bee": {
        "name": "Bee",
        "role": "Coordination and team play",
        "overall_stars": 5,
        "fits": {"iq": 5, "route-empire": 5, "connect4": 5, "ludo": 7, "chess": 4, "dot": 6, "oware": 5},
    },
    "gorilla": {
        "name": "Gorilla",
        "role": "Defensive play and protection",
        "overall_stars": 5,
        "fits": {"iq": 4, "route-empire": 6, "connect4": 6, "ludo": 5, "chess": 6, "dot": 5, "oware": 7},
    },
}
DEFAULT_BY_GAME = {
    "iq": "owl",
    "route-empire": "eagle",
    "connect4": "panther",
    "ludo": "bee",
    "chess": "owl",
    "dot": "falcon",
    "oware": "gorilla",
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



def _difficulty(value: object) -> str:
    level = str(value or "standard").strip().lower()
    if level not in {"easy", "standard", "strong", "a7"}:
        raise ValueError("arena_agent_difficulty_invalid")
    return level


def dot_edge(view: object, *, difficulty: object = "standard") -> tuple[str, str]:
    if not isinstance(view, dict) or view.get("status") != "active":
        raise ValueError("arena_agent_dot_state_invalid")
    level = _difficulty(difficulty)
    existing = {tuple(edge) for edge in view.get("edges", [])}
    nodes = [f"{x},{y}" for x in range(3) for y in range(3)]
    legal = []
    for a in nodes:
        ax, ay = map(int, a.split(","))
        for b in nodes:
            bx, by = map(int, b.split(","))
            if abs(ax - bx) + abs(ay - by) != 1:
                continue
            edge = tuple(sorted((a, b)))
            if edge not in existing and edge not in legal:
                legal.append(edge)
    if not legal:
        raise ValueError("arena_agent_no_legal_move")
    if level in {"strong", "a7"}:
        def completed_count(edges):
            edge_set = set(edges)
            total = 0
            for x in range(2):
                for y in range(2):
                    needed = {
                        tuple(sorted((f"{x},{y}", f"{x+1},{y}"))),
                        tuple(sorted((f"{x},{y}", f"{x},{y+1}"))),
                        tuple(sorted((f"{x+1},{y}", f"{x+1},{y+1}"))),
                        tuple(sorted((f"{x},{y+1}", f"{x+1},{y+1}"))),
                    }
                    total += needed <= edge_set
            return total
        before = completed_count(existing)
        scoring = [
            edge for edge in legal
            if completed_count(existing | {edge}) > before
        ]
        if scoring:
            return scoring[0]
    return legal[-1] if level == "easy" else legal[0]


def oware_pit(view: object, *, difficulty: object = "standard") -> int:
    if not isinstance(view, dict) or view.get("status") != "active":
        raise ValueError("arena_agent_oware_state_invalid")
    level = _difficulty(difficulty)
    legal = list(view.get("legal_pits") or [])
    pits = list(view.get("pits") or [])
    if not legal or len(pits) != 12:
        raise ValueError("arena_agent_no_legal_move")
    if level == "easy":
        return legal[0]
    if level in {"strong", "a7"}:
        return max(legal, key=lambda pit: (pits[pit], pit))
    return legal[len(legal) // 2]


def ludo_piece(view: object, *, difficulty: object = "standard") -> str:
    if not isinstance(view, dict) or view.get("status") != "active":
        raise ValueError("arena_agent_ludo_state_invalid")
    level = _difficulty(difficulty)
    legal = list(view.get("movable_piece_ids") or [])
    if not legal:
        raise ValueError("arena_agent_no_legal_move")
    progress = {}
    for player in view.get("players") or []:
        for piece in player.get("pieces") or []:
            progress[str(piece.get("id"))] = int(piece.get("progress", -1))
    if level == "easy":
        return min(legal, key=lambda item: (progress.get(item, -1), item))
    if level in {"strong", "a7"}:
        return max(legal, key=lambda item: (progress.get(item, -1), item))
    return legal[0]


def chess_action(state: object, *, difficulty: object = "standard") -> dict[str, object]:
    if not isinstance(state, dict) or chess.validate(state).get("passed") is not True:
        raise ValueError("arena_agent_chess_state_invalid")
    if state.get("status") != "active":
        raise ValueError("arena_agent_chess_state_invalid")
    level = _difficulty(difficulty)
    color = state["turn"]
    values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}
    legal = []
    for source, piece in sorted(state["board"].items()):
        if piece[0] != color:
            continue
        for file in "abcdefgh":
            for rank in "12345678":
                target = file + rank
                if source == target:
                    continue
                promotion = "Q" if piece[1] == "P" and rank in {"1", "8"} else None
                if chess._apply_candidate(state, source, target, color, promotion) is None:
                    continue
                captured = state["board"].get(target)
                score = values.get(captured[1], 0) if captured else 0
                legal.append((score, source, target, promotion))
    if not legal:
        raise ValueError("arena_agent_no_legal_move")
    if level == "easy":
        _, source, target, promotion = legal[-1]
    elif level in {"strong", "a7"}:
        _, source, target, promotion = max(
            legal, key=lambda item: (item[0], item[2], item[1])
        )
    else:
        _, source, target, promotion = legal[0]
    return {"source": source, "target": target, "promotion": promotion}


def route_empire_action(view: object, *, difficulty: object = "standard") -> dict[str, object]:
    if not isinstance(view, dict) or view.get("status") != "active":
        raise ValueError("arena_agent_route_state_invalid")
    level = _difficulty(difficulty)
    player_id = str(view.get("current_player_id") or "")
    nodes = list(view.get("nodes") or [])
    owned = [node for node in nodes if node.get("owner_id") == player_id]
    open_nodes = [node for node in nodes if node.get("owner_id") is None]
    if level in {"strong", "a7"}:
        upgradable = [node for node in owned if int(node.get("level", 0)) < 3]
        if upgradable:
            target = max(upgradable, key=lambda node: int(node.get("level", 0)))
            return {"action": "develop", "node_id": target["id"]}
    if open_nodes:
        return {"action": "claim", "node_id": open_nodes[0]["id"]}
    edges = [tuple(edge) for edge in view.get("edges") or []]
    routes = {
        frozenset((route.get("from"), route.get("to")))
        for route in view.get("routes") or []
    }
    owned_ids = {node["id"] for node in owned}
    for a, b in edges:
        if a in owned_ids and b in owned_ids and frozenset((a, b)) not in routes:
            return {"action": "route", "node_id": a, "target_node_id": b}
    return {"action": "end_turn"}


def iq_choice(question: object, *, difficulty: object = "standard") -> str:
    if not isinstance(question, dict):
        raise ValueError("arena_agent_iq_question_invalid")
    level = _difficulty(difficulty)
    choices = list(question.get("choices") or [])
    if not choices:
        raise ValueError("arena_agent_no_legal_move")
    if level == "easy":
        return str(choices[0]["id"])
    material = str(question.get("prompt") or "") + "|" + "|".join(
        str(choice.get("label") or "") for choice in choices
    )
    index = int(hashlib.sha256(material.encode("utf-8")).hexdigest()[:8], 16) % len(choices)
    return str(choices[index]["id"])
