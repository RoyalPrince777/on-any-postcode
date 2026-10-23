"""Short-lived, pair-authorized WebRTC negotiation. Never stores media."""
from __future__ import annotations

import json
import uuid
from . import postgres_db, ptt_guest

KINDS = frozenset({"offer", "answer", "candidate", "hangup"})
MAX_PAYLOAD_BYTES = 16384


def _peer(identity: str) -> str:
    pair = ptt_guest.active_pair(identity)
    if not pair or not pair.get("peer_id"):
        raise ValueError("ptt_pair_required")
    return str(pair["peer_id"])


def send(identity: str, kind: str, payload: object) -> str:
    peer = _peer(identity)
    if kind not in KINDS or not isinstance(payload, dict):
        raise ValueError("invalid_signal")
    encoded = json.dumps(payload, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("signal_too_large")
    signal_id = str(uuid.uuid4())
    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO oap_ptt_signals(signal_id,sender_id,recipient_id,kind,payload)
               VALUES (%s,%s,%s,%s,%s::jsonb)""",
            (signal_id, identity, peer, kind, encoded),
        )
        connection.commit()
    return signal_id


def receive(identity: str) -> list[dict]:
    peer = _peer(identity)
    with postgres_db.connect() as connection:
        connection.execute("DELETE FROM oap_ptt_signals WHERE expires_at <= CURRENT_TIMESTAMP")
        rows = connection.execute(
            """DELETE FROM oap_ptt_signals
               WHERE signal_id IN (
                 SELECT signal_id FROM oap_ptt_signals
                 WHERE recipient_id=%s AND sender_id=%s
                   AND expires_at > CURRENT_TIMESTAMP
                 ORDER BY created_at,signal_id LIMIT 32
                 FOR UPDATE SKIP LOCKED
               )
               RETURNING signal_id,kind,payload""",
            (identity, peer),
        ).fetchall()
        connection.commit()
    return [{"id": str(row[0]), "kind": row[1], "payload": row[2]} for row in rows]
