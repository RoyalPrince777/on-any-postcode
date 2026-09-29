"""First-party OAP Arena Connect 4 engine.

Bounded two-player, server-authoritative, session-scoped game.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from typing import Any

SCHEMA = "oap.arena.connect4.v1"
SESSION_KEY = "oap_connect4_v1"
ROWS = 6
COLS = 7
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)

def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()

def _seal(state: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(state)
    out.pop("checkpoint", None)
    out["checkpoint"] = _digest(out)
    return out

def _valid_request_id(value: object) -> str:
    result = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(result):
        raise ValueError("connect4_request_id_invalid")
    return result

def new_game(player_one: object = "Player One", player_two: object = "Player Two") -> dict[str, Any]:
    names = [" ".join(str(player_one).split()), " ".join(str(player_two).split())]
    if any(not n or len(n) > 40 for n in names) or names[0].casefold() == names[1].casefold():
        raise ValueError("connect4_players_invalid")
    state = {
        "schema": SCHEMA,
        "game_id": str(uuid.uuid4()),
        "status": "active",
        "players": [{"id":"p1","name":names[0],"piece":1},{"id":"p2","name":names[1],"piece":2}],
        "turn_index": 0,
        "board": [[0 for _ in range(COLS)] for _ in range(ROWS)],
        "winner_id": None,
        "moves": 0,
        "request_receipts": [],
    }
    return _seal(state)

def validate(state: object) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["connect4_state_missing"]}
    errors=[]
    if state.get("schema") != SCHEMA:
        errors.append("connect4_schema_invalid")
    if state.get("status") not in {"active","completed","stopped"}:
        errors.append("connect4_status_invalid")
    board=state.get("board")
    if not isinstance(board,list) or len(board)!=ROWS or any(not isinstance(r,list) or len(r)!=COLS for r in board):
        errors.append("connect4_board_invalid")
    expected=copy.deepcopy(state); expected.pop("checkpoint",None)
    if state.get("checkpoint") != _digest(expected):
        errors.append("connect4_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}

def _validated_copy(state: object) -> dict[str, Any]:
    check=validate(state)
    if not check["passed"]:
        raise ValueError(check["errors"][0])
    return copy.deepcopy(state)

def _winner(board: list[list[int]], piece: int) -> bool:
    for r in range(ROWS):
        for c in range(COLS):
            if c <= COLS-4 and all(board[r][c+i]==piece for i in range(4)): return True
            if r <= ROWS-4 and all(board[r+i][c]==piece for i in range(4)): return True
            if r <= ROWS-4 and c <= COLS-4 and all(board[r+i][c+i]==piece for i in range(4)): return True
            if r <= ROWS-4 and c >= 3 and all(board[r+i][c-i]==piece for i in range(4)): return True
    return False

def public_state(state: dict[str, Any] | None) -> dict[str, Any]:
    if state is None:
        return {"started":False,"status":"idle"}
    check=validate(state)
    if not check["passed"]:
        raise ValueError(check["errors"][0])
    current=state["players"][state["turn_index"]]
    return {
        "started":True,
        "game_id":state["game_id"],
        "status":state["status"],
        "players":copy.deepcopy(state["players"]),
        "current_player_id":current["id"],
        "current_player_name":current["name"],
        "board":copy.deepcopy(state["board"]),
        "winner_id":state["winner_id"],
        "moves":state["moves"],
        "payments":False,
        "server_authoritative":True,
    }

def drop(state: object, *, column: object, request_id: object) -> dict[str, Any]:
    current=_validated_copy(state)
    req=_valid_request_id(request_id)
    if any(x["request_id"]==req for x in current["request_receipts"]):
        return current
    if current["status"]!="active":
        raise ValueError(f"connect4_game_{current['status']}")
    if not isinstance(column,int) or not 0 <= column < COLS:
        raise ValueError("connect4_column_invalid")
    row=None
    for r in range(ROWS-1,-1,-1):
        if current["board"][r][column]==0:
            row=r; break
    if row is None:
        raise ValueError("connect4_column_full")
    player=current["players"][current["turn_index"]]
    current["board"][row][column]=player["piece"]
    current["moves"]+=1
    current["request_receipts"].append({"request_id":req,"action":"drop","column":column})
    if _winner(current["board"],player["piece"]):
        current["status"]="completed"; current["winner_id"]=player["id"]
    elif current["moves"] == ROWS*COLS:
        current["status"]="completed"; current["winner_id"]=None
    else:
        current["turn_index"] = 1-current["turn_index"]
    return _seal(current)

def stop(state: object, *, request_id: object) -> dict[str, Any]:
    current=_validated_copy(state)
    req=_valid_request_id(request_id)
    if any(x["request_id"]==req for x in current["request_receipts"]):
        return current
    if current["status"]!="active":
        raise ValueError("connect4_stop_denied")
    current["status"]="stopped"
    current["request_receipts"].append({"request_id":req,"action":"stop"})
    return _seal(current)
