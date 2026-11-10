"""First-party OAP Arena Oware (Abapa core) engine."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid

SCHEMA = "oap.arena.oware.v1"
SESSION_KEY = "oap_oware_v1"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
PIT_COUNT = 12
PITS_PER_PLAYER = 6
INITIAL_SEEDS_PER_PIT = 4
TOTAL_SEEDS = 48


def _canon(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _digest(value):
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _seal(state):
    result = copy.deepcopy(state)
    result.pop("checkpoint", None)
    result["checkpoint"] = _digest(result)
    return result


def _request_id(value):
    request_id = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(request_id):
        raise ValueError("oware_request_id_invalid")
    return request_id


def _side(player_index):
    return range(6) if player_index == 0 else range(6, 12)


def _opponent_side(player_index):
    return range(6, 12) if player_index == 0 else range(6)


def _normalise_players(players):
    if players is None:
        players = ["Player One", "Player Two"]
    if not isinstance(players, list) or len(players) != 2:
        raise ValueError("oware_player_count_invalid")
    names = [" ".join(str(item).split()) for item in players]
    if any(not name or len(name) > 40 for name in names):
        raise ValueError("oware_players_invalid")
    if len({name.casefold() for name in names}) != 2:
        raise ValueError("oware_players_invalid")
    return names


def new_game(players=None):
    names = _normalise_players(players)
    return _seal(
        {
            "schema": SCHEMA,
            "game_id": str(uuid.uuid4()),
            "status": "active",
            "players": [
                {"id": "p1", "name": names[0], "captured": 0},
                {"id": "p2", "name": names[1], "captured": 0},
            ],
            "pits": [INITIAL_SEEDS_PER_PIT] * PIT_COUNT,
            "turn_index": 0,
            "winner_id": None,
            "draw": False,
            "result": None,
            "request_receipts": [],
        }
    )


def validate(state):
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["oware_state_missing"]}
    errors = []
    if state.get("schema") != SCHEMA:
        errors.append("oware_schema_invalid")
    if state.get("status") not in {"active", "completed", "stopped"}:
        errors.append("oware_status_invalid")
    pits = state.get("pits")
    if (
        not isinstance(pits, list)
        or len(pits) != PIT_COUNT
        or any(not isinstance(seed, int) or seed < 0 for seed in pits)
    ):
        errors.append("oware_pits_invalid")
    players = state.get("players")
    if not isinstance(players, list) or len(players) != 2:
        errors.append("oware_players_invalid")
    else:
        captured = [player.get("captured") for player in players if isinstance(player, dict)]
        if len(captured) != 2 or any(not isinstance(value, int) or value < 0 for value in captured):
            errors.append("oware_capture_invalid")
        elif isinstance(pits, list) and len(pits) == PIT_COUNT and sum(pits) + sum(captured) != TOTAL_SEEDS:
            errors.append("oware_seed_conservation_invalid")
    if state.get("turn_index") not in {0, 1}:
        errors.append("oware_turn_invalid")
    expected = copy.deepcopy(state)
    expected.pop("checkpoint", None)
    if state.get("checkpoint") != _digest(expected):
        errors.append("oware_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}


def _copy(state):
    checked = validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    return copy.deepcopy(state)


def _sow(pits, start):
    seeds = pits[start]
    if seeds <= 0:
        raise ValueError("oware_pit_empty")
    result = list(pits)
    result[start] = 0
    cursor = start
    while seeds:
        cursor = (cursor + 1) % PIT_COUNT
        if cursor == start:
            cursor = (cursor + 1) % PIT_COUNT
        result[cursor] += 1
        seeds -= 1
    return result, cursor


def _feeds_opponent(pits, player_index, pit):
    before = sum(pits[index] for index in _opponent_side(player_index))
    if before:
        return True
    after, _ = _sow(pits, pit)
    return sum(after[index] for index in _opponent_side(player_index)) > 0


def legal_pits(state):
    checked = _copy(state)
    if checked["status"] != "active":
        return []
    player_index = checked["turn_index"]
    candidates = [index for index in _side(player_index) if checked["pits"][index] > 0]
    opponent_empty = sum(checked["pits"][index] for index in _opponent_side(player_index)) == 0
    if opponent_empty:
        candidates = [
            index for index in candidates
            if _feeds_opponent(checked["pits"], player_index, index)
        ]
    return candidates


def _capture(pits, player_index, landing):
    opponent = set(_opponent_side(player_index))
    captured_indices = []
    cursor = landing
    while cursor in opponent and pits[cursor] in {2, 3}:
        captured_indices.append(cursor)
        cursor = (cursor - 1) % PIT_COUNT
    if not captured_indices:
        return pits, 0, False
    opponent_total = sum(pits[index] for index in opponent)
    captured_total = sum(pits[index] for index in captured_indices)
    if captured_total == opponent_total:
        return pits, 0, True
    result = list(pits)
    for index in captured_indices:
        result[index] = 0
    return result, captured_total, False


def public_state(state):
    if state is None:
        return {"started": False, "status": "idle"}
    checked = _copy(state)
    player = checked["players"][checked["turn_index"]]
    return {
        "started": True,
        "status": checked["status"],
        "players": copy.deepcopy(checked["players"]),
        "pits": list(checked["pits"]),
        "current_player_id": player["id"],
        "current_player_name": player["name"],
        "legal_pits": legal_pits(checked),
        "winner_id": checked["winner_id"],
        "draw": checked["draw"],
        "result": checked.get("result"),
        "total_seeds": TOTAL_SEEDS,
        "ruleset": "Abapa core",
        "payments": False,
    }


def _finish_no_legal_move(state):
    for player_index in (0, 1):
        remaining = sum(state["pits"][index] for index in _side(player_index))
        state["players"][player_index]["captured"] += remaining
        for index in _side(player_index):
            state["pits"][index] = 0
    first = state["players"][0]["captured"]
    second = state["players"][1]["captured"]
    state["status"] = "completed"
    state["draw"] = first == second
    state["winner_id"] = (
        None
        if first == second
        else state["players"][0]["id"] if first > second else state["players"][1]["id"]
    )
    state["result"] = "no_legal_move"


def move(state, *, pit, request_id):
    current = _copy(state)
    req = _request_id(request_id)
    if any(item["request_id"] == req for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError(f"oware_game_{current['status']}")
    if not isinstance(pit, int) or pit not in range(PIT_COUNT):
        raise ValueError("oware_pit_invalid")
    allowed = legal_pits(current)
    if pit not in allowed:
        raise ValueError("oware_move_not_legal")

    player_index = current["turn_index"]
    sown, landing = _sow(current["pits"], pit)
    captured_board, captured, grand_slam_forfeited = _capture(
        sown, player_index, landing
    )
    current["pits"] = captured_board
    current["players"][player_index]["captured"] += captured
    current["request_receipts"].append(
        {
            "request_id": req,
            "action": "move",
            "pit": pit,
            "captured": captured,
            "grand_slam_forfeited": grand_slam_forfeited,
        }
    )

    score = current["players"][player_index]["captured"]
    other_score = current["players"][1 - player_index]["captured"]
    if score >= 25:
        current["status"] = "completed"
        current["winner_id"] = current["players"][player_index]["id"]
        current["result"] = "score"
    elif score == 24 and other_score == 24:
        current["status"] = "completed"
        current["draw"] = True
        current["result"] = "draw_24_24"
    else:
        current["turn_index"] = 1 - player_index
        if not legal_pits(_seal(current)):
            _finish_no_legal_move(current)
    return _seal(current)


def stop(state, *, request_id):
    current = _copy(state)
    req = _request_id(request_id)
    if any(item["request_id"] == req for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError("oware_stop_denied")
    current["status"] = "stopped"
    current["request_receipts"].append({"request_id": req, "action": "stop"})
    return _seal(current)
