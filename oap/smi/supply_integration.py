"""Governed provider-neutral external travel lookup contract for OAP.

External services can provide fresh reference/search evidence on demand. They are
not OAP partners, are not persisted into the OAP Direct catalogue, and never gain
booking, payment, identity, supplier or platform authority.

Booking.com remains declared only as an optional lookup profile because the
connected assistant surface can query it when the Founder asks. That does not
prove the Render runtime has a Booking.com API connection and does not create an
OAP commercial partnership.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

SUPPLY_INTEGRATION_REVISION = "2026-09-04-v2"

SUPPORTED_CATEGORIES: tuple[str, ...] = (
    "stay",
    "attraction",
    "car_rental",
)


@dataclass(frozen=True)
class SupplyProvider:
    provider_id: str
    name: str
    provider_type: str
    categories: tuple[str, ...]
    supports_search: bool
    supports_booking_handoff: bool
    supports_direct_booking: bool
    supports_payment: bool
    external_authority: bool = False


@dataclass(frozen=True)
class SupplyOffer:
    provider_id: str
    category: str
    source_offer_id: str
    title: str
    place_label: str
    availability_state: str
    observed_at: str
    source_url: str
    currency: str | None = None
    total_price: float | None = None
    price_basis: str | None = None
    expires_at: str | None = None


_PROVIDERS: tuple[SupplyProvider, ...] = (
    SupplyProvider(
        provider_id="booking_com",
        name="Booking.com",
        provider_type="optional_on_demand_external_lookup",
        categories=SUPPORTED_CATEGORIES,
        supports_search=True,
        supports_booking_handoff=False,
        supports_direct_booking=False,
        supports_payment=False,
        external_authority=False,
    ),
)

_PROVIDER_BY_ID = {provider.provider_id: provider for provider in _PROVIDERS}


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


def _iso8601(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    return True


def _https_url(value: str) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme == "https" and bool(parsed.netloc)


def providers() -> tuple[SupplyProvider, ...]:
    """Return immutable external lookup declarations."""

    return _PROVIDERS


def provider(provider_id: str) -> SupplyProvider | None:
    """Return one optional external lookup declaration."""

    return _PROVIDER_BY_ID.get(str(provider_id or "").strip().casefold())


def normalize_offer(payload: Mapping[str, Any]) -> SupplyOffer:
    """Validate one externally observed lookup result without making it OAP supply."""

    provider_id = str(payload.get("provider_id") or "").strip().casefold()
    provider_item = provider(provider_id)
    if provider_item is None:
        raise ValueError("unknown_supply_provider")

    category = str(payload.get("category") or "").strip().casefold()
    if category not in provider_item.categories:
        raise ValueError("unsupported_supply_category")

    source_offer_id = str(payload.get("source_offer_id") or "").strip()
    title = str(payload.get("title") or "").strip()
    place_label = str(payload.get("place_label") or "").strip()
    availability_state = str(payload.get("availability_state") or "").strip().casefold()
    observed_at = str(payload.get("observed_at") or "").strip()
    source_url = str(payload.get("source_url") or "").strip()

    if not source_offer_id or not title or not place_label:
        raise ValueError("supply_offer_identity_required")
    if availability_state not in {"available", "limited", "unavailable", "unknown"}:
        raise ValueError("invalid_availability_state")
    if not _iso8601(observed_at):
        raise ValueError("valid_observed_at_required")
    if not _https_url(source_url):
        raise ValueError("https_source_url_required")

    currency_raw = payload.get("currency")
    price_raw = payload.get("total_price")
    currency: str | None = None
    total_price: float | None = None
    price_basis = str(payload.get("price_basis") or "").strip() or None

    if price_raw is not None:
        currency = str(currency_raw or "").strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("iso_currency_required_for_price")
        try:
            total_price = float(price_raw)
        except (TypeError, ValueError) as exc:
            raise TypeError("numeric_total_price_required") from exc
        if total_price < 0:
            raise ValueError("total_price_cannot_be_negative")
        if not price_basis:
            raise ValueError("price_basis_required")
    elif currency_raw:
        raise ValueError("currency_without_price_not_allowed")

    expires_at_raw = str(payload.get("expires_at") or "").strip()
    expires_at = expires_at_raw or None
    if expires_at and not _iso8601(expires_at):
        raise ValueError("valid_expires_at_required")

    return SupplyOffer(
        provider_id=provider_id,
        category=category,
        source_offer_id=source_offer_id,
        title=title,
        place_label=place_label,
        availability_state=availability_state,
        observed_at=observed_at,
        source_url=source_url,
        currency=currency,
        total_price=total_price,
        price_basis=price_basis,
        expires_at=expires_at,
    )


def offer_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a Matrix/SMI-safe transient lookup evidence record."""

    offer = normalize_offer(payload)
    return {
        **asdict(offer),
        "source_kind": "external_lookup_only",
        "persistent_oap_supply": False,
        "observed_not_inferred": True,
        "provider_authority": False,
        "oap_authority": True,
        "human_authority_final": True,
        "booking_execution_authorized": False,
        "payment_execution_authorized": False,
    }


