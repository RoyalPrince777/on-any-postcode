"""First-party supplier/manufacturer network for OAP Market.

OAP stays the customer-facing store and canonical order owner. This module can
create made-to-order products atomically with their design and supplier records,
but it never calls a supplier API, places an external supplier order, captures
payment, transfers money, or dispatches a carrier.
"""

from __future__ import annotations

import json
import re
import uuid
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from . import postgres_db, product_store

SUPPLIER_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
STATES = {"DRAFT", "READY", "STOPPED", "RECOVERY_REQUIRED"}
DESIGN_STATES = {"DRAFT", "READY", "STOPPED", "RECOVERY_REQUIRED"}


class SupplierNetworkUnavailable(RuntimeError):
    """Raised when Supplier Network state cannot be read or written safely."""


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _clean(value: object, *, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _bounded_strings(values: object, *, limit: int, item_limit: int, code: str) -> list[str]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(code)
    result = []
    for raw in values[:limit]:
        value = _clean(raw, limit=item_limit)
        if value and value not in result:
            result.append(value)
    if not result:
        raise ValueError(code)
    return result


def _price_minor(value: object) -> int:
    try:
        amount = Decimal(str(value or "").strip()).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid_product_price") from exc
    if amount < 0 or amount > Decimal(1000000):
        raise ValueError("invalid_product_price")
    return int(amount * 100)


class SupplierNetworkStore:
    """Durable product→manufacturer mapping with no external execution."""

    @staticmethod
    def _table_exists(connection, table_name: str) -> bool:
        row = connection.execute(
            """SELECT 1 FROM information_schema.tables
               WHERE table_schema='public' AND table_name=%s LIMIT 1""",
            (table_name,),
        ).fetchone()
        return row is not None

    def _ensure_schema(self, connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS oap_market_supplier_bindings (
                binding_id UUID PRIMARY KEY,
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                supplier_slug TEXT NOT NULL,
                supplier_label TEXT NOT NULL,
                supplier_product_ref TEXT NOT NULL,
                supplier_variant_ref TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL,
                stop_reason TEXT NOT NULL DEFAULT '',
                evidence_reference TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS oap_market_design_products (
                design_id UUID PRIMARY KEY,
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                garment_type TEXT NOT NULL,
                artwork_reference TEXT NOT NULL,
                placements JSONB NOT NULL DEFAULT '[]'::jsonb,
                colors JSONB NOT NULL DEFAULT '[]'::jsonb,
                sizes JSONB NOT NULL DEFAULT '[]'::jsonb,
                made_to_order BOOLEAN NOT NULL DEFAULT TRUE,
                state TEXT NOT NULL,
                stop_reason TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id)
            )
            """
        )

    def create_made_to_order_product(
        self,
        *,
        seller_identity_id: object,
        name: object,
        description: object,
        price: object,
        garment_type: object,
        artwork_reference: object,
        placements: object,
        colors: object,
        sizes: object,
        supplier_slug: object,
        supplier_label: object,
        supplier_product_ref: object,
        supplier_variant_ref: object = "",
        evidence_reference: object = "",
    ) -> dict[str, Any]:
        """Atomically create listing + design + supplier mapping.

        The product is visible as a Market listing, but order intents remain
        blocked until the supplier/design state is explicitly marked READY.
        """

        seller = _uuid(seller_identity_id, "invalid_seller_identity")
        name_value = _clean(name, limit=160)
        description_value = _clean(description, limit=3000)
        garment = _clean(garment_type, limit=120)
        artwork = _clean(artwork_reference, limit=500)
        slug = _clean(supplier_slug, limit=64).lower()
        label = _clean(supplier_label, limit=120)
        product_ref = _clean(supplier_product_ref, limit=240)
        variant_ref = _clean(supplier_variant_ref, limit=240)
        evidence = _clean(evidence_reference, limit=500)
        price_minor = _price_minor(price)
        placement_values = _bounded_strings(
            placements, limit=8, item_limit=40, code="design_placements_required"
        )
        color_values = _bounded_strings(
            colors, limit=24, item_limit=40, code="design_colors_required"
        )
        size_values = _bounded_strings(
            sizes, limit=24, item_limit=20, code="design_sizes_required"
        )

        if not name_value:
            raise ValueError("product_name_required")
        if not garment:
            raise ValueError("garment_type_required")
        if not artwork:
            raise ValueError("artwork_reference_required")
        if not SUPPLIER_SLUG.fullmatch(slug):
            raise ValueError("invalid_supplier_slug")
        if not label:
            raise ValueError("supplier_label_required")
        if not product_ref:
            raise ValueError("supplier_product_ref_required")

        design_id = str(uuid.uuid4())
        binding_id = str(uuid.uuid4())
        try:
            with postgres_db.connect() as connection:
                self._ensure_schema(connection)
                active = connection.execute(
                    "SELECT 1 FROM users WHERE id=%s AND status='active'", (seller,)
                ).fetchone()
                if active is None:
                    raise ValueError("seller_unavailable")
                recent = connection.execute(
                    """SELECT COUNT(*) FROM products WHERE seller_id=%s
                       AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'""",
                    (seller,),
                ).fetchone()
                if recent and int(recent[0]) >= product_store.MAX_LISTINGS_PER_HOUR:
                    raise ValueError("market_rate_limit")

                product_row = connection.execute(
                    """INSERT INTO products(
                           seller_id,name,description,price_minor,currency,active
                       ) VALUES (%s,%s,%s,%s,'GBP',TRUE)
                       RETURNING id""",
                    (seller, name_value, description_value, price_minor),
                ).fetchone()
                product = str(product_row[0])

                connection.execute(
                    """INSERT INTO oap_market_supplier_bindings(
                           binding_id,product_id,seller_identity_id,supplier_slug,
                           supplier_label,supplier_product_ref,supplier_variant_ref,
                           state,evidence_reference
                       ) VALUES (%s,%s,%s,%s,%s,%s,%s,'DRAFT',%s)""",
                    (
                        binding_id,
                        product,
                        seller,
                        slug,
                        label,
                        product_ref,
                        variant_ref,
                        evidence,
                    ),
                )
                connection.execute(
                    """INSERT INTO oap_market_design_products(
                           design_id,product_id,seller_identity_id,garment_type,
                           artwork_reference,placements,colors,sizes,made_to_order,state
                       ) VALUES (
                           %s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,TRUE,'DRAFT'
                       )""",
                    (
                        design_id,
                        product,
                        seller,
                        garment,
                        artwork,
                        json.dumps(placement_values),
                        json.dumps(color_values),
                        json.dumps(size_values),
                    ),
                )
                connection.commit()
        except (PermissionError, ValueError):
            raise
        except Exception as exc:
            raise SupplierNetworkUnavailable("made_to_order_product_create_failed") from exc

        return {
            "product_id": product,
            "design_id": design_id,
            "binding_id": binding_id,
            "made_to_order": True,
            "garment_type": garment,
            "supplier": {"slug": slug, "label": label},
            "state": "DRAFT",
            "order_intent_allowed": False,
            "supplier_api_called": False,
            "external_order_created": False,
            "payment_capture_performed": False,
            "money_transfer_performed": False,
            "human_authority_final": True,
        }

    def bind_product(
        self,
        *,
        seller_identity_id: object,
        product_id: object,
        supplier_slug: object,
        supplier_label: object,
        supplier_product_ref: object,
        supplier_variant_ref: object = "",
        evidence_reference: object = "",
    ) -> dict[str, Any]:
        seller = _uuid(seller_identity_id, "invalid_seller_identity")
        product = _uuid(product_id, "invalid_product_id")
        slug = _clean(supplier_slug, limit=64).lower()
        label = _clean(supplier_label, limit=120)
        product_ref = _clean(supplier_product_ref, limit=240)
        variant_ref = _clean(supplier_variant_ref, limit=240)
        evidence = _clean(evidence_reference, limit=500)

        if not SUPPLIER_SLUG.fullmatch(slug):
            raise ValueError("invalid_supplier_slug")
        if not label:
            raise ValueError("supplier_label_required")
        if not product_ref:
            raise ValueError("supplier_product_ref_required")

        binding_id = str(uuid.uuid4())
        try:
            with postgres_db.connect() as connection:
                self._ensure_schema(connection)
                owned = connection.execute(
                    """SELECT 1 FROM products
                       WHERE id=%s AND seller_id=%s AND active=TRUE LIMIT 1""",
                    (product, seller),
                ).fetchone()
                if owned is None:
                    raise PermissionError("product_not_owned")
                row = connection.execute(
                    """INSERT INTO oap_market_supplier_bindings(
                           binding_id,product_id,seller_identity_id,supplier_slug,
                           supplier_label,supplier_product_ref,supplier_variant_ref,
                           state,evidence_reference
                       ) VALUES (%s,%s,%s,%s,%s,%s,%s,'DRAFT',%s)
                       ON CONFLICT (product_id) DO UPDATE SET
                           supplier_slug=EXCLUDED.supplier_slug,
                           supplier_label=EXCLUDED.supplier_label,
                           supplier_product_ref=EXCLUDED.supplier_product_ref,
                           supplier_variant_ref=EXCLUDED.supplier_variant_ref,
                           state='DRAFT',
                           stop_reason='',
                           evidence_reference=EXCLUDED.evidence_reference,
                           updated_at=CURRENT_TIMESTAMP
                       RETURNING binding_id,state""",
                    (
                        binding_id,
                        product,
                        seller,
                        slug,
                        label,
                        product_ref,
                        variant_ref,
                        evidence,
                    ),
                ).fetchone()
                connection.commit()
        except (PermissionError, ValueError):
            raise
        except Exception as exc:
            raise SupplierNetworkUnavailable("supplier_binding_write_failed") from exc

        return {
            "binding_id": str(row[0]),
            "product_id": product,
            "supplier": {"slug": slug, "label": label},
            "state": str(row[1]),
            "order_intent_allowed": False,
            "external_order_created": False,
            "supplier_api_called": False,
            "payment_capture_performed": False,
            "money_transfer_performed": False,
            "human_authority_final": True,
        }

    def mark_ready(
        self,
        *,
        seller_identity_id: object,
        product_id: object,
        evidence_reference: object,
    ) -> dict[str, Any]:
        seller = _uuid(seller_identity_id, "invalid_seller_identity")
        product = _uuid(product_id, "invalid_product_id")
        evidence = _clean(evidence_reference, limit=500)
        if not evidence:
            raise ValueError("supplier_evidence_required")
        try:
            with postgres_db.connect() as connection:
                self._ensure_schema(connection)
                row = connection.execute(
                    """UPDATE oap_market_supplier_bindings
                       SET state='READY',evidence_reference=%s,
                           stop_reason='',updated_at=CURRENT_TIMESTAMP
                       WHERE product_id=%s AND seller_identity_id=%s
                       RETURNING binding_id,supplier_slug,supplier_label""",
                    (evidence, product, seller),
                ).fetchone()
                if row is None:
                    raise PermissionError("supplier_binding_not_owned")
                connection.execute(
                    """UPDATE oap_market_design_products
                       SET state='READY',stop_reason='',updated_at=CURRENT_TIMESTAMP
                       WHERE product_id=%s AND seller_identity_id=%s""",
                    (product, seller),
                )
                connection.commit()
        except (PermissionError, ValueError):
            raise
        except Exception as exc:
            raise SupplierNetworkUnavailable("supplier_binding_ready_failed") from exc
        return {
            "binding_id": str(row[0]),
            "product_id": product,
            "supplier": {"slug": str(row[1]), "label": str(row[2])},
            "state": "READY",
            "order_intent_allowed": False,
            "provider_execution_enabled": False,
            "external_order_created": False,
            "human_authority_final": True,
        }

    def stop(
        self,
        *,
        seller_identity_id: object,
        product_id: object,
        reason: object = "human_stop",
    ) -> dict[str, Any]:
        seller = _uuid(seller_identity_id, "invalid_seller_identity")
        product = _uuid(product_id, "invalid_product_id")
        why = _clean(reason, limit=240) or "human_stop"
        try:
            with postgres_db.connect() as connection:
                self._ensure_schema(connection)
                row = connection.execute(
                    """UPDATE oap_market_supplier_bindings
                       SET state='STOPPED',stop_reason=%s,updated_at=CURRENT_TIMESTAMP
                       WHERE product_id=%s AND seller_identity_id=%s
                       RETURNING binding_id,supplier_slug,supplier_label""",
                    (why, product, seller),
                ).fetchone()
                if row is None:
                    raise PermissionError("supplier_binding_not_owned")
                connection.execute(
                    """UPDATE oap_market_design_products
                       SET state='STOPPED',stop_reason=%s,updated_at=CURRENT_TIMESTAMP
                       WHERE product_id=%s AND seller_identity_id=%s""",
                    (why, product, seller),
                )
                connection.commit()
        except (PermissionError, ValueError):
            raise
        except Exception as exc:
            raise SupplierNetworkUnavailable("supplier_binding_stop_failed") from exc
        return {
            "binding_id": str(row[0]),
            "product_id": product,
            "supplier": {"slug": str(row[1]), "label": str(row[2])},
            "state": "STOPPED",
            "stop_reason": why,
            "order_intent_allowed": False,
            "external_execution_allowed": False,
            "human_authority_final": True,
        }

    def owner_bindings(self, *, seller_identity_id: object) -> list[dict[str, Any]]:
        seller = _uuid(seller_identity_id, "invalid_seller_identity")
        try:
            with postgres_db.connect(readonly=True) as connection:
                if not self._table_exists(connection, "oap_market_supplier_bindings"):
                    return []
                rows = connection.execute(
                    """SELECT binding_id,product_id,supplier_slug,supplier_label,
                              supplier_product_ref,supplier_variant_ref,state,
                              stop_reason,evidence_reference,updated_at
                       FROM oap_market_supplier_bindings
                       WHERE seller_identity_id=%s
                       ORDER BY updated_at DESC""",
                    (seller,),
                ).fetchall()
        except Exception as exc:
            raise SupplierNetworkUnavailable("supplier_binding_read_failed") from exc
        return [
            {
                "binding_id": str(row[0]),
                "product_id": str(row[1]),
                "supplier": {"slug": str(row[2]), "label": str(row[3])},
                "supplier_product_ref": str(row[4]),
                "supplier_variant_ref": str(row[5] or ""),
                "state": str(row[6]),
                "stop_reason": str(row[7] or ""),
                "evidence_reference": str(row[8] or ""),
                "updated_at": row[9].isoformat(),
                "order_intent_allowed": False,
                "external_execution_allowed": False,
                "human_authority_final": True,
            }
            for row in rows
        ]

    def public_projection(self, *, product_ids: list[object]) -> dict[str, dict[str, Any]]:
        """Return public-safe made-to-order state without claiming supplier identity."""

        products = []
        for value in product_ids[:200]:
            try:
                products.append(_uuid(value, "invalid_product_id"))
            except ValueError:
                continue
        if not products:
            return {}
        try:
            with postgres_db.connect(readonly=True) as connection:
                if not self._table_exists(connection, "oap_market_supplier_bindings"):
                    return {}
                if not self._table_exists(connection, "oap_market_design_products"):
                    return {}
                rows = connection.execute(
                    """SELECT b.product_id,b.state,
                              d.garment_type,d.colors,d.sizes,d.made_to_order,d.state
                       FROM oap_market_supplier_bindings b
                       LEFT JOIN oap_market_design_products d
                         ON d.product_id=b.product_id
                       WHERE b.product_id = ANY(%s::uuid[])""",
                    (products,),
                ).fetchall()
        except Exception as exc:
            raise SupplierNetworkUnavailable("supplier_projection_read_failed") from exc
        return {
            str(row[0]): {
                "fulfilment_state": str(row[1]),
                "made_to_order": bool(row[5]) if row[5] is not None else False,
                "garment_type": str(row[2] or ""),
                "colors": list(row[3] or []),
                "sizes": list(row[4] or []),
                "design_state": str(row[6] or ""),
                "supplier_identity_public": False,
                "provider_execution_enabled": False,
                "order_intent_allowed": False,
                "external_execution_allowed": False,
            }
            for row in rows
        }

    def order_intent_allowed(self, *, product_id: object) -> dict[str, object]:
        """Fail closed for supplier-managed products until provider execution is proven.

        Ordinary non-supplier products retain existing Market ordering. A mapped
        made-to-order product may be internally READY for design/catalogue review,
        but that is not authority to accept an order that depends on an external
        manufacturer. A later provider adapter must replace this lock with
        evidence-backed execution readiness.
        """

        product = _uuid(product_id, "invalid_product_id")
        try:
            with postgres_db.connect(readonly=True) as connection:
                if not self._table_exists(connection, "oap_market_supplier_bindings"):
                    return {"allowed": True, "supplier_managed": False}
                row = connection.execute(
                    """SELECT state FROM oap_market_supplier_bindings
                       WHERE product_id=%s LIMIT 1""",
                    (product,),
                ).fetchone()
        except Exception as exc:
            raise SupplierNetworkUnavailable("supplier_order_gate_failed") from exc
        if row is None:
            return {"allowed": True, "supplier_managed": False}
        return {
            "allowed": False,
            "supplier_managed": True,
            "supplier_state": str(row[0]),
            "provider_execution_enabled": False,
            "reason": "supplier_execution_not_proven",
        }


STORE = SupplierNetworkStore()


def schema_status() -> dict[str, object]:
    """Read production schema readiness without creating or changing tables."""

    try:
        with postgres_db.connect(readonly=True) as connection:
            supplier_bindings_ready = SupplierNetworkStore._table_exists(
                connection, "oap_market_supplier_bindings"
            )
            design_products_ready = SupplierNetworkStore._table_exists(
                connection, "oap_market_design_products"
            )
    except (postgres_db._driver().Error, RuntimeError, OSError):
        return {
            "database_reachable": False,
            "supplier_bindings_ready": False,
            "design_products_ready": False,
            "schema_ready": False,
            "provider_execution_enabled": False,
        }

    return {
        "database_reachable": True,
        "supplier_bindings_ready": supplier_bindings_ready,
        "design_products_ready": design_products_ready,
        "schema_ready": supplier_bindings_ready and design_products_ready,
        "provider_execution_enabled": False,
    }


def truth_status() -> dict[str, object]:
    return {
        "organ": "OAP Supplier Network",
        "canonical_front_door": "OAP Market",
        "supports_oap_owned_products": True,
        "supports_certified_public_merchants": True,
        "supports_made_to_order_products": True,
        "supplier_examples": ["tapstitch"],
        "inventory_required_by_oap": False,
        "supplier_api_called": False,
        "external_order_created": False,
        "payment_capture_performed": False,
        "money_transfer_performed": False,
        "sika_settlement_remains_separate": True,
        "provider_adapter_required_for_execution": True,
        "human_authority_final": True,
    }
