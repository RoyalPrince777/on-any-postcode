"""Reusable OAP Intelligence Capability Registry.

The registry makes specialist capabilities available to the locked seven
Intelligence Worlds without creating new Worlds, brains, agents or execution
authorities. Nexus connects capability context, Matrix specialist agents remain
inside Matrix, Oasis presents human-facing experiences, Guardian enforces safety
and permissions, and Human Authority remains final.

Architecture readiness is not transaction readiness. Booking, payment, access,
provider supply and commercial settlement stay fail-closed until real governed
integrations and production evidence exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

REGISTRY_REVISION = "2026-09-04-v1"

LOCKED_WORLD_IDS: tuple[str, ...] = (
    "earth",
    "language",
    "life",
    "movement",
    "civic",
    "civilisation",
    "matrix",
)

COMMERCIAL_JOURNEY: tuple[str, ...] = (
    "Explorer",
    "Discover",
    "Compare",
    "Plan",
    "Travel",
    "Stay",
    "Activity/Adventure",
    "Book",
    "Pay",
    "Pass",
    "Move",
    "Experience",
    "Support",
    "Chronicle",
)

SYSTEM_BOUNDARIES: tuple[dict[str, str], ...] = (
    {"id": "nexus", "role": "Connect capability context across OAP systems."},
    {"id": "matrix", "role": "Keep specialist Matrix Intelligence agents inside Matrix."},
    {"id": "oasis", "role": "Provide environment and human-facing presentation."},
    {"id": "guardian", "role": "Protect permissions, privacy, safety and compliance gates."},
    {"id": "human_authority", "role": "Remain final authority for consequential actions."},
)


@dataclass(frozen=True)
class IntelligenceCapability:
    capability_id: str
    name: str
    purpose: str
    world_ids: tuple[str, ...]
    trigger_terms: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    execution_class: str = "advisory"
    supply_integration_required: bool = False
    regulated_integration_required: bool = False


_CAPABILITIES: tuple[IntelligenceCapability, ...] = (
    IntelligenceCapability(
        "alignment",
        "Alignment Intelligence",
        "Keep goals, evidence, policy, capability boundaries and Human Authority aligned.",
        LOCKED_WORLD_IDS,
        ("align", "alignment", "goal", "policy", "boundary", "authority"),
    ),
    IntelligenceCapability(
        "laboratory",
        "Laboratory Intelligence",
        "Coordinate governed experiments, hypotheses, measurements, testbeds and evidence review.",
        ("earth", "life", "movement", "civilisation", "matrix"),
        ("lab", "laboratory", "experiment", "prototype", "testbed", "hypothesis"),
        dependencies=("alignment", "compliance"),
    ),
    IntelligenceCapability(
        "travel",
        "Travel Intelligence",
        "Reason across destinations, journeys, stays, activities, access and disruption.",
        ("earth", "movement", "civic", "civilisation", "matrix"),
        ("travel", "trip", "journey", "holiday", "vacation", "destination"),
        dependencies=("place", "transport", "stay", "itinerary", "disruption"),
    ),
    IntelligenceCapability(
        "movement",
        "Movement Intelligence Capability",
        "Coordinate routes, mobility state, accessibility, logistics and movement context.",
        ("earth", "movement", "civic", "matrix"),
        ("move", "movement", "route", "mobility", "logistics", "navigation"),
        dependencies=("place", "transport", "access", "disruption"),
    ),
    IntelligenceCapability(
        "booking",
        "Booking Intelligence",
        "Prepare and validate booking intent, inventory choice, terms and confirmation state.",
        ("movement", "civic", "life", "matrix"),
        ("book", "booking", "reserve", "reservation", "ticket", "confirmation"),
        dependencies=("availability", "pricing", "identity_trust", "compliance"),
        execution_class="human_gated_transaction",
        supply_integration_required=True,
    ),
    IntelligenceCapability(
        "events",
        "Events Intelligence",
        "Understand activities, adventures, community occasions, schedules and attendance context.",
        ("earth", "movement", "civic", "civilisation", "matrix"),
        ("event", "events", "activity", "adventure", "festival", "concert"),
        dependencies=("place", "availability", "access", "recommendation"),
    ),
    IntelligenceCapability(
        "place",
        "Place Intelligence",
        "Model destinations, venues, neighbourhoods, geography, local context and suitability.",
        ("earth", "civic", "movement", "matrix"),
        ("place", "venue", "destination", "postcode", "borough", "location"),
    ),
    IntelligenceCapability(
        "stay",
        "Stay Intelligence",
        "Reason about accommodation type, suitability, access, duration and stay context.",
        ("earth", "life", "movement", "civic", "matrix"),
        ("stay", "hotel", "hostel", "accommodation", "room", "lodging"),
        dependencies=("place", "availability", "pricing", "reputation", "access"),
        supply_integration_required=True,
    ),
    IntelligenceCapability(
        "transport",
        "Transport Intelligence",
        "Compare and coordinate transport modes, schedules, routes, constraints and resilience.",
        ("earth", "movement", "civic", "matrix"),
        ("transport", "train", "bus", "flight", "taxi", "rail", "drive"),
        dependencies=("place", "availability", "pricing", "disruption", "access"),
        supply_integration_required=True,
    ),
    IntelligenceCapability(
        "experience",
        "Experience Intelligence",
        "Shape useful human experiences across culture, activity, place, accessibility and context.",
        ("earth", "life", "civic", "civilisation", "matrix"),
        ("experience", "things to do", "culture", "visit", "enjoy", "explore"),
        dependencies=("place", "events", "recommendation", "access"),
    ),
    IntelligenceCapability(
        "availability",
        "Availability Intelligence",
        "Represent time-bounded inventory, capacity, schedules and whether an option is actually obtainable.",
        ("movement", "civic", "matrix"),
        ("available", "availability", "sold out", "capacity", "slot", "inventory"),
        dependencies=("place",),
        supply_integration_required=True,
    ),
    IntelligenceCapability(
        "pricing",
        "Pricing Intelligence",
        "Compare current prices, fees, taxes, conditions, value and price provenance without inventing quotes.",
        ("civic", "life", "movement", "matrix"),
        ("price", "pricing", "cost", "fee", "fare", "rate", "cheap"),
        dependencies=("availability", "compliance"),
        supply_integration_required=True,
    ),
    IntelligenceCapability(
        "commerce",
        "Commerce Intelligence",
        "Coordinate legitimate offers, merchants, products, services, terms and commercial journeys.",
        ("life", "civic", "civilisation", "matrix"),
        ("commerce", "market", "merchant", "shop", "buy", "sell", "offer"),
        dependencies=("pricing", "identity_trust", "reputation", "compliance"),
    ),
    IntelligenceCapability(
        "payment",
        "Payment Intelligence",
        "Prepare governed payment intent, amount, currency, settlement state and receipt evidence.",
        ("life", "civic", "matrix"),
        ("pay", "payment", "checkout", "card", "wallet", "receipt", "refund"),
        dependencies=("commerce", "pricing", "identity_trust", "compliance"),
        execution_class="human_gated_regulated_transaction",
        regulated_integration_required=True,
    ),
    IntelligenceCapability(
        "identity_trust",
        "Identity & Trust Intelligence",
        "Support certified identity, authentication, provenance, trust state and fraud-resistant decisions.",
        ("life", "civic", "civilisation", "matrix"),
        ("identity", "trust", "certified", "login", "authentication", "fraud"),
        dependencies=("compliance",),
    ),
    IntelligenceCapability(
        "access",
        "Access Intelligence",
        "Coordinate permissions, passes, eligibility, accessibility and authorised entry.",
        ("life", "movement", "civic", "matrix"),
        ("access", "pass", "entry", "permission", "eligible", "accessible"),
        dependencies=("identity_trust", "compliance"),
        execution_class="human_gated_authorisation",
    ),
    IntelligenceCapability(
        "weather_environment",
        "Weather & Environment Intelligence",
        "Combine weather, climate, environmental hazards and local conditions with journey and activity context.",
        ("earth", "life", "movement", "civic", "matrix"),
        ("weather", "environment", "rain", "storm", "heat", "air quality", "climate"),
        dependencies=("place",),
    ),
    IntelligenceCapability(
        "disruption",
        "Disruption Intelligence",
        "Detect and reason about delays, closures, outages, cancellations, hazards and degraded service.",
        ("earth", "movement", "civic", "matrix"),
        ("delay", "closure", "cancelled", "canceled", "outage", "disruption", "strike"),
        dependencies=("place", "transport", "weather_environment"),
    ),
    IntelligenceCapability(
        "communication",
        "Communication Intelligence",
        "Support clear multilingual, multimodal and accessible communication with provenance and consent.",
        ("language", "life", "civic", "civilisation", "matrix"),
        ("communicate", "message", "translate", "language", "voice", "call", "support"),
    ),
    IntelligenceCapability(
        "recommendation",
        "Recommendation Intelligence",
        "Rank suitable options using explicit preferences, evidence, constraints and explainable trade-offs.",
        LOCKED_WORLD_IDS,
        ("recommend", "best", "suggest", "compare", "which", "choose"),
        dependencies=("reputation", "pricing", "availability", "access"),
    ),
    IntelligenceCapability(
        "itinerary",
        "Itinerary Intelligence",
        "Build coherent multi-step plans across place, time, movement, stay and activities.",
        ("earth", "movement", "civic", "civilisation", "matrix"),
        ("itinerary", "schedule", "plan my trip", "day plan", "route plan"),
        dependencies=("travel", "place", "transport", "stay", "events", "disruption"),
    ),
    IntelligenceCapability(
        "agency",
        "Agency Intelligence",
        "Coordinate OAP Travel Agency planning, supply relationships, disclosed commissions and service workflows.",
        ("movement", "civic", "civilisation", "matrix"),
        ("agency", "travel agency", "agent", "commission", "package", "supplier"),
        dependencies=("travel", "booking", "commerce", "customer_service", "compliance"),
        execution_class="human_gated_commercial",
        supply_integration_required=True,
    ),
    IntelligenceCapability(
        "customer_service",
        "Customer Service Intelligence",
        "Resolve questions, changes, cancellations, complaints and support journeys with auditable handoffs.",
        ("language", "life", "civic", "matrix"),
        ("customer service", "support", "help", "complaint", "cancel", "change booking"),
        dependencies=("communication", "identity_trust", "booking", "compliance"),
    ),
    IntelligenceCapability(
        "reputation",
        "Reputation Intelligence",
        "Assess review evidence, reliability, provenance and trust signals without covert profiling.",
        ("life", "civic", "civilisation", "matrix"),
        ("review", "rating", "reputation", "reliable", "trusted", "quality"),
        dependencies=("identity_trust", "compliance"),
    ),
    IntelligenceCapability(
        "humanitarian",
        "Humanitarian Intelligence Capability",
        "Coordinate civilian protection, verified emergency context, accessibility, aid information and dignity-first response.",
        ("earth", "language", "life", "movement", "civic", "matrix"),
        ("humanitarian", "emergency", "disaster", "outbreak", "refugee", "aid", "civilian"),
        dependencies=(
            "alignment",
            "place",
            "weather_environment",
            "disruption",
            "communication",
            "compliance",
        ),
    ),
    IntelligenceCapability(
        "compliance",
        "Compliance Intelligence",
        "Apply legal, policy, licensing, consumer, privacy and regulated-activity gates before consequential claims or actions.",
        LOCKED_WORLD_IDS,
        ("compliance", "legal", "law", "licence", "license", "regulation", "privacy", "terms"),
        dependencies=("alignment",),
    ),
)

_BY_ID = {item.capability_id: item for item in _CAPABILITIES}


def capabilities() -> tuple[IntelligenceCapability, ...]:
    """Return the immutable registered capability set."""

    return _CAPABILITIES


def capability(capability_id: str) -> IntelligenceCapability | None:
    """Return one capability by canonical ID."""

    return _BY_ID.get(str(capability_id or "").strip().casefold())


def capabilities_for_world(world_id: str) -> tuple[IntelligenceCapability, ...]:
    """Return capabilities available to one canonical Intelligence World."""

    clean = str(world_id or "").strip().casefold()
    if clean not in LOCKED_WORLD_IDS:
        return ()
    return tuple(item for item in _CAPABILITIES if clean in item.world_ids)


def _term_matches(text: str, term: str) -> bool:
    pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
    return re.search(pattern, text) is not None


def select_capabilities(
    query: str,
    *,
    world_ids: tuple[str, ...] | list[str] = (),
    limit: int = 8,
) -> tuple[str, ...]:
    """Select relevant capability IDs without granting execution authority."""

    text = str(query or "").casefold()
    allowed_worlds = {
        str(item).strip().casefold()
        for item in world_ids
        if str(item).strip().casefold() in LOCKED_WORLD_IDS
    }
    safe_limit = min(max(int(limit), 1), 12)
    ranked: list[tuple[int, int, IntelligenceCapability]] = []
    for index, item in enumerate(_CAPABILITIES):
        if allowed_worlds and not (allowed_worlds & set(item.world_ids)):
            continue
        score = sum(_term_matches(text, term) for term in item.trigger_terms)
        if score:
            ranked.append((score, -index, item))
    ranked.sort(reverse=True)
    selected = [entry[2].capability_id for entry in ranked[:safe_limit]]
    if selected and "alignment" not in selected:
        if len(selected) >= safe_limit:
            selected[-1] = "alignment"
        else:
            selected.append("alignment")
    return tuple(dict.fromkeys(selected))[:safe_limit]


def validate_registry(
    runtime_world_ids: tuple[str, ...] | list[str] = LOCKED_WORLD_IDS,
) -> dict[str, Any]:
    """Validate the registry against the seven-World constitutional boundary."""

    runtime_worlds = tuple(str(item) for item in runtime_world_ids)
    ids = tuple(item.capability_id for item in _CAPABILITIES)
    names = tuple(item.name for item in _CAPABILITIES)
    unknown_worlds = sorted(
        {
            world_id
            for item in _CAPABILITIES
            for world_id in item.world_ids
            if world_id not in LOCKED_WORLD_IDS
        }
    )
    unknown_dependencies = sorted(
        {
            dependency
            for item in _CAPABILITIES
            for dependency in item.dependencies
            if dependency not in _BY_ID
        }
    )
    errors: list[str] = []
    if runtime_worlds != LOCKED_WORLD_IDS:
        errors.append("Runtime Intelligence Worlds differ from the locked seven-World order")
    if len(ids) != 26:
        errors.append("The approved reusable capability set must contain exactly 26 capabilities")
    if len(ids) != len(set(ids)) or len(names) != len(set(names)):
        errors.append("Capability IDs and names must be unique")
    if unknown_worlds:
        errors.append(
            "Capability references unknown Intelligence Worlds: " + ", ".join(unknown_worlds)
        )
    if unknown_dependencies:
        errors.append(
            "Capability references unknown dependencies: " + ", ".join(unknown_dependencies)
        )
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "world_count": len(runtime_worlds),
        "capability_count": len(ids),
        "unique_capability_ids": len(ids) == len(set(ids)),
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "brain_count_added": 0,
        "matrix_agents_remain_inside_matrix": True,
        "nexus_connected": True,
        "oasis_presentation_layer": True,
        "guardian_gate_required": True,
        "human_authority_final": True,
    }


def status(
    runtime_world_ids: tuple[str, ...] | list[str] = LOCKED_WORLD_IDS,
) -> dict[str, Any]:
    """Return registry architecture status without claiming live commerce supply."""

    validation = validate_registry(runtime_world_ids)
    transactional = tuple(
        item.capability_id for item in _CAPABILITIES if item.execution_class != "advisory"
    )
    supply_required = tuple(
        item.capability_id for item in _CAPABILITIES if item.supply_integration_required
    )
    regulated_required = tuple(
        item.capability_id
        for item in _CAPABILITIES
        if item.regulated_integration_required
    )
    return {
        "component": "OAP Intelligence Capability Registry",
        "revision": REGISTRY_REVISION,
        "registry_software_ready": validation["passed"],
        "architecture_defined": validation["passed"],
        "validation": validation,
        "world_count": 7,
        "capability_count": len(_CAPABILITIES),
        "capabilities": tuple(
            {
                "id": item.capability_id,
                "name": item.name,
                "purpose": item.purpose,
                "world_ids": item.world_ids,
                "dependencies": item.dependencies,
                "execution_class": item.execution_class,
                "supply_integration_required": item.supply_integration_required,
                "regulated_integration_required": item.regulated_integration_required,
                "operational_state": "architecture_defined",
            }
            for item in _CAPABILITIES
        ),
        "commercial_journey": COMMERCIAL_JOURNEY,
        "oap_travel_agency": {
            "target_role": "legitimate_travel_agency_and_commercial_orchestrator",
            "allowed_revenue_models": (
                "disclosed_supplier_commission",
                "disclosed_service_fee",
                "disclosed_booking_fee_where_legal",
            ),
            "hidden_fees_allowed": False,
            "real_supply_integrations_connected": False,
            "booking_transactions_live": False,
            "payment_transactions_live": False,
            "commission_settlement_live": False,
            "production_claim_allowed": False,
        },
        "transactional_capability_ids": transactional,
        "supply_integration_required_ids": supply_required,
        "regulated_integration_required_ids": regulated_required,
        "provider_connection_count": 0,
        "supply_integrations_connected": False,
        "booking_transactions_live": False,
        "payment_transactions_live": False,
        "transaction_execution_ready": False,
        "systems": SYSTEM_BOUNDARIES,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "brain_count_added": 0,
        "external_provider_authority": False,
        "human_authority_final": True,
        "truth_boundary": (
            "The reusable 26-capability architecture is implemented as a registry. "
            "Capabilities are not new Intelligence Worlds or automatically agents. "
            "Real supply, booking, payment, access and commission settlement remain "
            "fail-closed until governed integrations, tests and production evidence exist."
        ),
    }
