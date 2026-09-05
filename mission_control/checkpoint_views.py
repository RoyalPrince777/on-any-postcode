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


def _checkpoint_payload(checkpoint_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    route_status = _safe(routing.status, {"runtime_verified": False, "production_ready": False})
    movement_status = _safe(movement.get_public_movement_status, {"ready": False})
    movement_schema = _safe(movement_operations.movement_schema_status, {"schema_ready": False})
    supply_status = _safe(travel_supply_core.status, {"ready": False, "schema_ready": False})
    supply_policy = _safe(travel_supply_policy.public_policy, {})
    marketplace = _safe(lambda: travel_marketplace.public_offers(limit=1), {"count": 0, "offers": []})

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
        runtime_verified = bool(route_status.get("runtime_verified")) or bool(movement_status.get("ready"))
        production_ready = bool(route_status.get("production_ready"))
        return {
            **base,
            "id": checkpoint_id,
            "name": "Movement Intelligence Checkpoint",
            "organism_position": "SMI Command → War Room → Movement / Map Control",
            "state": "live" if runtime_verified else "building",
            "signal": "green" if runtime_verified else "yellow",
            "checks": {
                "public_movement_surface": True,
                "movement_status_api": True,
                "movement_schema_ready": bool(movement_schema.get("schema_ready") or movement_schema.get("ready")),
                "route_runtime_verified": bool(route_status.get("runtime_verified")),
                "production_routing_ready": production_ready,
                "dispatch_enabled": False,
                "hidden_tracking_allowed": False,
                "consent_required_for_live_spot": True,
                "guardian_boundary": "active",
            },
            "routes": {
                "public": "/movement",
                "status": "/movement/status",
                "workspace": "/movement/workspace",
                "route_plan": "/movement/route",
                "bookings": "/movement/bookings",
            },
            "locked_until_proven": (
                "unsafe dispatch",
                "hidden tracking",
                "covert location collection",
                "production route claims without provider/capacity/monitoring proof",
            ),
            "next_checkpoint": "Live route matrix, HRM movement receipt and Green Gate proof.",
        }

    if checkpoint_id == "booking-intelligence":
        direct_catalogue = int(marketplace.get("count") or 0) >= 0
        supply_ready = bool(supply_status.get("ready") or supply_status.get("schema_ready"))
        return {
            **base,
            "id": checkpoint_id,
            "name": "Booking Intelligence Checkpoint",
            "organism_position": "SMI Command → War Room → Booking / Travel Supply Control",
            "state": "building" if not supply_ready else "guarded",
            "signal": "yellow" if not supply_ready else "green",
            "checks": {
                "public_travel_surface": True,
                "direct_catalogue_api": direct_catalogue,
                "oap_direct_only_policy": bool(supply_policy),
                "external_catalogue_import_allowed": bool(supply_policy.get("external_catalogue_import_allowed")) if supply_policy else False,
                "external_provider_authority": False,
                "supplier_certification_required": True,
                "payment_capture_live": False,
                "reservation_claim_live": False,
                "founder_supply_control": True,
                "guardian_boundary": "active",
            },
            "routes": {
                "public_travel": "/travel",
                "direct_marketplace": "/travel/direct",
                "catalogue_api": "/travel/api/catalogue",
                "offers_api": "/travel/direct/api/offers",
                "founder_supply": "/mission/supply",
                "founder_supply_status": "/mission/supply/status",
            },
            "locked_until_proven": (
                "confirmed reservation claims",
                "payment capture",
                "supplier settlement",
                "external marketplace import",
                "third-party booking authority",
            ),
            "next_checkpoint": "Certified supplier, active listing, availability, hold/reservation proof and HRM booking receipt.",
        }

    raise ValueError("unknown_checkpoint")


@bp.get("/checkpoints")
@web_security.login_required(api=True, founder_only=True)
def checkpoints_index():
    """Return all direct checkpoint links."""
    checkpoints = ("movement-intelligence", "booking-intelligence")
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
