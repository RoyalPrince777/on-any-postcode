"""OAP Direct marketplace discovery and Founder-controlled supply operations.

This module sits on the existing first-party OAP Supply Core. It adds no schema,
brain, Intelligence World or autonomous commercial authority. Public discovery
only returns Certified supplier + ACTIVE listing + ACTIVE future inventory.
All marketplace writes are authenticated, human-triggered web operations and all
payment, Pass and commission execution remains separately gated.
"""
from __future__ import annotations

from typing import Any

from . import postgres_db, travel_supply_core

DIRECT_MARKETPLACE_REVISION = "2026-09-04-v2"
_PUBLIC_LIMIT_MAX = 50
_FOUNDER_LIMIT_MAX = 100
_STORE = travel_supply_core.PostgresTravelSupplyStore()


def _bounded_limit(value: object, *, default: int, maximum: int) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(limit, 1), maximum)


def _optional_text(value: object, maximum: int) -> str | None:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return None
    return text[:maximum]


def public_offers(
    *,
    category: object = None,
    country: object = None,
    limit: object = 24,
) -> dict[str, Any]:
    """Return only currently bookable, privacy-reduced OAP Direct supply."""

    schema = travel_supply_core.supply_core_schema_status()
    if not schema.get("schema_ready"):
        return {
            "component": "OAP Direct",
            "revision": DIRECT_MARKETPLACE_REVISION,
            "ready": False,
            "offers": [],
            "count": 0,
            "source": "oap_direct",
            "error": "supply_core_not_ready",
        }
    category_value = _optional_text(category, 40)
    if category_value is not None:
        category_value = category_value.casefold()
        if category_value not in travel_supply_core.SUPPLY_CATEGORIES:
            raise ValueError("invalid_supply_category")
    country_value = _optional_text(country, 120)
    row_limit = _bounded_limit(limit, default=24, maximum=_PUBLIC_LIMIT_MAX)
    clauses = [
        "s.state='ACTIVE'",
        "s.ends_at>CURRENT_TIMESTAMP",
        "s.capacity_total>s.capacity_held+s.capacity_confirmed",
        "l.state='ACTIVE'",
        "p.state='CERTIFIED'",
        "p.commercial_terms_state='CERTIFIED'",
    ]
    params: list[object] = []
    if category_value is not None:
        clauses.append("l.category=%s")
        params.append(category_value)
    if country_value is not None:
        clauses.append("LOWER(l.country)=LOWER(%s)")
        params.append(country_value)
    params.append(row_limit)
    query = f"""SELECT l.listing_id,s.slot_id,l.category,l.title,l.description,
                       l.place_label,l.postcode,l.borough,l.country,
                       s.starts_at,s.ends_at,s.capacity_total,s.capacity_held,
                       s.capacity_confirmed,s.price_minor,s.currency,s.price_basis,
                       s.observed_at,p.display_name
                FROM oap_supply_inventory_slots s
                JOIN oap_supply_listings l ON l.listing_id=s.listing_id
                JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
                WHERE {' AND '.join(clauses)}
                ORDER BY s.starts_at ASC,l.updated_at DESC
                LIMIT %s"""
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    offers: list[dict[str, Any]] = []
    for row in rows:
        available = max(0, int(row[11]) - int(row[12]) - int(row[13]))
        offers.append(
            {
                "source": "oap_direct",
                "listing_id": str(row[0]),
                "slot_id": str(row[1]),
                "category": str(row[2]),
                "title": str(row[3]),
                "description": str(row[4]),
                "place_label": str(row[5]),
                "postcode": str(row[6] or ""),
                "borough": str(row[7] or ""),
                "country": str(row[8]),
                "starts_at": row[9].isoformat(),
                "ends_at": row[10].isoformat(),
                "available_quantity": available,
                "unit_price_minor": int(row[14]),
                "currency": str(row[15]),
                "price_basis": str(row[16]),
                "observed_at": row[17].isoformat(),
                "supplier_name": str(row[18]),
                "certified_supplier": True,
                "observed_not_inferred": True,
                "provider_authority": False,
            }
        )
    return {
        "component": "OAP Direct",
        "revision": DIRECT_MARKETPLACE_REVISION,
        "ready": True,
        "offers": offers,
        "count": len(offers),
        "source": "oap_direct",
        "public_buyer_data_exposed": False,
        "external_provider_authority": False,
    }


