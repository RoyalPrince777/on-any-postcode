"""Global OAP Arena progression, league, dispute and spectator intelligence.

This module is deliberately non-financial. It coordinates proven Arena results
into divisions and geographic championship progression while disputes and STOP
fail closed. Spectator state is a read-only projection of authoritative results.
"""
from __future__ import annotations

import copy
import hashlib
import json
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

LEVELS = ("POSTCODE", "BOROUGH_REGION", "COUNTRY", "CONTINENT", "GLOBAL")
DIVISIONS = ("OPEN", "BRONZE", "SILVER", "GOLD", "ELITE")
DISPUTE_STATES = ("OPEN", "UNDER_REVIEW", "UPHELD", "REJECTED", "RESOLVED")
GLOBAL_SCHEMA = "oap.arena.global.v1"


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _receipt_hash(value: object) -> str:
    receipt = str(value or "").strip().lower()
    if len(receipt) != 64 or any(ch not in "0123456789abcdef" for ch in receipt):
        raise ValueError("arena_receipt_hash_invalid")
    return receipt


def _seal(state: Mapping[str, Any]) -> dict[str, Any]:
    result = {k: copy.deepcopy(v) for k, v in state.items() if k != "checkpoint"}
    result["checkpoint"] = _digest(result)
    return result


def _append_receipt(state: dict[str, Any], action: str, detail: Mapping[str, Any]) -> None:
    receipts = state.setdefault("receipts", [])
    previous = receipts[-1]["hash"] if receipts else "GENESIS"
    record = {
        "id": str(uuid.uuid4()),
        "at": datetime.now(UTC).isoformat(),
        "action": action,
        "detail": dict(detail),
        "previous_hash": previous,
    }
    receipts.append({**record, "hash": _digest(record)})


def verify_receipts(state: Mapping[str, Any]) -> bool:
    previous = "GENESIS"
    for item in state.get("receipts", []):
        record = {k: v for k, v in item.items() if k != "hash"}
        if record.get("previous_hash") != previous or item.get("hash") != _digest(record):
            return False
        previous = item["hash"]
    return True


def create_league(*, name: object, level: object, participant_ids: Sequence[object]) -> dict[str, Any]:
    label = " ".join(str(name or "").split())[:120]
    level_name = str(level or "").strip().upper()
    if not label:
        raise ValueError("arena_league_name_required")
    if level_name not in LEVELS:
        raise ValueError("arena_league_level_invalid")
    participants = tuple(_uuid(x, "arena_participant_invalid") for x in participant_ids)
    if not 2 <= len(participants) <= 64:
        raise ValueError("arena_league_participant_count_invalid")
    if len(set(participants)) != len(participants):
        raise ValueError("arena_league_duplicate_participant")
    standings = {
        participant: {"played": 0, "wins": 0, "draws": 0, "losses": 0, "points": 0}
        for participant in participants
    }
    state = {
        "schema": GLOBAL_SCHEMA,
        "league_id": str(uuid.uuid4()),
        "name": label,
        "level": level_name,
        "division": "OPEN",
        "status": "ACTIVE",
        "participants": participants,
        "standings": standings,
        "results": [],
        "disputes": [],
        "receipts": [],
        "payments": False,
        "prizes": False,
        "external_distribution": False,
    }
    _append_receipt(state, "league_created", {"level": level_name, "participants": len(participants)})
    return _seal(state)


def validate(state: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["arena_global_missing"]}
    if state.get("schema") != GLOBAL_SCHEMA:
        errors.append("arena_global_schema_invalid")
    if state.get("level") not in LEVELS:
        errors.append("arena_global_level_invalid")
    if state.get("division") not in DIVISIONS:
        errors.append("arena_global_division_invalid")
    if state.get("status") not in {"ACTIVE", "HELD", "COMPLETED", "STOPPED"}:
        errors.append("arena_global_status_invalid")
    if any(state.get(key) is not False for key in ("payments", "prizes", "external_distribution")):
        errors.append("arena_global_boundary_invalid")
    if not verify_receipts(state):
        errors.append("arena_global_receipt_chain_invalid")
    raw = {k: copy.deepcopy(v) for k, v in state.items() if k != "checkpoint"}
    if state.get("checkpoint") != _digest(raw):
        errors.append("arena_global_checkpoint_invalid")
    return {"passed": not errors, "errors": errors}


