"""Authenticated, bounded first-party text chat for Connect 4 rooms only.

Requires explicit migrations/0011_oap_arena_connect4_chat.sql application.
Messages are accessible exclusively to holders of a valid seat reconnect token.
"""
from __future__ import annotations

from . import arena_rooms, postgres_db


def _seat(connection, room: str, token_hash: str) -> int:
    row = connection.execute(
        """SELECT p.seat FROM oap_arena_room_players p
           JOIN oap_arena_rooms r ON r.room_id=p.room_id
           WHERE p.room_id=%s AND p.reconnect_token_hash=%s
             AND r.game_key='connect4' AND r.status IN ('WAITING','ACTIVE')
           LIMIT 1""", (room, token_hash),
    ).fetchone()
    if row is None:
        raise ValueError("arena_chat_access_denied")
    return int(row[0])


def read(*, room_id: object, reconnect_token: object) -> dict:
    room = arena_rooms._room_id(room_id)
    token_hash = arena_rooms._token_hash(reconnect_token)
    try:
        with postgres_db.connect(readonly=True) as connection:
            seat = _seat(connection, room, token_hash)
            rows = connection.execute(
                """SELECT message_id,seat,message,created_at
                   FROM oap_arena_connect4_chat
                   WHERE room_id=%s ORDER BY message_id DESC LIMIT 50""", (room,),
            ).fetchall()
    except ValueError:
        raise
    except Exception as exc:
        raise arena_rooms.ArenaRoomUnavailable("arena_chat_read_unavailable") from exc
    return {
        "your_seat": seat,
        "messages": [
            {"id": int(r[0]), "seat": int(r[1]), "text": str(r[2]),
             "created_at": r[3].isoformat()}
            for r in reversed(rows)
        ],
    }


def send(*, room_id: object, reconnect_token: object, request_id: object,
         message: object) -> dict:
    room = arena_rooms._room_id(room_id)
    token_hash = arena_rooms._token_hash(reconnect_token)
    req = arena_rooms._request_id(request_id)
    if not isinstance(message, str):
        raise TypeError("arena_chat_message_invalid")
    text = message.strip()
    if not text or len(text) > 280 or any(ord(ch) < 32 and ch not in '\n\t' for ch in text):
        raise ValueError("arena_chat_message_invalid")
    try:
        with postgres_db.connect() as connection:
            # Serialise sends per room, including concurrent messages from the same seat.
            connection.execute("SELECT room_id FROM oap_arena_rooms WHERE room_id=%s FOR UPDATE", (room,))
            seat = _seat(connection, room, token_hash)
            replay = connection.execute(
                """SELECT message_id,message FROM oap_arena_connect4_chat
                   WHERE room_id=%s AND seat=%s AND request_id=%s""",
                (room, seat, req),
            ).fetchone()
            if replay:
                if replay[1] != text:
                    raise ValueError("arena_chat_idempotency_conflict")
                connection.commit()
                return {"id": int(replay[0]), "duplicate": True}
            recent = connection.execute(
                """SELECT 1 FROM oap_arena_connect4_chat
                   WHERE room_id=%s AND seat=%s
                     AND created_at > CURRENT_TIMESTAMP-INTERVAL '2 seconds'
                   LIMIT 1""", (room, seat),
            ).fetchone()
            if recent:
                raise ValueError("arena_chat_rate_limited")
            row = connection.execute(
                """INSERT INTO oap_arena_connect4_chat
                   (room_id,seat,request_id,message) VALUES (%s,%s,%s,%s)
                   RETURNING message_id""", (room, seat, req, text),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise arena_rooms.ArenaRoomUnavailable("arena_chat_send_unavailable") from exc
    return {"id": int(row[0]), "duplicate": False}