def founder_snapshot(*, limit: object = 40) -> dict[str, Any]:
    """Return bounded operational supply state for the private Founder surface."""

    core = travel_supply_core.status()
    result: dict[str, Any] = {
        "component": "OAP Direct Supplier Control",
        "revision": DIRECT_MARKETPLACE_REVISION,
        "core": core,
        "suppliers": [],
        "listings": [],
        "inventory": [],
        "reservations": [],
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "external_provider_authority": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
    }
    if not core.get("schema_ready"):
        return result
    row_limit = _bounded_limit(limit, default=40, maximum=_FOUNDER_LIMIT_MAX)
    with postgres_db.connect(readonly=True) as connection:
        suppliers = connection.execute(
            """SELECT supplier_id,owner_identity_id,display_name,supplier_type,state,
                      commercial_terms_state,commission_basis_points,
                      service_fee_basis_points,terms_version,updated_at
               FROM oap_supply_suppliers ORDER BY updated_at DESC LIMIT %s""",
            (row_limit,),
        ).fetchall()
        listings = connection.execute(
            """SELECT l.listing_id,l.supplier_id,p.display_name,l.category,l.title,
                      l.place_label,l.country,l.state,l.updated_at
               FROM oap_supply_listings l
               JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
               ORDER BY l.updated_at DESC LIMIT %s""",
            (row_limit,),
        ).fetchall()
        inventory = connection.execute(
            """SELECT s.slot_id,s.listing_id,l.title,s.starts_at,s.ends_at,
                      s.capacity_total,s.capacity_held,s.capacity_confirmed,
                      s.price_minor,s.currency,s.price_basis,s.state,s.observed_at
               FROM oap_supply_inventory_slots s
               JOIN oap_supply_listings l ON l.listing_id=s.listing_id
               ORDER BY s.updated_at DESC LIMIT %s""",
            (row_limit,),
        ).fetchall()
        reservations = connection.execute(
            """SELECT r.reservation_id,l.title,p.display_name,r.quantity,
                      r.total_amount_minor,r.currency,r.state,r.payment_state,
                      r.pass_state,r.commission_state,r.created_at
               FROM oap_supply_reservations r
               JOIN oap_supply_listings l ON l.listing_id=r.listing_id
               JOIN oap_supply_suppliers p ON p.supplier_id=r.supplier_id
               ORDER BY r.created_at DESC LIMIT %s""",
            (row_limit,),
        ).fetchall()
    result["suppliers"] = [
        {
            "supplier_id": str(row[0]),
            "owner_identity_id": str(row[1]),
            "display_name": str(row[2]),
            "supplier_type": str(row[3]),
            "state": str(row[4]),
            "commercial_terms_state": str(row[5]),
            "commission_basis_points": int(row[6]),
            "service_fee_basis_points": int(row[7]),
            "terms_version": str(row[8]),
            "updated_at": row[9].isoformat(),
        }
        for row in suppliers
    ]
    result["listings"] = [
        {
            "listing_id": str(row[0]),
            "supplier_id": str(row[1]),
            "supplier_name": str(row[2]),
            "category": str(row[3]),
            "title": str(row[4]),
            "place_label": str(row[5]),
            "country": str(row[6]),
            "state": str(row[7]),
            "updated_at": row[8].isoformat(),
        }
        for row in listings
    ]
    result["inventory"] = [
        {
            "slot_id": str(row[0]),
            "listing_id": str(row[1]),
            "listing_title": str(row[2]),
            "starts_at": row[3].isoformat(),
            "ends_at": row[4].isoformat(),
            "capacity_total": int(row[5]),
            "capacity_held": int(row[6]),
            "capacity_confirmed": int(row[7]),
            "price_minor": int(row[8]),
            "currency": str(row[9]),
            "price_basis": str(row[10]),
            "state": str(row[11]),
            "observed_at": row[12].isoformat(),
        }
        for row in inventory
    ]
    result["reservations"] = [
        {
            "reservation_id": str(row[0]),
            "listing_title": str(row[1]),
            "supplier_name": str(row[2]),
            "quantity": int(row[3]),
            "total_amount_minor": int(row[4]),
            "currency": str(row[5]),
            "state": str(row[6]),
            "payment_state": str(row[7]),
            "pass_state": str(row[8]),
            "commission_state": str(row[9]),
            "created_at": row[10].isoformat(),
            "buyer_identity_exposed": False,
        }
        for row in reservations
    ]
    return result


