"""Durable first-party product cores for OAP Music, Market and Post Office.

The module owns OAP-side records and workflow state. It never distributes music
to an external DSP, streams copyrighted media from an unapproved store, captures
money, pays royalties, hands parcels to a carrier or activates a physical Post
Office. Those consequential edges stay provider/Human-Authority gated.

Schema mutation is explicit only; status reads never create tables.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from . import postgres_db

PRODUCT_CORE_MIGRATION_VERSION = "0006_music_market_post_office"
PRODUCT_CORE_TABLES = frozenset(
    {
        "oap_music_releases",
        "oap_music_tracks",
        "oap_music_playlists",
        "oap_music_playlist_items",
        "oap_music_distribution_intents",
        "oap_music_royalty_reports",
        "oap_market_storefronts",
        "oap_market_orders",
        "oap_market_order_items",
        "oap_market_payment_intents",
        "oap_market_fulfilment_intents",
        "oap_post_offices",
        "oap_post_office_requests",
        "oap_post_office_parcels",
    }
)

PRODUCT_SUITE: tuple[dict[str, Any], ...] = (
    {
        "id": "music",
        "name": "OAP Music",
        "core": "OAP Tune Core",
        "purpose": "Artist catalogue, releases, playlists, rights, royalties and distribution workflow.",
        "own_equivalent": "TuneCore + Spotify-style first-party music layer",
        "external_lock": "External DSP delivery, licensed audio delivery and royalty payout require approved providers/rights.",
    },
    {
        "id": "market",
        "name": "OAP Market",
        "core": "OAP Commerce Core",
        "purpose": "Storefronts, products, orders, payment intents and fulfilment workflow.",
        "own_equivalent": "Shopify-style first-party commerce layer",
        "external_lock": "Card capture and third-party fulfilment require approved payment/fulfilment providers.",
    },
    {
        "id": "post-office",
        "name": "OAP Post Office",
        "core": "OAP Post Core",
        "purpose": "Digital and physical access hubs, service requests and parcel workflow.",
        "own_equivalent": "OAP-owned postcode access and service network",
        "external_lock": "Physical-site activation and carrier handoff require verified operations and approved carriers.",
    },
)

BLOCKED_EXTERNAL_ACTIONS = (
    "external_music_distribution",
    "unlicensed_audio_delivery",
    "royalty_payout",
    "payment_capture",
    "money_transfer",
    "external_fulfilment_handoff",
    "parcel_carrier_handoff",
    "physical_post_office_activation",
)

_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")
_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")
_RELEASE_TYPES = frozenset({"single", "ep", "album"})
_VISIBILITY = frozenset({"PRIVATE", "UNLISTED", "PUBLIC"})
_POST_SERVICE_TYPES = frozenset(
    {
        "MAIL",
        "PARCEL_COLLECTION",
        "PARCEL_DROP",
        "IDENTITY_SUPPORT",
        "MARKET_SUPPORT",
        "SIKA_SUPPORT",
        "HUMAN_SUPPORT",
    }
)

PRODUCT_CORE_SCHEMA_STATEMENTS = (
    """INSERT INTO oap_roles(role_id,name,authority_level) VALUES
        ('MUSIC_CREATOR','Certified Music Creator',5),
        ('MARKET_MERCHANT','Certified Market Merchant',5),
        ('POST_OFFICE_OPERATOR','Certified Post Office Operator',5)
        ON CONFLICT (role_id) DO NOTHING""",
    """CREATE TABLE IF NOT EXISTS oap_music_releases (
        release_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        title TEXT NOT NULL,
        release_type TEXT NOT NULL CHECK (release_type IN ('single','ep','album')),
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','REVIEW_REQUIRED','APPROVED','PUBLISHED','ARCHIVED')),
        rights_status TEXT NOT NULL DEFAULT 'SELF_DECLARED'
            CHECK (rights_status IN ('SELF_DECLARED','REVIEW_REQUIRED','VERIFIED','REJECTED')),
        external_distribution_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (external_distribution_state IN
                ('PROVIDER_REQUIRED','READY','SUBMITTED','DELIVERED','FAILED')),
        idempotency_key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_music_release_owner_created
        ON oap_music_releases(owner_identity_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_music_tracks (
        track_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        title TEXT NOT NULL,
        position SMALLINT NOT NULL CHECK (position BETWEEN 1 AND 99),
        media_ref TEXT NOT NULL,
        duration_ms INTEGER CHECK (duration_ms IS NULL OR duration_ms BETWEEN 1000 AND 7200000),
        explicit BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(release_id, position))""",
    """CREATE TABLE IF NOT EXISTS oap_music_playlists (
        playlist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        visibility TEXT NOT NULL DEFAULT 'PRIVATE'
            CHECK (visibility IN ('PRIVATE','UNLISTED','PUBLIC')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_music_playlist_items (
        playlist_id UUID NOT NULL REFERENCES oap_music_playlists(playlist_id)
            ON DELETE CASCADE,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id)
            ON DELETE CASCADE,
        position INTEGER NOT NULL CHECK (position > 0),
        added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (playlist_id, track_id),
        UNIQUE(playlist_id, position))""",
    """CREATE TABLE IF NOT EXISTS oap_music_distribution_intents (
        intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        release_id UUID NOT NULL UNIQUE REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (state IN ('PROVIDER_REQUIRED','READY','SUBMITTED','DELIVERED','FAILED','CANCELLED')),
        provider_reference TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_music_royalty_reports (
        report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        track_id UUID NOT NULL REFERENCES oap_music_tracks(track_id) ON DELETE RESTRICT,
        source TEXT NOT NULL,
        units BIGINT NOT NULL DEFAULT 0 CHECK (units >= 0),
        amount_minor BIGINT NOT NULL DEFAULT 0 CHECK (amount_minor >= 0),
        currency TEXT NOT NULL DEFAULT 'GBP',
        state TEXT NOT NULL DEFAULT 'ESTIMATE'
            CHECK (state IN ('ESTIMATE','VERIFIED','PAYOUT_PROVIDER_REQUIRED','PAID_EXTERNALLY')),
        period_start DATE,
        period_end DATE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_music_royalty_owner_created
        ON oap_music_royalty_reports(owner_identity_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_market_storefronts (
        storefront_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        seller_identity_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
        store_name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','REVIEW_REQUIRED','ACTIVE','SUSPENDED','CLOSED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_market_orders (
        order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        state TEXT NOT NULL DEFAULT 'PAYMENT_PROVIDER_REQUIRED'
            CHECK (state IN ('DRAFT','PLACED','PAYMENT_PROVIDER_REQUIRED','PAID',
                             'FULFILMENT_PROVIDER_REQUIRED','FULFILLED','CANCELLED','FAILED')),
        currency TEXT NOT NULL DEFAULT 'GBP',
        subtotal_minor BIGINT NOT NULL CHECK (subtotal_minor >= 0),
        idempotency_key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_market_order_buyer_created
        ON oap_market_orders(buyer_identity_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_market_order_items (
        order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL REFERENCES oap_market_orders(order_id) ON DELETE CASCADE,
        product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
        quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 99),
        unit_price_minor BIGINT NOT NULL CHECK (unit_price_minor >= 0),
        product_name TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_market_payment_intents (
        intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL UNIQUE REFERENCES oap_market_orders(order_id)
            ON DELETE CASCADE,
        amount_minor BIGINT NOT NULL CHECK (amount_minor >= 0),
        currency TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (state IN ('PROVIDER_REQUIRED','CREATED','AUTHORIZED','CAPTURED','CANCELLED','FAILED')),
        provider_reference TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_market_fulfilment_intents (
        fulfilment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL UNIQUE REFERENCES oap_market_orders(order_id)
            ON DELETE CASCADE,
        state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (state IN ('PROVIDER_REQUIRED','READY','HANDED_OFF','DELIVERED','CANCELLED','FAILED')),
        provider_reference TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_post_offices (
        post_office_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        postcode TEXT,
        borough TEXT,
        country TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PLANNED'
            CHECK (state IN ('PLANNED','PILOT_READY','ACTIVE','SUSPENDED','CLOSED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_post_office_requests (
        request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        post_office_id UUID REFERENCES oap_post_offices(post_office_id)
            ON DELETE SET NULL,
        service_type TEXT NOT NULL
            CHECK (service_type IN ('MAIL','PARCEL_COLLECTION','PARCEL_DROP',
                'IDENTITY_SUPPORT','MARKET_SUPPORT','SIKA_SUPPORT','HUMAN_SUPPORT')),
        state TEXT NOT NULL DEFAULT 'REQUESTED'
            CHECK (state IN ('REQUESTED','REVIEW_REQUIRED','READY','COMPLETED','CANCELLED')),
        details JSONB NOT NULL DEFAULT '{}'::jsonb,
        idempotency_key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_post_request_identity_created
        ON oap_post_office_requests(identity_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_post_office_parcels (
        parcel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        post_office_id UUID REFERENCES oap_post_offices(post_office_id)
            ON DELETE SET NULL,
        direction TEXT NOT NULL CHECK (direction IN ('INBOUND','OUTBOUND')),
        state TEXT NOT NULL DEFAULT 'CARRIER_REQUIRED'
            CHECK (state IN ('CREATED','AT_OAP_HUB','CARRIER_REQUIRED','HANDED_OFF',
                             'READY_FOR_COLLECTION','COLLECTED','RETURNED','CANCELLED')),
        oap_tracking_code TEXT NOT NULL UNIQUE,
        external_carrier_reference TEXT,
        idempotency_key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
)

PRODUCT_CORE_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(PRODUCT_CORE_SCHEMA_STATEMENTS).encode("utf-8")
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


def _active_identity(connection: Any, identity_id: str) -> None:
    row = connection.execute(
        "SELECT 1 FROM users WHERE id=%s AND status='active' LIMIT 1",
        (identity_id,),
    ).fetchone()
    if row is None:
        raise PermissionError("active_identity_required")


def product_core_schema_status() -> dict[str, Any]:
    """Read product-core readiness without mutating the database."""

    result: dict[str, Any] = {
        "migration": PRODUCT_CORE_MIGRATION_VERSION,
        "checksum": PRODUCT_CORE_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "tables": 0,
        "expected_tables": len(PRODUCT_CORE_TABLES),
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
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public'"
                ).fetchall()
            }
            result["tables"] = len(PRODUCT_CORE_TABLES & tables)
            if not PRODUCT_CORE_TABLES <= tables:
                result["error"] = "product_core_schema_pending"
                return result
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (PRODUCT_CORE_MIGRATION_VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != PRODUCT_CORE_MIGRATION_CHECKSUM:
                result["error"] = "product_core_migration_not_verified"
                return result
            result["schema_ready"] = True
            return result
    except Exception:  # noqa: BLE001 - redact database/provider details.
        result["error"] = "product_core_store_unavailable"
        return result


def init_product_core_schema(
    *, assume_yes: bool = False, dry_run: bool = False
) -> dict[str, Any]:
    """Apply product-core schema only after explicit Human Authority invocation."""

    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        raise RuntimeError("Base PostgreSQL schema must be ready first")
    if dry_run:
        return {
            "dry_run": True,
            "migration": PRODUCT_CORE_MIGRATION_VERSION,
            "checksum": PRODUCT_CORE_MIGRATION_CHECKSUM,
            "tables": len(PRODUCT_CORE_TABLES),
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800006,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (PRODUCT_CORE_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != PRODUCT_CORE_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied product-core migration checksum mismatch")
        if row is None:
            for statement in PRODUCT_CORE_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (PRODUCT_CORE_MIGRATION_VERSION, PRODUCT_CORE_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return product_core_schema_status()


def platform_status() -> dict[str, Any]:
    """Return truthful first-party readiness and external locks."""

    schema = product_core_schema_status()
    core_ready = bool(schema.get("schema_ready"))
    return {
        "component": "OAP Product Cores",
        "ready": core_ready,
        "schema": schema,
        "products": tuple(
            {
                **item,
                "oap_core_ready": core_ready,
                "external_edge_ready": False,
            }
            for item in PRODUCT_SUITE
        ),
        "blocked_external_actions": BLOCKED_EXTERNAL_ACTIONS,
        "human_authority_final": True,
        "independent_external_execution": False,
    }


class PostgresProductCoreStore:
    """Owner-scoped OAP product workflows with consequential edges disabled."""

    def create_release(
        self,
        *,
        owner_identity_id: object,
        title: object,
        release_type: object,
        idempotency_key: object,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        title_value = _text(title, name="release_title", maximum=180)
        kind = str(release_type or "").strip().casefold()
        if kind not in _RELEASE_TYPES:
            raise ValueError("invalid_release_type")
        key = _idempotency(idempotency_key)
        with postgres_db.connect() as connection:
            _active_identity(connection, owner)
            row = connection.execute(
                """INSERT INTO oap_music_releases
                   (owner_identity_id,title,release_type,idempotency_key)
                   VALUES (%s,%s,%s,%s)
                   ON CONFLICT (idempotency_key) DO UPDATE
                     SET idempotency_key=EXCLUDED.idempotency_key
                   RETURNING release_id,title,release_type,state,rights_status,
                             external_distribution_state,created_at""",
                (owner, title_value, kind, key),
            ).fetchone()
            connection.commit()
        return {
            "release_id": str(row[0]),
            "title": str(row[1]),
            "release_type": str(row[2]),
            "state": str(row[3]),
            "rights_status": str(row[4]),
            "distribution_state": str(row[5]),
            "created_at": row[6].isoformat(),
            "external_distribution_performed": False,
        }

    def add_track(
        self,
        *,
        owner_identity_id: object,
        release_id: object,
        title: object,
        position: object,
        media_ref: object,
        duration_ms: object = None,
        explicit: bool = False,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        title_value = _text(title, name="track_title", maximum=180)
        media = _text(media_ref, name="media_ref", maximum=512)
        try:
            track_position = int(position)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_track_position") from exc
        if not 1 <= track_position <= 99:
            raise ValueError("invalid_track_position")
        duration = None
        if duration_ms not in (None, ""):
            try:
                duration = int(duration_ms)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid_duration_ms") from exc
            if not 1000 <= duration <= 7_200_000:
                raise ValueError("invalid_duration_ms")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT state FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (release, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("release_not_owned")
            if str(row[0]) not in {"DRAFT", "REVIEW_REQUIRED"}:
                raise ValueError("release_not_editable")
            track = connection.execute(
                """INSERT INTO oap_music_tracks
                   (release_id,title,position,media_ref,duration_ms,explicit)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   RETURNING track_id,title,position,created_at""",
                (release, title_value, track_position, media, duration, bool(explicit)),
            ).fetchone()
            connection.commit()
        return {
            "track_id": str(track[0]),
            "title": str(track[1]),
            "position": int(track[2]),
            "created_at": track[3].isoformat(),
            "audio_delivery_enabled": False,
        }

    def submit_release_for_review(
        self, *, owner_identity_id: object, release_id: object
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        with postgres_db.connect() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM oap_music_tracks WHERE release_id=%s",
                (release,),
            ).fetchone()
            if not count or int(count[0]) < 1:
                raise ValueError("release_requires_track")
            row = connection.execute(
                """UPDATE oap_music_releases
                   SET state='REVIEW_REQUIRED',rights_status='REVIEW_REQUIRED',
                       updated_at=CURRENT_TIMESTAMP
                   WHERE release_id=%s AND owner_identity_id=%s
                     AND state IN ('DRAFT','REVIEW_REQUIRED')
                   RETURNING state,rights_status,external_distribution_state,updated_at""",
                (release, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("release_not_reviewable")
            connection.execute(
                """INSERT INTO oap_music_distribution_intents
                   (release_id,owner_identity_id,state)
                   VALUES (%s,%s,'PROVIDER_REQUIRED')
                   ON CONFLICT (release_id) DO NOTHING""",
                (release, owner),
            )
            connection.commit()
        return {
            "state": str(row[0]),
            "rights_status": str(row[1]),
            "distribution_state": str(row[2]),
            "updated_at": row[3].isoformat(),
            "requires_human_rights_review": True,
            "external_distribution_performed": False,
        }

    def create_playlist(
        self,
        *,
        owner_identity_id: object,
        title: object,
        visibility: object = "PRIVATE",
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        title_value = _text(title, name="playlist_title", maximum=180)
        visibility_value = str(visibility or "PRIVATE").strip().upper()
        if visibility_value not in _VISIBILITY:
            raise ValueError("invalid_playlist_visibility")
        with postgres_db.connect() as connection:
            _active_identity(connection, owner)
            row = connection.execute(
                """INSERT INTO oap_music_playlists
                   (owner_identity_id,title,visibility)
                   VALUES (%s,%s,%s)
                   RETURNING playlist_id,title,visibility,created_at""",
                (owner, title_value, visibility_value),
            ).fetchone()
            connection.commit()
        return {
            "playlist_id": str(row[0]),
            "title": str(row[1]),
            "visibility": str(row[2]),
            "created_at": row[3].isoformat(),
        }

    def create_storefront(
        self,
        *,
        seller_identity_id: object,
        store_name: object,
        slug: object,
    ) -> dict[str, Any]:
        seller = _uuid(seller_identity_id, "seller_identity_id")
        name_value = _text(store_name, name="store_name", maximum=180)
        slug_value = str(slug or "").strip().casefold()
        if not _SLUG.fullmatch(slug_value):
            raise ValueError("invalid_store_slug")
        with postgres_db.connect() as connection:
            _active_identity(connection, seller)
            row = connection.execute(
                """INSERT INTO oap_market_storefronts
                   (seller_identity_id,store_name,slug)
                   VALUES (%s,%s,%s)
                   ON CONFLICT (seller_identity_id) DO UPDATE SET
                     store_name=EXCLUDED.store_name,
                     slug=EXCLUDED.slug,
                     updated_at=CURRENT_TIMESTAMP
                   RETURNING storefront_id,store_name,slug,state,updated_at""",
                (seller, name_value, slug_value),
            ).fetchone()
            connection.commit()
        return {
            "storefront_id": str(row[0]),
            "store_name": str(row[1]),
            "slug": str(row[2]),
            "state": str(row[3]),
            "updated_at": row[4].isoformat(),
            "payment_capture_enabled": False,
        }

    def create_order_intent(
        self,
        *,
        buyer_identity_id: object,
        product_id: object,
        quantity: object,
        idempotency_key: object,
    ) -> dict[str, Any]:
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        product = _uuid(product_id, "product_id")
        key = _idempotency(idempotency_key)
        try:
            qty = int(quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_quantity") from exc
        if not 1 <= qty <= 99:
            raise ValueError("invalid_quantity")
        with postgres_db.connect() as connection:
            _active_identity(connection, buyer)
            product_row = connection.execute(
                """SELECT p.seller_id,p.name,p.price_minor,p.currency
                   FROM products p JOIN users u ON u.id=p.seller_id
                   WHERE p.id=%s AND p.active=TRUE AND u.status='active'
                   FOR SHARE""",
                (product,),
            ).fetchone()
            if product_row is None:
                raise ValueError("product_unavailable")
            seller = str(product_row[0])
            if seller == buyer:
                raise ValueError("cannot_buy_own_product")
            subtotal = int(product_row[2]) * qty
            order = connection.execute(
                """INSERT INTO oap_market_orders
                   (buyer_identity_id,seller_identity_id,state,currency,
                    subtotal_minor,idempotency_key)
                   VALUES (%s,%s,'PAYMENT_PROVIDER_REQUIRED',%s,%s,%s)
                   ON CONFLICT (idempotency_key) DO UPDATE
                     SET idempotency_key=EXCLUDED.idempotency_key
                   RETURNING order_id,state,currency,subtotal_minor,created_at""",
                (buyer, seller, str(product_row[3]), subtotal, key),
            ).fetchone()
            connection.execute(
                """INSERT INTO oap_market_order_items
                   (order_id,product_id,quantity,unit_price_minor,product_name)
                   SELECT %s,%s,%s,%s,%s
                   WHERE NOT EXISTS (
                     SELECT 1 FROM oap_market_order_items
                     WHERE order_id=%s AND product_id=%s)""",
                (
                    order[0],
                    product,
                    qty,
                    int(product_row[2]),
                    str(product_row[1]),
                    order[0],
                    product,
                ),
            )
            connection.execute(
                """INSERT INTO oap_market_payment_intents
                   (order_id,amount_minor,currency,state)
                   VALUES (%s,%s,%s,'PROVIDER_REQUIRED')
                   ON CONFLICT (order_id) DO NOTHING""",
                (order[0], subtotal, str(product_row[3])),
            )
            connection.execute(
                """INSERT INTO oap_market_fulfilment_intents(order_id,state)
                   VALUES (%s,'PROVIDER_REQUIRED')
                   ON CONFLICT (order_id) DO NOTHING""",
                (order[0],),
            )
            connection.commit()
        return {
            "order_id": str(order[0]),
            "state": str(order[1]),
            "currency": str(order[2]),
            "subtotal_minor": int(order[3]),
            "created_at": order[4].isoformat(),
            "payment_capture_performed": False,
            "fulfilment_handoff_performed": False,
        }

    def create_post_office_request(
        self,
        *,
        identity_id: object,
        service_type: object,
        details: dict[str, Any] | None,
        idempotency_key: object,
        post_office_id: object = None,
    ) -> dict[str, Any]:
        identity = _uuid(identity_id, "identity_id")
        service = str(service_type or "").strip().upper()
        if service not in _POST_SERVICE_TYPES:
            raise ValueError("invalid_post_office_service")
        key = _idempotency(idempotency_key)
        payload = dict(details or {})
        if len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False)) > 4096:
            raise ValueError("post_office_details_too_large")
        hub = None if post_office_id in (None, "") else _uuid(post_office_id, "post_office_id")
        with postgres_db.connect() as connection:
            _active_identity(connection, identity)
            if hub is not None:
                exists = connection.execute(
                    """SELECT 1 FROM oap_post_offices
                       WHERE post_office_id=%s AND state IN ('PILOT_READY','ACTIVE')""",
                    (hub,),
                ).fetchone()
                if exists is None:
                    raise ValueError("post_office_unavailable")
            row = connection.execute(
                """INSERT INTO oap_post_office_requests
                   (identity_id,post_office_id,service_type,details,idempotency_key)
                   VALUES (%s,%s,%s,%s::jsonb,%s)
                   ON CONFLICT (idempotency_key) DO UPDATE
                     SET idempotency_key=EXCLUDED.idempotency_key
                   RETURNING request_id,service_type,state,created_at""",
                (identity, hub, service, json.dumps(payload), key),
            ).fetchone()
            connection.commit()
        return {
            "request_id": str(row[0]),
            "service_type": str(row[1]),
            "state": str(row[2]),
            "created_at": row[3].isoformat(),
            "human_support_available_by_workflow": True,
            "external_action_performed": False,
        }

    def create_parcel_intent(
        self,
        *,
        owner_identity_id: object,
        direction: object,
        idempotency_key: object,
        post_office_id: object = None,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        direction_value = str(direction or "").strip().upper()
        if direction_value not in {"INBOUND", "OUTBOUND"}:
            raise ValueError("invalid_parcel_direction")
        key = _idempotency(idempotency_key)
        hub = None if post_office_id in (None, "") else _uuid(post_office_id, "post_office_id")
        tracking_code = "OAP-" + hashlib.sha256(
            f"{owner}:{key}".encode("utf-8")
        ).hexdigest()[:20].upper()
        with postgres_db.connect() as connection:
            _active_identity(connection, owner)
            row = connection.execute(
                """INSERT INTO oap_post_office_parcels
                   (owner_identity_id,post_office_id,direction,state,
                    oap_tracking_code,idempotency_key)
                   VALUES (%s,%s,%s,'CARRIER_REQUIRED',%s,%s)
                   ON CONFLICT (idempotency_key) DO UPDATE
                     SET idempotency_key=EXCLUDED.idempotency_key
                   RETURNING parcel_id,direction,state,oap_tracking_code,created_at""",
                (owner, hub, direction_value, tracking_code, key),
            ).fetchone()
            connection.commit()
        return {
            "parcel_id": str(row[0]),
            "direction": str(row[1]),
            "state": str(row[2]),
            "oap_tracking_code": str(row[3]),
            "created_at": row[4].isoformat(),
            "public_tracking": False,
            "carrier_handoff_performed": False,
        }
