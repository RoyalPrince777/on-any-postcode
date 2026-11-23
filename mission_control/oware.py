"""First-party OAP Arena Oware engine and local play modes."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import re
import uuid

from . import oware_nam_nam

SCHEMA = "oap.arena.oware.v1"
SESSION_KEY = "oap_oware_v1"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
PIT_COUNT = 12
PITS_PER_PLAYER = 6
INITIAL_SEEDS_PER_PIT = 4
TOTAL_SEEDS = 48
AGENT_DEPTHS = {"beginner": 0, "standard": 2, "expert": 4}
POSITION_WINDOW = 120
LOCAL_RECEIPT_LIMIT = 24


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


def new_game(players=None, *, agent_level=None, variant="abapa"):
    if variant not in ("abapa", "nam-nam"):
        raise ValueError("oware_variant_invalid")
    if agent_level is not None and (
        not isinstance(agent_level, str) or agent_level not in AGENT_DEPTHS
    ):
        raise ValueError("oware_agent_level_invalid")
    if agent_level is not None and players is None:
        players = ["Player One", "Oware Agent"]
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
            **({"agent_level": agent_level} if agent_level else {}),
            **({"variant": variant, "round": 1, "territory": 6} if variant == "nam-nam" else {}),
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
        elif "oware_pits_invalid" not in errors and sum(pits) + sum(captured) != TOTAL_SEEDS:
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


def _legal_pits(pits, player_index):
    side = _side(player_index)
    opponent_has_seeds = any(pits[index] for index in _opponent_side(player_index))
    return [
        index for index in side
        if pits[index] and (opponent_has_seeds or pits[index] > side[-1] - index)
    ]


def legal_pits(state):
    return _available_pits(_copy(state))


def _available_pits(state):
    if state["status"] != "active":
        return []
    if state.get("variant") == "nam-nam":
        return list(oware_nam_nam.options(_nam_nam_position(state)))
    return _legal_pits(state["pits"], state["turn_index"])


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
    last_move = next(
        (item for item in reversed(checked["request_receipts"]) if item["action"] == "move"),
        None,
    )
    nam_nam = checked.get("variant") == "nam-nam"
    return {
        "started": True,
        "game_id": checked["game_id"],
        "agent_level": checked.get("agent_level"),
        "status": checked["status"],
        "players": copy.deepcopy(checked["players"]),
        "pits": list(checked["pits"]),
        "current_player_id": player["id"],
        "current_player_name": player["name"],
        "legal_pits": _available_pits(checked),
        "last_pit": last_move["pit"] if last_move else None,
        "grand_slam_forfeited": last_move["grand_slam_forfeited"] if last_move else False,
        "winner_id": checked["winner_id"],
        "draw": checked["draw"],
        "result": checked.get("result"),
        "total_seeds": TOTAL_SEEDS,
        "variant": "nam-nam" if nam_nam else "abapa",
        "ruleset": "Nam-Nam" if nam_nam else "Abapa core",
        **({
            "round": checked["round"],
            "owners": oware_nam_nam.owners(checked["territory"]),
            "last_round": checked.get("last_round"),
        } if nam_nam else {}),
        "payments": False,
    }


def _settle_board(state, result):
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
    state["result"] = result


def _position(pits, turn_index):
    # One character per pit keeps the Flask session compact.
    return "".join(chr(65 + count) for count in pits) + str(turn_index)


def _nam_nam_position(state):
    return oware_nam_nam.Position(
        tuple(state["pits"]), tuple(player["captured"] for player in state["players"]),
        state["turn_index"], state["territory"], state["round"],
    )


def _move_nam_nam(state, pit, request_id):
    position = _nam_nam_position(state)
    options = oware_nam_nam.options(position)
    if pit not in options:
        raise ValueError("oware_move_not_legal")
    played = oware_nam_nam.play(position, options[pit])
    if played.round_number == position.round_number and not played.result:
        history = [] if played.scores != position.scores else state.get(
            "positions", [_position(position.pits, position.turn)]
        )
        key = _position(played.pits, played.turn)
        history = (history + [key])[-POSITION_WINDOW:]
        if history.count(key) >= 3:
            played = oware_nam_nam.replay_round(played)
        else:
            state["positions"] = history
    if played.round_number != position.round_number:
        state.pop("positions", None)
        state["last_round"] = list(played.last_round) if played.last_round else None
        state["result"] = None if played.last_round else "round_replayed"
    state.update(pits=list(played.pits), turn_index=played.turn, territory=played.territory, round=played.round_number)
    for player, score in zip(state["players"], played.scores):
        player["captured"] = score
    if played.result:
        winner = 0 if played.territory == PIT_COUNT else 1
        state.update(status="completed", result=played.result, winner_id=state["players"][winner]["id"])
    state["request_receipts"].append({
        "request_id": request_id, "action": "move", "pit": pit, "grand_slam_forfeited": False,
    })
    return _seal(state)


def move(state, *, pit, request_id):
    current = _copy(state)
    req = _request_id(request_id)
    if any(item["request_id"] == req for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError(f"oware_game_{current['status']}")
    if type(pit) is not int or pit not in range(PIT_COUNT):
        raise ValueError("oware_pit_invalid")
    if current.get("variant") == "nam-nam":
        return _move_nam_nam(current, pit, req)
    player_index = current["turn_index"]
    allowed = _legal_pits(current["pits"], player_index)
    if pit not in allowed:
        raise ValueError("oware_move_not_legal")

    previous_position = _position(current["pits"], player_index)
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
        if not _legal_pits(current["pits"], current["turn_index"]):
            _settle_board(current, "no_legal_move")
        else:
            positions = [] if captured else current.get("positions", [previous_position])
            positions = (positions + [_position(current["pits"], current["turn_index"])])[-POSITION_WINDOW:]
            current["positions"] = positions
            if positions.count(positions[-1]) >= 3:
                _settle_board(current, "repetition")
    return _seal(current)


def _agent_value(pits, scores, turn, depth):
    difference = scores[1] - scores[0]
    if max(scores) >= 25:
        return 100 + difference if difference > 0 else difference - 100
    legal = _legal_pits(pits, turn)
    if not legal:
        scores = [scores[index] + sum(pits[pit] for pit in _side(index)) for index in (0, 1)]
        difference = scores[1] - scores[0]
        if difference:
            return 100 + difference if difference > 0 else difference - 100
    if not legal or not depth or sum(scores) == TOTAL_SEEDS:
        return difference
    values = []
    for pit in legal:
        sown, landing = _sow(pits, pit)
        board, captured, _ = _capture(sown, turn, landing)
        next_scores = list(scores)
        next_scores[turn] += captured
        values.append(_agent_value(board, next_scores, 1 - turn, depth - 1))
    return max(values) if turn == 1 else min(values)


def play_local_turn(state, *, pit, request_id):
    request_id = _request_id(request_id)
    if request_id.startswith("agent-"):
        raise ValueError("oware_request_id_invalid")
    current = move(state, pit=pit, request_id=request_id)
    level = current.get("agent_level")
    if level and current.get("variant") == "nam-nam":
        reply = 0
        while current["status"] == "active" and current["turn_index"] == 1:
            position = _nam_nam_position(current)
            options = oware_nam_nam.options(position)
            agent_request = "agent-" + _digest([request_id, reply])
            choice = random.Random(agent_request).choice(list(options))
            depth = AGENT_DEPTHS[level]
            if depth:
                choice = max(options, key=lambda candidate: (
                    oware_nam_nam.agent_value(oware_nam_nam.play(position, options[candidate]), depth - 1),
                    candidate == choice,
                ))
            current = move(current, pit=choice, request_id=agent_request)
            reply += 1
    elif level and current["status"] == "active" and current["turn_index"] == 1:
        legal = _legal_pits(current["pits"], 1)
        choice = random.Random(request_id).choice(legal)
        if AGENT_DEPTHS[level]:
            scores = [player["captured"] for player in current["players"]]
            values = {}
            for candidate in legal:
                sown, landing = _sow(current["pits"], candidate)
                board, captured, _ = _capture(sown, 1, landing)
                values[candidate] = _agent_value(
                    board, [scores[0], scores[1] + captured], 0, AGENT_DEPTHS[level] - 1
                )
            choice = max(legal, key=lambda candidate: (values[candidate], candidate == choice))
        current = move(current, pit=choice, request_id="agent-" + _digest(request_id))
    current["request_receipts"] = current["request_receipts"][-LOCAL_RECEIPT_LIMIT:]
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