def create_supplier(payload: dict[str, Any]) -> dict[str, Any]:
    return _STORE.create_supplier(
        owner_identity_id=payload.get("owner_identity_id"),
        display_name=payload.get("display_name"),
        supplier_type=payload.get("supplier_type"),
    )


def submit_supplier(payload: dict[str, Any]) -> dict[str, Any]:
    return _STORE.submit_supplier_for_review(
        owner_identity_id=payload.get("owner_identity_id"),
        supplier_id=payload.get("supplier_id"),
    )


def certify_supplier(payload: dict[str, Any]) -> dict[str, Any]:
    return _STORE.certify_supplier(
        supplier_id=payload.get("supplier_id"),
        human_authority_approved=payload.get("human_authority_approved") is True,
        commission_basis_points=payload.get("commission_basis_points", 0),
        service_fee_basis_points=payload.get("service_fee_basis_points", 0),
        terms_version=payload.get("terms_version", "v1"),
    )


def create_listing(payload: dict[str, Any]) -> dict[str, Any]:
    return _STORE.create_listing(
        owner_identity_id=payload.get("owner_identity_id"),
        supplier_id=payload.get("supplier_id"),
        category=payload.get("category"),
        title=payload.get("title"),
        place_label=payload.get("place_label"),
        country=payload.get("country"),
        idempotency_key=payload.get("idempotency_key"),
        description=payload.get("description", ""),
        postcode=payload.get("postcode"),
        borough=payload.get("borough"),
    )


def activate_listing(payload: dict[str, Any]) -> dict[str, Any]:
    return _STORE.activate_listing(
        owner_identity_id=payload.get("owner_identity_id"),
        listing_id=payload.get("listing_id"),
        human_authority_approved=payload.get("human_authority_approved") is True,
    )


def set_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    return _STORE.set_inventory_slot(
        owner_identity_id=payload.get("owner_identity_id"),
        listing_id=payload.get("listing_id"),
        starts_at=payload.get("starts_at"),
        ends_at=payload.get("ends_at"),
        capacity_total=payload.get("capacity_total"),
        price_minor=payload.get("price_minor"),
        currency=payload.get("currency"),
        price_basis=payload.get("price_basis"),
    )


def quote_direct(payload: dict[str, Any]) -> dict[str, Any]:
    """Re-read a live OAP Direct slot before any capacity is held."""

    return _STORE.quote(
        listing_id=payload.get("listing_id"),
        starts_at=payload.get("starts_at"),
        ends_at=payload.get("ends_at"),
        quantity=payload.get("quantity", 1),
    )


def create_buyer_hold(
    payload: dict[str, Any], *, buyer_identity_id: str
) -> dict[str, Any]:
    """Create a short, capacity-backed hold for the authenticated buyer only."""

    return _STORE.create_hold(
        buyer_identity_id=buyer_identity_id,
        listing_id=payload.get("listing_id"),
        starts_at=payload.get("starts_at"),
        ends_at=payload.get("ends_at"),
        quantity=payload.get("quantity", 1),
        idempotency_key=payload.get("idempotency_key"),
        hold_minutes=15,
    )


def create_buyer_reservation(
    payload: dict[str, Any], *, buyer_identity_id: str
) -> dict[str, Any]:
    """Convert the authenticated buyer's live hold into a pending reservation."""

    return _STORE.create_reservation(
        buyer_identity_id=buyer_identity_id,
        hold_id=payload.get("hold_id"),
        human_confirmed=payload.get("human_confirmed") is True,
    )


def confirm_supplier_reservation(
    payload: dict[str, Any], *, owner_identity_id: str
) -> dict[str, Any]:
    """Let the authenticated supplier owner confirm a pending reservation."""

    return _STORE.confirm_reservation(
        owner_identity_id=owner_identity_id,
        reservation_id=payload.get("reservation_id"),
        supplier_confirmation_reference=payload.get("supplier_confirmation_reference"),
        supplier_confirmed=payload.get("supplier_confirmed") is True,
    )
