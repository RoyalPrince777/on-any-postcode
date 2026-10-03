# ruff: noqa: I001
"""OAP Global Transport public surface and install-readiness contract.

This module exposes one first-party front door over existing OAP movement,
transport intelligence, distribution and travel capabilities. It does not
pretend that a software route is a licensed carrier, dispatch network, payment
rail, customs authority or live third-party feed.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, redirect, render_template_string

from . import oap_ride
from .oap_ride_dashboards import bp as oap_ride_dashboards_bp
from .oap_ride_runtime_routes import bp as oap_ride_runtime_bp
from .oap_ride_journey_views import bp as oap_ride_journey_bp
from .oap_ride_guardian_routes import bp as oap_ride_guardian_bp
from .oap_ride_earnings_routes import bp as oap_ride_earnings_bp
from .oap_ride_commercial_routes import bp as oap_ride_commercial_bp
from .oap_ride_payment_bridge_routes import bp as oap_ride_payment_bridge_bp
from .oap_ride_driver_accessibility_routes import bp as oap_ride_driver_accessibility_bp
from .oap_ride_ops_routes import bp as oap_ride_ops_bp

bp = Blueprint("oap_global_transport", __name__)
bp.register_blueprint(oap_ride_dashboards_bp)
bp.register_blueprint(oap_ride_runtime_bp)
bp.register_blueprint(oap_ride_journey_bp)
bp.register_blueprint(oap_ride_guardian_bp)
bp.register_blueprint(oap_ride_earnings_bp)
bp.register_blueprint(oap_ride_commercial_bp)
bp.register_blueprint(oap_ride_payment_bridge_bp)
bp.register_blueprint(oap_ride_driver_accessibility_bp)
bp.register_blueprint(oap_ride_ops_bp)

PUBLIC_DOORS = (
    ("Journey", "End-to-end multimodal journey planning"),
    ("Move", "Movement, disruption and route state"),
    ("Ride", "Governed ride-request capability"),
    ("Transit", "Bus, rail, metro, tram and ferry"),
    ("Drive", "Personal vehicle and road journey layer"),
    ("Fly", "Air journey and airport layer"),
    ("Cargo", "Freight and cross-border planning"),
    ("Deliver", "Local and global delivery layer"),
    ("Fleet", "Commercial vehicle and driver operations"),
)

CAPABILITIES = (
    "journey", "move", "ride", "drive", "transit", "fly", "sail",
    "cycle", "walk", "cargo", "deliver", "fleet", "parking", "energy",
    "road", "terminal", "accessibility", "guardian_transport",
    "transport_market", "transport_intelligence", "transport_control_center",
)

INTEGRATIONS = (
    "oap_world", "smi", "guardian", "hrm", "alpha_signal", "incoming",
    "my_world", "sika_oap_pay", "oap_market", "oap_post_core",
    "distribution_runtime", "movement",
)

RIDE_API_MAP = {
    "request_journey": "/movement/bookings",
    "driver_availability": "/movement/availability",
    "oap_match": "/movement/bookings/<booking_id>/match",
    "accept_journey": "/movement/matches/<proposal_id>/accept",
}

LIVE_EXECUTION_GATES = {
    "carrier_dispatch": False,
    "ride_dispatch": False,
    "ticket_issuance": False,
    "fare_capture": False,
    "payment_movement": False,
    "customs_clearance": False,
    "external_tracking_feed": False,
    "vehicle_control": False,
}


EXECUTION_READINESS = {
    "carrier_dispatch": {
        "software_ready": True,
        "live_execution_authorised": False,
        "requires": ("licensed_carrier_binding", "capacity_evidence", "dispatch_receipt"),
    },
    "ride_dispatch": {
        "software_ready": True,
        "live_execution_authorised": False,
        "requires": ("eligible_driver_binding", "vehicle_evidence", "dispatch_receipt"),
    },
    "ticket_issuance": {
        "software_ready": True,
        "live_execution_authorised": False,
        "requires": ("issuer_authority", "inventory_or_entitlement_proof", "issued_ticket_receipt"),
    },
    "fare_capture": {
        "software_ready": True,
        "live_execution_authorised": False,
        "requires": ("regulated_payment_executor", "customer_authorisation", "capture_receipt"),
    },
    "payment_movement": {
        "software_ready": True,
        "live_execution_authorised": False,
        "requires": ("regulated_payment_executor", "submission_evidence", "settlement_evidence"),
    },
    "customs_clearance": {
        "software_ready": True,
        "live_execution_authorised": False,
        "requires": ("customs_authority_or_broker_binding", "declaration_reference", "clearance_receipt"),
    },
    "external_tracking_feed": {
        "software_ready": True,
        "live_execution_authorised": False,
        "requires": ("tracking_source_binding", "consent", "fresh_signed_or_verified_observation"),
    },
    "vehicle_control": {
        "software_ready": True,
        "live_execution_authorised": False,
        "requires": ("vehicle_identity_binding", "device_or_oem_authority", "command_receipt"),
    },
}


def execution_readiness() -> dict[str, object]:
    return {
        "product": "OAP Global Transport",
        "software_execution_layer_ready": all(
            item["software_ready"] for item in EXECUTION_READINESS.values()
        ),
        "live_execution_authorised": all(
            item["live_execution_authorised"] for item in EXECUTION_READINESS.values()
        ),
        "areas": {
            key: {
                "software_ready": bool(value["software_ready"]),
                "live_execution_authorised": bool(value["live_execution_authorised"]),
                "requires": list(value["requires"]),
            }
            for key, value in EXECUTION_READINESS.items()
        },
        "truth_boundary": (
            "Software execution contracts are installed. External or physical execution "
            "remains fail-closed until the required real evidence exists."
        ),
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    return {
        "product": "OAP Global Transport",
        "front_door": "/transport",
        "alias": "/global-transport",
        "architecture": "One World -> One Front Door -> Many Transport Systems Inside",
        "software_surface_install_ready": True,
        "first_party_surface": True,
        "public_doors": [name.lower() for name, _ in PUBLIC_DOORS],
        "capability_count": len(CAPABILITIES),
        "capabilities": list(CAPABILITIES),
        "integrations": list(INTEGRATIONS),
        "existing_transport_intelligence_reused": True,
        "post_core_authoritative_for_parcels": True,
        "human_authority_final": True,
        "live_execution_gates": dict(LIVE_EXECUTION_GATES),
        "execution_readiness": execution_readiness(),
        "live_external_transport_execution": False,
        "mission_scope": "software_and_digital_only",
        "physical_operations_in_scope": False,
        "truth_boundary": (
            "Install-ready OAP software and digital coordination surface only. "
            "Physical transport operations, vehicle operation, custody and real-world "
            "carrier execution are outside this build."
        ),
    }


def _no_store(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Global Transport</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#090909;color:#f5f5f5;font-family:system-ui,-apple-system,sans-serif}
main{max-width:920px;margin:auto;padding:24px 16px 48px}
.hero{padding:24px;border:1px solid #7a6420;border-radius:22px;background:linear-gradient(145deg,#17130a,#0c0c0c)}
.eyebrow{color:#d8b64b;font-weight:800;letter-spacing:.08em}.hero h1{margin:.3rem 0;font-size:clamp(2rem,7vw,4rem)}
.hero p{color:#ccc;max-width:680px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:18px}
.card{display:block;text-decoration:none;color:#fff;padding:18px;border-radius:18px;border:1px solid #292929;background:#111}
.card strong{display:block;font-size:1.15rem;color:#f0cf63}.card span{display:block;color:#aaa;margin-top:7px;line-height:1.35}
.bar{margin-top:18px;padding:14px;border-radius:14px;background:#121212;color:#bbb}.green{color:#6ee7a8}.purple{color:#c4a1ff}
small{display:block;margin-top:18px;color:#777}
</style>
</head>
<body><main>
<section class="hero">
<div class="eyebrow">🌍 ON ANY POSTCODE</div>
<h1>Global Transport</h1>
<p>One World → One Front Door → Many Transport Systems Inside.</p>
<div class="bar"><span class="green">● Software surface ready</span> · <span class="purple">● Live execution stays evidence-gated</span></div>
</section>
<section class="grid">
{% for name, description in doors %}
<a class="card" href="{{ '/transport/ride' if name == 'Ride' else '/transport/status#' ~ name|lower }}"><strong>{{ name }}</strong><span>{{ description }}</span></a>
{% endfor %}
</section>
<small>Software + digital coordination only. Physical transport operations are outside this build. Human Authority remains final.</small>
</main></body></html>"""


