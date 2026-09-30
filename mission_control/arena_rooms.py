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

from . import connect4, postgres_db

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
    if game == "connect4" and seats != 2:
        raise ValueError("arena_room_connect4_requires_two_seats")
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
                """SELECT seat FROM oap_arena_room_players
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
    if str(room_row[1]) == "connect4" and game_state:
        game_state = connect4.public_state(game_state)
    return {
        "room_id": room,
        "your_seat": int(authorized[0]),
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



def connect4_action(
    *,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    column: object = None,
) -> dict[str, Any]:
    """Commit a verified Connect 4 turn under a PostgreSQL room row lock.

    The caller supplies an action, never a board or score. Duplicate action IDs
    are accepted only when their complete binding matches the original request.
    """
    room = _room_id(room_id)
    token_hash = _token_hash(reconnect_token)
    req = _request_id(request_id)
    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 0:
        raise ValueError("arena_room_revision_invalid")
    verb = str(action or "")
    if verb not in {"drop", "stop"}:
        raise ValueError("arena_room_action_invalid")
    if verb == "drop" and (isinstance(column, bool) or not isinstance(column, int) or not 0 <= column < 7):
        raise ValueError("connect4_column_invalid")
    if verb == "stop" and column is not None:
        raise ValueError("arena_room_action_invalid")
    digest = hashlib.sha256(
        json.dumps(
            [room, token_hash, expected_revision, req, verb, column],
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()

    try:
        with postgres_db.connect() as connection:
            room_row = connection.execute(
                """SELECT game_key,status,capacity,revision,game_state
                   FROM oap_arena_rooms WHERE room_id=%s FOR UPDATE""",
                (room,),
            ).fetchone()
            if room_row is None:
                raise ValueError("arena_room_not_found")
            game_key, status, capacity, revision, stored = room_row
            if game_key != "connect4" or int(capacity) != 2:
                raise ValueError("arena_room_game_invalid")
            seat_row = connection.execute(
                """SELECT seat FROM oap_arena_room_players
                   WHERE room_id=%s AND reconnect_token_hash=%s LIMIT 1""",
                (room, token_hash),
            ).fetchone()
            if seat_row is None:
                raise ValueError("arena_room_access_denied")
            seat = int(seat_row[0])
            replay = connection.execute(
                """SELECT revision,action_hash FROM oap_arena_room_updates
                   WHERE room_id=%s AND request_id=%s LIMIT 1""",
                (room, req),
            ).fetchone()
            if replay is not None:
                if str(replay[1]) != digest:
                    raise ValueError("arena_room_idempotency_conflict")
                connection.commit()
                return {"room_id": room, "revision": int(replay[0]), "duplicate": True}
            if int(revision) != expected_revision:
                raise ValueError("arena_room_revision_conflict")
            if status != "ACTIVE":
                raise ValueError("arena_room_not_active")
            players = connection.execute(
                """SELECT seat,display_name FROM oap_arena_room_players
                   WHERE room_id=%s ORDER BY seat ASC""",
                (room,),
            ).fetchall()
            if len(players) != 2 or [int(p[0]) for p in players] != [1, 2]:
                raise ValueError("arena_room_players_invalid")
            if isinstance(stored, str):
                stored = json.loads(stored)
            game_state = stored or connect4.new_game(players[0][1], players[1][1])
            current = connect4.public_state(game_state)
            if verb == "drop":
                if current["current_player_id"] != f"p{seat}":
                    raise ValueError("arena_room_not_your_turn")
                next_state = connect4.drop(game_state, column=column, request_id=req)
            else:
                next_state = connect4.stop(game_state, request_id=req)
            next_view = connect4.public_state(next_state)
            next_status = (
                "COMPLETED" if next_view["status"] == "completed"
                else "STOPPED" if next_view["status"] == "stopped"
                else "ACTIVE"
            )
            new_revision = int(revision) + 1
            connection.execute(
                """UPDATE oap_arena_rooms
                   SET game_state=%s::jsonb,status=%s,revision=%s,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE room_id=%s AND revision=%s""",
                (json.dumps(next_state, sort_keys=True), next_status, new_revision, room, revision),
            )
            connection.execute(
                """INSERT INTO oap_arena_room_updates
                   (room_id,request_id,revision,action_hash)
                   VALUES (%s,%s,%s,%s)""",
                (room, req, new_revision, digest),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise ArenaRoomUnavailable("arena_room_connect4_action_failed") from exc
    return {
        "room_id": room, "revision": new_revision, "duplicate": False,
        "status": next_status, "game_state": next_view,
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
        "revision_conflict_guard": True,
        "connect4_server_actions": True,
        "arbitrary_client_game_state_writes": False,
        "chat": False,
        "payments": False,
        "explicit_migration_required": True,
        "deployed": False,
    }
