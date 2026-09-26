"""Durable, privacy-minimised ALL IN A.I. mission lifecycle receipts.

Reuses the canonical Governance workspace, SMI HRM memory table and audit chain.
No new database or schema is introduced. Raw mission text is never persisted.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from . import postgres_db

_PREFIX = "OAP-ALL-IN-AI"
_ACTION = "OAP_ALL_IN_AI_MISSION_CHECKPOINT"
_ALLOWED_STATES = {"planned", "stopped", "recovered"}


class MissionStoreUnavailable(RuntimeError):
    """Raised when durable mission state cannot be proven safely."""


def _identity(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_mission_identity") from exc


def _mission_id(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_mission_id") from exc


def _digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _safe_plan_snapshot(plan: dict[str, Any]) -> dict[str, Any]:
    mission = plan["mission"]
    binding = plan["smi_binding"]
    route = binding["agi_route"]
    command = binding["command_review"]
    return {
        "task_type": str(mission["task_type"]),
        "high_impact": bool(mission["high_impact"]),
        "research_mode": str(mission["research_mode"]),
        "mission_length": int(mission["length"]),
        "world_ids": tuple(str(item) for item in route["world_ids"]),
        "specialist_ids": tuple(str(item) for item in route["specialist_ids"]),
        "command_path": tuple(str(item) for item in command["command_path"]),
        "war_room_next": bool(command["war_room_next"]),
        "judgement_next": bool(command["judgement_next"]),
        "prompt_retained": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def _latest_row(connection, identity: str, mission: str):
    prefix = f"{_PREFIX}:{mission}:v"
    return connection.execute(
        """SELECT record_id,body
           FROM oap_workspace_records
           WHERE identity_id=%s
             AND workspace_id='governance'
             AND title LIKE %s
           ORDER BY created_at DESC, record_id DESC
           LIMIT 1""",
        (identity, prefix + "%"),
    ).fetchone()


def _parse_entry(row) -> dict[str, Any]:
    if row is None:
        raise MissionStoreUnavailable("mission_receipt_not_found")
    try:
        entry = json.loads(str(row[1]))
    except (TypeError, ValueError) as exc:
        raise MissionStoreUnavailable("mission_receipt_unreadable") from exc
    if not isinstance(entry, dict):
        raise MissionStoreUnavailable("mission_receipt_invalid")
    payload = {key: value for key, value in entry.items() if key != "digest"}
    if entry.get("digest") != _digest(payload):
        raise MissionStoreUnavailable("mission_receipt_tampered")
    return entry


def _append(
    identity_id: object,
    *,
    mission_id: object,
    mission_hash: str,
    state: str,
    plan_snapshot: dict[str, Any],
    expected_previous_hash: str,
) -> dict[str, Any]:
    identity = _identity(identity_id)
    mission = _mission_id(mission_id)
    if state not in _ALLOWED_STATES:
        raise ValueError("invalid_mission_state")
    if (
        len(mission_hash) != 64
        or any(char not in "0123456789abcdef" for char in mission_hash)
    ):
        raise ValueError("invalid_mission_hash")

    try:
        with postgres_db.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (f"all-in-ai:{mission}",),
            )
            latest_row = _latest_row(connection, identity, mission)
            if latest_row is None:
                version = 1
                previous_hash = "GENESIS"
                required = ""
            else:
                latest = _parse_entry(latest_row)
                version = int(latest["version"]) + 1
                previous_hash = str(latest["digest"])
                required = previous_hash
            if expected_previous_hash != required:
                raise RuntimeError("stale_mission_version")

            payload = {
                "mission_id": mission,
                "version": version,
                "previous_hash": previous_hash,
                "mission_hash": mission_hash,
                "state": state,
                "plan": plan_snapshot,
                "stopped": state == "stopped",
                "recovered": state == "recovered",
                "resumable": True,
                "prompt_retained": False,
                "execution_granted": False,
                "approval_granted": False,
                "human_authority_final": True,
            }
            entry = {**payload, "digest": _digest(payload)}
            body = json.dumps(
                entry,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            title = f"{_PREFIX}:{mission}:v{version}"
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'governance',%s,%s,'draft')
                   RETURNING record_id""",
                (identity, title, body),
            ).fetchone()
            record_id = str(row[0])

            memory_request_id = str(uuid.uuid4())
            rationale = {
                "component": "ALL IN A.I. Mission Keeper",
                "mission_id": mission,
                "state": state,
                "world_ids": plan_snapshot["world_ids"],
                "specialist_ids": plan_snapshot["specialist_ids"],
                "command_path": plan_snapshot["command_path"],
                "prompt_retained": False,
                "execution_granted": False,
                "human_authority_final": True,
            }
            connection.execute(
                """INSERT INTO smi_memory_records(
                       request_id,identity_id,task_type,content_hash,summary,
                       output_state,signal_level,rationale_json,
                       processing_states_json
                   ) VALUES (
                       %s,%s,'ALL_IN_AI_MISSION',%s,%s,
                       'SYSTEM_LOG_ONLY','WHITE',%s::jsonb,%s::jsonb
                   )""",
                (
                    memory_request_id,
                    identity,
                    mission_hash,
                    f"ALL IN A.I. mission {state}; privacy-reduced receipt recorded.",
                    json.dumps(rationale, sort_keys=True),
                    json.dumps(
                        [
                            "ALL_IN_AI_MISSION_CHECKPOINT",
                            state.upper(),
                            "HRM_RECORDED",
                            "AUDIT_RECORDED",
                        ]
                    ),
                ),
            )

            connection.execute("SELECT pg_advisory_xact_lock(%s)", (73190517,))
            previous = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            audit_previous_hash = str(previous[0]) if previous else "GENESIS"
            metadata = {
                "workspace_id": "governance",
                "mission_id": mission,
                "version": version,
                "digest": entry["digest"],
                "record_id": record_id,
                "memory_request_id": memory_request_id,
                "state": state,
                "prompt_retained": False,
                "execution_granted": False,
                "approval_granted": False,
                "human_authority_final": True,
            }
            canonical = json.dumps(
                metadata,
                sort_keys=True,
                separators=(",", ":"),
            )
            current_hash = hashlib.sha256(
                (audit_previous_hash + canonical).encode("utf-8")
            ).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'HUMAN_AUTHORITY',0,%s,%s,%s,%s,%s::jsonb
                   )""",
                (
                    audit_previous_hash,
                    current_hash,
                    identity,
                    _ACTION,
                    f"all_in_ai_mission:{mission}",
                    f"privacy_reduced_all_in_ai_mission_{state}",
                    mission,
                    canonical,
                ),
            )
            connection.commit()
    except (ValueError, RuntimeError, MissionStoreUnavailable):
        raise
    except Exception as exc:
        raise MissionStoreUnavailable("mission_checkpoint_write_failed") from exc

    return read(identity, mission)


def create(
    identity_id: object,
    *,
    mission_id: object,
    mission_hash: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """Persist the initial planned state with HRM and audit receipts."""

    return _append(
        identity_id,
        mission_id=mission_id,
        mission_hash=mission_hash,
        state="planned",
        plan_snapshot=_safe_plan_snapshot(plan),
        expected_previous_hash="",
    )


def stop(
    identity_id: object,
    mission_id: object,
    *,
    expected_previous_hash: str,
) -> dict[str, Any]:
    """Append an idempotent STOP checkpoint without granting execution."""

    current = read(identity_id, mission_id)
    if current["state"] == "stopped":
        return current
    return _append(
        identity_id,
        mission_id=mission_id,
        mission_hash=str(current["mission_hash"]),
        state="stopped",
        plan_snapshot=dict(current["plan"]),
        expected_previous_hash=expected_previous_hash,
    )


def recover(
    identity_id: object,
    mission_id: object,
    *,
    expected_previous_hash: str,
) -> dict[str, Any]:
    """Recover a stopped mission to reviewable state; never resume execution."""

    current = read(identity_id, mission_id)
    if current["state"] != "stopped":
        raise RuntimeError("mission_not_stopped")
    return _append(
        identity_id,
        mission_id=mission_id,
        mission_hash=str(current["mission_hash"]),
        state="recovered",
        plan_snapshot=dict(current["plan"]),
        expected_previous_hash=expected_previous_hash,
    )


def read(identity_id: object, mission_id: object) -> dict[str, Any]:
    """Read and independently cross-check workspace, audit and HRM receipts."""

    identity = _identity(identity_id)
    mission = _mission_id(mission_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = _latest_row(connection, identity, mission)
            entry = _parse_entry(row)
            record_id = str(row[0])
            receipt = connection.execute(
                """SELECT metadata
                   FROM audit_events
                   WHERE actor_id=%s
                     AND action=%s
                     AND target=%s
                   ORDER BY event_seq DESC
                   LIMIT 1""",
                (identity, _ACTION, f"all_in_ai_mission:{mission}"),
            ).fetchone()
            if receipt is None:
                raise MissionStoreUnavailable("mission_audit_receipt_missing")
            metadata = receipt[0]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            if not isinstance(metadata, dict):
                raise MissionStoreUnavailable("mission_audit_receipt_invalid")
            if (
                str(metadata.get("record_id")) != record_id
                or metadata.get("digest") != entry["digest"]
                or int(metadata.get("version") or 0) != int(entry["version"])
            ):
                raise MissionStoreUnavailable("mission_audit_receipt_mismatch")

            memory_request_id = str(metadata.get("memory_request_id") or "")
            memory = connection.execute(
                """SELECT content_hash
                   FROM smi_memory_records
                   WHERE request_id=%s
                     AND identity_id=%s
                     AND task_type='ALL_IN_AI_MISSION'
                   LIMIT 1""",
                (memory_request_id, identity),
            ).fetchone()
            if memory is None or str(memory[0]) != str(entry["mission_hash"]):
                raise MissionStoreUnavailable("mission_hrm_receipt_mismatch")
    except MissionStoreUnavailable:
        raise
    except Exception as exc:
        raise MissionStoreUnavailable("mission_readback_failed") from exc

    return {
        **entry,
        "record_id": record_id,
        "memory_request_id": memory_request_id,
        "read_back_verified": True,
        "audit_verified": True,
        "hrm_verified": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    return {
        "component": "ALL IN A.I. Durable Mission Store",
        "canonical_workspace_reused": "governance",
        "canonical_hrm_reused": True,
        "canonical_audit_chain_reused": True,
        "new_database_created": False,
        "schema_migration_required": False,
        "raw_mission_retained": False,
        "stop_supported": True,
        "recovery_supported": True,
        "read_back_required": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }
