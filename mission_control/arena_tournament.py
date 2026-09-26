"""Bounded first-party OAP Arena team and tournament engine.

Four-team single-elimination brackets only. Results must be backed by a 64-char
competition receipt hash. No prizes, payments, public deployment or ranking
mutation are performed here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

TOURNAMENT_SCHEMA = "oap.arena.tournament.v1"
MAX_TEAM_MEMBERS = 4


def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


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
        raise ValueError("arena_result_receipt_invalid")
    return receipt


def create_team(*, name: object, member_ids: Sequence[object]) -> dict[str, Any]:
    label = " ".join(str(name or "").split())[:80]
    if not label:
        raise ValueError("arena_team_name_required")
    members = tuple(_uuid(item, "arena_team_member_invalid") for item in member_ids)
    if not 1 <= len(members) <= MAX_TEAM_MEMBERS:
        raise ValueError("arena_team_size_invalid")
    if len(set(members)) != len(members):
        raise ValueError("arena_team_duplicate_member")
    return {
        "team_id": str(uuid.uuid4()),
        "name": label,
        "member_ids": members,
    }


def _unsealed(state: Mapping[str, Any]) -> dict[str, Any]:
    return {k: copy.deepcopy(v) for k, v in state.items() if k != "checkpoint"}


def _seal(state: Mapping[str, Any]) -> dict[str, Any]:
    result = _unsealed(state)
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


def create_tournament(*, name: object, teams: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    label = " ".join(str(name or "").split())[:120]
    if not label:
        raise ValueError("arena_tournament_name_required")
    if len(teams) != 4:
        raise ValueError("arena_tournament_requires_four_teams")

    normalized = []
    all_members: list[str] = []
    team_ids: list[str] = []
    for team in teams:
        team_id = _uuid(team.get("team_id"), "arena_team_id_invalid")
        team_name = " ".join(str(team.get("name") or "").split())[:80]
        members = tuple(_uuid(x, "arena_team_member_invalid") for x in team.get("member_ids", ()))
        if not team_name or not 1 <= len(members) <= MAX_TEAM_MEMBERS:
            raise ValueError("arena_team_invalid")
        if len(set(members)) != len(members):
            raise ValueError("arena_team_duplicate_member")
        normalized.append({"team_id": team_id, "name": team_name, "member_ids": members})
        team_ids.append(team_id)
        all_members.extend(members)

    if len(set(team_ids)) != 4:
        raise ValueError("arena_tournament_duplicate_team")
    if len(set(all_members)) != len(all_members):
        raise ValueError("arena_tournament_member_on_multiple_teams")

    matches = [
        {"match_no": 1, "round": "SEMIFINAL", "team_a_id": team_ids[0], "team_b_id": team_ids[1], "winner_team_id": None, "receipt_hash": None},
        {"match_no": 2, "round": "SEMIFINAL", "team_a_id": team_ids[2], "team_b_id": team_ids[3], "winner_team_id": None, "receipt_hash": None},
        {"match_no": 3, "round": "FINAL", "team_a_id": None, "team_b_id": None, "winner_team_id": None, "receipt_hash": None},
    ]
    state = {
        "schema": TOURNAMENT_SCHEMA,
        "tournament_id": str(uuid.uuid4()),
        "name": label,
        "status": "ACTIVE",
        "teams": normalized,
        "matches": matches,
        "champion_team_id": None,
        "receipts": [],
        "payments": False,
        "prizes": False,
    }
    _append_receipt(state, "tournament_created", {"team_ids": team_ids})
    return _seal(state)


def validate_tournament(state: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return {"passed": False, "errors": ["arena_tournament_missing"]}
    if state.get("schema") != TOURNAMENT_SCHEMA:
        errors.append("arena_tournament_schema_invalid")
    if state.get("status") not in {"ACTIVE", "COMPLETED", "STOPPED"}:
        errors.append("arena_tournament_status_invalid")
    teams = state.get("teams")
    matches = state.get("matches")
    if not isinstance(teams, list) or len(teams) != 4:
        errors.append("arena_tournament_teams_invalid")
    if not isinstance(matches, list) or len(matches) != 3:
        errors.append("arena_tournament_matches_invalid")
    if not verify_receipts(state):
        errors.append("arena_tournament_receipt_chain_invalid")
    if state.get("checkpoint") != _digest(_unsealed(state)):
        errors.append("arena_tournament_checkpoint_invalid")
    if state.get("payments") is not False or state.get("prizes") is not False:
        errors.append("arena_tournament_money_boundary_invalid")
    return {"passed": not errors, "errors": errors}


def _copy(state: object) -> dict[str, Any]:
    check = validate_tournament(state)
    if not check["passed"]:
        raise ValueError(check["errors"][0])
    return copy.deepcopy(state)


def record_result(
    state: object,
    *,
    match_no: int,
    winner_team_id: object,
    receipt_hash: object,
) -> dict[str, Any]:
    current = _copy(state)
    if current["status"] != "ACTIVE":
        raise ValueError("arena_tournament_not_active")
    if match_no not in {1, 2, 3}:
        raise ValueError("arena_tournament_match_invalid")
    match = current["matches"][match_no - 1]
    if match["winner_team_id"] is not None:
        existing = (match["winner_team_id"], match["receipt_hash"])
        incoming = (_uuid(winner_team_id, "arena_team_id_invalid"), _receipt_hash(receipt_hash))
        if existing == incoming:
            return current
        raise ValueError("arena_tournament_result_conflict")

    winner = _uuid(winner_team_id, "arena_team_id_invalid")
    receipt = _receipt_hash(receipt_hash)
    allowed = {match["team_a_id"], match["team_b_id"]}
    if None in allowed:
        raise ValueError("arena_tournament_match_not_ready")
    if winner not in allowed:
        raise ValueError("arena_tournament_winner_not_participant")
    if any(item["receipt_hash"] == receipt for item in current["matches"] if item["receipt_hash"]):
        raise ValueError("arena_tournament_receipt_reused")

    match["winner_team_id"] = winner
    match["receipt_hash"] = receipt
    _append_receipt(current, "match_result_recorded", {"match_no": match_no, "winner_team_id": winner, "receipt_hash": receipt})

    if match_no in {1, 2}:
        semi1 = current["matches"][0]["winner_team_id"]
        semi2 = current["matches"][1]["winner_team_id"]
        if semi1 and semi2:
            current["matches"][2]["team_a_id"] = semi1
            current["matches"][2]["team_b_id"] = semi2
            _append_receipt(current, "final_ready", {"team_a_id": semi1, "team_b_id": semi2})
    else:
        current["champion_team_id"] = winner
        current["status"] = "COMPLETED"
        _append_receipt(current, "tournament_completed", {"champion_team_id": winner})

    return _seal(current)


def stop_tournament(state: object, *, reason: object) -> dict[str, Any]:
    current = _copy(state)
    if current["status"] != "ACTIVE":
        raise ValueError("arena_tournament_stop_denied")
    text = " ".join(str(reason or "").split())[:240]
    if not text:
        raise ValueError("arena_tournament_stop_reason_required")
    current["status"] = "STOPPED"
    _append_receipt(current, "tournament_stopped", {"reason": text})
    return _seal(current)


def public_state(state: Mapping[str, Any]) -> dict[str, Any]:
    check = validate_tournament(dict(state))
    if not check["passed"]:
        raise ValueError(check["errors"][0])
    return {
        "tournament_id": state["tournament_id"],
        "name": state["name"],
        "status": state["status"],
        "teams": tuple({"team_id": t["team_id"], "name": t["name"]} for t in state["teams"]),
        "matches": tuple(copy.deepcopy(state["matches"])),
        "champion_team_id": state["champion_team_id"],
        "payments": False,
        "prizes": False,
        "deployed": False,
    }
