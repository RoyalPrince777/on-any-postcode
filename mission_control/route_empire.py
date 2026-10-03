"""First-party OAP Route Empire v1 game engine.

Session-scoped, server-authoritative and payment-free. The v1 board is a
synthetic local board keyed by a player-selected place label; it does not claim
live map accuracy or expose precise location.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from typing import Any

SCHEMA = "oap.arena.route-empire.v1"
SESSION_KEY = "oap_route_empire_v1"
MAX_PLAYERS = 4
MIN_PLAYERS = 2
START_POINTS = 12
WIN_INFLUENCE = 12
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

NODE_BLUEPRINT = (
    ("north", "North Quarter"),
    ("market", "Market Quarter"),
    ("east", "East Quarter"),
    ("green", "Green Quarter"),
    ("south", "South Quarter"),
    ("station", "Station Quarter"),
    ("west", "West Quarter"),
    ("centre", "Central Quarter"),
)
EDGE_BLUEPRINT = (
    ("north", "market"), ("market", "east"), ("east", "green"),
    ("green", "south"), ("south", "station"), ("station", "west"),
    ("west", "north"), ("market", "centre"), ("green", "centre"),
    ("station", "centre"), ("north", "centre"),
)

def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()

def _seal(state: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(state)
    result.pop("checkpoint", None)
    result["checkpoint"] = _digest(result)
    return result

def _request_id(value: object) -> str:
    result = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(result):
        raise ValueError("route_empire_request_id_invalid")
    return result

def _clean_label(value: object, *, code: str, maximum: int = 60) -> str:
    result = " ".join(str(value or "").split())
    if not result or len(result) > maximum:
        raise ValueError(code)
    return result

def _player_id(name: str, index: int) -> str:
    return f"p{index + 1}-{hashlib.sha256(name.encode('utf-8')).hexdigest()[:8]}"

def new_game(*, location: object, players: object) -> dict[str, Any]:
    location_label = _clean_label(location, code="route_empire_location_invalid", maximum=80)
    if not isinstance(players, list) or not MIN_PLAYERS <= len(players) <= MAX_PLAYERS:
        raise ValueError("route_empire_player_count_invalid")
    names = [_clean_label(name, code="route_empire_player_name_invalid", maximum=40) for name in players]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("route_empire_player_names_duplicate")
    player_rows = [
        {"id": _player_id(name, i), "name": name, "points": START_POINTS, "influence": 0}
        for i, name in enumerate(names)
    ]
    nodes = [
        {"id": node_id, "label": label, "owner_id": None, "level": 0}
        for node_id, label in NODE_BLUEPRINT
    ]
    state = {
        "schema": SCHEMA,
        "game_id": str(uuid.uuid4()),
        "status": "active",
        "location_label": location_label,
        "board_source": "synthetic_local_v1",
        "precise_location_used": False,
        "players": player_rows,
        "turn_index": 0,
        "round": 1,
        "nodes": nodes,
        "routes": [],
        "edges": [list(edge) for edge in EDGE_BLUEPRINT],
        "request_receipts": [],
        "winner_id": None,
    }
    return _seal(state)

def validate(state: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["route_empire_state_missing"]}
    if state.get("schema") != SCHEMA:
        errors.append("route_empire_schema_invalid")
    players = state.get("players")
    if not isinstance(players, list) or not MIN_PLAYERS <= len(players) <= MAX_PLAYERS:
        errors.append("route_empire_players_invalid")
    if state.get("status") not in {"active", "stopped", "completed"}:
        errors.append("route_empire_status_invalid")
    idx = state.get("turn_index")
    if not isinstance(idx, int) or not isinstance(players, list) or not 0 <= idx < max(1, len(players)):
        errors.append("route_empire_turn_invalid")
    nodes = state.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != len(NODE_BLUEPRINT):
        errors.append("route_empire_nodes_invalid")
    expected = copy.deepcopy(state)
    expected.pop("checkpoint", None)
    if state.get("checkpoint") != _digest(expected):
        errors.append("route_empire_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}

def _current_player(state: dict[str, Any]) -> dict[str, Any]:
    return state["players"][state["turn_index"]]

def public_state(state: dict[str, Any] | None) -> dict[str, Any]:
    if state is None:
        return {"started": False, "status": "idle"}
    checked = validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    current = _current_player(state)
    return {
        "started": True,
        "game_id": state["game_id"],
        "status": state["status"],
        "location_label": state["location_label"],
        "board_source": state["board_source"],
        "precise_location_used": False,
        "players": copy.deepcopy(state["players"]),
        "current_player_id": current["id"],
        "current_player_name": current["name"],
        "round": state["round"],
        "nodes": copy.deepcopy(state["nodes"]),
        "routes": copy.deepcopy(state["routes"]),
        "edges": copy.deepcopy(state["edges"]),
        "winner_id": state["winner_id"],
        "winner_name": next((p["name"] for p in state["players"] if p["id"] == state["winner_id"]), None),
        "payments": False,
        "real_property_rights": False,
        "human_authority_final": True,
    }

def _validated_copy(state: object) -> dict[str, Any]:
    checked = validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    return copy.deepcopy(state)

def _dedupe(state: dict[str, Any], request_id: str) -> bool:
    return any(item.get("request_id") == request_id for item in state["request_receipts"])

def _record(state: dict[str, Any], request_id: str, action: str) -> None:
    state["request_receipts"].append({"request_id": request_id, "action": action})
    del state["request_receipts"][:-32]

def _node(state: dict[str, Any], node_id: object) -> dict[str, Any]:
    key = str(node_id or "")
    for node in state["nodes"]:
        if node["id"] == key:
            return node
    raise ValueError("route_empire_node_invalid")

def _charge(player: dict[str, Any], amount: int) -> None:
    if player["points"] < amount:
        raise ValueError("route_empire_points_insufficient")
    player["points"] -= amount

def _check_win(state: dict[str, Any]) -> None:
    for player in state["players"]:
        if player["influence"] >= WIN_INFLUENCE:
            state["winner_id"] = player["id"]
            state["status"] = "completed"
            return
    if all(node["owner_id"] for node in state["nodes"]):
        ranked = sorted(state["players"], key=lambda p: (p["influence"], p["points"]), reverse=True)
        if len(ranked) == 1 or (ranked[0]["influence"], ranked[0]["points"]) != (ranked[1]["influence"], ranked[1]["points"]):
            state["winner_id"] = ranked[0]["id"]
            state["status"] = "completed"

def action(state: object, *, action: object, request_id: object, node_id: object = None, target_node_id: object = None) -> dict[str, Any]:
    current = _validated_copy(state)
    req = _request_id(request_id)
    if _dedupe(current, req):
        return current
    if current["status"] != "active":
        raise ValueError(f"route_empire_game_{current['status']}")
    player = _current_player(current)
    command = str(action or "").strip()

    if command == "claim":
        node = _node(current, node_id)
        if node["owner_id"] is not None:
            raise ValueError("route_empire_node_claimed")
        _charge(player, 2)
        node["owner_id"] = player["id"]
        node["level"] = 1
        player["influence"] += 2
    elif command == "develop":
        node = _node(current, node_id)
        if node["owner_id"] != player["id"]:
            raise ValueError("route_empire_develop_not_owner")
        if node["level"] >= 3:
            raise ValueError("route_empire_develop_max")
        _charge(player, 2)
        node["level"] += 1
        player["influence"] += 1
    elif command == "route":
        source = _node(current, node_id)
        target = _node(current, target_node_id)
        edge = {source["id"], target["id"]}
        if source["owner_id"] != player["id"] or target["owner_id"] != player["id"]:
            raise ValueError("route_empire_route_not_owner")
        if [source["id"], target["id"]] not in current["edges"] and [target["id"], source["id"]] not in current["edges"]:
            raise ValueError("route_empire_route_not_adjacent")
        if any({r["from"], r["to"]} == edge for r in current["routes"]):
            raise ValueError("route_empire_route_exists")
        _charge(player, 1)
        current["routes"].append({"from": source["id"], "to": target["id"], "owner_id": player["id"]})
        player["influence"] += 1
    elif command == "end_turn":
        current["turn_index"] = (current["turn_index"] + 1) % len(current["players"])
        if current["turn_index"] == 0:
            current["round"] += 1
            for row in current["players"]:
                row["points"] += 2
    elif command == "stop":
        current["status"] = "stopped"
    else:
        raise ValueError("route_empire_action_invalid")

    _record(current, req, command)
    _check_win(current)
    return _seal(current)
