"""Durable civilization facts emitted atomically by authoritative OAP organs.

This is an outbox, not an execution queue. Writing an event grants no downstream
authority. Consumers must independently validate their own authority and
idempotency before creating consequences.
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Mapping

SCHEMA_VERSION = "oap.civilization.event.v1"
MATCH_FINISHED = "MATCH_FINISHED"


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def append_match_finished(
    connection: Any,
    *,
    room_id: object,
    request_id: object,
    game_state: Mapping[str, Any],
    revision: int,
) -> str:
    """Append one Chess terminal fact using the caller's open transaction."""
    room = _uuid(room_id, "civilization_event_entity_invalid")
    cause = str(request_id or "").strip()
    if not cause:
        raise ValueError("civilization_event_causation_required")
    if not isinstance(revision, int) or revision <= 0:
        raise ValueError("civilization_event_revision_invalid")
    if str(game_state.get("status")) != "completed":
        raise ValueError("civilization_event_match_not_completed")

    event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"oap:arena:chess:{room}:MATCH_FINISHED"))
    payload = {
        "game": "chess",
        "room_id": room,
        "revision": revision,
        "result": game_state.get("result"),
        "winner": game_state.get("winner"),
        "checkpoint": game_state.get("checkpoint"),
    }
    connection.execute(
        """INSERT INTO oap_civilization_events(
               event_id,event_type,schema_version,source_organ,entity_type,
               entity_id,causation_id,correlation_id,payload,state
           ) VALUES (%s,%s,%s,'ARENA','CHESS_MATCH',%s,%s,%s,%s::jsonb,'PENDING')
           ON CONFLICT (source_organ,event_type,entity_id) DO NOTHING""",
        (
            event_id,
            MATCH_FINISHED,
            SCHEMA_VERSION,
            room,
            cause,
            room,
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
        ),
    )
    return event_id
