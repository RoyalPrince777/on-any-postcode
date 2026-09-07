"""Governed live operational memory retrieval for the Founder-private SMI.

This layer gives SMI bounded, read-only access to meaningful OAP state without
copying raw databases into prompts. Canonical memory remains authoritative.
Operational records are context only, are treated as data rather than
instructions, and are privacy-reduced before they reach generation.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from oap.contracts import MemoryItem, OutputState

OPERATIONAL_MEMORY_REVISION = "2026-09-07-v1"
MAX_ITEMS = 5
_MAX_TEXT = 420
_LINK_TERMS = frozenset({"link", "linkup", "message", "circle", "voice", "call", "seen", "landed"})
_BOOKING_TERMS = frozenset({"booking", "book", "travel", "direct", "reservation", "hold", "supplier"})


def _safe_text(value: object, limit: int = _MAX_TEXT) -> str:
    return " ".join(str(value or "").split())[:limit]


def _tokens(value: object) -> set[str]:
    return {item for item in re.findall(r"[a-z0-9]+", str(value or "").casefold()) if len(item) > 1}


def _decode_public_post(scope: str, body: object, postcode: object) -> str:
    raw = str(body or "")
    data: dict[str, Any] = {}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            data = parsed
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    if scope == "oap_signal":
        return f"PUBLIC OAP DATA ONLY — Signal by {_safe_text(data.get('name') or 'member', 60)}: {_safe_text(data.get('body') or raw, 260)}"
    if scope == "oap_team_room":
        return f"PUBLIC OAP DATA ONLY — World Room {_safe_text(postcode, 60)} · {_safe_text(data.get('name') or 'member', 60)}: {_safe_text(data.get('message') or raw, 240)}"
    if scope == "oap_flag":
        return f"PUBLIC OAP DATA ONLY — Flag signal recorded: {_safe_text(raw, 100)}"
    return f"PUBLIC OAP DATA ONLY — {_safe_text(raw, 280)}"


def _candidate(source: str, text: str, created_at: datetime, query_tokens: set[str], boost: int = 0) -> tuple[int, float, str, str, datetime]:
    clean = _safe_text(text)
    overlap = len(_tokens(clean) & query_tokens)
    score = boost + (overlap * 5)
    timestamp = created_at.timestamp() if isinstance(created_at, datetime) else 0.0
    return score, timestamp, source, clean, created_at


def _table_exists(connection: Any, name: str) -> bool:
    row = connection.execute("SELECT to_regclass(%s)", (f"public.{name}",)).fetchone()
    return bool(row and row[0])


def _founder_identity(connection: Any) -> str | None:
    row = connection.execute(
        """SELECT i.identity_id
           FROM oap_identities i
           JOIN oap_identity_roles ir ON ir.identity_id=i.identity_id
           JOIN oap_roles r ON r.role_id=ir.role_id
           WHERE i.status='ACTIVE' AND r.authority_level=0
           ORDER BY i.updated_at DESC LIMIT 1"""
    ).fetchone()
    return str(row[0]) if row else None


def operational_memory_items(
    task_type: str | None = None,
    *,
    query: str = "",
    limit: int = MAX_ITEMS,
) -> tuple[MemoryItem, ...]:
    """Retrieve the most relevant privacy-reduced live OAP memories.

    The current product has one Founder-private SMI surface. Retrieval therefore
    resolves the active level-zero Human Authority and never exposes another
    private user's records. Public Signals/Rooms are eligible because they are
    already published OAP data. Private Link text is only retrieved when the
    Founder explicitly asks about Link/message context.
    """

    safe_limit = min(max(int(limit), 1), MAX_ITEMS)
    query_tokens = _tokens(query) | _tokens(task_type)
    candidates: list[tuple[int, float, str, str, datetime]] = []
    try:
        from mission_control import postgres_db

        if not postgres_db.configured():
            return ()
        with postgres_db.connect(readonly=True) as connection:
            founder_id = _founder_identity(connection)
            if not founder_id:
                return ()

            for row in connection.execute(
                """SELECT summary,created_at FROM smi_memory_records
                   WHERE identity_id=%s AND task_type='OAP_EVENT'
                   ORDER BY created_at DESC LIMIT 30""",
                (founder_id,),
            ).fetchall():
                candidates.append(_candidate("event", f"OAP EVENT MEMORY — {_safe_text(row[0], 320)}", row[1], query_tokens, 4))

            for row in connection.execute(
                """SELECT action,target,reason,timestamp FROM audit_events
                   WHERE action <> 'SMI_REVIEWED'
                   ORDER BY timestamp DESC LIMIT 40"""
            ).fetchall():
                text = f"AUDIT MEMORY — {row[0]} · {row[1]} · {_safe_text(row[2], 260)}"
                candidates.append(_candidate("audit", text, row[3], query_tokens, 3))

            for row in connection.execute(
                """SELECT scope,body,postcode,created_at FROM posts
                   WHERE status='published'
                   ORDER BY created_at DESC LIMIT 24"""
            ).fetchall():
                text = _decode_public_post(str(row[0]), row[1], row[2])
                candidates.append(_candidate("public", text, row[3], query_tokens, 1))

            for row in connection.execute(
                """SELECT workspace_id,title,body,updated_at FROM oap_workspace_records
                   WHERE identity_id=%s AND status <> 'archived'
                   ORDER BY updated_at DESC LIMIT 20""",
                (founder_id,),
            ).fetchall():
                text = f"PRIVATE FOUNDER MEMORY DATA ONLY — {row[0]} workspace · {_safe_text(row[1], 100)} · {_safe_text(row[2], 260)}"
                candidates.append(_candidate("workspace", text, row[3], query_tokens, 3))

            for row in connection.execute(
                """SELECT name,active,updated_at FROM products
                   WHERE seller_id=%s ORDER BY updated_at DESC LIMIT 12""",
                (founder_id,),
            ).fetchall():
                text = f"MARKET MEMORY — {_safe_text(row[0], 140)} · {'active' if row[1] else 'inactive'} listing"
                candidates.append(_candidate("market", text, row[2], query_tokens, 2))

            for row in connection.execute(
                """SELECT t.transaction_type,t.created_at
                   FROM transactions t JOIN wallets w ON w.id=t.wallet_id
                   WHERE w.user_id=%s ORDER BY t.created_at DESC LIMIT 12""",
                (founder_id,),
            ).fetchall():
                text = f"SIKA MEMORY — {_safe_text(row[0], 100)} transaction recorded; amount/reference withheld from automatic context"
                candidates.append(_candidate("sika", text, row[1], query_tokens, 2))

            if query_tokens & _LINK_TERMS:
                for row in connection.execute(
                    """SELECT sender_id,recipient_id,body,created_at FROM messages
                       WHERE sender_id=%s OR recipient_id=%s
                       ORDER BY created_at DESC LIMIT 10""",
                    (founder_id, founder_id),
                ).fetchall():
                    direction = "sent" if str(row[0]) == founder_id else "received"
                    text = f"PRIVATE LINK MEMORY DATA ONLY — {direction} Link: {_safe_text(row[2], 280)}"
                    candidates.append(_candidate("link", text, row[3], query_tokens, 6))

            if query_tokens & _BOOKING_TERMS and _table_exists(connection, "oap_supply_reservations"):
                for row in connection.execute(
                    """SELECT r.state,l.title,r.created_at
                       FROM oap_supply_reservations r
                       JOIN oap_supply_listings l ON l.listing_id=r.listing_id
                       WHERE r.buyer_identity_id=%s
                       ORDER BY r.created_at DESC LIMIT 10""",
                    (founder_id,),
                ).fetchall():
                    text = f"BOOKING MEMORY — {_safe_text(row[1], 160)} · reservation state {row[0]}"
                    candidates.append(_candidate("booking", text, row[2], query_tokens, 6))
    except Exception:  # noqa: BLE001 -- memory failure must never break SMI.
        return ()

    ordered = sorted(candidates, key=lambda item: (item[0], item[1]), reverse=True)
    seen: set[str] = set()
    items: list[MemoryItem] = []
    for _, _, source, text, created_at in ordered:
        if not text or text in seen:
            continue
        seen.add(text)
        digest = hashlib.sha256(f"{source}|{text}|{created_at.isoformat()}".encode()).hexdigest()[:20]
        items.append(
            MemoryItem(
                memory_id=f"operational:{digest}",
                task_type="OPERATIONAL",
                summary=text,
                output_state=OutputState.SYSTEM_LOG_ONLY.value,
                created_at=created_at if isinstance(created_at, datetime) else datetime.now(timezone.utc),
            )
        )
        if len(items) >= safe_limit:
            break
    return tuple(items)


def status() -> dict[str, object]:
    try:
        from mission_control import postgres_db
        configured = postgres_db.configured()
    except Exception:  # noqa: BLE001
        configured = False
    return {
        "component": "SMI Operational Memory",
        "revision": OPERATIONAL_MEMORY_REVISION,
        "ready": True,
        "store_configured": configured,
        "automatic_retrieval": True,
        "founder_private_scope": True,
        "public_signal_memory": True,
        "workspace_memory": True,
        "market_memory": True,
        "sika_memory": True,
        "booking_memory": True,
        "private_link_on_demand": True,
        "raw_database_dump": False,
        "raw_credentials_included": False,
        "precise_live_location_auto_memory": False,
        "private_reasoning_included": False,
        "memory_is_data_not_instructions": True,
        "human_authority_final": True,
    }
