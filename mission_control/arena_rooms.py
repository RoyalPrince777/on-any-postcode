"""Durable shared room foundation for first-party OAP Arena multiplayer.

Rooms provide invite codes, reconnect tokens and compare-and-swap game-state
updates. They do not provide chat, payments, prizes or matchmaking claims.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import uuid
from typing import Any

from . import postgres_db

SUPPORTED_GAMES = frozenset({"iq", "route-empire", "connect4", "ludo", "chess", "dot"})
ROOM_CODE_PATTERN = re.compile(r"^[A-Z2-9]{6}$")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class ArenaRoomUnavailable(RuntimeError):
    """Raised when durable room storage cannot complete safely."""


def _room_id(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("arena_room_id_invalid") from exc


def _name(value: object) -> str:
    result = " ".join(str(value or "").split())
    if not 1 <= len(result) <= 40:
        raise ValueError("arena_room_player_name_invalid")
    return result


def _capacity(value: object) -> int:
    if not isinstance(value, int) or not 2 <= value <= 4:
        raise ValueError("arena_room_capacity_invalid")
    return value


def _game(value: object) -> str:
    result = str(value or "").strip().lower()
    if result not in SUPPORTED_GAMES:
        raise ValueError("arena_room_game_invalid")
    return result


def _request_id(value: object) -> str:
    result = str(value or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(result):
        raise ValueError("arena_room_request_id_invalid")
    return result


def _token() -> str:
    return secrets.token_urlsafe(32)


def _token_hash(token: object) -> str:
    value = str(token or "")
    if len(value) < 32:
        raise ValueError("arena_room_reconnect_token_invalid")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _room_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(6))


def create_room(*, game_key: object, host_name: object, capacity: object = 2) -> dict[str, Any]:
    game = _game(game_key)
    name = _name(host_name)
    seats = _capacity(capacity)
    room_id = str(uuid.uuid4())
    player_id = str(uuid.uuid4())
    token = _token()
    token_hash = _token_hash(token)

    try:
        with postgres_db.connect() as connection:
            for _ in range(8):
                code = _room_code()
                inserted = connection.execute(
                    """INSERT INTO oap_arena_rooms
                       (room_id,room_code,game_key,status,capacity,revision,game_state)
                       VALUES (%s,%s,%s,'WAITING',%s,0,'{}'::jsonb)
                       ON CONFLICT (room_code) DO NOTHING
                       RETURNING room_code""",
                    (room_id, code, game, seats),
                ).fetchone()
                if inserted is not None:
                    break
            else:
                raise ArenaRoomUnavailable("arena_room_code_exhausted")

            connection.execute(
                """INSERT INTO oap_arena_room_players
                   (room_id,player_id,display_name,seat,reconnect_token_hash)
                   VALUES (%s,%s,%s,1,%s)""",
                (room_id, player_id, name, token_hash),
            )
            connection.commit()
    except ArenaRoomUnavailable:
        raise
    except Exception as exc:
        raise ArenaRoomUnavailable("arena_room_create_failed") from exc

    return {
        "room_id": room_id,
        "room_code": code,
        "player_id": player_id,
        "reconnect_token": token,
        "game_key": game,
        "capacity": seats,
        "status": "WAITING",
        "revision": 0,
    }


def join_room(*, room_code: object, display_name: object) -> dict[str, Any]:
    code = str(room_code or "").strip().upper()
    if not ROOM_CODE_PATTERN.fullmatch(code):
        raise ValueError("arena_room_code_invalid")
    name = _name(display_name)
    player_id = str(uuid.uuid4())
    token = _token()
    token_hash = _token_hash(token)

    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT room_id,game_key,status,capacity
                   FROM oap_arena_rooms
                   WHERE room_code=%s
                   FOR UPDATE""",
                (code,),
            ).fetchone()
            if row is None:
                raise ValueError("arena_room_not_found")
            room_id, game_key, status, capacity = row
            if status not in {"WAITING", "ACTIVE"}:
                raise ValueError("arena_room_join_closed")
            seat_row = connection.execute(
                """SELECT COALESCE(MAX(seat),0),COUNT(*)
                   FROM oap_arena_room_players
                   WHERE room_id=%s""",
                (room_id,),
            ).fetchone()
            next_seat = int(seat_row[0]) + 1
            count = int(seat_row[1])
            if count >= int(capacity) or next_seat > int(capacity):
                raise ValueError("arena_room_full")
            connection.execute(
                """INSERT INTO oap_arena_room_players
                   (room_id,player_id,display_name,seat,reconnect_token_hash)
                   VALUES (%s,%s,%s,%s,%s)""",
                (room_id, player_id, name, next_seat, token_hash),
            )
            if count + 1 >= 2:
                connection.execute(
                    """UPDATE oap_arena_rooms
                       SET status='ACTIVE',updated_at=CURRENT_TIMESTAMP
                       WHERE room_id=%s AND status='WAITING'""",
                    (room_id,),
                )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise ArenaRoomUnavailable("arena_room_join_failed") from exc

    return {
        "room_id": str(room_id),
        "room_code": code,
        "player_id": player_id,
        "reconnect_token": token,
        "game_key": str(game_key),
        "seat": next_seat,
    }


def room_state(*, room_id: object, reconnect_token: object) -> dict[str, Any]:
    room = _room_id(room_id)
    token_hash = _token_hash(reconnect_token)
    try:
        with postgres_db.connect(readonly=True) as connection:
            authorized = connection.execute(
                """SELECT 1 FROM oap_arena_room_players
                   WHERE room_id=%s AND reconnect_token_hash=%s
                   LIMIT 1""",
                (room, token_hash),
            ).fetchone()
            if authorized is None:
                raise ValueError("arena_room_access_denied")
            room_row = connection.execute(
                """SELECT room_code,game_key,status,capacity,revision,game_state
                   FROM oap_arena_rooms WHERE room_id=%s LIMIT 1""",
                (room,),
            ).fetchone()
            if room_row is None:
                raise ValueError("arena_room_not_found")
            players = connection.execute(
                """SELECT player_id,display_name,seat
                   FROM oap_arena_room_players
                   WHERE room_id=%s ORDER BY seat ASC""",
                (room,),
            ).fetchall()
    except ValueError:
        raise
    except Exception as exc:
        raise ArenaRoomUnavailable("arena_room_read_failed") from exc

    game_state = room_row[5]
    if isinstance(game_state, str):
        game_state = json.loads(game_state)
    return {
        "room_id": room,
        "room_code": str(room_row[0]),
        "game_key": str(room_row[1]),
        "status": str(room_row[2]),
        "capacity": int(room_row[3]),
        "revision": int(room_row[4]),
        "game_state": game_state or {},
        "players": [
            {"player_id": str(row[0]), "display_name": str(row[1]), "seat": int(row[2])}
            for row in players
        ],
        "chat": False,
        "payments": False,
    }


def update_game_state(*, room_id: object, reconnect_token: object, expected_revision: object,
                      game_state: object, request_id: object) -> dict[str, Any]:
    """Fail closed: multiplayer moves require a server-authoritative game adapter.

    Accepting client-supplied board JSON would allow forged results and turn skipping.
    """
    raise ValueError("arena_room_server_game_adapter_required")


def status() -> dict[str, bool]:
    return {
        "durable_rooms": True,
        "invite_codes": True,
        "reconnect_tokens": True,
        "revision_conflict_guard": False,
        "arbitrary_client_game_state_writes": False,
        "chat": False,
        "payments": False,
        "explicit_migration_required": True,
        "deployed": False,
    }
