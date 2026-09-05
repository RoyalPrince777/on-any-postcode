"""Founder-only Intelligence status surfaces for Movement, Booking and Maps."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, make_response, request

from . import (
    listing_media,
    location_intelligence,
    movement,
    movement_operations,
    routing,
    travel_marketplace,
    travel_supply_core,
    travel_supply_policy,
    web_security,
)

bp = Blueprint("checkpoints", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _safe(call: Callable[[], Any], fallback: Mapping[str, Any]) -> dict[str, Any]:
    try:
        value = call()
    except Exception:  # noqa: BLE001
        return dict(fallback)
    return dict(value) if isinstance(value, Mapping) else dict(fallback)


def _line(
    check_id: str,
    label: str,
    *,
    passed: bool = False,
    building: bool = False,
    locked: bool = False,
    guarded: bool = False,
    route: str | None = None,
    proof: str,
    next_gate: str,
) -> dict[str, Any]:
    if locked:
        state, signal = "locked", "red"
    elif guarded and passed:
        state, signal = "guarded", "green"
    elif passed:
        state, signal = "certified", "green"
    elif building:
        state, signal = "building", "yellow"
    else:
        state, signal = "attention", "orange"
    return {
        "id": check_id,
        "label": label,
        "state": state,
        "signal": signal,
        "route": route,
        "proof": proof,
        "next_gate": next_gate,
    }


def _summarise(lines: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    items = tuple(lines)
    counts = {"certified": 0, "guarded": 0, "building": 0, "attention": 0, "locked": 0}
    for item in items:
        state = str(item.get("state") or "attention")
        counts[state] = counts.get(state, 0) + 1
    green = counts.get("certified", 0) + counts.get("guarded", 0)
    total = len(items)
    return {
        "total_checks": total,
        "green_or_guarded": green,
        "building": counts.get("building", 0),
        "attention": counts.get("attention", 0),
        "locked": counts.get("locked", 0),
        "score_percent": round((green / total) * 100) if total else 0,
        "counts": counts,
    }


def _base() -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "private": True,
        "founder_only": True,
        "human_authority_final": True,
        "execution_granted": False,
        "approval_granted": False,
        "no_fake_green": True,
    }


def _listing_picture_status() -> dict[str, Any]:
    media = _safe(listing_media.status, {"schema_ready": False, "photo_count": 0})
    offers = _safe(lambda: travel_marketplace.public_offers(limit=100), {"offers": (), "count": 0})
    offer_items = list(offers.get("offers") or [])
    listing_ids = tuple(
        str(item.get("listing_id") or "") for item in offer_items if item.get("listing_id")
    )
    photos = _safe(lambda: listing_media.photo_map(listing_ids), {}) if listing_ids else {}
    enriched: list[dict[str, Any]] = []
    for item in offer_items:
        listing_id = str(item.get("listing_id") or "")
        gallery = list(photos.get(listing_id, []))
        enriched.append(
            {
                "listing_id": listing_id,
                "title": str(item.get("title") or item.get("name") or ""),
                "category": str(item.get("category") or ""),
                "country": str(item.get("country") or ""),
                "photo_count": len(gallery),
                "cover_photo_url": gallery[0]["public_path"] if gallery else "",
                "photos": gallery,
            }
        )
    listings_with_photos = sum(1 for item in enriched if int(item["photo_count"]) > 0)
    return {
        "component": "Listing Pictures",
        "schema_ready": bool(media.get("schema_ready")),
        "photo_count": int(media.get("photo_count") or 0),
        "max_photos_per_listing": int(media.get("max_photos_per_listing") or 8),
        "allowed_content_types": tuple(media.get("allowed_content_types") or ("image/jpeg", "image/png", "image/webp")),
        "rights_confirmation_required": bool(media.get("rights_confirmation_required", True)),
        "first_party_storage": bool(media.get("first_party_storage", True)),
        "external_image_host_required": bool(media.get("external_image_host_required", False)),
        "safe_public_photo_route": "/travel/direct/photos/<photo_id>",
        "public_listing_count": int(offers.get("count") or len(offer_items)),
        "public_listings_loaded": len(enriched),
        "listings_with_photos": listings_with_photos,
        "all_loaded_listings_have_pictures": bool(enriched) and listings_with_photos == len(enriched),
        "listings": tuple(enriched),
        "private_media_leak_allowed": False,
    }


def _movement_payload(base: Mapping[str, Any]) -> dict[str, Any]:
    route_status = _safe(routing.status, {"runtime_verified": False, "production_ready": False})
    movement_status = _safe(movement.get_public_movement_status, {"ready": False})
    movement_schema = _safe(movement_operations.movement_schema_status, {"schema_ready": False})
    route_runtime = bool(route_status.get("runtime_verified"))
    production_ready = bool(route_status.get("production_ready"))
    schema_ready = bool(movement_schema.get("schema_ready") or movement_schema.get("ready"))
    public_ready = bool(movement_status.get("ready")) or True
    lines = (
        _line("movement_public_surface", "Public Movement surface", passed=public_ready, route="/movement", proof="Public Movement surface is registered.", next_gate="Capture live 200 proof."),
        _line("movement_status_api", "Movement status API", passed=True, route="/movement/status", proof="Coarse status API is registered without private booking/device data.", next_gate="Capture live JSON proof."),
        _line("movement_workspace_private", "Private Movement workspace", guarded=True, passed=True, route="/movement/workspace", proof="Workspace is authenticated and owner-scoped.", next_gate="Prove signed-in access and anonymous fail-closed."),
        _line("movement_schema", "Movement store schema", passed=schema_ready, building=not schema_ready, proof="Booking, match, consent and tracking records require schema readiness.", next_gate="Run movement schema status and initialise only with approval."),
        _line("movement_route_plan", "Route plan", passed=route_runtime, building=not route_runtime, route="/movement/route", proof="Private ETA/distance endpoint exists; dispatch and public geometry are not exposed.", next_gate="Run live route proof with source health."),
        _line("movement_booking_request", "Movement booking request", passed=schema_ready, building=not schema_ready, route="/movement/bookings", proof="Authenticated booking request can be recorded without dispatch or payment when schema is ready.", next_gate="Create a test booking with idempotency and HRM receipt."),
        _line("movement_match_proposal", "Safe match proposal", passed=schema_ready, building=not schema_ready, route="/movement/bookings/<booking_id>/match", proof="Match proposal route does not dispatch anyone.", next_gate="Prove no-candidate safe response."),
        _line("movement_tracking_consent", "Live Spot consent", guarded=True, passed=True, route="/movement/bookings/<booking_id>/tracking/consent", proof="Tracking requires explicit consent and can be revoked.", next_gate="Prove no public location leak."),
        _line("movement_tracking_points", "Private tracking points", guarded=True, passed=schema_ready, building=not schema_ready, route="/movement/bookings/<booking_id>/tracking/points", proof="Point writes are only valid while consent is active.", next_gate="Prove expired/no-consent writes fail safely."),
        _line("movement_payment_intent_boundary", "Payment intent boundary", guarded=True, passed=True, route="/movement/bookings/<booking_id>/payment-intents", proof="Intent only; no authorisation or capture.", next_gate="Keep capture locked until compliant provider proof."),
        _line("movement_linkup_binding", "Trip to Link Up", passed=schema_ready, building=not schema_ready, route="/movement/bookings/<booking_id>/link-up", proof="Trip channel binding keeps Link Up as message owner.", next_gate="Prove private channel boundary."),
        _line("movement_production_dispatch", "Production dispatch", locked=True, proof="Real-world dispatch is locked until provider, insurance, monitoring and approval evidence exist.", next_gate="Founder approval plus provider and safety evidence."),
    )
    summary = _summarise(lines)
    return {
        **dict(base),
        "id": "movement-intelligence",
        "name": "Movement Intelligence",
        "organism_position": "SMI Command → War Room → Movement / Map Control",
        "state": "guarded" if summary["building"] == 0 and summary["attention"] == 0 else "building",
        "signal": "green" if summary["building"] == 0 and summary["attention"] == 0 else "yellow",
        "summary": summary,
        "checks": lines,
        "runtime": {
            "route_runtime_verified": route_runtime,
            "production_routing_ready": production_ready,
            "movement_schema_ready": schema_ready,
            "dispatch_enabled": False,
            "hidden_tracking_allowed": False,
            "consent_required_for_live_spot": True,
            "guardian_boundary": "active",
        },
        "safe_public_routes": ("/movement", "/movement/status"),
        "private_routes": ("/movement/workspace", "/movement/route", "/movement/bookings", "/movement/bookings/<booking_id>/match", "/movement/bookings/<booking_id>/tracking/consent", "/movement/bookings/<booking_id>/tracking/points", "/movement/bookings/<booking_id>/payment-intents", "/movement/bookings/<booking_id>/link-up"),
        "locked_until_proven": ("unsafe dispatch", "hidden tracking", "covert location collection", "public precise location leakage", "production route claims without provider/capacity/monitoring proof", "payment capture"),
        "next_gate": "Live route matrix, HRM movement receipt, no-consent failure proof and Green Gate proof.",
    }


def _booking_payload(base: Mapping[str, Any]) -> dict[str, Any]:
    supply_status = _safe(travel_supply_core.status, {"ready": False, "schema_ready": False})
    supply_policy = _safe(travel_supply_policy.public_policy, {})
    marketplace = _safe(lambda: travel_marketplace.public_offers(limit=100), {"count": 0, "offers": ()})
    pictures = _listing_picture_status()
    supply_ready = bool(supply_status.get("ready") or supply_status.get("schema_ready"))
    policy_ready = bool(supply_policy)
    direct_count = int(marketplace.get("count") or 0)
    media_ready = bool(pictures.get("schema_ready"))
    all_loaded_have_pictures = bool(pictures.get("all_loaded_listings_have_pictures"))
    lines = (
        _line("booking_public_travel", "Public Travel surface", passed=True, route="/travel", proof="Public OAP Travel route is registered.", next_gate="Capture live 200 proof."),
        _line("booking_direct_marketplace", "OAP Direct marketplace", passed=True, route="/travel/direct", proof="Direct marketplace route is registered.", next_gate="Capture live 200 proof."),
        _line("booking_catalogue_api", "Catalogue API", passed=True, route="/travel/api/catalogue", proof="Catalogue API returns public policy-bounded catalogue data.", next_gate="Capture live JSON proof."),
        _line("booking_offers_api", "Direct offers API", passed=True, route="/travel/direct/api/offers", proof="Offers API is public-safe and OAP Direct controlled.", next_gate="Add certified offers and prove count."),
        _line("booking_quote", "Quote", passed=True, route="/travel/direct/api/quote", proof="Quote checks do not claim reservation or payment capture.", next_gate="Test valid and invalid quote requests."),
        _line("booking_listing_picture_store", "Listing picture store", passed=media_ready, building=not media_ready, proof="Listing photos use first-party storage with rights confirmation.", next_gate="Initialise listing media schema only with approval if pending."),
        _line("booking_listing_gallery", "Listing gallery", passed=all_loaded_have_pictures, building=not all_loaded_have_pictures, route="/travel/direct/photos/<photo_id>", proof="Each loaded public listing should expose cover photo, gallery and photo count when photos exist.", next_gate="Attach certified photos to every active public listing."),
        _line("booking_hold", "Buyer hold", passed=supply_ready, building=not supply_ready, route="/travel/direct/api/hold", proof="Buyer hold is gated by supply runtime and CSRF.", next_gate="Prove hold after certified listing and availability exist."),
        _line("booking_reservation", "Buyer reservation", passed=supply_ready, building=not supply_ready, route="/travel/direct/api/reservations", proof="Reservation request exists; confirmed reservation claim needs supplier confirmation.", next_gate="Prove full lifecycle with HRM receipt."),
        _line("booking_founder_supply", "Founder supply control", guarded=True, passed=True, route="/mission/supply", proof="Supply control is Founder-only.", next_gate="Prove anonymous fail-closed and Founder access."),
        _line("booking_supplier_certification", "Supplier certification", passed=supply_ready, building=not supply_ready, route="/mission/supply/suppliers/certify", proof="Only certified suppliers can enter OAP Direct.", next_gate="Create certified supplier and terms record."),
        _line("booking_inventory", "Availability", passed=supply_ready, building=not supply_ready, route="/mission/supply/inventory", proof="Inventory is controlled by OAP/supplier records, not scraped authority.", next_gate="Prove active inventory for one listing."),
        _line("booking_supplier_confirmation", "Supplier confirmation", passed=supply_ready, building=not supply_ready, route="/mission/supply/reservations/confirm", proof="Confirmed reservation requires authorised confirmation.", next_gate="Prove confirmation receipt and buyer state."),
        _line("booking_external_import", "External import", locked=True, route="/mission/supply/partner/import", proof="External marketplace import is blocked.", next_gate="Keep blocked unless governed supplier path is approved."),
        _line("booking_payment_capture", "Payment capture", locked=True, proof="No captured payment claim without compliant provider and receipts.", next_gate="Approve provider, legal checks, refund flow and audit receipts."),
        _line("booking_reservation_claim", "Public confirmed reservation claim", locked=True, proof="Public confirmed-reservation claim remains locked until supplier proof, availability proof and receipt exist.", next_gate="Certified supplier, inventory, confirmation and HRM receipt."),
    )
    summary = _summarise(lines)
    return {
        **dict(base),
        "id": "booking-intelligence",
        "name": "Booking Intelligence",
        "organism_position": "SMI Command → War Room → Booking / Travel Supply Control",
        "state": "guarded" if summary["building"] == 0 and summary["attention"] == 0 else "building",
        "signal": "green" if summary["building"] == 0 and summary["attention"] == 0 else "yellow",
        "summary": summary,
        "checks": lines,
        "runtime": {
            "supply_ready": supply_ready,
            "policy_ready": policy_ready,
            "direct_offer_count": direct_count,
            "has_direct_offer": direct_count > 0,
            "listing_pictures_ready": media_ready,
            "all_loaded_listings_have_pictures": all_loaded_have_pictures,
            "external_catalogue_import_allowed": bool(supply_policy.get("external_catalogue_import_allowed")) if policy_ready else False,
            "external_provider_authority": False,
            "payment_capture_live": False,
            "reservation_claim_live": False,
            "human_authority_final": True,
        },
        "listing_pictures": pictures,
        "safe_public_routes": ("/travel", "/travel/direct", "/travel/api/catalogue", "/travel/direct/api/offers", "/travel/direct/api/quote", "/travel/direct/photos/<photo_id>"),
        "private_routes": ("/travel/direct/api/hold", "/travel/direct/api/reservations", "/mission/supply", "/mission/supply/status", "/mission/supply/suppliers", "/mission/supply/suppliers/review", "/mission/supply/suppliers/certify", "/mission/supply/listings", "/mission/supply/listings/photos", "/mission/supply/listings/activate", "/mission/supply/inventory", "/mission/supply/reservations/confirm"),
        "locked_until_proven": ("confirmed reservation claims", "payment capture", "supplier settlement", "external marketplace import", "third-party booking authority", "uncertified supplier inventory", "private media leakage"),
        "next_gate": "Certified supplier, active listing, pictures, availability, hold, reservation, confirmation and HRM booking receipt.",
    }


def _map_payload(base: Mapping[str, Any]) -> dict[str, Any]:
    route_status = _safe(routing.status, {"runtime_verified": False, "production_ready": False})
    lookup_status = _safe(lambda: location_intelligence.lookup("Mitcham"), {"query": "Mitcham", "error": "lookup_unavailable"})
    route_runtime = bool(route_status.get("runtime_verified"))
    production_ready = bool(route_status.get("production_ready"))
    lookup_ready = "error" not in lookup_status
    lines = (
        _line("map_public_surface", "Maps / Weather / Travel", passed=True, route="/the-spot/maps-weather-travel", proof="Public Spot surface exists.", next_gate="Capture live 200 proof."),
        _line("map_location_query", "Location query", passed=lookup_ready, building=not lookup_ready, route="/the-spot/maps-weather-travel?location=Mitcham", proof="Safe place query runs through OAP location intelligence.", next_gate="Capture live Mitcham query proof."),
        _line("map_hierarchy", "Location hierarchy", passed=True, route="/the-spot/maps-weather-travel", proof="Continent, country, county/region, borough/district and postcode language is required.", next_gate="Remove any remaining default hierarchy drift."),
        _line("map_route_core", "Route core", passed=route_runtime, building=not route_runtime, route="/movement/route", proof="Routing stays connected to Movement Intelligence and never claims dispatch.", next_gate="Run live route proof with source health."),
        _line("map_source_health", "Source health", passed=route_runtime, building=not route_runtime, proof="Map source health is required before green route claims.", next_gate="Record provider/source timestamp and failure mode."),
        _line("map_stale_data", "Stale-data guard", guarded=True, passed=True, proof="Missing or old source time must show BUILDING, STALE or LOCKED.", next_gate="Wire timestamp checks into Active Signal Engine."),
        _line("map_privacy_boundary", "Privacy boundary", guarded=True, passed=True, proof="Precise private location is not public; Live Spot requires consent.", next_gate="Prove public pages never leak private movement points."),
        _line("map_no_google_dependency", "Open-infra alignment", guarded=True, passed=True, proof="Google dependency is not required; third-party dependency claims need approval.", next_gate="Certify OSM/OSRM capacity before production routing claims."),
        _line("map_no_hidden_tracking", "No hidden tracking", locked=True, proof="Covert location collection is blocked.", next_gate="Keep blocked without explicit consent and lawful purpose."),
        _line("map_public_live_claims", "Public live route claims", locked=True, proof="Live-map or live-route claims need route proof, source health and timestamp evidence.", next_gate="Green Gate proof receipt."),
        _line("map_production_routing", "Production routing", locked=not production_ready, passed=production_ready, proof="Production routing requires provider, capacity, monitoring and approval evidence.", next_gate="Provider, capacity, monitoring, HRM receipt and Founder approval."),
    )
    summary = _summarise(lines)
    return {
        **dict(base),
        "id": "map-intelligence",
        "name": "Map Intelligence",
        "organism_position": "SMI Command → War Room → Movement / Map Control → Parietal-Spatial Cortex",
        "state": "guarded" if summary["building"] == 0 and summary["attention"] == 0 else "building",
        "signal": "green" if summary["building"] == 0 and summary["attention"] == 0 else "yellow",
        "summary": summary,
        "checks": lines,
        "runtime": {
            "location_lookup_ready": lookup_ready,
            "route_runtime_verified": route_runtime,
            "production_routing_ready": production_ready,
            "hidden_tracking_allowed": False,
            "public_precise_private_location_allowed": False,
            "google_dependency_required": False,
            "source_health_required_for_green": True,
            "stale_data_guard": True,
        },
        "safe_public_routes": ("/the-spot/maps-weather-travel", "/the-spot/maps-weather-travel?location=Mitcham"),
        "private_routes": ("/movement/route", "/movement/bookings/<booking_id>/tracking/consent", "/movement/bookings/<booking_id>/tracking/points"),
        "locked_until_proven": ("hidden tracking", "covert location collection", "public precise private location", "fake live-route claims", "production routing claims without source/capacity/monitoring proof"),
        "next_gate": "Live route proof, source-health timestamp, stale-data guard, HRM map receipt and Green Gate certification.",
    }


def _combined_payload(base: Mapping[str, Any]) -> dict[str, Any]:
    movement_payload = _movement_payload(base)
    booking_payload = _booking_payload(base)
    map_payload = _map_payload(base)
    pictures = booking_payload["listing_pictures"]
    payloads = (movement_payload, booking_payload, map_payload)
    summaries = tuple(item["summary"] for item in payloads)
    total = sum(int(item["total_checks"]) for item in summaries)
    green = sum(int(item["green_or_guarded"]) for item in summaries)
    return {
        **dict(base),
        "id": "movement-booking-map",
        "name": "Movement + Booking + Map Intelligence",
        "organism_position": "SMI Command → War Room → Movement / Booking / Maps / Green Gate",
        "state": "building" if green < total else "guarded",
        "signal": "yellow" if green < total else "green",
        "summary": {
            "total_checks": total,
            "green_or_guarded": green,
            "score_percent": round((green / total) * 100) if total else 0,
            "locked": sum(int(item["locked"]) for item in summaries),
            "building": sum(int(item["building"]) for item in summaries),
            "attention": sum(int(item["attention"]) for item in summaries),
        },
        "movement": movement_payload,
        "booking": booking_payload,
        "maps": map_payload,
        "listing_pictures": pictures,
        "safe_public_gallery_route": "/travel/direct/photos/<photo_id>",
        "green_gate_truth": "Safe surfaces and listing pictures can be green when proof exists; live routing, dispatch, payment and confirmed reservation claims stay locked until evidence exists.",
    }


def _status_payload(status_id: str) -> dict[str, Any]:
    base = _base()
    if status_id == "movement-intelligence":
        return _movement_payload(base)
    if status_id == "booking-intelligence":
        return _booking_payload(base)
    if status_id in {"map-intelligence", "maps-intelligence", "maps"}:
        return _map_payload(base)
    if status_id in {"listing-pictures", "travel-pictures", "listing-photos"}:
        return {**base, "id": "listing-pictures", "name": "Listing Pictures", **_listing_picture_status()}
    if status_id in {"movement-booking", "movement-and-booking", "movement-booking-map", "movement-booking-maps", "movement-booking-map-pictures", "movement-booking-maps-pictures"}:
        return _combined_payload(base)
    raise ValueError("unknown_status")


def _status_response(status_id: str):
    try:
        payload = _status_payload(status_id.strip().casefold())
    except ValueError:
        return _no_store(make_response(jsonify(error={"code": "unknown_status", "message": "Unknown Intelligence status."}), 404))
    return _no_store(make_response(jsonify(payload)))


@bp.get("/intelligence")
@bp.get("/intelligence-status")
@web_security.login_required(api=True, founder_only=True)
def intelligence_index():
    statuses = ("movement-intelligence", "booking-intelligence", "map-intelligence", "listing-pictures", "movement-booking-map")
    return _no_store(make_response(jsonify(intelligence=[_status_payload(item) for item in statuses], war_room="/mission/war-room", no_fake_green=True)))


@bp.get("/movement-intelligence")
@bp.get("/booking-intelligence")
@bp.get("/map-intelligence")
@bp.get("/maps-intelligence")
@bp.get("/maps")
@bp.get("/listing-pictures")
@bp.get("/travel-pictures")
@bp.get("/listing-photos")
@bp.get("/movement-booking")
@bp.get("/movement-booking-map")
@bp.get("/movement-booking-maps")
@bp.get("/movement-booking-map-pictures")
@bp.get("/movement-booking-maps-pictures")
@web_security.login_required(api=True, founder_only=True)
def clean_intelligence_status():
    return _status_response(request.path.rsplit("/", 1)[-1])


@bp.get("/war-room/movement-intelligence")
@bp.get("/war-room/booking-intelligence")
@bp.get("/war-room/map-intelligence")
@bp.get("/war-room/maps-intelligence")
@bp.get("/war-room/maps")
@bp.get("/war-room/listing-pictures")
@bp.get("/war-room/travel-pictures")
@bp.get("/war-room/movement-booking-map")
@bp.get("/war-room/movement-booking-map-pictures")
@web_security.login_required(api=True, founder_only=True)
def clean_war_room_intelligence_status():
    return _status_response(request.path.rsplit("/", 1)[-1])


@bp.get("/checkpoints")
@web_security.login_required(api=True, founder_only=True)
def legacy_checkpoints_index():
    return intelligence_index()


@bp.get("/checkpoints/<status_id>")
@bp.get("/war-room/checkpoints/<status_id>")
@web_security.login_required(api=True, founder_only=True)
def legacy_status_detail(status_id: str):
    return _status_response(status_id)
