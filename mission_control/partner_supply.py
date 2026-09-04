"""Audited short-lived partner-supply snapshots for OAP Travel.

External catalogue data is evidence, not OAP-owned inventory. Snapshots keep
provider provenance and expire quickly so stale availability/pricing cannot look
live. No schema is applied at import/startup time; migration requires explicit
Human Authority approval.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from oap.smi import supply_integration

from . import postgres_db

PARTNER_SUPPLY_MIGRATION_VERSION = "0008_partner_supply_snapshots"
PARTNER_SUPPLY_REVISION = "2026-09-04-v1"
PARTNER_SUPPLY_TABLES = frozenset(
    {"oap_partner_supply_snapshots", "oap_partner_supply_offers"}
)
MAX_SNAPSHOT_TTL = timedelta(hours=24)

PARTNER_SUPPLY_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_partner_supply_snapshots (
        snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        provider_id TEXT NOT NULL,
        search_key TEXT NOT NULL,
        category TEXT NOT NULL,
        source_scope TEXT NOT NULL,
        observed_at TIMESTAMPTZ NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL,
        source_digest TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (state IN ('ACTIVE','EXPIRED','REVOKED')),
        imported_by_role TEXT NOT NULL DEFAULT 'HUMAN_AUTHORITY'
            CHECK (imported_by_role='HUMAN_AUTHORITY'),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (expires_at > observed_at),
        UNIQUE(provider_id, source_digest))""",
    """CREATE INDEX IF NOT EXISTS ix_partner_supply_snapshot_live
        ON oap_partner_supply_snapshots(provider_id, category, state, expires_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_partner_supply_offers (
        offer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        snapshot_id UUID NOT NULL REFERENCES oap_partner_supply_snapshots(snapshot_id)
            ON DELETE CASCADE,
        source_offer_id TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        place_label TEXT NOT NULL,
        availability_state TEXT NOT NULL
            CHECK (availability_state IN ('available','limited','unavailable','unknown')),
        currency TEXT,
        total_price_minor BIGINT CHECK (total_price_minor IS NULL OR total_price_minor >= 0),
        price_basis TEXT,
        source_url TEXT NOT NULL,
        observed_at TIMESTAMPTZ NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (expires_at > observed_at),
        UNIQUE(snapshot_id, source_offer_id))""",
    """CREATE INDEX IF NOT EXISTS ix_partner_supply_offer_live
        ON oap_partner_supply_offers(category, availability_state, expires_at DESC)""",
)
PARTNER_SUPPLY_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(PARTNER_SUPPLY_SCHEMA_STATEMENTS).encode()
).hexdigest()


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


def _text(value: object, name: str, maximum: int) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        raise ValueError(f"{name}_required")
    if len(text) > maximum:
        raise ValueError(f"{name}_too_long")
    return text


def _price_minor(value: float | None) -> int | None:
    if value is None:
        return None
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid_partner_price") from exc
    return int(amount * 100)