def runtime_provider_status(provider_id: str) -> dict[str, Any]:
    """Return fail-closed runtime readiness for one optional lookup source."""

    item = provider(provider_id)
    if item is None:
        raise ValueError("unknown_supply_provider")
    prefix = f"OAP_SUPPLY_{provider_id.upper()}"
    connected = _truthy(os.getenv(f"{prefix}_CONNECTED"))
    search_certified = connected and _truthy(os.getenv(f"{prefix}_SEARCH_CERTIFIED"))
    return {
        "provider_id": item.provider_id,
        "name": item.name,
        "provider_type": item.provider_type,
        "categories": item.categories,
        "runtime_connected": connected,
        "live_search_certified": search_certified,
        "commercial_terms_certified": False,
        "direct_booking_certified": False,
        "booking_handoff_supported": False,
        "payment_supported": False,
        "persistent_import_allowed": False,
        "partner_relationship": False,
        "external_authority": False,
        "human_authority_final": True,
    }


def validate_supply_integration() -> dict[str, Any]:
    """Validate lookup declarations and OAP authority boundaries."""

    ids = tuple(item.provider_id for item in _PROVIDERS)
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("Supply provider IDs must be unique")
    for item in _PROVIDERS:
        if not item.categories or not set(item.categories) <= set(SUPPORTED_CATEGORIES):
            errors.append(f"Provider {item.provider_id} has invalid lookup categories")
        if item.external_authority:
            errors.append(f"Provider {item.provider_id} cannot hold OAP authority")
        if item.supports_booking_handoff or item.supports_direct_booking or item.supports_payment:
            errors.append(f"Lookup source {item.provider_id} cannot execute OAP commerce")
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "provider_count": len(_PROVIDERS),
        "provider_ids_unique": len(ids) == len(set(ids)),
        "persistent_partner_supply": False,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "external_provider_authority": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    """Return truthful external lookup readiness."""

    validation = validate_supply_integration()
    runtime = tuple(runtime_provider_status(item.provider_id) for item in _PROVIDERS)
    connected = tuple(item for item in runtime if item["runtime_connected"])
    searchable = tuple(item for item in runtime if item["live_search_certified"])
    return {
        "component": "OAP External Travel Lookup Layer",
        "revision": SUPPLY_INTEGRATION_REVISION,
        "adapter_framework_ready": validation["passed"],
        "validation": validation,
        "supported_categories": SUPPORTED_CATEGORIES,
        "providers": runtime,
        "provider_count": len(runtime),
        "runtime_connected_count": len(connected),
        "live_search_provider_count": len(searchable),
        "direct_booking_provider_count": 0,
        "live_supply_connected": False,
        "booking_transactions_live": False,
        "payment_transactions_live": False,
        "commission_settlement_live": False,
        "booking_handoff_architecture_ready": False,
        "persistent_partner_supply": False,
        "provider_neutral": True,
        "external_provider_authority": False,
        "human_authority_final": True,
        "observed_at": datetime.now(UTC).isoformat(),
        "truth_boundary": (
            "External services are optional on-demand lookup sources only. OAP does not "
            "persist their search results as Partner Supply and does not route OAP booking, "
            "payment or supplier authority through them. Assistant-side lookup access is "
            "separate from the OAP Render runtime."
        ),
    }
