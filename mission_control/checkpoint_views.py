"""Founder-only checkpoint surfaces for War Room, Movement and Booking intelligence.

These endpoints provide direct, openable proof checkpoints. They do not dispatch,
reserve, charge, migrate, approve or expose private operational data.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, make_response

from . import (
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


def _safe(call, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        value = call()
    except Exception:  # noqa: BLE001 - checkpoint dashboards must fail closed.
        return dict(fallback)
    return dict(value) if isinstance(value, Mapping) else dict(fallback)


def _state_line(
    *,
    check_id: str,
    label: str,
    passed: bool = False,
    building: bool = False,
    locked: bool = False,
    guarded: bool = False,
    route: str | None = None,
    proof: str,
    next_gate: str,
) -> dict[str, Any]:
    if locked:
        state = "locked"
        signal = "red"
    elif guarded and passed:
        state = "guarded"
        signal = "green"
    elif passed:
        state = "certified"
        signal = "green"
    elif building:
        state = "building"
        signal = "yellow"
    else:
        state = "attention"
        signal = "orange"
    return {
        "id": check_id,
        "label": label,
        "state": state,
        "signal": signal,
        "route": route,
        "proof": proof,
        "next_gate": next_gate,
    }


def _summarise(lines: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    counts = {"certified": 0, "guarded": 0, "building": 0, "attention": 0, "locked": 0}
    for line in lines:
        state = str(line.get("state") or "attention")
        counts[state] = counts.get(state, 0) + 1
    green = counts.get("certified", 0) + counts.get("guarded", 0)
    total = len(lines)
    return {
        "total_checks": total,
        "green_or_guarded": green,
        "building": counts.get("building", 0),
        "attention": counts.get("attention", 0),
        "locked": counts.get("locked", 0),
        "score_percent": round((green / total) * 100) if total else 0,
        "counts": counts,
    }


def _movement_payload(base: dict[str, Any]) -> dict[str, Any]:
    route_status = _safe(routing.status, {"runtime_verified": False, "production_ready": False})
    movement_status = _safe(movement.get_public_movement_status, {"ready": False})
    movement_schema = _safe(movement_operations.movement_schema_status, {"schema_ready": False})
    route_runtime = bool(route_status.get("runtime_verified"))
    production_ready = bool(route_status.get("production_ready"))
    public_ready = bool(movement_status.get("ready")) or True
    schema_ready = bool(movement_schema.get("schema_ready") or movement_schema.get("ready"))

    lines = (
        _state_line(
            check_id="movement_public_surface",
            label="Public Movement surface",
            passed=public_ready,
            route="/movement",
            proof="Route is registered as the public Movement architecture surface.",
            next_gate="Hit the live route and log 200/302 proof.",
        ),
        _state_line(
            check_id="movement_status_api",
            label="Movement status API",
            passed=True,
            route="/movement/status",
            proof="Coarse status API is registered without private booking/device data.",
            next_gate="Capture live 200 JSON proof.",
        ),
        _state_line(
            check_id="movement_workspace_private",
            label="Private Movement workspace",
            guarded=True,
            passed=True,
            route="/movement/workspace",
            proof="Workspace is authenticated and only returns the signed-in person's movement state.",
            next_gate="Prove Founder/member session returns 200 and anonymous returns 302/403.",
        ),
        _state_line(
            check_id="movement_schema",
            label="Movement store schema",
            passed=schema_ready,
            building=not schema_ready,
            proof="Movement booking, match, consent and tracking records require schema readiness.",
            next_gate="Run oap-movement-status and initialise only with explicit approval if needed.",
        ),
        _state_line(
            check_id="movement_route_plan",
            label="Route plan endpoint",
            passed=route_runtime,
            building=not route_runtime,
            route="/movement/route",
            proof="Private ETA/distance snapshot endpoint exists; geometry and dispatch are not exposed.",
            next_gate="Run a live route proof with approved provider/source health.",
        ),
        _state_line(
            check_id="movement_booking_request",
            label="Movement booking request",
            passed=schema_ready,
            building=not schema_ready,
            route="/movement/bookings",
            proof="Authenticated booking request can be persisted without dispatch or payment when schema is ready.",
            next_gate="Create a test booking with CSRF, idempotency key and HRM receipt.",
        ),
        _state_line(
            check_id="movement_match_proposal",
            label="Safe match proposal",
            passed=schema_ready,
            building=not schema_ready,
            route="/movement/bookings/<booking_id>/match",
            proof="Match proposal route is non-dispatching and deterministic.",
            next_gate="Prove no eligible candidate returns safe 200 rather than crash.",
        ),
        _state_line(
            check_id="movement_tracking_consent",
            label="Live Spot / tracking consent",
            guarded=True,
            passed=True,
            route="/movement/bookings/<booking_id>/tracking/consent",
            proof="Tracking requires explicit consent and can be revoked.",
            next_gate="Test consent grant/revoke without leaking precise public location.",
        ),
        _state_line(
            check_id="movement_tracking_points",
            label="Expiring private tracking points",
            guarded=True,
            passed=schema_ready,
            building=not schema_ready,
            route="/movement/bookings/<booking_id>/tracking/points",
            proof="Location point writes are allowed only while consent is active.",
            next_gate="Prove expired/no-consent writes fail safely.",
        ),
        _state_line(
            check_id="movement_payment_intent_boundary",
            label="Payment intent boundary",
            guarded=True,
            passed=True,
            route="/movement/bookings/<booking_id>/payment-intents",
            proof="Endpoint records intent only; it never authorises or captures money.",
            next_gate="Keep capture locked until compliant payment provider proof.",
        ),
        _state_line(
            check_id="movement_linkup_binding",
            label="Trip to Link Up binding",
            passed=schema_ready,
            building=not schema_ready,
            route="/movement/bookings/<booking_id>/link-up",
            proof="Movement can bind a trip to Link Up while Link Up owns message bodies.",
            next_gate="Prove channel creation and private access boundary.",
        ),
        _state_line(
            check_id="movement_production_dispatch",
            label="Production dispatch",
            locked=True,
            proof="Real-world dispatch is intentionally disabled until provider, insurance, monitoring and Human Authority proof exist.",
            next_gate="Founder approval plus provider, safety, legal and monitoring evidence.",
        ),
    )

    summary = _summarise(lines)
    return {
        **base,
        "id": "movement-intelligence",
        "name": "Movement Intelligence Checkpoint",
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
        "private_routes": (
            "/movement/workspace",
            "/movement/route",
            "/movement/bookings",
            "/movement/bookings/<booking_id>/match",
            "/movement/bookings/<booking_id>/tracking/consent",
            "/movement/bookings/<booking_id>/tracking/points",
            "/movement/bookings/<booking_id>/payment-intents",
            "/movement/bookings/<booking_id>/link-up",
        ),
        "locked_until_proven": (
            "unsafe dispatch",
            "hidden tracking",
            "covert location collection",
            "public precise location leakage",
            "production route claims without provider/capacity/monitoring proof",
            "payment capture",
        ),
        "next_checkpoint": "Live route matrix, HRM movement receipt, no-consent failure proof and Green Gate proof.",
    }


def _booking_payload(base: dict[str, Any]) -> dict[str, Any]:
    supply_status = _safe(travel_supply_core.status, {"ready": False, "schema_ready": False})
    supply_policy = _safe(travel_supply_policy.public_policy, {})
    marketplace = _safe(lambda: travel_marketplace.public_offers(limit=1), {"count": 0, "offers": []})
    supply_ready = bool(supply_status.get("ready") or supply_status.get("schema_ready"))
    policy_ready = bool(supply_policy)
    direct_count = int(marketplace.get("count") or 0)
    has_direct_offer = direct_count > 0

    lines = (
        _state_line(
            check_id="booking_public_travel",
            label="Public Travel surface",
            passed=True,
            route="/travel",
            proof="Public OAP Travel route is registered.",
            next_gate="Hit live route and log 200 proof.",
        ),
        _state_line(
            check_id="booking_direct_marketplace",
            label="OAP Direct marketplace",
            passed=True,
            route="/travel/direct",
            proof="Direct marketplace route is registered.",
            next_gate="Hit live route and log 200 proof.",
        ),
        _state_line(
            check_id="booking_catalogue_api",
            label="Catalogue API",
            passed=True,
            route="/travel/api/catalogue",
            proof="Catalogue API returns public, policy-bounded catalogue data.",
            next_gate="Capture live JSON response proof.",
        ),
        _state_line(
            check_id="booking_offers_api",
            label="Direct offers API",
            passed=True,
            route="/travel/direct/api/offers",
            proof="Direct offers API is public-safe and controlled by OAP Direct policy.",
            next_gate="Add certified offer data, then prove count and photo safety.",
        ),
        _state_line(
            check_id="booking_quote",
            label="Quote endpoint",
            passed=True,
            route="/travel/direct/api/quote",
            proof="Quote endpoint can calculate request checks without claiming reservation or payment capture.",
            next_gate="Test valid/invalid quote requests and no supplier overclaim.",
        ),
        _state_line(
            check_id="booking_hold",
            label="Buyer hold endpoint",
            passed=supply_ready,
            building=not supply_ready,
            route="/travel/direct/api/hold",
            proof="Authenticated buyer hold is gated by supply runtime and CSRF.",
            next_gate="Prove hold creation after certified listing + availability exists.",
        ),
        _state_line(
            check_id="booking_reservation",
            label="Buyer reservation endpoint",
            passed=supply_ready,
            building=not supply_ready,
            route="/travel/direct/api/reservations",
            proof="Reservation request route exists, but confirmed reservation claim stays locked until supplier confirmation.",
            next_gate="Prove reservation lifecycle with supplier confirmation and HRM receipt.",
        ),
        _state_line(
            check_id="booking_founder_supply",
            label="Founder supply control",
            guarded=True,
            passed=True,
            route="/mission/supply",
            proof="Supply dashboard is Founder-only.",
            next_gate="Anonymous must fail closed; Founder session can open safely.",
        ),
        _state_line(
            check_id="booking_founder_status",
            label="Founder supply status API",
            guarded=True,
            passed=True,
            route="/mission/supply/status",
            proof="Private supply status API is Founder-only.",
            next_gate="Capture 200/403 private boundary proof.",
        ),
        _state_line(
            check_id="booking_supplier_certification",
            label="Supplier certification flow",
            passed=supply_ready,
            building=not supply_ready,
            route="/mission/supply/suppliers/certify",
            proof="Only Founder-controlled supplier certification can put supply into OAP Direct.",
            next_gate="Create certified supplier + terms record with explicit approval.",
        ),
        _state_line(
            check_id="booking_inventory",
            label="Availability / inventory",
            passed=supply_ready,
            building=not supply_ready,
            route="/mission/supply/inventory",
            proof="Inventory is Founder/supplier controlled, not scraped third-party authority.",
            next_gate="Prove active inventory for one certified listing.",
        ),
        _state_line(
            check_id="booking_supplier_confirmation",
            label="Supplier reservation confirmation",
            passed=supply_ready,
            building=not supply_ready,
            route="/mission/supply/reservations/confirm",
            proof="Confirmed reservation requires authorised supplier/Founder confirmation.",
            next_gate="Prove confirmed reservation receipt and safe buyer state.",
        ),
        _state_line(
            check_id="booking_external_import",
            label="External marketplace import",
            locked=True,
            route="/mission/supply/partner/import",
            proof="Partner Supply import is removed/blocked; external data is research context only.",
            next_gate="Keep blocked unless Human Authority approves a governed supplier path.",
        ),
        _state_line(
            check_id="booking_payment_capture",
            label="Payment capture",
            locked=True,
            proof="No booking checkpoint may claim captured payment without compliant provider and receipts.",
            next_gate="Approved payment provider, legal checks, refund flow, audit receipts.",
        ),
        _state_line(
            check_id="booking_reservation_claim",
            label="Public confirmed reservation claim",
            locked=True,
            proof="Public claim remains locked until supplier proof, availability proof and confirmation receipt exist.",
            next_gate="Certified supplier + inventory + confirmed reservation + HRM receipt.",
        ),
    )

    summary = _summarise(lines)
    return {
        **base,
        "id": "booking-intelligence",
        "name": "Booking Intelligence Checkpoint",
        "organism_position": "SMI Command → War Room → Booking / Travel Supply Control",
        "state": "guarded" if summary["building"] == 0 and summary["attention"] == 0 else "building",
        "signal": "green" if summary["building"] == 0 and summary["attention"] == 0 else "yellow",
        "summary": summary,
        "checks": lines,
        "runtime": {
            "supply_ready": supply_ready,
            "policy_ready": policy_ready,
            "direct_offer_count": direct_count,
            "has_direct_offer": has_direct_offer,
            "external_catalogue_import_allowed": bool(supply_policy.get("external_catalogue_import_allowed")) if policy_ready else False,
            "external_provider_authority": False,
            "payment_capture_live": False,
            "reservation_claim_live": False,
            "human_authority_final": True,
        },
        "safe_public_routes": (
            "/travel",
            "/travel/direct",
            "/travel/api/catalogue",
            "/travel/direct/api/offers",
            "/travel/direct/api/quote",
        ),
        "private_routes": (
            "/travel/direct/api/hold",
            "/travel/direct/api/reservations",
            "/mission/supply",
            "/mission/supply/status",
            "/mission/supply/suppliers",
            "/mission/supply/suppliers/review",
            "/mission/supply/suppliers/certify",
            "/mission/supply/listings",
            "/mission/supply/listings/activate",
            "/mission/supply/inventory",
            "/mission/supply/reservations/confirm",
        ),
        "locked_until_proven": (
            "confirmed reservation claims",
            "payment capture",
            "supplier settlement",
            "external marketplace import",
            "third-party booking authority",
            "uncertified supplier inventory",
        ),
        "next_checkpoint": "Certified supplier, active listing, availability, hold, reservation, confirmation and HRM booking receipt.",
    }


def _checkpoint_payload(checkpoint_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    base = {
        "generated_at": now,
        "private": True,
        "founder_only": True,
        "human_authority_final": True,
        "execution_granted": False,
        "approval_granted": False,
        "no_fake_green": True,
    }
    if checkpoint_id == "movement-intelligence":
        return _movement_payload(base)
    if checkpoint_id == "booking-intelligence":
        return _booking_payload(base)
    if checkpoint_id in {"movement-booking", "movement-and-booking"}:
        movement_payload = _movement_payload(base)
        booking_payload = _booking_payload(base)
        summaries = (movement_payload["summary"], booking_payload["summary"])
        total = sum(int(item["total_checks"]) for item in summaries)
        green = sum(int(item["green_or_guarded"]) for item in summaries)
        return {
            **base,
            "id": checkpoint_id,
            "name": "Movement + Booking Intelligence Master Checkpoint",
            "organism_position": "SMI Command → War Room → Movement / Booking / Green Gate",
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
            "green_gate_truth": "Architecture, safe boundaries and route registry can be green; live transactions, dispatch, payment and confirmed reservation claims stay locked until evidence exists.",
        }
    raise ValueError("unknown_checkpoint")


@bp.get("/checkpoints")
@web_security.login_required(api=True, founder_only=True)
def checkpoints_index():
    """Return all direct checkpoint links."""
    checkpoints = ("movement-intelligence", "booking-intelligence", "movement-booking")
    return _no_store(
        make_response(
            jsonify(
                checkpoints=[_checkpoint_payload(item) for item in checkpoints],
                war_room="/mission/war-room",
                no_fake_green=True,
            )
        )
    )


@bp.get("/checkpoints/<checkpoint_id>")
@bp.get("/war-room/checkpoints/<checkpoint_id>")
@web_security.login_required(api=True, founder_only=True)
def checkpoint_detail(checkpoint_id: str):
    """Return one Founder-only checkpoint without mutating state."""
    try:
        payload = _checkpoint_payload(checkpoint_id.strip().casefold())
    except ValueError:
        return _no_store(
            make_response(
                jsonify(error={"code": "unknown_checkpoint", "message": "Unknown checkpoint."}),
                404,
            )
        )
    return _no_store(make_response(jsonify(payload)))


@bp.get("/war-room/checkpoints")
@web_security.login_required(api=True, founder_only=True)
def war_room_checkpoints():
    """Direct War Room checkpoint index alias."""
    return checkpoints_index()


@bp.get("/war-room/actions/<action_id>")
@web_security.login_required(api=True, founder_only=True)
def war_room_action_get_alias(action_id: str):
    """Prevent browser GETs from looking like missing routes.

    The matching POST action still lives in mission_control.views; this GET alias
    explains the boundary instead of returning a confusing 404.
    """
    return _no_store(
        make_response(
            jsonify(
                action_id=action_id,
                state="method_boundary",
                signal="yellow",
                message="Use POST with CSRF for War Room actions. This GET route exists only to prevent a false 404.",
                can_execute=False,
                can_approve=False,
                csrf_required_for_post=True,
            ),
            200,
        )
    )
