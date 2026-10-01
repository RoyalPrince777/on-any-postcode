"""First-party OAP Arena Ludo classic-core engine."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import secrets
import uuid

SCHEMA = "oap.arena.ludo.v2"
SESSION_KEY = "oap_ludo_v1"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

TOKENS_PER_PLAYER = 4
TRACK_LENGTH = 52
FINISH = 57
START_OFFSETS = (0, 13, 26, 39)
SAFE_GLOBAL_SQUARES = frozenset({0, 8, 13, 21, 26, 34, 39, 47})


def _canon(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _digest(value):
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _seal(state):
    sealed = copy.deepcopy(state)
    sealed.pop("checkpoint", None)
    sealed["checkpoint"] = _digest(sealed)
    return sealed


def _req(value):
    request_id = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(request_id):
        raise ValueError("ludo_request_id_invalid")
    return request_id


def new_game(players: object):
    if not isinstance(players, list) or not 2 <= len(players) <= 4:
        raise ValueError("ludo_player_count_invalid")
    names = [" ".join(str(item).split()) for item in players]
    if (
        any(not name or len(name) > 40 for name in names)
        or len({name.casefold() for name in names}) != len(names)
    ):
        raise ValueError("ludo_players_invalid")
    return _seal(
        {
            "schema": SCHEMA,
            "game_id": str(uuid.uuid4()),
            "status": "active",
            "players": [
                {"id": f"p{index + 1}", "name": name, "pieces": [-1] * TOKENS_PER_PLAYER}
                for index, name in enumerate(names)
            ],
            "turn_index": 0,
            "die": None,
            "six_streak": 0,
            "winner_id": None,
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
    players = state.get("players")
    if not isinstance(players, list) or not 2 <= len(players) <= 4:
        errors.append("ludo_players_invalid")
    else:
        for player in players:
            pieces = player.get("pieces")
            if (
                not isinstance(pieces, list)
                or len(pieces) != TOKENS_PER_PLAYER
                or any(not isinstance(pos, int) or pos < -1 or pos > FINISH for pos in pieces)
            ):
                errors.append("ludo_pieces_invalid")
                break
    if state.get("die") is not None and state.get("die") not in range(1, 7):
        errors.append("ludo_die_invalid")
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


def _global_square(player_index, position):
    if position < 0 or position >= TRACK_LENGTH:
        return None
    return (START_OFFSETS[player_index] + position) % TRACK_LENGTH


def _legal_piece_indices(state, player_index=None, die=None):
    if state["status"] != "active":
        return []
    player_index = state["turn_index"] if player_index is None else player_index
    die = state["die"] if die is None else die
    if die not in range(1, 7):
        return []
    legal = []
    for index, position in enumerate(state["players"][player_index]["pieces"]):
        if position == -1:
            if die == 6:
                legal.append(index)
        elif position < FINISH and position + die <= FINISH:
            legal.append(index)
    return legal


def _advance_turn(state):
    state["turn_index"] = (state["turn_index"] + 1) % len(state["players"])
    state["six_streak"] = 0


def _capture(state, mover_index, landing):
    square = _global_square(mover_index, landing)
    if square is None or square in SAFE_GLOBAL_SQUARES:
        return []
    captured = []
    for player_index, player in enumerate(state["players"]):
        if player_index == mover_index:
            continue
        for piece_index, position in enumerate(player["pieces"]):
            if _global_square(player_index, position) == square:
                player["pieces"][piece_index] = -1
                captured.append(
                    {"player_id": player["id"], "piece_index": piece_index}
                )
    return captured


def public_state(state):
    if state is None:
        return {"started": False, "status": "idle"}
    result = validate(state)
    if not result["passed"]:
        raise ValueError(result["errors"][0])
    player = state["players"][state["turn_index"]]
    return {
        "started": True,
        "status": state["status"],
        "players": copy.deepcopy(state["players"]),
        "current_player_id": player["id"],
        "current_player_name": player["name"],
        "die": state["die"],
        "legal_pieces": _legal_piece_indices(state),
        "winner_id": state["winner_id"],
        "finish": FINISH,
        "safe_squares": sorted(SAFE_GLOBAL_SQUARES),
        "ruleset": "Ludo classic core",
        "payments": False,
    }


def roll(state, *, request_id: object, forced_die: int | None = None):
    current = _copy(state)
    req = _req(request_id)
    prior = next(
        (item for item in current["request_receipts"] if item["request_id"] == req),
        None,
    )
    if prior is not None:
        return current
    if current["status"] != "active":
        raise ValueError(f"ludo_game_{current['status']}")
    if current["die"] is not None:
        raise ValueError("ludo_roll_pending")
    if forced_die is not None and forced_die not in range(1, 7):
        raise ValueError("ludo_die_invalid")

    die = forced_die if forced_die is not None else secrets.randbelow(6) + 1
    current["six_streak"] = current["six_streak"] + 1 if die == 6 else 0
    receipt = {"request_id": req, "action": "roll", "die": die}

    if current["six_streak"] >= 3:
        receipt["forfeited"] = True
        current["request_receipts"].append(receipt)
        current["die"] = None
        _advance_turn(current)
        return _seal(current)

    current["die"] = die
    legal = _legal_piece_indices(current)
    if not legal:
        receipt["passed"] = True
        current["request_receipts"].append(receipt)
        current["die"] = None
        _advance_turn(current)
        return _seal(current)

    current["request_receipts"].append(receipt)
    return _seal(current)


def move(state, *, piece_index: object, request_id: object):
    current = _copy(state)
    req = _req(request_id)
    if any(item["request_id"] == req for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError(f"ludo_game_{current['status']}")
    if current["die"] is None:
        raise ValueError("ludo_roll_required")
    if not isinstance(piece_index, int) or piece_index not in range(TOKENS_PER_PLAYER):
        raise ValueError("ludo_piece_invalid")
    legal = _legal_piece_indices(current)
    if piece_index not in legal:
        raise ValueError("ludo_move_not_legal")

    player_index = current["turn_index"]
    player = current["players"][player_index]
    die = current["die"]
    before = player["pieces"][piece_index]
    landing = 0 if before == -1 else before + die
    player["pieces"][piece_index] = landing
    captured = _capture(current, player_index, landing)
    current["request_receipts"].append(
        {
            "request_id": req,
            "action": "move",
            "piece_index": piece_index,
            "die": die,
            "from": before,
            "to": landing,
            "captured": captured,
        }
    )
    current["die"] = None

    if all(position == FINISH for position in player["pieces"]):
        current["status"] = "completed"
        current["winner_id"] = player["id"]
    elif die == 6 or captured:
        if die != 6:
            current["six_streak"] = 0
    else:
        _advance_turn(current)
    return _seal(current)


def stop(state, *, request_id: object):
    current = _copy(state)
    req = _req(request_id)
    if any(item["request_id"] == req for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError("ludo_stop_denied")
    current["status"] = "stopped"
    current["request_receipts"].append({"request_id": req, "action": "stop"})
    return _seal(current)