def prepare_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a Founder-approved partner catalogue snapshot without writing it."""

    if payload.get("human_authority_approved") is not True:
        raise PermissionError("human_authority_approval_required")
    provider_id = _text(payload.get("provider_id"), "provider_id", 80).casefold()
    if supply_integration.provider(provider_id) is None:
        raise ValueError("unknown_supply_provider")
    search_key = _text(payload.get("search_key"), "search_key", 240)
    category = _text(payload.get("category"), "category", 40).casefold()
    source_scope = _text(payload.get("source_scope"), "source_scope", 240)
    observed_at = _timestamp(payload.get("observed_at"), "observed_at")
    expires_at = _timestamp(payload.get("expires_at"), "expires_at")
    if expires_at <= observed_at or expires_at - observed_at > MAX_SNAPSHOT_TTL:
        raise ValueError("partner_snapshot_ttl_must_be_within_24_hours")
    raw_offers = payload.get("offers")
    if not isinstance(raw_offers, list) or not raw_offers or len(raw_offers) > 100:
        raise ValueError("partner_offers_required_1_to_100")

    offers: list[dict[str, Any]] = []
    for raw in raw_offers:
        if not isinstance(raw, dict):
            raise TypeError("partner_offer_must_be_object")
        candidate = dict(raw)
        candidate["provider_id"] = provider_id
        candidate["category"] = category
        candidate.setdefault("observed_at", observed_at.isoformat())
        candidate.setdefault("expires_at", expires_at.isoformat())
        normalized = supply_integration.normalize_offer(candidate)
        offer_observed = _timestamp(normalized.observed_at, "offer_observed_at")
        offer_expires = _timestamp(normalized.expires_at or expires_at, "offer_expires_at")
        if offer_expires > expires_at or offer_observed < observed_at - timedelta(minutes=5):
            raise ValueError("offer_freshness_outside_snapshot_window")
        offers.append(
            {
                "source_offer_id": normalized.source_offer_id,
                "category": normalized.category,
                "title": normalized.title,
                "place_label": normalized.place_label,
                "availability_state": normalized.availability_state,
                "currency": normalized.currency,
                "total_price_minor": _price_minor(normalized.total_price),
                "price_basis": normalized.price_basis,
                "source_url": normalized.source_url,
                "observed_at": offer_observed,
                "expires_at": offer_expires,
            }
        )

    canonical = {
        "provider_id": provider_id,
        "search_key": search_key,
        "category": category,
        "source_scope": source_scope,
        "observed_at": observed_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "offers": [
            {
                **item,
                "observed_at": item["observed_at"].isoformat(),
                "expires_at": item["expires_at"].isoformat(),
            }
            for item in offers
        ],
    }
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {**canonical, "source_digest": digest, "offers": offers}


def schema_status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "migration": PARTNER_SUPPLY_MIGRATION_VERSION,
        "checksum": PARTNER_SUPPLY_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "tables": 0,
        "expected_tables": len(PARTNER_SUPPLY_TABLES),
        "error": None,
    }
    if not postgres_db.postgres_status().get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ).fetchall()
            tables = {str(row[0]) for row in rows}
            result["tables"] = len(PARTNER_SUPPLY_TABLES & tables)
            if not PARTNER_SUPPLY_TABLES <= tables:
                result["error"] = "partner_supply_schema_pending"
                return result
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (PARTNER_SUPPLY_MIGRATION_VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != PARTNER_SUPPLY_MIGRATION_CHECKSUM:
                result["error"] = "partner_supply_migration_not_verified"
                return result
            result["schema_ready"] = True
            return result
    except Exception:  # noqa: BLE001
        result["error"] = "partner_supply_store_unavailable"
        return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if not postgres_db.postgres_status().get("initialized"):
        raise RuntimeError("Base PostgreSQL schema must be ready first")
    if dry_run:
        return {
            "dry_run": True,
            "migration": PARTNER_SUPPLY_MIGRATION_VERSION,
            "checksum": PARTNER_SUPPLY_MIGRATION_CHECKSUM,
            "tables": len(PARTNER_SUPPLY_TABLES),
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800008,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (PARTNER_SUPPLY_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != PARTNER_SUPPLY_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied partner-supply migration checksum mismatch")
        if row is None:
            for statement in PARTNER_SUPPLY_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (PARTNER_SUPPLY_MIGRATION_VERSION, PARTNER_SUPPLY_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return schema_status()


def import_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_snapshot(payload)
    if not schema_status().get("schema_ready"):
        raise RuntimeError("partner_supply_schema_not_ready")
    with postgres_db.connect() as connection:
        row = connection.execute(
            """INSERT INTO oap_partner_supply_snapshots
               (provider_id,search_key,category,source_scope,observed_at,expires_at,
                source_digest,state,imported_by_role)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'ACTIVE','HUMAN_AUTHORITY')
               ON CONFLICT(provider_id,source_digest) DO UPDATE
               SET expires_at=EXCLUDED.expires_at,state='ACTIVE'
               RETURNING snapshot_id""",
            (
                prepared["provider_id"],
                prepared["search_key"],
                prepared["category"],
                prepared["source_scope"],
                prepared["observed_at"],
                prepared["expires_at"],
                prepared["source_digest"],
            ),
        ).fetchone()
        if row is None:
            raise RuntimeError("partner_snapshot_insert_failed")
        snapshot_id = str(row[0])
        connection.execute(
            "DELETE FROM oap_partner_supply_offers WHERE snapshot_id=%s", (snapshot_id,)
        )
        for offer in prepared["offers"]:
            connection.execute(
                """INSERT INTO oap_partner_supply_offers
                   (snapshot_id,source_offer_id,category,title,place_label,
                    availability_state,currency,total_price_minor,price_basis,
                    source_url,observed_at,expires_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    snapshot_id,
                    offer["source_offer_id"],
                    offer["category"],
                    offer["title"],
                    offer["place_label"],
                    offer["availability_state"],
                    offer["currency"],
                    offer["total_price_minor"],
                    offer["price_basis"],
                    offer["source_url"],
                    offer["observed_at"],
                    offer["expires_at"],
                ),
            )
        connection.commit()
    return {
        "snapshot_id": snapshot_id,
        "provider_id": prepared["provider_id"],
        "offer_count": len(prepared["offers"]),
        "expires_at": prepared["expires_at"],
        "source_digest": prepared["source_digest"],
        "external_provider_authority": False,
        "human_authority_final": True,
    }