def _copy(state: object) -> dict[str, Any]:
    checked = validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    return copy.deepcopy(state)


def record_result(
    state: object,
    *,
    player_a_id: object,
    player_b_id: object,
    player_a_score: int,
    player_b_score: int,
    receipt_hash: object,
) -> dict[str, Any]:
    current = _copy(state)
    if current["status"] != "ACTIVE":
        raise ValueError("arena_league_not_active")
    a = _uuid(player_a_id, "arena_participant_invalid")
    b = _uuid(player_b_id, "arena_participant_invalid")
    participants = set(current["participants"])
    if a == b or {a, b} - participants:
        raise ValueError("arena_result_participant_invalid")
    if not isinstance(player_a_score, int) or not isinstance(player_b_score, int):
        raise TypeError("arena_score_invalid")
    if not 0 <= player_a_score <= 7 or not 0 <= player_b_score <= 7:
        raise ValueError("arena_score_invalid")
    receipt = _receipt_hash(receipt_hash)
    existing = next((r for r in current["results"] if r["receipt_hash"] == receipt), None)
    if existing:
        exact = (
            existing["player_a_id"], existing["player_b_id"],
            existing["player_a_score"], existing["player_b_score"]
        )
        if exact == (a, b, player_a_score, player_b_score):
            return current
        raise ValueError("arena_result_receipt_conflict")

    result = {
        "result_id": str(uuid.uuid4()),
        "player_a_id": a,
        "player_b_id": b,
        "player_a_score": player_a_score,
        "player_b_score": player_b_score,
        "receipt_hash": receipt,
        "disputed": False,
    }
    current["results"].append(result)
    sa = current["standings"][a]
    sb = current["standings"][b]
    sa["played"] += 1
    sb["played"] += 1
    if player_a_score > player_b_score:
        sa["wins"] += 1; sa["points"] += 3; sb["losses"] += 1
    elif player_b_score > player_a_score:
        sb["wins"] += 1; sb["points"] += 3; sa["losses"] += 1
    else:
        sa["draws"] += 1; sb["draws"] += 1; sa["points"] += 1; sb["points"] += 1
    _append_receipt(current, "league_result_recorded", {"result_id": result["result_id"], "receipt_hash": receipt})
    return _seal(current)


def open_dispute(state: object, *, result_id: object, raised_by: object, reason: object) -> dict[str, Any]:
    current = _copy(state)
    raiser = _uuid(raised_by, "arena_dispute_identity_invalid")
    text = " ".join(str(reason or "").split())[:500]
    if not text:
        raise ValueError("arena_dispute_reason_required")
    result = next((r for r in current["results"] if r["result_id"] == str(result_id)), None)
    if result is None:
        raise ValueError("arena_dispute_result_missing")
    if raiser not in {result["player_a_id"], result["player_b_id"]}:
        raise ValueError("arena_dispute_not_participant")
    if result["disputed"]:
        raise ValueError("arena_dispute_already_open")
    dispute = {
        "dispute_id": str(uuid.uuid4()),
        "result_id": result["result_id"],
        "raised_by": raiser,
        "reason": text,
        "state": "OPEN",
        "resolution": None,
    }
    current["disputes"].append(dispute)
    result["disputed"] = True
    current["status"] = "HELD"
    _append_receipt(current, "dispute_opened", {"dispute_id": dispute["dispute_id"], "result_id": result["result_id"]})
    return _seal(current)


