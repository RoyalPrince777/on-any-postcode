"""Owner-scoped, read-only bridge from OAP Fashion drafts to OAP Commerce.

No new tables, orders, publication, payments, manufacturing, or supplier calls.
A durable Fashion catalogue requires separately reviewed storage and migration.
"""
from __future__ import annotations

from collections.abc import Mapping

from .fashion_first_party import FashionDraft, FashionError, identity


def fashion_market_projection(
    *, actor_id: object, draft: FashionDraft, commerce: Mapping[str, object]
) -> dict[str, object]:
    """Reconcile an approved OAP Fashion draft to an existing seller-owned product.

    Caller supplies a trusted, owner-scoped commerce_dashboard projection.
    Never accept an untrusted client-provided commerce object as proof.
    """
    owner = identity(actor_id)
    if owner != identity(draft.owner_identity_id):
        raise FashionError("not_product_owner")
    if commerce.get("organ") != "OAP Commerce Core":
        raise FashionError("untrusted_commerce_projection")
    products = commerce.get("products")
    if not isinstance(products, list):
        raise FashionError("commerce_products_unavailable")
    matches = [p for p in products if isinstance(p, dict) and p.get("product_id") == draft.product_id]
    if len(matches) != 1:
        raise FashionError("owned_market_product_not_found")
    product = matches[0]
    if product.get("name") != draft.name:
        raise FashionError("fashion_market_product_mismatch")
    if product.get("active") is not True:
        raise FashionError("market_product_inactive")
    projection = draft.market_projection(owner)
    variants = projection["variants"]
    if any(v["price_minor"] != product.get("price_minor")
           or v["currency"] != product.get("currency") for v in variants):
        raise FashionError("fashion_market_price_mismatch")
    return {
        "organ": "OAP Fashion × OAP Market",
        "product_id": draft.product_id,
        "owner_identity_id": owner,
        "fashion": projection,
        "market_product": {
            "product_id": product["product_id"],
            "name": product["name"],
            "price_minor": product["price_minor"],
            "currency": product["currency"],
        },
        "source": "owner_scoped_commerce_dashboard",
        "durable_fashion_storage_verified": False,
        "publication_performed": False,
        "inventory_verified": False,
        "payment_performed": False,
        "external_fulfilment_performed": False,
        "human_authority_final": True,
    }
