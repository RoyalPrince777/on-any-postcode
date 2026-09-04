"""First-party OAP Booking Core.

OAP owns the booking journey, state machine, comparison and confirmation logic.
External suppliers remain replaceable inventory/evidence sources with zero OAP
authority. This module can prepare and approve booking handoffs, but it cannot
claim that a reservation, payment, pass or supplier commission has completed
without separately certified runtime evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Mapping

from . import supply_integration

BOOKING_CORE_REVISION = "2026-09-04-v1"
DEFAULT_MAX_OFFER_AGE_SECONDS = 900


@dataclass(frozen=True)
class BookingIntent:
    intent_id: str
    provider_id: str
    category: str
    source_offer_id: str
    title: str
    place_label: str
    availability_state: str
    observed_at: str
    source_url: str
    currency: str | None
    total_price: float | None
    price_basis: str | None
    expires_at: str | None
    state: str
    human_confirmation_required: bool
    human_confirmed: bool
    booking_execution_authorized: bool
    payment_execution_authorized: bool
    pass_issuance_authorized: bool


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _now_utc(now: datetime | None = None) -> datetime:
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(UTC)


def _intent_id(provider_id: str, category: str, source_offer_id: str, observed_at: str) -> str:
    seed = "|".join((provider_id, category, source_offer_id, observed_at))
    return "oap-book-" + sha256(seed.encode("utf-8")).hexdigest()[:16]


def offer_freshness(
    payload: Mapping[str, Any],
    *,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_OFFER_AGE_SECONDS,
) -> dict[str, Any]:
    """Return evidence freshness for an externally observed supplier offer."""

    offer = supply_integration.normalize_offer(payload)
    current = _now_utc(now)
    observed = _parse_time(offer.observed_at)
    age_seconds = max(0, int((current - observed).total_seconds()))
    expired = bool(offer.expires_at and _parse_time(offer.expires_at) <= current)
    stale = age_seconds > max(1, int(max_age_seconds))
    return {
        "fresh": not stale and not expired,
        "stale": stale,
        "expired": expired,
        "age_seconds": age_seconds,
        "max_age_seconds": max(1, int(max_age_seconds)),
        "observed_at": offer.observed_at,
        "expires_at": offer.expires_at,
    }


def prepare_booking_intent(
    payload: Mapping[str, Any],
    *,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_OFFER_AGE_SECONDS,
) -> BookingIntent:
    """Prepare an OAP-owned booking intent from verified supplier evidence."""

    offer = supply_integration.normalize_offer(payload)
    if offer.availability_state not in {"available", "limited"}:
        raise ValueError("offer_not_bookable")
    freshness = offer_freshness(payload, now=now, max_age_seconds=max_age_seconds)
    if not freshness["fresh"]:
        raise ValueError("offer_evidence_stale_or_expired")

    return BookingIntent(
        intent_id=_intent_id(
            offer.provider_id,
            offer.category,
            offer.source_offer_id,
            offer.observed_at,
        ),
        provider_id=offer.provider_id,
        category=offer.category,
        source_offer_id=offer.source_offer_id,
        title=offer.title,
        place_label=offer.place_label,
        availability_state=offer.availability_state,
        observed_at=offer.observed_at,
        source_url=offer.source_url,
        currency=offer.currency,
        total_price=offer.total_price,
        price_basis=offer.price_basis,
        expires_at=offer.expires_at,
        state="awaiting_human_confirmation",
        human_confirmation_required=True,
        human_confirmed=False,
        booking_execution_authorized=False,
        payment_execution_authorized=False,
        pass_issuance_authorized=False,
    )


def confirm_booking_intent(intent: BookingIntent, *, human_approved: bool) -> BookingIntent:
    """Record Human Authority approval without pretending a supplier booking occurred."""

    if intent.state != "awaiting_human_confirmation":
        raise ValueError("booking_intent_not_awaiting_confirmation")
    if not human_approved:
        return replace(intent, state="declined", human_confirmed=False)

    provider = supply_integration.provider(intent.provider_id)
    if provider is None:
        raise ValueError("unknown_supply_provider")
    next_state = "handoff_ready" if provider.supports_booking_handoff else "approved_waiting_supply"
    return replace(intent, state=next_state, human_confirmed=True)


def booking_handoff(intent: BookingIntent) -> dict[str, Any]:
    """Return a safe external supplier handoff; this is not a confirmed reservation."""

    if intent.state != "handoff_ready" or not intent.human_confirmed:
        raise ValueError("booking_handoff_not_ready")
    provider = supply_integration.provider(intent.provider_id)
    if provider is None or not provider.supports_booking_handoff:
        raise ValueError("provider_handoff_not_supported")
    return {
        "intent_id": intent.intent_id,
        "provider_id": intent.provider_id,
        "supplier_name": provider.name,
        "handoff_url": intent.source_url,
        "state": "external_supplier_handoff",
        "reservation_confirmed": False,
        "payment_captured": False,
        "pass_issued": False,
        "provider_authority": False,
        "human_authority_final": True,
        "truth_boundary": (
            "This handoff opens the supplier evidence/booking destination. It does not "
            "prove that a reservation, payment or pass has completed inside OAP."
        ),
    }


def intent_record(intent: BookingIntent) -> dict[str, Any]:
    """Return an auditable non-PII booking-intent record."""

    return {
        **asdict(intent),
        "oap_owned_booking_state": True,
        "supplier_inventory_external": True,
        "provider_authority": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    """Return truthful readiness for OAP Booking Core."""

    supply = supply_integration.status()
    return {
        "component": "OAP Booking Core",
        "revision": BOOKING_CORE_REVISION,
        "first_party_booking_orchestration_ready": True,
        "offer_freshness_validation_ready": True,
        "booking_intent_state_machine_ready": True,
        "human_confirmation_gate_ready": True,
        "supplier_handoff_ready": bool(supply["booking_handoff_architecture_ready"]),
        "live_supply_search_ready": bool(supply["live_supply_connected"]),
        "direct_booking_execution_ready": bool(supply["booking_transactions_live"]),
        "payment_execution_ready": False,
        "pass_issuance_ready": False,
        "commission_settlement_ready": False,
        "owns_supplier_inventory": False,
        "owns_booking_experience": True,
        "provider_neutral": True,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "external_provider_authority": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
        "truth_boundary": (
            "OAP owns the booking experience and booking-intent orchestration. External "
            "providers may supply inventory and booking destinations. A real reservation, "
            "payment, pass or commission is not live until its separate governed runtime "
            "integration and production evidence are certified."
        ),
    }