def resolve_dispute(
    state: object,
    *,
    dispute_id: object,
    outcome: object,
    resolution: object,
) -> dict[str, Any]:
    current = _copy(state)
    decision = str(outcome or "").strip().upper()
    if decision not in {"UPHELD", "REJECTED"}:
        raise ValueError("arena_dispute_outcome_invalid")
    text = " ".join(str(resolution or "").split())[:500]
    if not text:
        raise ValueError("arena_dispute_resolution_required")
    dispute = next((d for d in current["disputes"] if d["dispute_id"] == str(dispute_id)), None)
    if dispute is None:
        raise ValueError("arena_dispute_missing")
    if dispute["state"] not in {"OPEN", "UNDER_REVIEW"}:
        raise ValueError("arena_dispute_already_resolved")
    dispute["state"] = decision
    dispute["resolution"] = text
    result = next(r for r in current["results"] if r["result_id"] == dispute["result_id"])
    result["disputed"] = False
    if not any(d["state"] in {"OPEN", "UNDER_REVIEW"} for d in current["disputes"]):
        current["status"] = "ACTIVE"
    _append_receipt(current, "dispute_resolved", {"dispute_id": dispute["dispute_id"], "outcome": decision})
    return _seal(current)


def set_division(state: object, *, division: object) -> dict[str, Any]:
    current = _copy(state)
    target = str(division or "").strip().upper()
    if target not in DIVISIONS:
        raise ValueError("arena_division_invalid")
    if current["status"] != "ACTIVE":
        raise ValueError("arena_division_change_denied")
    current["division"] = target
    _append_receipt(current, "division_set", {"division": target})
    return _seal(current)


def qualify_next_level(state: object, *, top_n: int = 1) -> dict[str, Any]:
    current = _copy(state)
    if current["status"] != "ACTIVE":
        raise ValueError("arena_qualification_held")
    if any(r["disputed"] for r in current["results"]):
        raise ValueError("arena_qualification_dispute_open")
    if current["level"] == "GLOBAL":
        raise ValueError("arena_already_global")
    bounded = max(1, min(int(top_n), len(current["participants"])))
    ordered = sorted(
        current["standings"].items(),
        key=lambda item: (-item[1]["points"], -item[1]["wins"], item[1]["played"], item[0]),
    )
    qualified = [player_id for player_id, _ in ordered[:bounded]]
    next_level = LEVELS[LEVELS.index(current["level"]) + 1]
    _append_receipt(current, "qualification_locked", {"next_level": next_level, "qualified": qualified})
    current["status"] = "COMPLETED"
    current["qualified"] = qualified
    current["next_level"] = next_level
    return _seal(current)


def stop(state: object, *, reason: object) -> dict[str, Any]:
    current = _copy(state)
    if current["status"] == "STOPPED":
        return current
    text = " ".join(str(reason or "").split())[:240]
    if not text:
        raise ValueError("arena_stop_reason_required")
    current["status"] = "STOPPED"
    _append_receipt(current, "league_stopped", {"reason": text})
    return _seal(current)


def spectator_view(state: Mapping[str, Any]) -> dict[str, Any]:
    checked = validate(dict(state))
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    ordered = sorted(
        state["standings"].items(),
        key=lambda item: (-item[1]["points"], -item[1]["wins"], item[1]["played"], item[0]),
    )
    return {
        "name": state["name"],
        "level": state["level"],
        "division": state["division"],
        "status": state["status"],
        "standings": tuple({"participant_id": pid, **stats} for pid, stats in ordered),
        "result_count": len(state["results"]),
        "open_disputes": sum(d["state"] in {"OPEN", "UNDER_REVIEW"} for d in state["disputes"]),
        "payments": False,
        "prizes": False,
        "external_distribution": False,
    }


def status() -> dict[str, Any]:
    return {
        "levels": LEVELS,
        "divisions": DIVISIONS,
        "leagues": True,
        "geographic_progression": True,
        "spectator_projection": True,
        "disputes": True,
        "moderation_hold": True,
        "payments": False,
        "prizes": False,
        "external_distribution": False,
        "deployed": False,
    }
