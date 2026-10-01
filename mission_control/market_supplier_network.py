"""First-party supplier mappings for OAP Market.

This module records which external manufacturer may fulfil an OAP-owned Market
product. It never calls a supplier API, captures payment, transfers money,
places an external order, or hands work to a carrier.

OAP remains the customer-facing store and canonical order owner. Supplier
execution stays evidence-gated behind a later provider adapter.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from . import postgres_db

SUPPLIER_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
STATES = {"DRAFT", "READY", "STOPPED", "RECOVERY_REQUIRED"}


class SupplierNetworkUnavailable(RuntimeError):
    """Raised when the durable Supplier Network cannot be read or written safely."""


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _clean(value: object, *, limit: int) -> str:
    return str(value or "").strip()[:limit]


class SupplierNetworkStore:
    """Durable product→manufacturer mapping without external execution."""

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
            "external_execution_allowed": False,
            "human_authority_final": True,
        }

    def owner_bindings(self, *, seller_identity_id: object) -> list[dict[str, Any]]:
        seller = _uuid(seller_identity_id, "invalid_seller_identity")
        try:
            with postgres_db.connect(readonly=True) as connection:
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
                "external_execution_allowed": False,
                "human_authority_final": True,
            }
            for row in rows
        ]

    def public_projection(self, *, product_ids: list[object]) -> dict[str, dict[str, Any]]:
        """Return non-secret manufacturing labels for public Market cards."""

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
                rows = connection.execute(
                    """SELECT product_id,supplier_label,state
                       FROM oap_market_supplier_bindings
                       WHERE product_id = ANY(%s::uuid[])
                         AND state IN ('READY','STOPPED')""",
                    (products,),
                ).fetchall()
        except Exception as exc:
            raise SupplierNetworkUnavailable("supplier_projection_read_failed") from exc
        return {
            str(row[0]): {
                "manufacturer": str(row[1]),
                "fulfilment_state": str(row[2]),
                "external_execution_allowed": False,
            }
            for row in rows
        }


STORE = SupplierNetworkStore()


def truth_status() -> dict[str, object]:
    return {
        "organ": "OAP Supplier Network",
        "canonical_front_door": "OAP Market",
        "supports_oap_owned_products": True,
        "supports_certified_public_merchants": True,
        "supplier_examples": ["tapstitch"],
        "supplier_api_called": False,
        "external_order_created": False,
        "payment_capture_performed": False,
        "money_transfer_performed": False,
        "sika_settlement_remains_separate": True,
        "provider_adapter_required_for_execution": True,
        "human_authority_final": True,
    }
