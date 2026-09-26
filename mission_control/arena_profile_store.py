"""Durable OAP Arena player profiles, match history and rankings.

This store binds Arena competition records to the canonical authenticated users(id)
identity and PostgreSQL foundation. Schema changes remain explicit: importing this
module never creates or migrates tables.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import postgres_db


class ArenaStoreUnavailable(RuntimeError):
    """Raised when durable Arena storage cannot complete safely."""


def _uuid(value: object, code: str = "arena_identity_invalid") -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def profile(identity_id: object) -> dict[str, Any] | None:
    identity = _uuid(identity_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT p.identity_id,COALESCE(u.display_name,u.username),
                          p.matches_played,p.wins,p.losses,p.draws,p.points,
                          p.updated_at
                   FROM oap_arena_player_profiles p
                   JOIN users u ON u.id=p.identity_id
                   WHERE p.identity_id=%s AND u.status='active'
                   LIMIT 1""",
                (identity,),
            ).fetchone()
    except Exception as exc:
        raise ArenaStoreUnavailable("arena_profile_read_failed") from exc
    if row is None:
        return None
    return {
        "identity_id": str(row[0]),
        "display_name": str(row[1]),
        "matches_played": int(row[2]),
        "wins": int(row[3]),
        "losses": int(row[4]),
        "draws": int(row[5]),
        "points": int(row[6]),
        "updated_at": row[7].isoformat(),
    }


def ranking(*, limit: int = 100) -> list[dict[str, Any]]:
    bounded = max(1, min(int(limit), 100))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT p.identity_id,COALESCE(u.display_name,u.username),
                          p.matches_played,p.wins,p.losses,p.draws,p.points
                   FROM oap_arena_player_profiles p
                   JOIN users u ON u.id=p.identity_id
                   WHERE u.status='active'
                   ORDER BY p.points DESC,p.wins DESC,p.matches_played ASC,
                            p.identity_id ASC
                   LIMIT %s""",
                (bounded,),
            ).fetchall()
    except Exception as exc:
        raise ArenaStoreUnavailable("arena_ranking_read_failed") from exc
    return [
        {
            "rank": index,
            "identity_id": str(row[0]),
            "display_name": str(row[1]),
            "matches_played": int(row[2]),
            "wins": int(row[3]),
            "losses": int(row[4]),
            "draws": int(row[5]),
            "points": int(row[6]),
        }
        for index, row in enumerate(rows, start=1)
    ]


def record_completed_match(
    *,
    match_id: object,
    player_a_id: object,
    player_b_id: object,
    player_a_score: int,
    player_b_score: int,
    receipt_hash: object,
) -> dict[str, Any]:
    match = _uuid(match_id, "arena_match_id_invalid")
    player_a = _uuid(player_a_id)
    player_b = _uuid(player_b_id)
    if player_a == player_b:
        raise ValueError("arena_match_distinct_players_required")
    if not isinstance(player_a_score, int) or not 0 <= player_a_score <= 7:
        raise ValueError("arena_score_invalid")
    if not isinstance(player_b_score, int) or not 0 <= player_b_score <= 7:
        raise ValueError("arena_score_invalid")
    receipt = str(receipt_hash or "").strip()
    if len(receipt) != 64 or any(ch not in "0123456789abcdef" for ch in receipt.lower()):
        raise ValueError("arena_receipt_hash_invalid")

    if player_a_score > player_b_score:
        outcome_a, outcome_b = "WIN", "LOSS"
    elif player_b_score > player_a_score:
        outcome_a, outcome_b = "LOSS", "WIN"
    else:
        outcome_a = outcome_b = "DRAW"

    def points(outcome: str) -> int:
        return 3 if outcome == "WIN" else 1 if outcome == "DRAW" else 0

    try:
        with postgres_db.connect() as connection:
            users = connection.execute(
                """SELECT id FROM users
                   WHERE id IN (%s,%s) AND status='active'""",
                (player_a, player_b),
            ).fetchall()
            if {str(row[0]) for row in users} != {player_a, player_b}:
                raise ValueError("arena_player_unavailable")

            existing = connection.execute(
                """SELECT player_a_id,player_b_id,player_a_score,player_b_score,
                          receipt_hash
                   FROM oap_arena_matches WHERE match_id=%s LIMIT 1""",
                (match,),
            ).fetchone()
            if existing is not None:
                expected = (
                    player_a,
                    player_b,
                    player_a_score,
                    player_b_score,
                    receipt.lower(),
                )
                actual = (
                    str(existing[0]),
                    str(existing[1]),
                    int(existing[2]),
                    int(existing[3]),
                    str(existing[4]),
                )
                if actual != expected:
                    raise ValueError("arena_match_idempotency_conflict")
                connection.commit()
                return {"match_id": match, "duplicate": True}

            connection.execute(
                """INSERT INTO oap_arena_matches(
                       match_id,player_a_id,player_b_id,player_a_score,
                       player_b_score,receipt_hash,status
                   ) VALUES (%s,%s,%s,%s,%s,%s,'COMPLETED')""",
                (match, player_a, player_b, player_a_score, player_b_score, receipt.lower()),
            )
            for identity, outcome in ((player_a, outcome_a), (player_b, outcome_b)):
                connection.execute(
                    """INSERT INTO oap_arena_player_profiles(
                           identity_id,matches_played,wins,losses,draws,points
                       ) VALUES (
                           %s,1,
                           CASE WHEN %s='WIN' THEN 1 ELSE 0 END,
                           CASE WHEN %s='LOSS' THEN 1 ELSE 0 END,
                           CASE WHEN %s='DRAW' THEN 1 ELSE 0 END,
                           %s
                       )
                       ON CONFLICT (identity_id) DO UPDATE SET
                           matches_played=oap_arena_player_profiles.matches_played+1,
                           wins=oap_arena_player_profiles.wins+
                               CASE WHEN EXCLUDED.wins=1 THEN 1 ELSE 0 END,
                           losses=oap_arena_player_profiles.losses+
                               CASE WHEN EXCLUDED.losses=1 THEN 1 ELSE 0 END,
                           draws=oap_arena_player_profiles.draws+
                               CASE WHEN EXCLUDED.draws=1 THEN 1 ELSE 0 END,
                           points=oap_arena_player_profiles.points+EXCLUDED.points,
                           updated_at=CURRENT_TIMESTAMP""",
                    (identity, outcome, outcome, outcome, points(outcome)),
                )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise ArenaStoreUnavailable("arena_match_write_failed") from exc

    return {
        "match_id": match,
        "duplicate": False,
        "player_a_outcome": outcome_a,
        "player_b_outcome": outcome_b,
    }


def status() -> dict[str, bool]:
    return {
        "canonical_users_identity": True,
        "durable_profiles": True,
        "durable_match_history": True,
        "rankings": True,
        "explicit_migration_required": True,
        "payments": False,
        "prizes": False,
        "deployed": False,
    }
