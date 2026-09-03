"""Bounded production stores for LinkUp, Market and SIKA projections."""

from __future__ import annotations

import re
import uuid
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from . import postgres_db

MAX_MESSAGES_PER_MINUTE = 20
MAX_LISTINGS_PER_HOUR = 20
_BLOCKED_MESSAGE = re.compile(
    r"\b(?:credential theft|ransomware|malware|doxx(?:ing)?|disable safety)\b",
    re.IGNORECASE,
)


class ProductStoreUnavailable(RuntimeError):
    """Raised when a configured product store cannot complete safely."""


def _identity(value: object, code: str = "invalid_identity") -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def linkup_dashboard(identity_id: object) -> dict[str, Any]:
    """Return a private directory and conversation threads for this identity only."""

    identity = _identity(identity_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            directory_rows = connection.execute(
                """SELECT id,COALESCE(display_name,username),postcode,borough,country
                   FROM users WHERE status='active' AND id<>%s
                   ORDER BY COALESCE(display_name,username) LIMIT 100""",
                (identity,),
            ).fetchall()
            message_rows = connection.execute(
                """SELECT m.id,m.sender_id,m.recipient_id,m.body,m.read_at,
                          m.created_at,
                          COALESCE(sender.display_name,sender.username),
                          COALESCE(recipient.display_name,recipient.username)
                   FROM messages m
                   JOIN users sender ON sender.id=m.sender_id
                   JOIN users recipient ON recipient.id=m.recipient_id
                   WHERE m.sender_id=%s OR m.recipient_id=%s
                   ORDER BY m.created_at DESC LIMIT 200""",
                (identity, identity),
            ).fetchall()
    except Exception as exc:
        raise ProductStoreUnavailable("linkup_read_failed") from exc

    directory = [
        {
            "identity_id": str(row[0]),
            "display_name": str(row[1]),
            "postcode": str(row[2] or ""),
            "borough": str(row[3] or ""),
            "country": str(row[4] or ""),
        }
        for row in directory_rows
    ]
    people = {person["identity_id"]: person for person in directory}
    messages = [
        {
            "message_id": str(row[0]),
            "direction": "sent" if str(row[1]) == identity else "received",
            "sender": str(row[6]),
            "recipient": str(row[7]),
            "other_identity_id": (
                str(row[2]) if str(row[1]) == identity else str(row[1])
            ),
            "body": str(row[3]),
            "read": row[4] is not None,
            "created_at": row[5].isoformat(),
        }
        for row in message_rows
    ]
    grouped: dict[str, dict[str, Any]] = {}
    for message in messages:
        other_id = str(message["other_identity_id"])
        thread = grouped.setdefault(
            other_id,
            {
                "other_identity_id": other_id,
                "display_name": people.get(other_id, {}).get("display_name")
                or (message["recipient"] if message["direction"] == "sent" else message["sender"]),
                "postcode": people.get(other_id, {}).get("postcode", ""),
                "unread_count": 0,
                "latest_at": message["created_at"],
                "messages": [],
            },
        )
        thread["messages"].append(message)
        if message["direction"] == "received" and not message["read"]:
            thread["unread_count"] += 1
    threads = list(grouped.values())
    for thread in threads:
        thread["messages"].reverse()
    threads.sort(key=lambda item: str(item["latest_at"]), reverse=True)
    return {"directory": directory, "messages": messages, "threads": threads}


def send_message(sender_id: object, recipient_id: object, body: object) -> str:
    sender = _identity(sender_id, "invalid_sender")
    recipient = _identity(recipient_id, "invalid_recipient")
    message = str(body or "").strip()[:4000]
    if sender == recipient:
        raise ValueError("cannot_message_self")
    if not message:
        raise ValueError("message_required")
    if _BLOCKED_MESSAGE.search(message):
        raise ValueError("guardian_blocked_message")
    try:
        with postgres_db.connect() as connection:
            users = connection.execute(
                """SELECT id FROM users
                   WHERE id IN (%s,%s) AND status='active'""",
                (sender, recipient),
            ).fetchall()
            if {str(row[0]) for row in users} != {sender, recipient}:
                raise ValueError("recipient_unavailable")
            recent = connection.execute(
                """SELECT COUNT(*) FROM messages
                   WHERE sender_id=%s
                     AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'""",
                (sender,),
            ).fetchone()
            if recent and int(recent[0]) >= MAX_MESSAGES_PER_MINUTE:
                raise ValueError("linkup_rate_limit")
            row = connection.execute(
                """INSERT INTO messages(sender_id,recipient_id,body)
                   VALUES (%s,%s,%s) RETURNING id""",
                (sender, recipient, message),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise ProductStoreUnavailable("linkup_write_failed") from exc
    return str(row[0])


def mark_message_read(identity_id: object, message_id: object) -> bool:
    identity = _identity(identity_id)
    message = _identity(message_id, "invalid_message")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE messages SET read_at=COALESCE(read_at,CURRENT_TIMESTAMP)
                   WHERE id=%s AND recipient_id=%s RETURNING id""",
                (message, identity),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise ProductStoreUnavailable("linkup_read_receipt_failed") from exc
    return row is not None


def list_products(*, limit: int = 100) -> list[dict[str, Any]]:
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT p.id,p.name,p.description,p.price_minor,p.currency,
                          p.created_at,COALESCE(u.display_name,u.username),
                          u.postcode,u.borough,u.country
                   FROM products p JOIN users u ON u.id=p.seller_id
                   WHERE p.active=TRUE AND u.status='active'
                   ORDER BY p.created_at DESC LIMIT %s""",
                (min(200, max(1, int(limit))),),
            ).fetchall()
    except Exception as exc:
        raise ProductStoreUnavailable("market_read_failed") from exc
    return [
        {
            "product_id": str(row[0]),
            "name": str(row[1]),
            "description": str(row[2] or ""),
            "price": f"{Decimal(int(row[3])) / Decimal(100):.2f}",
            "currency": str(row[4]),
            "created_at": row[5].isoformat(),
            "seller": str(row[6]),
            "postcode": str(row[7] or ""),
            "borough": str(row[8] or ""),
            "country": str(row[9] or ""),
        }
        for row in rows
    ]


def create_product(seller_id: object, *, name: object, description: object, price: object) -> str:
    seller = _identity(seller_id)
    name_value = str(name or "").strip()[:160]
    description_value = str(description or "").strip()[:3000]
    if not name_value:
        raise ValueError("product_name_required")
    try:
        amount = Decimal(str(price or "").strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid_product_price") from exc
    if amount < 0 or amount > Decimal(1000000):
        raise ValueError("invalid_product_price")
    price_minor = int(amount * 100)
    try:
        with postgres_db.connect() as connection:
            active = connection.execute("SELECT 1 FROM users WHERE id=%s AND status='active'", (seller,)).fetchone()
            if active is None:
                raise ValueError("seller_unavailable")
            recent = connection.execute(
                """SELECT COUNT(*) FROM products WHERE seller_id=%s
                   AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'""",
                (seller,),
            ).fetchone()
            if recent and int(recent[0]) >= MAX_LISTINGS_PER_HOUR:
                raise ValueError("market_rate_limit")
            row = connection.execute(
                """INSERT INTO products(seller_id,name,description,price_minor,currency,active)
                   VALUES (%s,%s,%s,%s,'GBP',TRUE) RETURNING id""",
                (seller, name_value, description_value, price_minor),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise ProductStoreUnavailable("market_write_failed") from exc
    return str(row[0])


def sika_summary(identity_id: object) -> dict[str, Any]:
    """Return contribution credits only; SIKA is not represented as money."""

    identity = _identity(identity_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            wallet = connection.execute(
                """SELECT id,balance,currency_code,updated_at FROM wallets
                   WHERE user_id=%s""",
                (identity,),
            ).fetchone()
            rows = []
            if wallet:
                rows = connection.execute(
                    """SELECT amount,transaction_type,reference,metadata,created_at
                       FROM transactions WHERE wallet_id=%s
                       ORDER BY created_at DESC LIMIT 100""",
                    (wallet[0],),
                ).fetchall()
    except Exception as exc:
        raise ProductStoreUnavailable("sika_read_failed") from exc
    return {
        "balance": int(wallet[1]) if wallet else 0,
        "unit": str(wallet[2]) if wallet else "SIKA",
        "money": False,
        "updated_at": wallet[3].isoformat() if wallet else None,
        "transactions": [
            {"amount": int(row[0]), "type": str(row[1]), "reference": str(row[2]), "created_at": row[4].isoformat()}
            for row in rows
        ],
    }


def status() -> dict[str, object]:
    needed = {"messages", "products", "wallets", "transactions"}
    result: dict[str, object] = {
        "tables": {name: False for name in sorted(needed)},
        "ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public' AND table_name=ANY(%s)""",
                (list(needed),),
            ).fetchall()
            present = {str(row[0]) for row in rows}
            result["tables"] = {name: name in present for name in sorted(needed)}
            result["ready"] = needed <= present
    except Exception:  # noqa: BLE001
        result["error"] = "product_store_unavailable"
    return result