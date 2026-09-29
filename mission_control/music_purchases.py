"""Governed OAP Music purchase-intent and ownership registry.

This module records buyer intent and durable ownership only after an explicit
settlement transition. It does not capture cards, move money, or execute SIKA.
"""
from __future__ import annotations

from uuid import UUID, uuid4

from . import postgres_db

MUSIC_PURCHASE_MIGRATION_VERSION = "0017_oap_music_purchases"

PRICE_FLOORS_MINOR = {
    "single": 100,
    "ep": 300,
    "album": 500,
    "deluxe": 700,
}
CURRENCY = "GBP"

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_purchase_intents (
        purchase_id UUID PRIMARY KEY,
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        item_type TEXT NOT NULL CHECK (item_type IN ('TRACK','RELEASE')),
        item_id UUID NOT NULL,
        edition_type TEXT NOT NULL CHECK (edition_type IN ('single','ep','album','deluxe')),
        amount_minor BIGINT NOT NULL CHECK (amount_minor >= 100),
        currency TEXT NOT NULL DEFAULT 'GBP',
        state TEXT NOT NULL DEFAULT 'PAYMENT_REQUIRED'
            CHECK (state IN ('PAYMENT_REQUIRED','SETTLED','CANCELLED','REFUNDED')),
        idempotency_key TEXT NOT NULL,
        settlement_reference TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        settled_at TIMESTAMPTZ,
        UNIQUE(buyer_identity_id,idempotency_key)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_purchase_buyer_created
       ON oap_music_purchase_intents(buyer_identity_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_music_owned_items (
        ownership_id UUID PRIMARY KEY,
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        purchase_id UUID NOT NULL UNIQUE REFERENCES oap_music_purchase_intents(purchase_id)
            ON DELETE RESTRICT,
        item_type TEXT NOT NULL CHECK (item_type IN ('TRACK','RELEASE')),
        item_id UUID NOT NULL,
        edition_type TEXT NOT NULL CHECK (edition_type IN ('single','ep','album','deluxe')),
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMPTZ,
        UNIQUE(buyer_identity_id,item_type,item_id)
    )""",
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def price_intent(edition_type: object, amount_minor: object | None = None) -> dict[str, object]:
    edition = str(edition_type or "").strip().lower()
    if edition not in PRICE_FLOORS_MINOR:
        raise ValueError("invalid_music_edition")
    floor = PRICE_FLOORS_MINOR[edition]
    try:
        amount = floor if amount_minor in (None, "") else int(amount_minor)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_music_amount") from exc
    if amount < floor:
        raise ValueError(f"minimum_{edition}_price_is_{floor}_minor")
    return {
        "edition_type": edition,
        "currency": CURRENCY,
        "minimum_amount_minor": floor,
        "amount_minor": amount,
        "pay_more_allowed": True,
        "payment_capture_performed": False,
        "sika_execution_performed": False,
        "ownership_created": False,
        "human_authority_final": True,
    }


class MusicPurchaseStore:
    def create_intent(
        self,
        *,
        buyer_identity_id: object,
        item_type: object,
        item_id: object,
        edition_type: object,
        amount_minor: object,
        idempotency_key: object,
    ) -> dict[str, object]:
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        item = _uuid(item_id, "item_id")
        kind = str(item_type or "").strip().upper()
        if kind not in {"TRACK", "RELEASE"}:
            raise ValueError("invalid_music_item_type")
        key = str(idempotency_key or "").strip()
        if len(key) < 8 or len(key) > 160:
            raise ValueError("invalid_idempotency_key")
        quote = price_intent(edition_type, amount_minor)
        purchase_id = str(uuid4())
        with postgres_db.connect() as connection:
            existing = connection.execute(
                """SELECT purchase_id,item_type,item_id,edition_type,amount_minor,currency,state
                   FROM oap_music_purchase_intents
                   WHERE buyer_identity_id=%s AND idempotency_key=%s""",
                (buyer, key),
            ).fetchone()
            if existing is None:
                row = connection.execute(
                    """INSERT INTO oap_music_purchase_intents(
                       purchase_id,buyer_identity_id,item_type,item_id,edition_type,
                       amount_minor,currency,state,idempotency_key)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,'PAYMENT_REQUIRED',%s)
                       RETURNING purchase_id,item_type,item_id,edition_type,amount_minor,currency,state""",
                    (purchase_id,buyer,kind,item,quote["edition_type"],quote["amount_minor"],CURRENCY,key),
                ).fetchone()
            else:
                row = existing
                if (
                    str(row[1]) != kind
                    or str(row[2]) != item
                    or str(row[3]) != quote["edition_type"]
                    or int(row[4]) != int(quote["amount_minor"])
                ):
                    raise ValueError("idempotency_key_reused")
            connection.commit()
        return {
            "purchase_id": str(row[0]),
            "item_type": str(row[1]),
            "item_id": str(row[2]),
            "edition_type": str(row[3]),
            "amount_minor": int(row[4]),
            "currency": str(row[5]),
            "state": str(row[6]),
            "payment_capture_performed": False,
            "sika_execution_performed": False,
            "ownership_created": str(row[6]) == "SETTLED",
        }

    def owned_items(self, *, buyer_identity_id: object) -> dict[str, object]:
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        try:
            with postgres_db.connect(readonly=True) as connection:
                rows = connection.execute(
                    """SELECT ownership_id,purchase_id,item_type,item_id,edition_type,created_at
                       FROM oap_music_owned_items
                       WHERE buyer_identity_id=%s AND active=TRUE
                       ORDER BY created_at DESC""",
                    (buyer,),
                ).fetchall()
        except Exception as exc:
            raise RuntimeError("music_ownership_store_unavailable") from exc
        items = [
            {
                "ownership_id": str(row[0]),
                "purchase_id": str(row[1]),
                "item_type": str(row[2]),
                "item_id": str(row[3]),
                "edition_type": str(row[4]),
                "owned_at": row[5].isoformat(),
            }
            for row in rows
        ]
        return {
            "library": "My Music",
            "buyer_identity_id": buyer,
            "items": items,
            "item_count": len(items),
            "ownership_source": "settled_purchase",
            "payment_capture_performed": False,
            "sika_execution_performed": False,
        }

    def record_settlement(
        self,
        *,
        purchase_id: object,
        settlement_reference: object,
    ) -> dict[str, object]:
        purchase = _uuid(purchase_id, "purchase_id")
        reference = str(settlement_reference or "").strip()
        if not reference or len(reference) > 240:
            raise ValueError("invalid_settlement_reference")
        ownership_id = str(uuid4())
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_music_purchase_intents
                   SET state='SETTLED',settlement_reference=%s,
                       settled_at=COALESCE(settled_at,CURRENT_TIMESTAMP)
                   WHERE purchase_id=%s AND state='PAYMENT_REQUIRED'
                   RETURNING buyer_identity_id,item_type,item_id,edition_type""",
                (reference,purchase),
            ).fetchone()
            if row is None:
                current = connection.execute(
                    """SELECT buyer_identity_id,item_type,item_id,edition_type,state
                       FROM oap_music_purchase_intents WHERE purchase_id=%s""",
                    (purchase,),
                ).fetchone()
                if current is None:
                    raise ValueError("purchase_not_found")
                if str(current[4]) != "SETTLED":
                    raise ValueError("purchase_not_settleable")
                row = current[:4]
            connection.execute(
                """INSERT INTO oap_music_owned_items(
                   ownership_id,buyer_identity_id,purchase_id,item_type,item_id,edition_type,active)
                   VALUES (%s,%s,%s,%s,%s,%s,TRUE)
                   ON CONFLICT (purchase_id) DO NOTHING""",
                (ownership_id,str(row[0]),purchase,str(row[1]),str(row[2]),str(row[3])),
            )
            connection.commit()
        return {
            "purchase_id": purchase,
            "state": "SETTLED",
            "ownership_created": True,
            "settlement_reference_recorded": True,
            "payment_capture_performed_by_this_module": False,
            "sika_execution_performed": False,
            "human_authority_final": True,
        }
