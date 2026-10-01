"""First-party OAP Arena Chess engine with standard move rules."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid

SCHEMA = "oap.arena.chess.v2"
SESSION_KEY = "oap_chess_v2"
REQ = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
PROMOTIONS = {"Q", "R", "B", "N"}


def _d(value):
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def _seal(state):
    result = copy.deepcopy(state)
    result.pop("checkpoint", None)
    result["checkpoint"] = _d(result)
    return result


def _position_key(state):
    payload = {
        "board": state["board"],
        "turn": state["turn"],
        "castling": state["castling"],
        "en_passant": state.get("en_passant"),
    }
    return _d(payload)


def new_game():
    board = {
        "a1": "wR", "b1": "wN", "c1": "wB", "d1": "wQ", "e1": "wK", "f1": "wB", "g1": "wN", "h1": "wR",
        "a2": "wP", "b2": "wP", "c2": "wP", "d2": "wP", "e2": "wP", "f2": "wP", "g2": "wP", "h2": "wP",
        "a8": "bR", "b8": "bN", "c8": "bB", "d8": "bQ", "e8": "bK", "f8": "bB", "g8": "bN", "h8": "bR",
        "a7": "bP", "b7": "bP", "c7": "bP", "d7": "bP", "e7": "bP", "f7": "bP", "g7": "bP", "h7": "bP",
    }
    state = {
        "schema": SCHEMA,
        "game_id": str(uuid.uuid4()),
        "status": "active",
        "turn": "w",
        "board": board,
        "winner": None,
        "result": None,
        "check": False,
        "castling": {"wK": True, "wQ": True, "bK": True, "bQ": True},
        "en_passant": None,
        "halfmove_clock": 0,
        "position_counts": {},
        "request_receipts": [],
    }
    state["position_counts"][_position_key(state)] = 1
    return _seal(state)


def validate(state):
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["chess_state_missing"]}
    errors = []
    expected = copy.deepcopy(state)
    expected.pop("checkpoint", None)
    if state.get("schema") != SCHEMA:
        errors.append("chess_schema_invalid")
    if state.get("status") not in {"active", "completed", "stopped"}:
        errors.append("chess_status_invalid")
    if state.get("checkpoint") != _d(expected):
        errors.append("chess_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}


def _copy(state):
    result = validate(state)
    if not result["passed"]:
        raise ValueError(result["errors"][0])
    return copy.deepcopy(state)


def _sq(value):
    return isinstance(value, str) and len(value) == 2 and value[0] in "abcdefgh" and value[1] in "12345678"


def _req(value):
    request_id = str(value or "").strip()
    if not REQ.fullmatch(request_id):
        raise ValueError("chess_request_id_invalid")
    return request_id


def _coords(square):
    return ord(square[0]) - 97, int(square[1]) - 1


def _square(x, y):
    return f"{chr(97 + x)}{y + 1}"


def _path_clear(board, src, dst):
    sx, sy = _coords(src)
    dx, dy = _coords(dst)
    fx, fy = dx - sx, dy - sy
    stepx = 0 if fx == 0 else (1 if fx > 0 else -1)
    stepy = 0 if fy == 0 else (1 if fy > 0 else -1)
    x, y = sx + stepx, sy + stepy
    while (x, y) != (dx, dy):
        if _square(x, y) in board:
            return False
        x += stepx
        y += stepy
    return True


def _basic_legal(piece, src, dst, board):
    sx, sy = _coords(src)
    dx, dy = _coords(dst)
    fx, fy = dx - sx, dy - sy
    color, kind = piece
    target = board.get(dst)
    if target and target[0] == color:
        return False
    if kind == "N":
        return (abs(fx), abs(fy)) in {(1, 2), (2, 1)}
    if kind == "K":
        return max(abs(fx), abs(fy)) == 1
    if kind == "P":
        direction = 1 if color == "w" else -1
        start = 1 if color == "w" else 6
        if fx == 0 and fy == direction and not target:
            return True
        if fx == 0 and sy == start and fy == 2 * direction and not target:
            return _square(sx, sy + direction) not in board
        return abs(fx) == 1 and fy == direction and target is not None and target[0] != color
    if kind in {"R", "B", "Q"}:
        if kind == "R" and not (fx == 0 or fy == 0):
            return False
        if kind == "B" and abs(fx) != abs(fy):
            return False
        if kind == "Q" and not (fx == 0 or fy == 0 or abs(fx) == abs(fy)):
            return False
        return _path_clear(board, src, dst)
    return False


def _king_square(board, color):
    return next((sq for sq, piece in board.items() if piece == color + "K"), None)


def _attacked(board, square, by_color):
    dx, dy = _coords(square)
    for src, piece in board.items():
        if piece[0] != by_color:
            continue
        sx, sy = _coords(src)
        if piece[1] == "P":
            direction = 1 if by_color == "w" else -1
            if abs(dx - sx) == 1 and dy - sy == direction:
                return True
            continue
        if _basic_legal(piece, src, square, board):
            return True
    return False


def _in_check(board, color):
    king = _king_square(board, color)
    return king is None or _attacked(board, king, "b" if color == "w" else "w")


def _castle_move(state, src, dst, color):
    rank = "1" if color == "w" else "8"
    if src != "e" + rank or dst not in {"g" + rank, "c" + rank}:
        return None
    side = "K" if dst[0] == "g" else "Q"
    if not state["castling"].get(color + side):
        return None
    rook_src = ("h" if side == "K" else "a") + rank
    rook_dst = ("f" if side == "K" else "d") + rank
    between = ["f" + rank, "g" + rank] if side == "K" else ["d" + rank, "c" + rank, "b" + rank]
    through = ["f" + rank, "g" + rank] if side == "K" else ["d" + rank, "c" + rank]
    if state["board"].get(rook_src) != color + "R":
        return None
    if any(square in state["board"] for square in between):
        return None
    if _in_check(state["board"], color):
        return None
    enemy = "b" if color == "w" else "w"
    if any(_attacked(state["board"], square, enemy) for square in through):
        return None
    return rook_src, rook_dst


def _apply_candidate(state, src, dst, color, promotion=None):
    board = copy.deepcopy(state["board"])
    piece = board.get(src)
    if not piece or piece[0] != color:
        return None
    target = board.get(dst)
    if target and target[1] == "K":
        return None

    captured = target is not None
    special = None
    if piece[1] == "K" and abs(_coords(dst)[0] - _coords(src)[0]) == 2:
        castle = _castle_move(state, src, dst, color)
        if castle is None:
            return None
        rook_src, rook_dst = castle
        board.pop(src)
        board[dst] = piece
        board.pop(rook_src)
        board[rook_dst] = color + "R"
        special = "castle"
    elif piece[1] == "P" and dst == state.get("en_passant") and dst not in board:
        sx, sy = _coords(src)
        dx, dy = _coords(dst)
        direction = 1 if color == "w" else -1
        if abs(dx - sx) != 1 or dy - sy != direction:
            return None
        captured_sq = _square(dx, dy - direction)
        if board.get(captured_sq) != ("b" if color == "w" else "w") + "P":
            return None
        board.pop(src)
        board.pop(captured_sq)
        board[dst] = piece
        captured = True
        special = "en_passant"
    else:
        if not _basic_legal(piece, src, dst, board):
            return None
        board.pop(src)
        board[dst] = piece

    if piece[1] == "P" and dst[1] in {"1", "8"}:
        if promotion not in PROMOTIONS:
            return None
        board[dst] = color + promotion
        special = "promotion"

    if _in_check(board, color):
        return None
    return board, captured, special


def _has_legal_move(state, color):
    for src, piece in state["board"].items():
        if piece[0] != color:
            continue
        for file in "abcdefgh":
            for rank in "12345678":
                dst = file + rank
                if src == dst:
                    continue
                promotion = "Q" if piece[1] == "P" and rank in {"1", "8"} else None
                if _apply_candidate(state, src, dst, color, promotion) is not None:
                    return True
    return False


def _insufficient_material(board):
    pieces = [(sq, piece) for sq, piece in board.items() if piece[1] != "K"]
    if not pieces:
        return True
    if len(pieces) == 1 and pieces[0][1][1] in {"B", "N"}:
        return True
    if len(pieces) == 2 and all(piece[1][1] == "B" for piece in pieces):
        colors = []
        for sq, _piece in pieces:
            x, y = _coords(sq)
            colors.append((x + y) % 2)
        return colors[0] == colors[1]
    return False


def _update_castling(state, piece, src, dst, captured_piece):
    color = piece[0]
    if piece[1] == "K":
        state["castling"][color + "K"] = False
        state["castling"][color + "Q"] = False
    if piece[1] == "R":
        mapping = {"h1": "wK", "a1": "wQ", "h8": "bK", "a8": "bQ"}
        if src in mapping:
            state["castling"][mapping[src]] = False
    if captured_piece and captured_piece[1] == "R":
        mapping = {"h1": "wK", "a1": "wQ", "h8": "bK", "a8": "bQ"}
        if dst in mapping:
            state["castling"][mapping[dst]] = False


def public_state(state):
    if state is None:
        return {"started": False, "status": "idle"}
    result = validate(state)
    if not result["passed"]:
        raise ValueError(result["errors"][0])
    return {
        "started": True,
        "status": state["status"],
        "turn": "White" if state["turn"] == "w" else "Black",
        "board": copy.deepcopy(state["board"]),
        "winner": state["winner"],
        "result": state.get("result"),
        "check": bool(state.get("check")),
        "castling": copy.deepcopy(state.get("castling", {})),
        "en_passant": state.get("en_passant"),
        "halfmove_clock": state.get("halfmove_clock", 0),
        "payments": False,
    }


def move(state, *, source: object, target: object, request_id: object, promotion: object = None):
    current = _copy(state)
    request_id = _req(request_id)
    src, dst = str(source), str(target)
    if any(item["request_id"] == request_id for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError(f"chess_game_{current['status']}")
    if not _sq(src) or not _sq(dst):
        raise ValueError("chess_square_invalid")

    piece = current["board"].get(src)
    if not piece or piece[0] != current["turn"]:
        raise ValueError("chess_turn_invalid")
    if current["board"].get(dst, "")[1:] == "K":
        raise ValueError("chess_king_capture_invalid")

    promotion_value = str(promotion or "").upper() or None
    if piece[1] == "P" and dst[1] in {"1", "8"} and promotion_value not in PROMOTIONS:
        raise ValueError("chess_promotion_required")
    if promotion_value is not None and promotion_value not in PROMOTIONS:
        raise ValueError("chess_promotion_invalid")

    captured_piece = current["board"].get(dst)
    applied = _apply_candidate(current, src, dst, current["turn"], promotion_value)
    if applied is None:
        basic_ok = _basic_legal(piece, src, dst, current["board"])
        castle_attempt = piece[1] == "K" and abs(_coords(dst)[0] - _coords(src)[0]) == 2
        en_passant_attempt = piece[1] == "P" and dst == current.get("en_passant")
        if basic_ok or castle_attempt or en_passant_attempt:
            raise ValueError("chess_self_check_invalid")
        raise ValueError("chess_move_invalid")

    next_board, captured, special = applied
    mover = current["turn"]
    opponent = "b" if mover == "w" else "w"
    _update_castling(current, piece, src, dst, captured_piece)
    current["board"] = next_board

    sx, sy = _coords(src)
    dx, dy = _coords(dst)
    current["en_passant"] = (
        _square(sx, sy + (1 if mover == "w" else -1))
        if piece[1] == "P" and abs(dy - sy) == 2
        else None
    )
    current["halfmove_clock"] = 0 if piece[1] == "P" or captured else current.get("halfmove_clock", 0) + 1
    current["turn"] = opponent
    current["request_receipts"].append(
        {
            "request_id": request_id,
            "action": "move",
            "source": src,
            "target": dst,
            "promotion": promotion_value,
            "special": special,
        }
    )

    opponent_in_check = _in_check(current["board"], opponent)
    current["check"] = opponent_in_check
    current["result"] = None
    current["winner"] = None

    if not _has_legal_move(current, opponent):
        current["status"] = "completed"
        current["result"] = "checkmate" if opponent_in_check else "stalemate"
        current["winner"] = ("White" if mover == "w" else "Black") if opponent_in_check else None
    elif _insufficient_material(current["board"]):
        current["status"] = "completed"
        current["result"] = "draw_insufficient_material"
    elif current["halfmove_clock"] >= 100:
        current["status"] = "completed"
        current["result"] = "draw_fifty_move"
    else:
        key = _position_key(current)
        current["position_counts"][key] = current["position_counts"].get(key, 0) + 1
        if current["position_counts"][key] >= 3:
            current["status"] = "completed"
            current["result"] = "draw_threefold"

    return _seal(current)


def stop(state, *, request_id: object):
    current = _copy(state)
    request_id = _req(request_id)
    if any(item["request_id"] == request_id for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError("chess_stop_denied")
    current["status"] = "stopped"
    current["request_receipts"].append({"request_id": request_id, "action": "stop"})
    return _seal(current)
