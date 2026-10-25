"""Owner-only barber SIKA price editing on OAP Direct's existing inventory.

This updates uncommitted, future, certified appointment slots only. It never
creates money, invents availability, replaces historical prices or authorises
a payment. Owner identity is always taken from authenticated server state.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

from . import barber_supply_extension, postgres_db

MAX_PRICE_MINOR = 1_000_000  # Up to 10,000.00 SIKA; bounded business input.


def _identity(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, AttributeError, ValueError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _price_minor(amount: object) -> int:
    if isinstance(amount, bool):
        raise ValueError("sika_price_invalid")
    raw = str(amount if amount is not None else "").strip()
    if not raw or len(raw) > 24:
        raise ValueError("sika_price_invalid")
    try:
        amount_decimal = Decimal(raw)
    except (ValueError, InvalidOperation) as exc:
        raise ValueError("sika_price_invalid") from exc
    if (
        not amount_decimal.is_finite()
        or amount_decimal <= 0
        or amount_decimal * 100 != (amount_decimal * 100).to_integral_value()
    ):
        raise ValueError("sika_price_invalid")
    minor = int(amount_decimal * 100)
    if minor > MAX_PRICE_MINOR:
        raise ValueError("sika_price_exceeds_limit")
    return minor


def _ready() -> None:
    if not barber_supply_extension.status().get("schema_ready"):
        raise RuntimeError("barber_supply_schema_not_ready")


def owner_slots(*, owner_identity_id: object) -> dict[str, object]:
    _ready()
    owner = _identity(owner_identity_id, "owner_identity_id")
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(
            """SELECT s.slot_id,l.listing_id,l.title,p.display_name,s.starts_at,
                      s.ends_at,s.price_minor,s.currency,s.capacity_held,
                      s.capacity_confirmed,s.state,s.observed_at
               FROM oap_supply_inventory_slots s
               JOIN oap_supply_listings l ON l.listing_id=s.listing_id
               JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
               WHERE p.owner_identity_id=%s AND p.supplier_type='service'
                 AND p.state='CERTIFIED' AND p.commercial_terms_state='CERTIFIED'
                 AND l.category='barber' AND l.state='ACTIVE'
                 AND s.starts_at>CURRENT_TIMESTAMP
               ORDER BY s.starts_at ASC LIMIT 100""",
            (owner,),
        ).fetchall()
    slots = [
        {
            "slot_id": str(r[0]),
            "listing_id": str(r[1]),
            "service": str(r[2]),
            "business": str(r[3]),
            "starts_at": r[4].isoformat(),
            "ends_at": r[5].isoformat(),
            "amount_sika": f"{Decimal(int(r[6])) / 100:.2f}",
            "currency": str(r[7]),
            "editable": (
                str(r[7]) == "GBP"
                and int(r[8]) == 0
                and int(r[9]) == 0
                and str(r[10]) == "ACTIVE"
            ),
            "observed_at": r[11].isoformat(),
        }
        for r in rows
    ]
    return {
        "component": "OAP Barber Owner Pricing",
        "slots": slots,
        "count": len(slots),
        "owner_scoped": True,
        "price_anchor": "1 SIKA = 1 GBP",
        "supplier_approval_required": True,
        "payment_enabled": False,
        "money_moved": False,
    }


def update_price(
    *, owner_identity_id: object, slot_id: object, amount_sika: object
) -> dict[str, object]:
    _ready()
    owner = _identity(owner_identity_id, "owner_identity_id")
    slot = _identity(slot_id, "slot_id")
    minor = _price_minor(amount_sika)
    with postgres_db.connect() as connection:
        row = connection.execute(
            """UPDATE oap_supply_inventory_slots s
               SET price_minor=%s,observed_at=CURRENT_TIMESTAMP,
                   updated_at=CURRENT_TIMESTAMP
               FROM oap_supply_listings l,oap_supply_suppliers p
               WHERE s.slot_id=%s AND s.listing_id=l.listing_id
                 AND l.supplier_id=p.supplier_id
                 AND p.owner_identity_id=%s
                 AND p.supplier_type='service'
                 AND p.state='CERTIFIED'
                 AND p.commercial_terms_state='CERTIFIED'
                 AND l.category='barber' AND l.state='ACTIVE'
                 AND s.state='ACTIVE' AND s.starts_at>CURRENT_TIMESTAMP
                 AND s.currency='GBP'
                 AND s.capacity_held=0 AND s.capacity_confirmed=0
               RETURNING s.slot_id,s.price_minor,s.observed_at""",
            (minor, slot, owner),
        ).fetchone()
        if row is None:
            raise PermissionError("slot_not_owned_or_price_locked")
        connection.commit()
    return {
        "slot_id": str(row[0]),
        "amount_sika": f"{Decimal(int(row[1])) / 100:.2f}",
        "currency": "GBP",
        "observed_at": row[2].isoformat(),
        "owner_scoped": True,
        "booked_prices_unchanged": True,
        "payment_authorised": False,
        "settlement_proven": False,
        "money_moved": False,
    }
