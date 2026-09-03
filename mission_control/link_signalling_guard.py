"""Current participant/relationship guard for Link signalling reads.

A queued negotiation event must never remain readable merely because its call
session is still active. Block and accepted-Link state are re-evaluated before
the signalling event table is touched.
"""
from __future__ import annotations

import uuid

from . import link_call_audit, link_relationships, linkup_safety, postgres_db


class LinkSignallingGuardUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def validate_read(identity_id: object, session_id: object) -> str:
    """Return the active peer only after current Block and Link checks pass."""

    identity = _uuid(identity_id, "invalid_identity")
    session = _uuid(session_id, "invalid_call_session")
    state = link_call_audit.status()
    if not state.get("ready"):
        raise LinkSignallingGuardUnavailable("link_call_audit_unavailable")

    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT initiator_id,recipient_id FROM link_call_sessions
                   WHERE session_id=%s AND state IN ('ringing','active')
                     AND expires_at>CURRENT_TIMESTAMP
                     AND (initiator_id=%s OR recipient_id=%s)
                   LIMIT 1""",
                (session, identity, identity),
            ).fetchone()
    except Exception as exc:
        raise LinkSignallingGuardUnavailable("link_call_session_check_failed") from exc

    if row is None:
        raise ValueError("active_call_session_required")
    initiator = str(row[0])
    recipient = str(row[1])
    peer = recipient if identity == initiator else initiator

    try:
        if linkup_safety.blocked_between(identity, peer):
            raise ValueError("link_blocked")
        if not link_relationships.accepted_between(identity, peer):
            raise ValueError("accepted_link_required")
    except ValueError:
        raise
    except (
        linkup_safety.LinkUpSafetyUnavailable,
        link_relationships.LinkRelationshipsUnavailable,
    ) as exc:
        raise LinkSignallingGuardUnavailable("link_relationship_guard_unavailable") from exc

    return peer