def public_offers(*, category: object = None, limit: object = 24) -> dict[str, Any]:
    schema = schema_status()
    if not schema.get("schema_ready"):
        return {
            "component": "OAP Partner Supply",
            "ready": False,
            "offers": [],
            "count": 0,
            "error": "partner_supply_schema_not_ready",
        }
    category_value = str(category or "").strip().casefold() or None
    if category_value and category_value not in supply_integration.SUPPORTED_CATEGORIES:
        raise ValueError("invalid_partner_supply_category")
    try:
        row_limit = min(max(int(limit), 1), 50)
    except (TypeError, ValueError):
        row_limit = 24
    clauses = [
        "s.state='ACTIVE'",
        "s.expires_at>CURRENT_TIMESTAMP",
        "o.expires_at>CURRENT_TIMESTAMP",
        "o.availability_state IN ('available','limited')",
    ]
    params: list[object] = []
    if category_value:
        clauses.append("o.category=%s")
        params.append(category_value)
    params.append(row_limit)
    query = f"""SELECT s.provider_id,s.search_key,o.source_offer_id,o.category,o.title,
                       o.place_label,o.availability_state,o.currency,o.total_price_minor,
                       o.price_basis,o.source_url,o.observed_at,o.expires_at
                FROM oap_partner_supply_offers o
                JOIN oap_partner_supply_snapshots s ON s.snapshot_id=o.snapshot_id
                WHERE {' AND '.join(clauses)}
                ORDER BY o.observed_at DESC LIMIT %s"""
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    offers = [
        {
            "source": "partner_supply",
            "source_kind": "replaceable_external_supply",
            "provider_id": str(row[0]),
            "search_key": str(row[1]),
            "source_offer_id": str(row[2]),
            "category": str(row[3]),
            "title": str(row[4]),
            "place_label": str(row[5]),
            "availability_state": str(row[6]),
            "currency": str(row[7] or ""),
            "total_price_minor": int(row[8]) if row[8] is not None else None,
            "price_basis": str(row[9] or ""),
            "source_url": str(row[10]),
            "observed_at": row[11].isoformat(),
            "expires_at": row[12].isoformat(),
            "certified_oap_supplier": False,
            "observed_not_inferred": True,
            "provider_authority": False,
        }
        for row in rows
    ]
    return {
        "component": "OAP Partner Supply",
        "revision": PARTNER_SUPPLY_REVISION,
        "ready": True,
        "offers": offers,
        "count": len(offers),
        "external_provider_authority": False,
        "booking_execution_authorized": False,
        "payment_execution_authorized": False,
    }


def status() -> dict[str, Any]:
    schema = schema_status()
    result = {
        "component": "OAP Partner Supply",
        "revision": PARTNER_SUPPLY_REVISION,
        "schema": schema,
        "schema_ready": bool(schema.get("schema_ready")),
        "active_snapshot_count": 0,
        "live_offer_count": 0,
        "snapshot_ttl_hours": int(MAX_SNAPSHOT_TTL.total_seconds() // 3600),
        "copies_external_catalogue": False,
        "external_provider_authority": False,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "human_authority_final": True,
    }
    if not result["schema_ready"]:
        return result
    with postgres_db.connect(readonly=True) as connection:
        snapshots = connection.execute(
            """SELECT COUNT(*) FROM oap_partner_supply_snapshots
               WHERE state='ACTIVE' AND expires_at>CURRENT_TIMESTAMP"""
        ).fetchone()
        offers = connection.execute(
            """SELECT COUNT(*) FROM oap_partner_supply_offers o
               JOIN oap_partner_supply_snapshots s ON s.snapshot_id=o.snapshot_id
               WHERE s.state='ACTIVE' AND s.expires_at>CURRENT_TIMESTAMP
                 AND o.expires_at>CURRENT_TIMESTAMP
                 AND o.availability_state IN ('available','limited')"""
        ).fetchone()
    result["active_snapshot_count"] = int(snapshots[0] if snapshots else 0)
    result["live_offer_count"] = int(offers[0] if offers else 0)
    return result
