"""Bounded two-player OAP Arena Competition Engine.

This layer reuses the canonical Arena challenge catalogue and proves governed
two-player match state, idempotent answers, STOP, signed checkpoints and
hash-chained receipts. It deliberately does not claim durable profiles,
rankings, prizes, payments or public deployment.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from mission_control import arena_intelligence

MATCH_SCHEMA = "oap.arena.match.v1"
MAX_REQUEST_RECEIPTS = 64
PLAYER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _valid_player_id(value: object) -> str:
    player_id = str(value or "").strip()
    if not PLAYER_ID_PATTERN.fullmatch(player_id):
        raise ValueError("arena_player_id_invalid")
    return player_id


def _valid_request_id(value: object) -> str:
    request_id = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(request_id):
        raise ValueError("invalid_request_id")
    return request_id


def _unsealed(state: Mapping[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in state.items() if key != "checkpoint"}


def _seal(state: Mapping[str, Any]) -> dict[str, Any]:
    result = _unsealed(state)
    result["checkpoint"] = _digest(result)
    return result


def _receipt(previous_hash: str, action: str, detail: Mapping[str, Any]) -> dict[str, Any]:
    record = {
        "id": str(uuid.uuid4()),
        "at": datetime.now(UTC).isoformat(),
        "action": action,
        "detail": dict(detail),
        "previous_hash": previous_hash,
    }
    return {**record, "hash": _digest(record)}


def _append_receipt(state: dict[str, Any], action: str, detail: Mapping[str, Any]) -> None:
    receipts = state.setdefault("receipts", [])
    previous_hash = str(receipts[-1]["hash"]) if receipts else "GENESIS"
    receipts.append(_receipt(previous_hash, action, detail))


def _request_record(state: dict[str, Any], record: Mapping[str, Any]) -> None:
    records = state.setdefault("request_receipts", [])
    records.append(dict(record))
    del records[:-MAX_REQUEST_RECEIPTS]


def _request_result(state: Mapping[str, Any], request_id: str) -> dict[str, Any] | None:
    for item in reversed(tuple(state.get("request_receipts") or ())):
        if item.get("request_id") == request_id:
            return dict(item)
    return None


def verify_receipt_chain(state: Mapping[str, Any]) -> bool:
    previous_hash = "GENESIS"
    for item in tuple(state.get("receipts") or ()):
        record = {key: value for key, value in item.items() if key != "hash"}
        if record.get("previous_hash") != previous_hash:
            return False
        if item.get("hash") != _digest(record):
            return False
        previous_hash = str(item["hash"])
    return True


def validate_match(state: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["arena_match_missing"]}
    if state.get("schema") != MATCH_SCHEMA:
        errors.append("arena_match_schema_invalid")
    if state.get("status") not in {"waiting", "active", "stopped", "completed"}:
        errors.append("arena_match_status_invalid")

    players = state.get("players")
    if not isinstance(players, list) or not 1 <= len(players) <= 2:
        errors.append("arena_match_players_invalid")
        players = []
    ids = [item.get("player_id") for item in players if isinstance(item, dict)]
    if len(ids) != len(set(ids)) or any(not isinstance(item, str) for item in ids):
        errors.append("arena_match_players_invalid")

    index = state.get("question_index")
    if not isinstance(index, int) or not 0 <= index <= len(arena_intelligence.CHALLENGE_CATALOG):
        errors.append("arena_match_question_index_invalid")

    answers = state.get("answers")
    if not isinstance(answers, dict):
        errors.append("arena_match_answers_invalid")
        answers = {}

    scores = state.get("scores")
    if not isinstance(scores, dict):
        errors.append("arena_match_scores_invalid")
        scores = {}
    else:
        for player_id in ids:
            value = scores.get(player_id)
            if not isinstance(value, int) or not 0 <= value <= len(arena_intelligence.CHALLENGE_CATALOG):
                errors.append("arena_match_scores_invalid")
                break

    if state.get("status") == "waiting" and len(players) != 1:
        errors.append("arena_match_waiting_invalid")
    if state.get("status") in {"active", "completed"} and len(players) != 2:
        errors.append("arena_match_active_players_invalid")
    if state.get("status") == "completed" and index != len(arena_intelligence.CHALLENGE_CATALOG):
        errors.append("arena_match_completion_invalid")

    for qid, by_player in answers.items():
        try:
            arena_intelligence._question(str(qid))
        except ValueError:
            errors.append("arena_match_question_unknown")
            break
        if not isinstance(by_player, dict):
            errors.append("arena_match_answers_invalid")
            break
        if any(player_id not in ids for player_id in by_player):
            errors.append("arena_match_answer_owner_invalid")
            break

    if len(tuple(state.get("request_receipts") or ())) > MAX_REQUEST_RECEIPTS:
        errors.append("arena_match_request_receipts_unbounded")
    if not verify_receipt_chain(state):
        errors.append("arena_match_receipt_chain_invalid")
    if state.get("checkpoint") != _digest(_unsealed(state)):
        errors.append("arena_match_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}


def _validated_copy(state: object) -> dict[str, Any]:
    validation = validate_match(state)
    if not validation["passed"]:
        raise ValueError(str(validation["errors"][0]))
    return copy.deepcopy(state)


def create_match(*, creator_id: object) -> dict[str, Any]:
    player_id = _valid_player_id(creator_id)
    state: dict[str, Any] = {
        "schema": MATCH_SCHEMA,
        "match_id": str(uuid.uuid4()),
        "status": "waiting",
        "players": [{"player_id": player_id, "seat": 1}],
        "question_index": 0,
        "answers": {},
        "scores": {player_id: 0},
        "request_receipts": [],
        "receipts": [],
        "result": None,
        "ranked": False,
        "durable": False,
    }
    _append_receipt(state, "match_created", {"creator_id": player_id})
    return _seal(state)


def join_match(
    state: object,
    *,
    player_id: object,
    request_id: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = _validated_copy(state)
    request_key = _valid_request_id(request_id)
    previous = _request_result(current, request_key)
    if previous is not None:
        return current, public_match(current, duplicate=True)

    joining = _valid_player_id(player_id)
    if current["status"] != "waiting":
        raise ValueError("arena_match_not_joinable")
    if joining in {item["player_id"] for item in current["players"]}:
        raise ValueError("arena_match_duplicate_player")

    current["players"].append({"player_id": joining, "seat": 2})
    current["scores"][joining] = 0
    current["status"] = "active"
    record = {"request_id": request_key, "kind": "join", "player_id": joining}
    _request_record(current, record)
    _append_receipt(current, "player_joined", {"player_id": joining})
    sealed = _seal(current)
    return sealed, public_match(sealed)


def _current_question(state: Mapping[str, Any]) -> Mapping[str, Any] | None:
    index = int(state["question_index"])
    if index >= len(arena_intelligence.CHALLENGE_CATALOG):
        return None
    return arena_intelligence.CHALLENGE_CATALOG[index]


def submit_answer(
    state: object,
    *,
    player_id: object,
    question_id: object,
    choice_id: object,
    request_id: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = _validated_copy(state)
    request_key = _valid_request_id(request_id)
    previous = _request_result(current, request_key)
    if previous is not None:
        return current, public_match(current, duplicate=True)

    if current["status"] != "active":
        raise ValueError(f"arena_match_{current['status']}")
    player = _valid_player_id(player_id)
    if player not in {item["player_id"] for item in current["players"]}:
        raise ValueError("arena_match_player_not_member")

    question = _current_question(current)
    if question is None:
        raise ValueError("arena_match_completed")
    if str(question_id or "") != question["id"]:
        raise ValueError("arena_question_mismatch")

    selected = str(choice_id or "")
    choices = {item["id"] for item in question["choices"]}
    if selected not in choices:
        raise ValueError("arena_choice_invalid")

    question_answers = current["answers"].setdefault(question["id"], {})
    if player in question_answers:
        raise ValueError("arena_match_player_already_answered")

    correct = selected == question["correct_choice_id"]
    question_answers[player] = {
        "choice_id": selected,
        "correct": correct,
    }
    record = {
        "request_id": request_key,
        "kind": "answer",
        "player_id": player,
        "question_id": question["id"],
        "correct": correct,
    }
    _request_record(current, record)
    _append_receipt(
        current,
        "match_answer_recorded",
        {
            "player_id": player,
            "question_id": question["id"],
            "request_id": request_key,
        },
    )

    if len(question_answers) == 2:
        for pid, answer_record in question_answers.items():
            if answer_record["correct"]:
                current["scores"][pid] += 1
        current["question_index"] += 1
        _append_receipt(
            current,
            "round_closed",
            {"question_id": question["id"], "round": current["question_index"]},
        )
        if current["question_index"] == len(arena_intelligence.CHALLENGE_CATALOG):
            current["status"] = "completed"
            ordered = sorted(
                current["scores"].items(),
                key=lambda item: (-item[1], item[0]),
            )
            top_score = ordered[0][1]
            winners = [pid for pid, score in ordered if score == top_score]
            current["result"] = {
                "scores": dict(current["scores"]),
                "winner_ids": winners,
                "tie": len(winners) > 1,
            }
            _append_receipt(
                current,
                "match_completed",
                {"winner_ids": winners, "tie": len(winners) > 1},
            )

    sealed = _seal(current)
    return sealed, public_match(sealed)


def stop_match(
    state: object,
    *,
    actor_id: object,
    request_id: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = _validated_copy(state)
    request_key = _valid_request_id(request_id)
    previous = _request_result(current, request_key)
    if previous is not None:
        return current, public_match(current, duplicate=True)

    actor = _valid_player_id(actor_id)
    if actor not in {item["player_id"] for item in current["players"]}:
        raise ValueError("arena_match_player_not_member")
    if current["status"] not in {"waiting", "active"}:
        raise ValueError("arena_match_stop_denied")

    current["status"] = "stopped"
    record = {"request_id": request_key, "kind": "stop", "actor_id": actor}
    _request_record(current, record)
    _append_receipt(current, "match_stopped", {"actor_id": actor})
    sealed = _seal(current)
    return sealed, public_match(sealed)


def public_match(
    state: Mapping[str, Any],
    *,
    duplicate: bool = False,
) -> dict[str, Any]:
    validation = validate_match(dict(state))
    if not validation["passed"]:
        raise ValueError(str(validation["errors"][0]))

    question = _current_question(state) if state["status"] == "active" else None
    public_question = None
    if question is not None:
        public_question = {
            "id": question["id"],
            "category": question["category"],
            "prompt": question["prompt"],
            "choices": tuple(dict(item) for item in question["choices"]),
            "number": int(state["question_index"]) + 1,
        }

    current_answers = {}
    if question is not None:
        current_answers = state["answers"].get(question["id"], {})

    receipts = tuple(state.get("receipts") or ())
    return {
        "match_id": state["match_id"],
        "status": state["status"],
        "players": tuple(dict(item) for item in state["players"]),
        "scores": dict(state["scores"]),
        "question_index": state["question_index"],
        "total_questions": len(arena_intelligence.CHALLENGE_CATALOG),
        "question": public_question,
        "answered_player_ids": tuple(sorted(current_answers)),
        "result": copy.deepcopy(state.get("result")),
        "duplicate": duplicate,
        "ranked": False,
        "durable": False,
        "payments": False,
        "prizes": False,
        "receipt_count": len(receipts),
        "latest_receipt_hash": receipts[-1]["hash"] if receipts else None,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    return {
        "id": "oap-arena-competition",
        "mode": "two_player_non_ranked_isolated_engine",
        "two_player_match_state": True,
        "server_authoritative_scoring": True,
        "idempotent_requests": True,
        "stop_enabled": True,
        "audit_receipts": True,
        "checkpoint_recovery": True,
        "durable_profiles": False,
        "rankings": False,
        "payments": False,
        "prizes": False,
        "public_routes": False,
        "deployed": False,
        "no_fake_green": True,
    }
