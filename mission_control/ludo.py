"""First-party OAP Arena Ludo engine.

OAP standard rules slice:
- 2-4 players, four pieces each
- server-generated die rolls (1-6)
- a six is required to enter a piece from yard
- 52-space shared ring plus a six-step private home lane
- safe shared squares cannot be captured
- captures return opposing pieces to yard
- rolling six or making a capture grants another turn
- exact roll required to finish; all four pieces home wins
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import secrets
import uuid

SCHEMA = "oap.arena.ludo.v2"
SESSION_KEY = "oap_ludo_v2"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

TRACK_LENGTH = 52
HOME_LENGTH = 6
FINISH_PROGRESS = TRACK_LENGTH + HOME_LENGTH
PIECES_PER_PLAYER = 4
START_OFFSETS = (0, 13, 26, 39)
SAFE_TRACK_SQUARES = frozenset({0, 8, 13, 21, 26, 34, 39, 47})


def _canon(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _digest(value):
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _seal(state):
    result = copy.deepcopy(state)
    result.pop("checkpoint", None)
    result["checkpoint"] = _digest(result)
    return result


def _req(value):
    request_id = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(request_id):
        raise ValueError("ludo_request_id_invalid")
    return request_id


def _clean_players(players):
    if not isinstance(players, list) or not 2 <= len(players) <= 4:
        raise ValueError("ludo_player_count_invalid")
    names = [" ".join(str(item).split()) for item in players]
    if any(not name or len(name) > 40 for name in names):
        raise ValueError("ludo_players_invalid")
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("ludo_players_invalid")
    return names


def new_game(players: object):
    names = _clean_players(players)
    roster = []
    for index, name in enumerate(names):
        roster.append(
            {
                "id": f"p{index + 1}",
                "name": name,
                "start_offset": START_OFFSETS[index],
                "pieces": [
                    {"id": f"p{index + 1}-{piece + 1}", "progress": -1}
                    for piece in range(PIECES_PER_PLAYER)
                ],
            }
        )
    return _seal(
        {
            "schema": SCHEMA,
            "game_id": str(uuid.uuid4()),
            "status": "active",
            "players": roster,
            "turn_index": 0,
            "winner_id": None,
            "pending_roll": None,
            "request_receipts": [],
        }
    )


def validate(state):
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["ludo_state_missing"]}
    errors = []
    if state.get("schema") != SCHEMA:
        errors.append("ludo_schema_invalid")
    if state.get("status") not in {"active", "completed", "stopped"}:
        errors.append("ludo_status_invalid")
    expected = copy.deepcopy(state)
    expected.pop("checkpoint", None)
    if state.get("checkpoint") != _digest(expected):
        errors.append("ludo_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}


def _copy(state):
    result = validate(state)
    if not result["passed"]:
        raise ValueError(result["errors"][0])
    return copy.deepcopy(state)


def _track_square(player, progress):
    if not 0 <= progress < TRACK_LENGTH:
        return None
    return (player["start_offset"] + progress) % TRACK_LENGTH


def _piece_public(player, piece):
    progress = piece["progress"]
    if progress < 0:
        zone = "yard"
        track_square = None
    elif progress < TRACK_LENGTH:
        zone = "track"
        track_square = _track_square(player, progress)
    elif progress < FINISH_PROGRESS:
        zone = "home"
        track_square = None
    else:
        zone = "finished"
        track_square = None
    return {
        "id": piece["id"],
        "progress": progress,
        "zone": zone,
        "track_square": track_square,
        "home_step": progress - TRACK_LENGTH + 1 if zone == "home" else None,
    }


def _can_move(piece, roll):
    progress = piece["progress"]
    if progress == FINISH_PROGRESS:
        return False
    if progress < 0:
        return roll == 6
    return progress + roll <= FINISH_PROGRESS


def _movable_piece_ids(state, roll):
    player = state["players"][state["turn_index"]]
    return [piece["id"] for piece in player["pieces"] if _can_move(piece, roll)]


def _advance_turn(state):
    state["turn_index"] = (state["turn_index"] + 1) % len(state["players"])


def public_state(state):
    if state is None:
        return {"started": False, "status": "idle"}
    result = validate(state)
    if not result["passed"]:
        raise ValueError(result["errors"][0])
    player = state["players"][state["turn_index"]]
    pending_roll = state.get("pending_roll")
    players = []
    for item in state["players"]:
        players.append(
            {
                "id": item["id"],
                "name": item["name"],
                "pieces": [_piece_public(item, piece) for piece in item["pieces"]],
                "finished": sum(
                    piece["progress"] == FINISH_PROGRESS for piece in item["pieces"]
                ),
            }
        )
    return {
        "started": True,
        "status": state["status"],
        "players": players,
        "current_player_id": player["id"],
        "current_player_name": player["name"],
        "winner_id": state["winner_id"],
        "pending_roll": pending_roll,
        "movable_piece_ids": (
            _movable_piece_ids(state, pending_roll)
            if state["status"] == "active" and pending_roll is not None
            else []
        ),
        "track_length": TRACK_LENGTH,
        "home_length": HOME_LENGTH,
        "safe_track_squares": sorted(SAFE_TRACK_SQUARES),
        "payments": False,
    }


def roll(state, *, request_id: object, die_value: int | None = None):
    current = _copy(state)
    request_id = _req(request_id)
    for receipt in current["request_receipts"]:
        if receipt["request_id"] == request_id:
            return current
    if current["status"] != "active":
        raise ValueError(f"ludo_game_{current['status']}")
    if current.get("pending_roll") is not None:
        raise ValueError("ludo_roll_pending")
    if die_value is None:
        value = secrets.randbelow(6) + 1
    elif isinstance(die_value, int) and 1 <= die_value <= 6:
        value = die_value
    else:
        raise ValueError("ludo_roll_invalid")

    current["pending_roll"] = value
    current["request_receipts"].append(
        {"request_id": request_id, "action": "roll", "value": value}
    )
    if not _movable_piece_ids(current, value):
        current["pending_roll"] = None
        if value != 6:
            _advance_turn(current)
    return _seal(current)


def move(state, *, piece_id: object, request_id: object):
    current = _copy(state)
    request_id = _req(request_id)
    for receipt in current["request_receipts"]:
        if receipt["request_id"] == request_id:
            return current
    if current["status"] != "active":
        raise ValueError(f"ludo_game_{current['status']}")
    roll_value = current.get("pending_roll")
    if roll_value is None:
        raise ValueError("ludo_roll_required")

    player = current["players"][current["turn_index"]]
    piece_id = str(piece_id or "").strip()
    piece = next((item for item in player["pieces"] if item["id"] == piece_id), None)
    if piece is None:
        raise ValueError("ludo_piece_invalid")
    if not _can_move(piece, roll_value):
        raise ValueError("ludo_piece_move_invalid")

    if piece["progress"] < 0:
        piece["progress"] = 0
    else:
        piece["progress"] += roll_value

    captured = []
    if 0 <= piece["progress"] < TRACK_LENGTH:
        landing = _track_square(player, piece["progress"])
        if landing not in SAFE_TRACK_SQUARES:
            for opponent in current["players"]:
                if opponent["id"] == player["id"]:
                    continue
                for target in opponent["pieces"]:
                    if (
                        0 <= target["progress"] < TRACK_LENGTH
                        and _track_square(opponent, target["progress"]) == landing
                    ):
                        target["progress"] = -1
                        captured.append(target["id"])

    current["pending_roll"] = None
    current["request_receipts"].append(
        {
            "request_id": request_id,
            "action": "move",
            "piece_id": piece_id,
            "roll": roll_value,
            "captured": captured,
        }
    )

    if all(item["progress"] == FINISH_PROGRESS for item in player["pieces"]):
        current["status"] = "completed"
        current["winner_id"] = player["id"]
    elif roll_value != 6 and not captured:
        _advance_turn(current)

    return _seal(current)


def stop(state, *, request_id: object):
    current = _copy(state)
    request_id = _req(request_id)
    if any(item["request_id"] == request_id for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError("ludo_stop_denied")
    current["status"] = "stopped"
    current["pending_roll"] = None
    current["request_receipts"].append(
        {"request_id": request_id, "action": "stop"}
    )
    return _seal(current)
