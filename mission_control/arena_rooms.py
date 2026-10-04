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

from . import chess, connect4, dot, iq_duel, ludo, oware, postgres_db, route_empire

SUPPORTED_GAMES = frozenset({"connect4", "dot", "chess", "ludo", "oware", "iq", "route-empire"})  # Only games with authoritative shared-room adapters.
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



def matchmake(*, game_key: object, display_name: object) -> dict[str, Any]:
    """Atomically join the oldest compatible waiting match or create one."""
    game = _game(game_key)
    name = _name(display_name)
    player_id = str(uuid.uuid4())
    token = _token()
    token_hash = _token_hash(token)

    try:
        with postgres_db.connect() as connection:
            waiting = connection.execute(
                """SELECT r.room_id,r.room_code
                   FROM oap_arena_rooms r
                   WHERE r.game_key=%s AND r.status='WAITING' AND r.capacity=2
                     AND NOT EXISTS (
                         SELECT 1 FROM oap_arena_room_players p
                         WHERE p.room_id=r.room_id
                           AND lower(p.display_name)=lower(%s)
                     )
                     AND (
                         SELECT COUNT(*) FROM oap_arena_room_players p
                         WHERE p.room_id=r.room_id
                     ) < 2
                   ORDER BY r.created_at ASC,r.room_id ASC
                   FOR UPDATE SKIP LOCKED
                   LIMIT 1""",
                (game, name),
            ).fetchone()

            if waiting is None:
                room_id = str(uuid.uuid4())
                for _ in range(8):
                    code = _room_code()
                    inserted = connection.execute(
                        """INSERT INTO oap_arena_rooms
                           (room_id,room_code,game_key,status,capacity,revision,game_state)
                           VALUES (%s,%s,%s,'WAITING',2,0,'{}'::jsonb)
                           ON CONFLICT (room_code) DO NOTHING
                           RETURNING room_code""",
                        (room_id, code, game),
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
                return {
                    "room_id": room_id,
                    "room_code": code,
                    "player_id": player_id,
                    "reconnect_token": token,
                    "game_key": game,
                    "seat": 1,
                    "status": "WAITING",
                    "matched": False,
                    "matchmaking": True,
                }

            room_id, code = waiting
            players = connection.execute(
                """SELECT seat,display_name FROM oap_arena_room_players
                   WHERE room_id=%s ORDER BY seat ASC
                   FOR UPDATE""",
                (room_id,),
            ).fetchall()
            if len(players) != 1 or int(players[0][0]) != 1:
                raise ArenaRoomUnavailable("arena_matchmaking_room_state_invalid")
            connection.execute(
                """INSERT INTO oap_arena_room_players
                   (room_id,player_id,display_name,seat,reconnect_token_hash)
                   VALUES (%s,%s,%s,2,%s)""",
                (room_id, player_id, name, token_hash),
            )
            if game in {"ludo", "oware", "iq", "route-empire"}:
                names = [str(players[0][1]), name]
                if game == "ludo":
                    initial_state = ludo.new_game(names)
                elif game == "oware":
                    initial_state = oware.new_game(names)
                elif game == "iq":
                    initial_state = iq_duel.new_game(names)
                else:
                    initial_state = route_empire.new_game(
                        location="OAP Arena Matchmaking",
                        players=names,
                    )
                connection.execute(
                    """UPDATE oap_arena_rooms
                       SET status='ACTIVE',game_state=%s::jsonb,updated_at=CURRENT_TIMESTAMP
                       WHERE room_id=%s AND status='WAITING'""",
                    (json.dumps(initial_state, sort_keys=True), room_id),
                )
            else:
                connection.execute(
                    """UPDATE oap_arena_rooms
                       SET status='ACTIVE',updated_at=CURRENT_TIMESTAMP
                       WHERE room_id=%s AND status='WAITING'""",
                    (room_id,),
                )
            connection.commit()
    except ArenaRoomUnavailable:
        raise
    except Exception as exc:
        raise ArenaRoomUnavailable("arena_matchmaking_failed") from exc

    return {
        "room_id": str(room_id),
        "room_code": str(code),
        "player_id": player_id,
        "reconnect_token": token,
        "game_key": game,
        "seat": 2,
        "status": "ACTIVE",
        "matched": True,
        "matchmaking": True,
    }


def create_room(*, game_key: object, host_name: object, capacity: object = 2) -> dict[str, Any]:
    game = _game(game_key)
    name = _name(host_name)
    seats = _capacity(capacity)
    if seats != 2:
        raise ValueError("arena_room_requires_two_seats")
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
            existing_players = connection.execute(
                """SELECT seat,display_name FROM oap_arena_room_players
                   WHERE room_id=%s ORDER BY seat ASC""",
                (room_id,),
            ).fetchall()
            if any(str(player[1]).casefold() == name.casefold() for player in existing_players):
                raise ValueError("arena_room_player_name_taken")
            next_seat = max((int(player[0]) for player in existing_players), default=0) + 1
            count = len(existing_players)
            if count >= int(capacity) or next_seat > int(capacity):
                raise ValueError("arena_room_full")
            connection.execute(
                """INSERT INTO oap_arena_room_players
                   (room_id,player_id,display_name,seat,reconnect_token_hash)
                   VALUES (%s,%s,%s,%s,%s)""",
                (room_id, player_id, name, next_seat, token_hash),
            )
            if count + 1 >= 2:
                if str(game_key) in {"ludo", "oware", "iq", "route-empire"}:
                    names = [str(player[1]) for player in existing_players] + [name]
                    if str(game_key) == "ludo":
                        initial_state = ludo.new_game(names)
                    elif str(game_key) == "oware":
                        initial_state = oware.new_game(names)
                    elif str(game_key) == "iq":
                        initial_state = iq_duel.new_game(names)
                    else:
                        initial_state = route_empire.new_game(location="OAP Arena Room", players=names)
                    connection.execute(
                        """UPDATE oap_arena_rooms
                           SET status='ACTIVE',game_state=%s::jsonb,updated_at=CURRENT_TIMESTAMP
                           WHERE room_id=%s AND status='WAITING'""",
                        (json.dumps(initial_state, sort_keys=True), room_id),
                    )
                else:
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
    if str(room_row[1]) in {"connect4", "dot", "chess", "ludo", "oware", "iq", "route-empire"} and game_state:
        game_key = str(room_row[1])
        if game_key == "iq":
            game_state = iq_duel.public_state(game_state, seat=int(authorized[0]))
        else:
            engine = {
                "connect4": connect4, "dot": dot, "chess": chess,
                "ludo": ludo, "oware": oware, "route-empire": route_empire,
            }[game_key]
            game_state = engine.public_state(game_state)
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




def _two_player_action(
    *,
    game_key: str,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    column: object = None,
    a: object = None,
    b: object = None,
    source: object = None,
    target: object = None,
    promotion: object = None,
    piece_id: object = None,
    pit: object = None,
) -> dict[str, Any]:
    """Shared locked transaction for server-authoritative two-player game moves."""
    engine = {"connect4": connect4, "dot": dot, "chess": chess, "ludo": ludo, "oware": oware}[game_key]
    room = _room_id(room_id)
    token_hash = _token_hash(reconnect_token)
    req = _request_id(request_id)
    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 0:
        raise ValueError("arena_room_revision_invalid")
    verb = str(action or "")
    if game_key == "connect4":
        if verb not in {"drop", "stop"}:
            raise ValueError("arena_room_action_invalid")
        if verb == "drop" and (isinstance(column, bool) or not isinstance(column, int) or not 0 <= column < 7):
            raise ValueError("connect4_column_invalid")
        if verb == "stop" and column is not None:
            raise ValueError("arena_room_action_invalid")
        if a is not None or b is not None:
            raise ValueError("arena_room_action_invalid")
        move_data = column
    elif game_key == "dot":
        if verb not in {"draw", "stop"} or column is not None:
            raise ValueError("arena_room_action_invalid")
        if verb == "draw":
            if not isinstance(a, str) or not isinstance(b, str) or not dot._adj(a, b):
                raise ValueError("dot_edge_invalid")
            move_data = sorted((a, b))
        else:
            if a is not None or b is not None:
                raise ValueError("arena_room_action_invalid")
            move_data = None
    elif game_key == "chess":
        if verb not in {"move", "stop"} or column is not None or a is not None or b is not None:
            raise ValueError("arena_room_action_invalid")
        if verb == "move":
            if not chess._sq(source) or not chess._sq(target):
                raise ValueError("chess_square_invalid")
            promotion_value = str(promotion or "").upper() or None
            if promotion_value is not None and promotion_value not in chess.PROMOTIONS:
                raise ValueError("chess_promotion_invalid")
            move_data = [source, target, promotion_value]
        else:
            if source is not None or target is not None or promotion is not None:
                raise ValueError("arena_room_action_invalid")
            move_data = None
    elif game_key == "ludo":
        if verb not in {"roll", "move", "stop"}:
            raise ValueError("arena_room_action_invalid")
        if any(value is not None for value in (column, a, b, source, target, promotion, pit)):
            raise ValueError("arena_room_action_invalid")
        if verb == "move":
            move_data = str(piece_id or "").strip()
            if not move_data:
                raise ValueError("ludo_piece_invalid")
        else:
            if piece_id is not None:
                raise ValueError("arena_room_action_invalid")
            move_data = None
    else:
        if verb not in {"move", "stop"}:
            raise ValueError("arena_room_action_invalid")
        if any(value is not None for value in (column, a, b, source, target, promotion, piece_id)):
            raise ValueError("arena_room_action_invalid")
        if verb == "move":
            if isinstance(pit, bool) or not isinstance(pit, int) or not 0 <= pit < oware.PIT_COUNT:
                raise ValueError("oware_pit_invalid")
            move_data = pit
        else:
            if pit is not None:
                raise ValueError("arena_room_action_invalid")
            move_data = None
    digest = hashlib.sha256(
        json.dumps(
            [room, token_hash, expected_revision, req, game_key, verb, move_data],
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
            stored_game, status, capacity, revision, stored = room_row
            if stored_game != game_key or int(capacity) != 2:
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
            if stored:
                game_state = stored
            elif game_key == "chess":
                game_state = chess.new_game()
            elif game_key in {"ludo", "oware"}:
                game_state = engine.new_game([players[0][1], players[1][1]])
            else:
                game_state = engine.new_game(players[0][1], players[1][1])
            current = engine.public_state(game_state)
            if verb != "stop":
                if game_key == "connect4":
                    expected_seat = 1 if current["current_player_id"] == "p1" else 2
                elif game_key == "dot":
                    expected_seat = 1 if current["turn_player_id"] == "p1" else 2
                elif game_key == "chess":
                    expected_seat = 1 if current["turn"] == "White" else 2
                else:
                    expected_seat = 1 if current["current_player_id"] == "p1" else 2
                if expected_seat != seat:
                    raise ValueError("arena_room_not_your_turn")
                if game_key == "connect4":
                    next_state = connect4.drop(game_state, column=column, request_id=req)
                elif game_key == "dot":
                    next_state = dot.draw(game_state, a=a, b=b, request_id=req)
                elif game_key == "chess":
                    next_state = chess.move(
                        game_state,
                        source=source,
                        target=target,
                        promotion=promotion,
                        request_id=req,
                    )
                elif game_key == "ludo":
                    if verb == "roll":
                        next_state = ludo.roll(game_state, request_id=req)
                    else:
                        next_state = ludo.move(game_state, piece_id=piece_id, request_id=req)
                else:
                    next_state = oware.move(game_state, pit=pit, request_id=req)
            else:
                next_state = engine.stop(game_state, request_id=req)
            next_view = engine.public_state(next_state)
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
        raise ArenaRoomUnavailable("arena_room_action_failed") from exc
    return {
        "room_id": room, "revision": new_revision, "duplicate": False,
        "status": next_status, "game_state": next_view,
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
    """Only the first-party engine may construct a multiplayer Connect 4 board."""
    return _two_player_action(
        game_key="connect4", room_id=room_id, reconnect_token=reconnect_token,
        expected_revision=expected_revision, request_id=request_id,
        action=action, column=column,
    )


def dot_action(
    *,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    a: object = None,
    b: object = None,
) -> dict[str, Any]:
    """Server-validated Dot edge/turn/box scoring under the shared room lock."""
    return _two_player_action(
        game_key="dot", room_id=room_id, reconnect_token=reconnect_token,
        expected_revision=expected_revision, request_id=request_id,
        action=action, a=a, b=b,
    )


def chess_action(
    *,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    source: object = None,
    target: object = None,
    promotion: object = None,
) -> dict[str, Any]:
    """Server-validated Chess move under the shared durable room lock."""
    return _two_player_action(
        game_key="chess",
        room_id=room_id,
        reconnect_token=reconnect_token,
        expected_revision=expected_revision,
        request_id=request_id,
        action=action,
        source=source,
        target=target,
        promotion=promotion,
    )


def ludo_action(
    *,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    piece_id: object = None,
) -> dict[str, Any]:
    """Server-authoritative two-player Ludo room action."""
    return _two_player_action(
        game_key="ludo",
        room_id=room_id,
        reconnect_token=reconnect_token,
        expected_revision=expected_revision,
        request_id=request_id,
        action=action,
        piece_id=piece_id,
    )


def oware_action(
    *,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    pit: object = None,
) -> dict[str, Any]:
    """Server-authoritative two-player Oware room action."""
    return _two_player_action(
        game_key="oware",
        room_id=room_id,
        reconnect_token=reconnect_token,
        expected_revision=expected_revision,
        request_id=request_id,
        action=action,
        pit=pit,
    )



def _custom_room_action(
    *,
    game_key: str,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Locked transaction for IQ duel and Route Empire room actions."""
    room = _room_id(room_id)
    token_hash = _token_hash(reconnect_token)
    req = _request_id(request_id)
    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 0:
        raise ValueError("arena_room_revision_invalid")
    verb = str(action or "").strip()
    digest = hashlib.sha256(
        json.dumps(
            [room, token_hash, expected_revision, req, game_key, verb, data],
            separators=(",", ":"), sort_keys=True,
        ).encode("utf-8")
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
            stored_game, status, capacity, revision, stored = room_row
            if str(stored_game) != game_key or int(capacity) != 2:
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
            if isinstance(stored, str):
                stored = json.loads(stored)
            if not stored:
                raise ValueError("arena_room_game_state_missing")

            if game_key == "iq":
                if verb == "answer":
                    next_state = iq_duel.answer(
                        stored, seat=seat, choice_id=data.get("choice_id"), request_id=req
                    )
                elif verb == "stop":
                    next_state = iq_duel.stop(stored, request_id=req)
                else:
                    raise ValueError("arena_room_action_invalid")
                next_view = iq_duel.public_state(next_state, seat=seat)
            else:
                if verb not in {"claim", "develop", "route", "end_turn", "stop"}:
                    raise ValueError("arena_room_action_invalid")
                if verb != "stop" and int(stored.get("turn_index", -1)) + 1 != seat:
                    raise ValueError("arena_room_not_your_turn")
                next_state = route_empire.action(
                    stored,
                    action=verb,
                    request_id=req,
                    node_id=data.get("node_id"),
                    target_node_id=data.get("target_node_id"),
                )
                next_view = route_empire.public_state(next_state)

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
        raise ArenaRoomUnavailable("arena_room_action_failed") from exc

    return {
        "room_id": room,
        "revision": new_revision,
        "duplicate": False,
        "status": next_status,
        "game_state": next_view,
    }


def iq_action(
    *,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    choice_id: object = None,
) -> dict[str, Any]:
    return _custom_room_action(
        game_key="iq",
        room_id=room_id,
        reconnect_token=reconnect_token,
        expected_revision=expected_revision,
        request_id=request_id,
        action=action,
        data={"choice_id": choice_id},
    )


def route_empire_action(
    *,
    room_id: object,
    reconnect_token: object,
    expected_revision: object,
    request_id: object,
    action: object,
    node_id: object = None,
    target_node_id: object = None,
) -> dict[str, Any]:
    return _custom_room_action(
        game_key="route-empire",
        room_id=room_id,
        reconnect_token=reconnect_token,
        expected_revision=expected_revision,
        request_id=request_id,
        action=action,
        data={"node_id": node_id, "target_node_id": target_node_id},
    )


def update_game_state(*, room_id: object, reconnect_token: object, expected_revision: object,
                      game_state: object, request_id: object) -> dict[str, Any]:
    """Fail closed: multiplayer moves require a server-authoritative game adapter.

    Accepting client-supplied board JSON would allow forged results and turn skipping.
    """
    raise ValueError("arena_room_server_game_adapter_required")


def status() -> dict[str, Any]:
    return {
        "durable_rooms": True,
        "playable_room_games_only": True,
        "invite_codes": True,\n        "quick_matchmaking": True,\n        "matchmaking_games": sorted(SUPPORTED_GAMES),
        "reconnect_tokens": True,
        "revision_conflict_guard": True,
        "connect4_server_actions": True,
        "dot_server_actions": True,
        "chess_server_actions": True,
        "ludo_server_actions": True,
        "oware_server_actions": True,
        "iq_duel_server_actions": True,
        "route_empire_server_actions": True,
        "arbitrary_client_game_state_writes": False,
        "chat": False,
        "payments": False,
        "explicit_migration_required": True,
        "deployed": False,
    }