@bp.get("/transport")
def transport_home():
    return _no_store(make_response(render_template_string(_PAGE, doors=PUBLIC_DOORS)))


@bp.get("/global-transport")
def transport_alias():
    return transport_home()


@bp.get("/transport/status")
def transport_status():
    return _no_store(jsonify(status()))


@bp.get("/transport/capabilities")
def transport_capabilities():
    state = status()
    return _no_store(jsonify({
        "product": state["product"],
        "capability_count": state["capability_count"],
        "capabilities": state["capabilities"],
        "integrations": state["integrations"],
        "live_execution_gates": state["live_execution_gates"],
        "execution_readiness": state["execution_readiness"],
        "human_authority_final": True,
    }))


@bp.get("/transport/execution-readiness")
def transport_execution_readiness():
    return _no_store(jsonify(execution_readiness()))


@bp.get("/transport/ride")
def transport_ride():
    return _no_store(jsonify(oap_ride.status()))


@bp.post("/transport/ride/request")
def ride_request_alias():
    return redirect("/movement/bookings", code=307)


@bp.post("/transport/ride/driver/availability")
def ride_driver_availability_alias():
    return redirect("/movement/availability", code=307)


@bp.post("/transport/ride/<booking_id>/match")
def ride_match_alias(booking_id: str):
    return redirect(f"/movement/bookings/{booking_id}/match", code=307)


@bp.post("/transport/ride/matches/<proposal_id>/accept")
def ride_accept_alias(proposal_id: str):
    return redirect(f"/movement/matches/{proposal_id}/accept", code=307)


@bp.get("/transport/ride/runtime")
def ride_runtime():
    return _no_store(jsonify({
        "product": "OAP Ride",
        "durable_owner": "OAP Movement",
        "api_map": RIDE_API_MAP,
        "certified_driver_matching": True,
        "race_safe_match_acceptance": True,
        "tracking_consent_store": True,
        "payment_intent_store": True,
        "trip_link_binding": True,
        "physical_operations_in_scope": False,
        "external_dispatch_performed": False,
    }))
