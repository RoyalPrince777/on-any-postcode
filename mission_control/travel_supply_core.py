"""First-party OAP Supply Core for direct marketplace inventory.

OAP owns direct-supplier records, listings, availability/pricing, reservation
holds and reservation evidence. Replaceable external suppliers remain separate.
No migration runs at import/startup time. Schema changes require explicit Human
Authority approval through ``oap-init-travel-supply --yes``.

Payment capture, Pass issuance and commission settlement remain separately
governed provider/compliance gates.
"""
from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from . import postgres_db

SUPPLY_CORE_MIGRATION_VERSION = "0007_oap_supply_core"
SUPPLY_CORE_REVISION = "2026-09-04-v1"
SUPPLY_CORE_TABLES = frozenset(
    {
        "oap_supply_suppliers",
        "oap_supply_listings",
        "oap_supply_inventory_slots",
        "oap_supply_reservation_holds",
        "oap_supply_reservations",
    }
)
SUPPLY_CATEGORIES = frozenset(
    {"stay", "attraction", "activity", "car_rental", "transport", "event"}
)
SUPPLIER_TYPES = frozenset(
    {"accommodation", "experience", "mobility", "venue", "mixed"}
)
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")

SUPPLY_CORE_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_supply_suppliers (
        supplier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
        display_name TEXT NOT NULL,
        supplier_type TEXT NOT NULL
            CHECK (supplier_type IN ('accommodation','experience','mobility','venue','mixed')),
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','REVIEW_REQUIRED','CERTIFIED','SUSPENDED','CLOSED')),
        commercial_terms_state TEXT NOT NULL DEFAULT 'REVIEW_REQUIRED'
            CHECK (commercial_terms_state IN ('REVIEW_REQUIRED','CERTIFIED','SUSPENDED')),
        commission_basis_points INTEGER NOT NULL DEFAULT 0
            CHECK (commission_basis_points BETWEEN 0 AND 10000),
        service_fee_basis_points INTEGER NOT NULL DEFAULT 0
            CHECK (service_fee_basis_points BETWEEN 0 AND 10000),
        terms_version TEXT NOT NULL DEFAULT 'none',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_supply_supplier_state_updated
        ON oap_supply_suppliers(state, updated_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_supply_listings (
        listing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        supplier_id UUID NOT NULL REFERENCES oap_supply_suppliers(supplier_id)
            ON DELETE CASCADE,
        category TEXT NOT NULL
            CHECK (category IN ('stay','attraction','activity','car_rental','transport','event')),
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        place_label TEXT NOT NULL,
        postcode TEXT,
        borough TEXT,
        country TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','REVIEW_REQUIRED','ACTIVE','SUSPENDED','ARCHIVED')),
        idempotency_key TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(supplier_id,idempotency_key))""",
    """CREATE INDEX IF NOT EXISTS ix_supply_listing_discovery
        ON oap_supply_listings(category, country, state, updated_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_supply_inventory_slots (
        slot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        listing_id UUID NOT NULL REFERENCES oap_supply_listings(listing_id)
            ON DELETE CASCADE,
        starts_at TIMESTAMPTZ NOT NULL,
        ends_at TIMESTAMPTZ NOT NULL,
        capacity_total INTEGER NOT NULL CHECK (capacity_total BETWEEN 1 AND 100000),
        capacity_held INTEGER NOT NULL DEFAULT 0 CHECK (capacity_held >= 0),
        capacity_confirmed INTEGER NOT NULL DEFAULT 0 CHECK (capacity_confirmed >= 0),
        price_minor BIGINT NOT NULL CHECK (price_minor >= 0),
        currency TEXT NOT NULL,
        price_basis TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (state IN ('ACTIVE','PAUSED','SOLD_OUT','CLOSED')),
        observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (ends_at > starts_at),
        CHECK (capacity_held + capacity_confirmed <= capacity_total),
        UNIQUE(listing_id,starts_at,ends_at))""",
    """CREATE INDEX IF NOT EXISTS ix_supply_inventory_lookup
        ON oap_supply_inventory_slots(listing_id, state, starts_at, ends_at)""",
    """CREATE TABLE IF NOT EXISTS oap_supply_reservation_holds (
        hold_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        slot_id UUID NOT NULL REFERENCES oap_supply_inventory_slots(slot_id)
            ON DELETE RESTRICT,
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 999),
        amount_minor BIGINT NOT NULL CHECK (amount_minor >= 0),
        currency TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'HELD'
            CHECK (state IN ('HELD','CONVERTED','RELEASED','EXPIRED')),
        expires_at TIMESTAMPTZ NOT NULL,
        idempotency_key TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(buyer_identity_id,idempotency_key))""",
    """CREATE INDEX IF NOT EXISTS ix_supply_hold_expiry
        ON oap_supply_reservation_holds(state, expires_at)""",
    """CREATE TABLE IF NOT EXISTS oap_supply_reservations (
        reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        hold_id UUID NOT NULL UNIQUE REFERENCES oap_supply_reservation_holds(hold_id)
            ON DELETE RESTRICT,
        listing_id UUID NOT NULL REFERENCES oap_supply_listings(listing_id)
            ON DELETE RESTRICT,
        supplier_id UUID NOT NULL REFERENCES oap_supply_suppliers(supplier_id)
            ON DELETE RESTRICT,
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 999),
        total_amount_minor BIGINT NOT NULL CHECK (total_amount_minor >= 0),
        currency TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PENDING_SUPPLIER_CONFIRMATION'
            CHECK (state IN ('PENDING_SUPPLIER_CONFIRMATION','CONFIRMED',
                             'DECLINED','CANCELLED','EXPIRED','FAILED')),
        supplier_confirmation_reference TEXT,
        payment_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (payment_state IN ('PROVIDER_REQUIRED','CREATED','AUTHORIZED',
                                     'CAPTURED','CANCELLED','FAILED')),
        pass_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (pass_state IN ('PROVIDER_REQUIRED','READY','ISSUED','REVOKED','FAILED')),
        commission_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (commission_state IN ('PROVIDER_REQUIRED','CALCULATED','SETTLED','VOID')),
        human_confirmed BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_supply_reservation_buyer_created
        ON oap_supply_reservations(buyer_identity_id, created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_supply_reservation_supplier_created
        ON oap_supply_reservations(supplier_id, created_at DESC)""",
)
SUPPLY_CORE_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SUPPLY_CORE_SCHEMA_STATEMENTS).encode()
).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _text(value: object, *, name: str, maximum: int, required: bool = True) -> str:
    text = " ".join(str(value or "").strip().split())
    if required and not text:
        raise ValueError(f"{name}_required")
    if len(text) > maximum:
        raise ValueError(f"{name}_too_long")
    return text


def _idempotency(value: object) -> str:
    key = str(value or "").strip()
    if not _IDEMPOTENCY.fullmatch(key):
        raise ValueError("invalid_idempotency_key")
    return key


def _currency(value: object) -> str:
    currency = str(value or "").strip().upper()
    if not _CURRENCY.fullmatch(currency):
        raise ValueError("invalid_currency")
    return currency


def _timestamp(value: object, name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid_{name}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _integer(value: object, name: str, *, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{name}") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"invalid_{name}")
    return number


def supply_core_schema_status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "migration": SUPPLY_CORE_MIGRATION_VERSION,
        "checksum": SUPPLY_CORE_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "tables": 0,
        "expected_tables": len(SUPPLY_CORE_TABLES),
        "error": None,
    }
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                ).fetchall()
            }
            result["tables"] = len(SUPPLY_CORE_TABLES & tables)
            if not SUPPLY_CORE_TABLES <= tables:
                result["error"] = "supply_core_schema_pending"
                return result
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (SUPPLY_CORE_MIGRATION_VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != SUPPLY_CORE_MIGRATION_CHECKSUM:
                result["error"] = "supply_core_migration_not_verified"
                return result
            result["schema_ready"] = True
            return result
    except Exception:  # noqa: BLE001
        result["error"] = "supply_core_store_unavailable"
        return result


def init_supply_core_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    """Apply the first-party supply schema only after explicit Human approval."""

    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        raise RuntimeError("Base PostgreSQL schema must be ready first")
    if dry_run:
        return {
            "dry_run": True,
            "migration": SUPPLY_CORE_MIGRATION_VERSION,
            "checksum": SUPPLY_CORE_MIGRATION_CHECKSUM,
            "tables": len(SUPPLY_CORE_TABLES),
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800007,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (SUPPLY_CORE_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != SUPPLY_CORE_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied supply-core migration checksum mismatch")
        if row is None:
            for statement in SUPPLY_CORE_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (SUPPLY_CORE_MIGRATION_VERSION, SUPPLY_CORE_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return supply_core_schema_status()


def status() -> dict[str, Any]:
    """Return truthful direct-marketplace readiness and live evidence counts."""

    schema = supply_core_schema_status()
    result: dict[str, Any] = {
        "component": "OAP Supply Core",
        "revision": SUPPLY_CORE_REVISION,
        "first_party": True,
        "software_ready": True,
        "schema_ready": bool(schema.get("schema_ready")),
        "schema": schema,
        "certified_supplier_count": 0,
        "active_listing_count": 0,
        "live_inventory_slot_count": 0,
        "confirmed_reservation_count": 0,
        "live_direct_supply": False,
        "direct_booking_runtime_ready": False,
        "payment_capture_live": False,
        "pass_issuance_live": False,
        "commission_settlement_live": False,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "external_provider_authority": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
    }
    if not result["schema_ready"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            certified = connection.execute(
                "SELECT COUNT(*) FROM oap_supply_suppliers WHERE state='CERTIFIED'"
            ).fetchone()
            listings = connection.execute(
                "SELECT COUNT(*) FROM oap_supply_listings WHERE state='ACTIVE'"
            ).fetchone()
            slots = connection.execute(
                """SELECT COUNT(*) FROM oap_supply_inventory_slots s
                   JOIN oap_supply_listings l ON l.listing_id=s.listing_id
                   JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
                   WHERE s.state='ACTIVE' AND s.ends_at>CURRENT_TIMESTAMP
                     AND s.capacity_total>s.capacity_held+s.capacity_confirmed
                     AND l.state='ACTIVE' AND p.state='CERTIFIED'"""
            ).fetchone()
            reservations = connection.execute(
                "SELECT COUNT(*) FROM oap_supply_reservations WHERE state='CONFIRMED'"
            ).fetchone()
        result["certified_supplier_count"] = int(certified[0] if certified else 0)
        result["active_listing_count"] = int(listings[0] if listings else 0)
        result["live_inventory_slot_count"] = int(slots[0] if slots else 0)
        result["confirmed_reservation_count"] = int(reservations[0] if reservations else 0)
        result["live_direct_supply"] = result["live_inventory_slot_count"] > 0
        result["direct_booking_runtime_ready"] = bool(
            result["certified_supplier_count"] > 0 and result["live_inventory_slot_count"] > 0
        )
        return result
    except Exception:  # noqa: BLE001
        result["schema_ready"] = False
        result["schema"]["error"] = "supply_core_status_query_failed"
        return result


class PostgresTravelSupplyStore:
    """Durable direct-supplier marketplace operations with bounded state changes."""

    def create_supplier(
        self,
        *,
        owner_identity_id: object,
        display_name: object,
        supplier_type: object,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        name = _text(display_name, name="supplier_display_name", maximum=180)
        kind = str(supplier_type or "").strip().casefold()
        if kind not in SUPPLIER_TYPES:
            raise ValueError("invalid_supplier_type")
        with postgres_db.connect() as connection:
            identity = connection.execute(
                "SELECT 1 FROM users WHERE id=%s AND status='active' LIMIT 1",
                (owner,),
            ).fetchone()
            if identity is None:
                raise PermissionError("active_identity_required")
            row = connection.execute(
                """INSERT INTO oap_supply_suppliers
                   (owner_identity_id,display_name,supplier_type)
                   VALUES (%s,%s,%s)
                   ON CONFLICT (owner_identity_id) DO UPDATE SET
                     display_name=EXCLUDED.display_name,
                     supplier_type=EXCLUDED.supplier_type,
                     updated_at=CURRENT_TIMESTAMP
                   RETURNING supplier_id,display_name,supplier_type,state,
                             commercial_terms_state,updated_at""",
                (owner, name, kind),
            ).fetchone()
            connection.commit()
        return {
            "supplier_id": str(row[0]),
            "display_name": str(row[1]),
            "supplier_type": str(row[2]),
            "state": str(row[3]),
            "commercial_terms_state": str(row[4]),
            "updated_at": row[5].isoformat(),
            "certified": str(row[3]) == "CERTIFIED",
        }

    def submit_supplier_for_review(
        self, *, owner_identity_id: object, supplier_id: object
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        supplier = _uuid(supplier_id, "supplier_id")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_supply_suppliers
                   SET state='REVIEW_REQUIRED',updated_at=CURRENT_TIMESTAMP
                   WHERE supplier_id=%s AND owner_identity_id=%s AND state='DRAFT'
                   RETURNING state,updated_at""",
                (supplier, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("supplier_not_reviewable")
            connection.commit()
        return {"state": str(row[0]), "updated_at": row[1].isoformat()}

    def certify_supplier(
        self,
        *,
        supplier_id: object,
        human_authority_approved: bool,
        commission_basis_points: object = 0,
        service_fee_basis_points: object = 0,
        terms_version: object = "v1",
    ) -> dict[str, Any]:
        if not human_authority_approved:
            raise PermissionError("human_authority_approval_required")
        supplier = _uuid(supplier_id, "supplier_id")
        commission = _integer(
            commission_basis_points,
            "commission_basis_points",
            minimum=0,
            maximum=10000,
        )
        service_fee = _integer(
            service_fee_basis_points,
            "service_fee_basis_points",
            minimum=0,
            maximum=10000,
        )
        terms = _text(terms_version, name="terms_version", maximum=80)
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_supply_suppliers
                   SET state='CERTIFIED',commercial_terms_state='CERTIFIED',
                       commission_basis_points=%s,service_fee_basis_points=%s,
                       terms_version=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE supplier_id=%s AND state='REVIEW_REQUIRED'
                   RETURNING state,commercial_terms_state,commission_basis_points,
                             service_fee_basis_points,terms_version,updated_at""",
                (commission, service_fee, terms, supplier),
            ).fetchone()
            if row is None:
                raise ValueError("supplier_not_ready_for_certification")
            connection.commit()
        return {
            "state": str(row[0]),
            "commercial_terms_state": str(row[1]),
            "commission_basis_points": int(row[2]),
            "service_fee_basis_points": int(row[3]),
            "terms_version": str(row[4]),
            "updated_at": row[5].isoformat(),
            "commission_settled": False,
        }

    def create_listing(
        self,
        *,
        owner_identity_id: object,
        supplier_id: object,
        category: object,
        title: object,
        place_label: object,
        country: object,
        idempotency_key: object,
        description: object = "",
        postcode: object = None,
        borough: object = None,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        supplier = _uuid(supplier_id, "supplier_id")
        category_value = str(category or "").strip().casefold()
        if category_value not in SUPPLY_CATEGORIES:
            raise ValueError("invalid_supply_category")
        title_value = _text(title, name="listing_title", maximum=180)
        description_value = _text(
            description, name="listing_description", maximum=4000, required=False
        )
        place = _text(place_label, name="place_label", maximum=240)
        country_value = _text(country, name="country", maximum=120)
        postcode_value = _text(postcode, name="postcode", maximum=32, required=False) or None
        borough_value = _text(borough, name="borough", maximum=120, required=False) or None
        key = _idempotency(idempotency_key)
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT state FROM oap_supply_suppliers
                   WHERE supplier_id=%s AND owner_identity_id=%s""",
                (supplier, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("supplier_not_owned")
            row = connection.execute(
                """INSERT INTO oap_supply_listings
                   (supplier_id,category,title,description,place_label,postcode,
                    borough,country,idempotency_key)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (supplier_id,idempotency_key) DO UPDATE SET
                     title=EXCLUDED.title,description=EXCLUDED.description,
                     place_label=EXCLUDED.place_label,postcode=EXCLUDED.postcode,
                     borough=EXCLUDED.borough,country=EXCLUDED.country,
                     updated_at=CURRENT_TIMESTAMP
                   RETURNING listing_id,category,title,place_label,country,state,updated_at""",
                (
                    supplier,
                    category_value,
                    title_value,
                    description_value,
                    place,
                    postcode_value,
                    borough_value,
                    country_value,
                    key,
                ),
            ).fetchone()
            connection.commit()
        return {
            "listing_id": str(row[0]),
            "category": str(row[1]),
            "title": str(row[2]),
            "place_label": str(row[3]),
            "country": str(row[4]),
            "state": str(row[5]),
            "updated_at": row[6].isoformat(),
        }

    def activate_listing(
        self,
        *,
        owner_identity_id: object,
        listing_id: object,
        human_authority_approved: bool,
    ) -> dict[str, Any]:
        if not human_authority_approved:
            raise PermissionError("human_authority_approval_required")
        owner = _uuid(owner_identity_id, "owner_identity_id")
        listing = _uuid(listing_id, "listing_id")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_supply_listings l
                   SET state='ACTIVE',updated_at=CURRENT_TIMESTAMP
                   FROM oap_supply_suppliers s
                   WHERE l.listing_id=%s AND l.supplier_id=s.supplier_id
                     AND s.owner_identity_id=%s AND s.state='CERTIFIED'
                     AND s.commercial_terms_state='CERTIFIED'
                     AND l.state IN ('DRAFT','REVIEW_REQUIRED','SUSPENDED')
                   RETURNING l.state,l.updated_at""",
                (listing, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("listing_activation_not_authorized")
            connection.commit()
        return {"state": str(row[0]), "updated_at": row[1].isoformat()}

    def set_inventory_slot(
        self,
        *,
        owner_identity_id: object,
        listing_id: object,
        starts_at: object,
        ends_at: object,
        capacity_total: object,
        price_minor: object,
        currency: object,
        price_basis: object,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        listing = _uuid(listing_id, "listing_id")
        start = _timestamp(starts_at, "starts_at")
        end = _timestamp(ends_at, "ends_at")
        if end <= start:
            raise ValueError("inventory_window_invalid")
        capacity = _integer(capacity_total, "capacity_total", minimum=1, maximum=100000)
        price = _integer(price_minor, "price_minor", minimum=0, maximum=10**12)
        currency_value = _currency(currency)
        basis = _text(price_basis, name="price_basis", maximum=180)
        with postgres_db.connect() as connection:
            listing_row = connection.execute(
                """SELECT l.state,s.state,s.commercial_terms_state
                   FROM oap_supply_listings l
                   JOIN oap_supply_suppliers s ON s.supplier_id=l.supplier_id
                   WHERE l.listing_id=%s AND s.owner_identity_id=%s""",
                (listing, owner),
            ).fetchone()
            if listing_row is None:
                raise PermissionError("listing_not_owned")
            if tuple(str(value) for value in listing_row) != (
                "ACTIVE",
                "CERTIFIED",
                "CERTIFIED",
            ):
                raise PermissionError("listing_not_live")
            row = connection.execute(
                """INSERT INTO oap_supply_inventory_slots
                   (listing_id,starts_at,ends_at,capacity_total,price_minor,currency,price_basis)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (listing_id,starts_at,ends_at) DO UPDATE SET
                     capacity_total=EXCLUDED.capacity_total,
                     price_minor=EXCLUDED.price_minor,currency=EXCLUDED.currency,
                     price_basis=EXCLUDED.price_basis,state='ACTIVE',
                     observed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
                   WHERE oap_supply_inventory_slots.capacity_held
                         + oap_supply_inventory_slots.capacity_confirmed
                         <= EXCLUDED.capacity_total
                   RETURNING slot_id,starts_at,ends_at,capacity_total,capacity_held,
                             capacity_confirmed,price_minor,currency,price_basis,state,
                             observed_at""",
                (listing, start, end, capacity, price, currency_value, basis),
            ).fetchone()
            if row is None:
                raise ValueError("capacity_below_existing_commitments")
            connection.commit()
        return {
            "slot_id": str(row[0]),
            "starts_at": row[1].isoformat(),
            "ends_at": row[2].isoformat(),
            "capacity_total": int(row[3]),
            "capacity_held": int(row[4]),
            "capacity_confirmed": int(row[5]),
            "price_minor": int(row[6]),
            "currency": str(row[7]),
            "price_basis": str(row[8]),
            "state": str(row[9]),
            "observed_at": row[10].isoformat(),
            "observed_not_inferred": True,
        }

    def quote(
        self,
        *,
        listing_id: object,
        starts_at: object,
        ends_at: object,
        quantity: object = 1,
    ) -> dict[str, Any]:
        listing = _uuid(listing_id, "listing_id")
        start = _timestamp(starts_at, "starts_at")
        end = _timestamp(ends_at, "ends_at")
        qty = _integer(quantity, "quantity", minimum=1, maximum=999)
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT s.slot_id,l.title,l.place_label,l.category,s.starts_at,s.ends_at,
                          s.capacity_total,s.capacity_held,s.capacity_confirmed,
                          s.price_minor,s.currency,s.price_basis,s.observed_at,p.supplier_id,
                          p.display_name
                   FROM oap_supply_inventory_slots s
                   JOIN oap_supply_listings l ON l.listing_id=s.listing_id
                   JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
                   WHERE l.listing_id=%s AND s.starts_at=%s AND s.ends_at=%s
                     AND s.state='ACTIVE' AND l.state='ACTIVE' AND p.state='CERTIFIED'
                     AND p.commercial_terms_state='CERTIFIED'
                   LIMIT 1""",
                (listing, start, end),
            ).fetchone()
        if row is None:
            raise ValueError("direct_supply_not_available")
        available = int(row[6]) - int(row[7]) - int(row[8])
        if available < qty:
            raise ValueError("insufficient_availability")
        return {
            "source": "oap_direct",
            "slot_id": str(row[0]),
            "listing_id": listing,
            "title": str(row[1]),
            "place_label": str(row[2]),
            "category": str(row[3]),
            "starts_at": row[4].isoformat(),
            "ends_at": row[5].isoformat(),
            "available_quantity": available,
            "requested_quantity": qty,
            "unit_price_minor": int(row[9]),
            "total_price_minor": int(row[9]) * qty,
            "currency": str(row[10]),
            "price_basis": str(row[11]),
            "observed_at": row[12].isoformat(),
            "supplier_id": str(row[13]),
            "supplier_name": str(row[14]),
            "provider_authority": False,
            "observed_not_inferred": True,
        }

    def create_hold(
        self,
        *,
        buyer_identity_id: object,
        listing_id: object,
        starts_at: object,
        ends_at: object,
        quantity: object,
        idempotency_key: object,
        hold_minutes: object = 15,
    ) -> dict[str, Any]:
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        listing = _uuid(listing_id, "listing_id")
        start = _timestamp(starts_at, "starts_at")
        end = _timestamp(ends_at, "ends_at")
        qty = _integer(quantity, "quantity", minimum=1, maximum=999)
        minutes = _integer(hold_minutes, "hold_minutes", minimum=1, maximum=60)
        key = _idempotency(idempotency_key)
        with postgres_db.connect() as connection:
            connection.execute(
                """UPDATE oap_supply_reservation_holds h
                   SET state='EXPIRED',updated_at=CURRENT_TIMESTAMP
                   WHERE h.state='HELD' AND h.expires_at<=CURRENT_TIMESTAMP"""
            )
            expired = connection.execute(
                """SELECT slot_id,COALESCE(SUM(quantity),0)
                   FROM oap_supply_reservation_holds
                   WHERE state='EXPIRED' AND updated_at=CURRENT_TIMESTAMP
                   GROUP BY slot_id"""
            ).fetchall()
            for slot_id, expired_quantity in expired:
                connection.execute(
                    """UPDATE oap_supply_inventory_slots
                       SET capacity_held=GREATEST(0,capacity_held-%s),
                           updated_at=CURRENT_TIMESTAMP
                       WHERE slot_id=%s""",
                    (int(expired_quantity), slot_id),
                )
            existing = connection.execute(
                """SELECT hold_id,slot_id,quantity,amount_minor,currency,state,expires_at
                   FROM oap_supply_reservation_holds
                   WHERE buyer_identity_id=%s AND idempotency_key=%s""",
                (buyer, key),
            ).fetchone()
            if existing is not None:
                connection.commit()
                return {
                    "hold_id": str(existing[0]),
                    "slot_id": str(existing[1]),
                    "quantity": int(existing[2]),
                    "amount_minor": int(existing[3]),
                    "currency": str(existing[4]),
                    "state": str(existing[5]),
                    "expires_at": existing[6].isoformat(),
                    "idempotent_replay": True,
                }
            slot = connection.execute(
                """SELECT s.slot_id,s.capacity_total,s.capacity_held,s.capacity_confirmed,
                          s.price_minor,s.currency
                   FROM oap_supply_inventory_slots s
                   JOIN oap_supply_listings l ON l.listing_id=s.listing_id
                   JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
                   WHERE l.listing_id=%s AND s.starts_at=%s AND s.ends_at=%s
                     AND s.state='ACTIVE' AND l.state='ACTIVE' AND p.state='CERTIFIED'
                     AND p.commercial_terms_state='CERTIFIED'
                   FOR UPDATE""",
                (listing, start, end),
            ).fetchone()
            if slot is None:
                raise ValueError("direct_supply_not_available")
            available = int(slot[1]) - int(slot[2]) - int(slot[3])
            if available < qty:
                raise ValueError("insufficient_availability")
            amount = int(slot[4]) * qty
            hold = connection.execute(
                """INSERT INTO oap_supply_reservation_holds
                   (slot_id,buyer_identity_id,quantity,amount_minor,currency,
                    expires_at,idempotency_key)
                   VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP+(%s * INTERVAL '1 minute'),%s)
                   RETURNING hold_id,state,expires_at,created_at""",
                (slot[0], buyer, qty, amount, str(slot[5]), minutes, key),
            ).fetchone()
            connection.execute(
                """UPDATE oap_supply_inventory_slots
                   SET capacity_held=capacity_held+%s,updated_at=CURRENT_TIMESTAMP
                   WHERE slot_id=%s""",
                (qty, slot[0]),
            )
            connection.commit()
        return {
            "hold_id": str(hold[0]),
            "slot_id": str(slot[0]),
            "quantity": qty,
            "amount_minor": amount,
            "currency": str(slot[5]),
            "state": str(hold[1]),
            "expires_at": hold[2].isoformat(),
            "created_at": hold[3].isoformat(),
            "reservation_confirmed": False,
            "payment_captured": False,
        }

    def create_reservation(
        self,
        *,
        buyer_identity_id: object,
        hold_id: object,
        human_confirmed: bool,
    ) -> dict[str, Any]:
        if not human_confirmed:
            raise PermissionError("human_confirmation_required")
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        hold = _uuid(hold_id, "hold_id")
        with postgres_db.connect() as connection:
            hold_row = connection.execute(
                """SELECT h.slot_id,h.quantity,h.amount_minor,h.currency,h.state,h.expires_at,
                          l.listing_id,l.supplier_id
                   FROM oap_supply_reservation_holds h
                   JOIN oap_supply_inventory_slots s ON s.slot_id=h.slot_id
                   JOIN oap_supply_listings l ON l.listing_id=s.listing_id
                   WHERE h.hold_id=%s AND h.buyer_identity_id=%s FOR UPDATE""",
                (hold, buyer),
            ).fetchone()
            if hold_row is None:
                raise PermissionError("hold_not_owned")
            if str(hold_row[4]) != "HELD" or hold_row[5] <= datetime.now(UTC):
                raise ValueError("hold_not_active")
            reservation = connection.execute(
                """INSERT INTO oap_supply_reservations
                   (hold_id,listing_id,supplier_id,buyer_identity_id,quantity,
                    total_amount_minor,currency,human_confirmed)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE)
                   ON CONFLICT (hold_id) DO UPDATE SET updated_at=CURRENT_TIMESTAMP
                   RETURNING reservation_id,state,payment_state,pass_state,
                             commission_state,created_at""",
                (
                    hold,
                    hold_row[6],
                    hold_row[7],
                    buyer,
                    int(hold_row[1]),
                    int(hold_row[2]),
                    str(hold_row[3]),
                ),
            ).fetchone()
            connection.execute(
                """UPDATE oap_supply_reservation_holds
                   SET state='CONVERTED',updated_at=CURRENT_TIMESTAMP WHERE hold_id=%s""",
                (hold,),
            )
            connection.commit()
        return {
            "reservation_id": str(reservation[0]),
            "state": str(reservation[1]),
            "payment_state": str(reservation[2]),
            "pass_state": str(reservation[3]),
            "commission_state": str(reservation[4]),
            "created_at": reservation[5].isoformat(),
            "supplier_confirmation_required": True,
            "payment_captured": False,
            "pass_issued": False,
            "commission_settled": False,
        }

    def confirm_reservation(
        self,
        *,
        owner_identity_id: object,
        reservation_id: object,
        supplier_confirmation_reference: object,
        supplier_confirmed: bool,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        reservation = _uuid(reservation_id, "reservation_id")
        reference = _text(
            supplier_confirmation_reference,
            name="supplier_confirmation_reference",
            maximum=180,
        )
        if not supplier_confirmed:
            raise PermissionError("supplier_confirmation_required")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT r.hold_id,r.quantity,h.slot_id,r.state
                   FROM oap_supply_reservations r
                   JOIN oap_supply_suppliers p ON p.supplier_id=r.supplier_id
                   JOIN oap_supply_reservation_holds h ON h.hold_id=r.hold_id
                   WHERE r.reservation_id=%s AND p.owner_identity_id=%s FOR UPDATE""",
                (reservation, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("reservation_not_owned_by_supplier")
            if str(row[3]) == "CONFIRMED":
                current = connection.execute(
                    """SELECT state,supplier_confirmation_reference,payment_state,pass_state,
                              commission_state,updated_at
                       FROM oap_supply_reservations WHERE reservation_id=%s""",
                    (reservation,),
                ).fetchone()
                connection.commit()
                return {
                    "state": str(current[0]),
                    "supplier_confirmation_reference": str(current[1]),
                    "payment_state": str(current[2]),
                    "pass_state": str(current[3]),
                    "commission_state": str(current[4]),
                    "updated_at": current[5].isoformat(),
                    "idempotent_replay": True,
                }
            if str(row[3]) != "PENDING_SUPPLIER_CONFIRMATION":
                raise ValueError("reservation_not_confirmable")
            updated = connection.execute(
                """UPDATE oap_supply_reservations
                   SET state='CONFIRMED',supplier_confirmation_reference=%s,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE reservation_id=%s
                   RETURNING state,payment_state,pass_state,commission_state,updated_at""",
                (reference, reservation),
            ).fetchone()
            connection.execute(
                """UPDATE oap_supply_inventory_slots
                   SET capacity_held=GREATEST(0,capacity_held-%s),
                       capacity_confirmed=capacity_confirmed+%s,
                       state=CASE
                         WHEN capacity_confirmed+%s >= capacity_total THEN 'SOLD_OUT'
                         ELSE state END,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE slot_id=%s""",
                (int(row[1]), int(row[1]), int(row[1]), row[2]),
            )
            connection.commit()
        return {
            "state": str(updated[0]),
            "supplier_confirmation_reference": reference,
            "payment_state": str(updated[1]),
            "pass_state": str(updated[2]),
            "commission_state": str(updated[3]),
            "updated_at": updated[4].isoformat(),
            "reservation_confirmed": True,
            "payment_captured": False,
            "pass_issued": False,
            "commission_settled": False,
        }
