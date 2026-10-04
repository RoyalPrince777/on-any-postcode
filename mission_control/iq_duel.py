"""Fair two-player IQ Arena duel wrapper.

Both seats answer the same bounded IQ Arena question before either score update
is revealed. This is a skills duel, never a clinical IQ test.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from typing import Any

from . import iq_arena

SCHEMA = "oap.arena.iq-duel.v1"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


def _canon(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _seal(state: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(state)
    result.pop("checkpoint", None)
    result["checkpoint"] = _digest(result)
    return result


def _req(value: object) -> str:
    result = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(result):
        raise ValueError("iq_duel_request_id_invalid")
    return result


def new_game(players: list[str]) -> dict[str, Any]:
    if not isinstance(players, list) or len(players) != 2:
        raise ValueError("iq_duel_player_count_invalid")
    names = [" ".join(str(name).split()) for name in players]
    if any(not name or len(name) > 40 for name in names) or names[0].casefold() == names[1].casefold():
        raise ValueError("iq_duel_players_invalid")
    return _seal({
        "schema": SCHEMA,
        "game_id": str(uuid.uuid4()),
        "status": "active",
        "players": [
            {"id": "p1", "name": names[0], "score": 0},
            {"id": "p2", "name": names[1], "score": 0},
        ],
        "question_index": 0,
        "pending_answers": {},
        "answered_count": 0,
        "winner_id": None,
        "draw": False,
        "request_receipts": [],
    })


def validate(state: object) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["iq_duel_state_missing"]}
    errors: list[str] = []
    if state.get("schema") != SCHEMA:
        errors.append("iq_duel_schema_invalid")
    if state.get("status") not in {"active", "completed", "stopped"}:
        errors.append("iq_duel_status_invalid")
    players = state.get("players")
    if not isinstance(players, list) or len(players) != 2:
        errors.append("iq_duel_players_invalid")
    index = state.get("question_index")
    if not isinstance(index, int) or not 0 <= index <= len(iq_arena.QUESTIONS):
        errors.append("iq_duel_question_invalid")
    expected = copy.deepcopy(state)
    expected.pop("checkpoint", None)
    if state.get("checkpoint") != _digest(expected):
        errors.append("iq_duel_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}


def _copy(state: object) -> dict[str, Any]:
    checked = validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    return copy.deepcopy(state)


def public_state(state: object, *, seat: int | None = None) -> dict[str, Any]:
    current = _copy(state)
    question = None
    if current["status"] == "active" and current["question_index"] < len(iq_arena.QUESTIONS):
        raw = iq_arena.QUESTIONS[current["question_index"]]
        question = {
            "id": raw["id"], "domain": raw["domain"], "prompt": raw["prompt"],
            "choices": copy.deepcopy(raw["choices"]), "number": current["question_index"] + 1,
        }
    answered_seats = sorted(int(value) for value in current["pending_answers"])
    return {
        "started": True,
        "status": current["status"],
        "players": copy.deepcopy(current["players"]),
        "question": question,
        "question_number": current["question_index"] + 1 if question else len(iq_arena.QUESTIONS),
        "total": len(iq_arena.QUESTIONS),
        "answered_count": current["answered_count"],
        "answered_seats": answered_seats,
        "your_answer_locked": bool(seat in answered_seats) if seat in {1, 2} else False,
        "winner_id": current["winner_id"],
        "draw": current["draw"],
        "skill_profile_only": True,
        "clinical_iq_score": False,
        "payments": False,
    }


def answer(state: object, *, seat: int, choice_id: object, request_id: object) -> dict[str, Any]:
    current = _copy(state)
    req = _req(request_id)
    if any(item["request_id"] == req for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError("iq_duel_not_active")
    if seat not in {1, 2}:
        raise ValueError("iq_duel_seat_invalid")
    seat_key = str(seat)
    if seat_key in current["pending_answers"]:
        raise ValueError("iq_duel_answer_already_locked")
    question = iq_arena.QUESTIONS[current["question_index"]]
    choice = str(choice_id or "")
    if choice not in {item["id"] for item in question["choices"]}:
        raise ValueError("iq_duel_choice_invalid")
    current["pending_answers"][seat_key] = choice
    current["request_receipts"].append({"request_id": req, "action": "answer", "seat": seat})
    if len(current["pending_answers"]) == 2:
        for player_seat in (1, 2):
            if current["pending_answers"][str(player_seat)] == question["answer"]:
                current["players"][player_seat - 1]["score"] += 1
        current["answered_count"] += 1
        current["pending_answers"] = {}
        current["question_index"] += 1
        if current["question_index"] >= len(iq_arena.QUESTIONS):
            current["status"] = "completed"
            first, second = current["players"][0]["score"], current["players"][1]["score"]
            current["draw"] = first == second
            current["winner_id"] = None if first == second else ("p1" if first > second else "p2")
    return _seal(current)


def stop(state: object, *, request_id: object) -> dict[str, Any]:
    current = _copy(state)
    req = _req(request_id)
    if any(item["request_id"] == req for item in current["request_receipts"]):
        return current
    if current["status"] != "active":
        raise ValueError("iq_duel_stop_denied")
    current["status"] = "stopped"
    current["pending_answers"] = {}
    current["request_receipts"].append({"request_id": req, "action": "stop"})
    return _seal(current)
