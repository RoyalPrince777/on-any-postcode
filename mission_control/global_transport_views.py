# ruff: noqa: I001
"""OAP Global Transport public surface and install-readiness contract.

This module exposes one first-party front door over existing OAP movement,
transport intelligence, distribution and travel capabilities. It does not
pretend that a software route is a licensed carrier, dispatch network, payment
rail, customs authority or live third-party feed.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, redirect, render_template_string, request

from . import authority, oap_ride, operator_gateway, transport_execution_evidence, web_security
from .oap_ride_dashboards import bp as oap_ride_dashboards_bp
from .oap_ride_runtime_routes import bp as oap_ride_runtime_bp
from .oap_ride_journey_views import bp as oap_ride_journey_bp
from .oap_ride_guardian_routes import bp as oap_ride_guardian_bp
from .oap_ride_earnings_routes import bp as oap_ride_earnings_bp
from .oap_ride_commercial_routes import bp as oap_ride_commercial_bp
from .oap_ride_payment_bridge_routes import bp as oap_ride_payment_bridge_bp
from .oap_ride_driver_accessibility_routes import bp as oap_ride_driver_accessibility_bp
from .oap_ride_ops_routes import bp as oap_ride_ops_bp
from .oap_eats_routes import bp as oap_eats_bp
from .travel_transport_views import bp as travel_transport_booking_bp

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
bp.register_blueprint(oap_eats_bp)
bp.register_blueprint(travel_transport_booking_bp)

PUBLIC_DOORS = (
    ("Journey", "End-to-end multimodal journey planning", "/travel"),
    ("Move", "Movement, disruption and route state", "/movement/workspace"),
    ("Ride", "Governed ride-request capability", "/transport/ride"),
    ("Transit", "Bus, rail, metro, tram and ferry", "/travel"),
    ("Drive", "Personal vehicle and road journey layer", "/oap-map?profile=driving"),
    ("Fly", "Air journey and airport layer", "/travel"),
    ("Cargo", "Freight and cross-border planning", "/distribution"),
    ("Deliver", "Local and global delivery layer", "/movement/workspace#book-title"),
    ("Fleet", "Commercial vehicle and driver operations", "/transport/ride/driver"),
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
    key: False for key in transport_execution_evidence.EXECUTION_REQUIREMENTS
}


EXECUTION_READINESS = {
    key: {
        "software_ready": True,
        "requires": requirements,
    }
    for key, requirements in transport_execution_evidence.EXECUTION_REQUIREMENTS.items()
}


def live_execution_gates() -> dict[str, bool]:
    evidence = transport_execution_evidence.status()
    areas = evidence.get("areas") if isinstance(evidence.get("areas"), dict) else {}
    return {
        key: bool(
            isinstance(areas.get(key), dict)
            and areas[key].get("live_execution_authorised") is True
        )
        for key in EXECUTION_READINESS
    }


def execution_readiness() -> dict[str, object]:
    evidence = transport_execution_evidence.status()
    evidence_areas = (
        evidence.get("areas") if isinstance(evidence.get("areas"), dict) else {}
    )
    areas = {}
    for key, value in EXECUTION_READINESS.items():
        evidence_area = evidence_areas.get(key)
        if not isinstance(evidence_area, dict):
            evidence_area = {}
        areas[key] = {
            "software_ready": bool(value["software_ready"]),
            "live_execution_authorised": bool(
                evidence_area.get("live_execution_authorised") is True
            ),
            "requires": list(value["requires"]),
            "verified": list(evidence_area.get("verified") or ()),
            "missing": list(
                evidence_area["missing"]
                if "missing" in evidence_area
                else value["requires"]
            ),
        }
    return {
        "product": "OAP Global Transport",
        "software_execution_layer_ready": all(
            item["software_ready"] for item in EXECUTION_READINESS.values()
        ),
        "live_execution_authorised": bool(areas) and all(
            item["live_execution_authorised"] for item in areas.values()
        ),
        "areas": areas,
        "evidence_store_reachable": bool(evidence.get("store_reachable")),
        "software_verified_external_authenticity": False,
        "truth_boundary": (
            "Software execution contracts are installed. Live execution unlocks only "
            "from reviewed VERIFIED external evidence references for every required item. "
            "Recording a reference does not make its external authenticity software-verified."
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
        "public_doors": [name.lower() for name, _, _ in PUBLIC_DOORS],
        "public_routes": {name.lower(): href for name, _, href in PUBLIC_DOORS},
        "capability_count": len(CAPABILITIES),
        "capabilities": list(CAPABILITIES),
        "integrations": list(INTEGRATIONS),
        "shared_bikes": operator_gateway.shared_bikes_status(),
        "operator_gateway": operator_gateway.status(),
        "existing_transport_intelligence_reused": True,
        "post_core_authoritative_for_parcels": True,
        "human_authority_final": True,
        "live_execution_gates": live_execution_gates(),
        "execution_readiness": execution_readiness(),
        "live_external_transport_execution": execution_readiness()["live_execution_authorised"],
        "mission_scope": "software_plus_evidence_gated_execution",
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
<link rel="manifest" href="/transport/manifest.webmanifest">
<meta name="theme-color" content="#050807">
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
<div class="bar">
<button type="button" data-oap-install hidden>Install OAP Transport</button>
<span data-oap-install-status role="status">Checking install support</span>
<span data-oap-install-platform hidden></span>
</div>
</section>
<section class="grid">
{% for name, description, href in doors %}
<a class="card" href="{{ href }}"><strong>{{ name }}</strong><span>{{ description }}</span></a>
{% endfor %}
</section>
<small>Software + digital coordination only. Physical transport operations remain evidence-gated. Human Authority remains final.</small>
<script src="/assets/oap-os.js" defer></script>
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


@bp.get("/transport/shared-bikes/status")
def transport_shared_bikes_status():
    return _no_store(jsonify(operator_gateway.shared_bikes_status()))


@bp.get("/transport/shared-bikes/mitcham")
def transport_shared_bikes_mitcham():
    try:
        payload = operator_gateway.nearby_shared_bikes_mitcham(
            radius_km=request.args.get("radius_km") or operator_gateway.DEFAULT_SHARED_BIKE_RADIUS_KM
        )
    except ValueError as exc:
        return _no_store(
            make_response(jsonify(error={"code": str(exc)[:80]}), 400)
        )
    return _no_store(jsonify(payload))


@bp.post("/transport/execution-evidence")
@web_security.login_required(api=True, founder_only=True)
def transport_execution_evidence_record():
    """Record one Founder-reviewed external execution evidence reference."""

    if not web_security.csrf_valid(request):
        return _no_store(
            make_response(
                jsonify(error={"code": "csrf_failed", "message": "Secure session required."}),
                403,
            )
        )
    user = web_security.current_authenticated_user()
    if user is None:
        return _no_store(
            make_response(
                jsonify(error={"code": "authentication_required", "message": "Founder sign-in required."}),
                401,
            )
        )
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _no_store(
            make_response(
                jsonify(error={"code": "invalid_request", "message": "A JSON object is required."}),
                400,
            )
        )
    try:
        receipt = transport_execution_evidence.record_evidence_reference(
            identity_id=str(user["id"]),
            area=payload.get("area"),
            requirement=payload.get("requirement"),
            evidence_ref=payload.get("evidence_ref"),
            evidence_hash=payload.get("evidence_hash"),
            issuer=payload.get("issuer"),
            scope=payload.get("scope"),
            attestor_type=payload.get("attestor_type"),
            verification_state=payload.get("verification_state"),
        )
    except authority.HumanAuthorityRequired:
        return _no_store(
            make_response(
                jsonify(error={"code": "human_authority_required", "message": "Level-zero Human Authority required."}),
                403,
            )
        )
    except ValueError as exc:
        return _no_store(
            make_response(
                jsonify(error={"code": "invalid_execution_evidence", "message": str(exc)}),
                400,
            )
        )
    except Exception:  # noqa: BLE001 - evidence intake fails closed.
        return _no_store(
            make_response(
                jsonify(error={"code": "execution_evidence_unavailable", "message": "Evidence could not be recorded safely."}),
                503,
            )
        )
    return _no_store(
        jsonify(
            receipt=receipt,
            execution_readiness=execution_readiness(),
            human_authority_final=True,
        )
    )



_RIDE_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0a0d10">
<title>OAP Rides</title>
<style>
:root{color-scheme:dark;--bg:#0a0d10;--panel:#12171b;--panel2:#172027;--line:#26323a;--gold:#efc85d;--blue:#80bfff;--green:#7ee2a8;--muted:#94a2ad;--text:#f7f9fa}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,sans-serif}
body{min-height:100vh}.app{max-width:760px;margin:auto;padding:env(safe-area-inset-top) 16px calc(92px + env(safe-area-inset-bottom))}
.top{display:flex;justify-content:space-between;align-items:center;padding:16px 0 10px;position:sticky;top:0;z-index:4;background:linear-gradient(var(--bg) 72%,transparent)}
.brand{display:flex;gap:11px;align-items:center;text-decoration:none;color:var(--text)}.mark{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(145deg,#16212a,#0e1114);border:1px solid #3b5363;color:var(--blue);font-weight:900}
.brand strong{display:block}.brand small{display:block;color:var(--muted)}.round{width:42px;height:42px;display:grid;place-items:center;border:1px solid var(--line);border-radius:14px;background:var(--panel);text-decoration:none;color:var(--text)}
.hero{padding:22px 0 8px}.eyebrow{font-size:.76rem;letter-spacing:.12em;color:var(--gold);font-weight:900}.hero h1{font-size:clamp(2rem,9vw,3.7rem);line-height:.98;margin:.45rem 0}.hero p{max-width:540px;color:#c3cbd1;margin:.6rem 0}
.routebox{margin:17px 0;padding:16px;border-radius:24px;background:linear-gradient(145deg,var(--panel2),var(--panel));border:1px solid var(--line)}
.route-line{display:grid;grid-template-columns:18px 1fr auto;gap:10px;align-items:center;padding:11px 4px}.route-line+.route-line{border-top:1px solid #202a30}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 0 4px #173328}.dot.to{background:var(--gold);box-shadow:0 0 0 4px #342d17}.route-line a{color:var(--text);text-decoration:none;font-weight:800}.route-line span{color:var(--muted);font-size:.82rem}.go{display:block;margin-top:12px;text-align:center;padding:14px;border-radius:16px;background:var(--gold);color:#17130a;text-decoration:none;font-weight:900}
.section-head{display:flex;justify-content:space-between;align-items:end;margin:24px 2px 12px}.section-head h2{margin:0;font-size:1.15rem}.section-head a{color:var(--blue);text-decoration:none;font-size:.88rem}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.card{min-height:118px;border:1px solid var(--line);border-radius:22px;padding:16px;background:linear-gradient(145deg,var(--panel2),var(--panel));color:var(--text);text-decoration:none;display:flex;flex-direction:column;justify-content:space-between}.card .emoji{font-size:1.6rem}.card strong{font-size:1.02rem}.card span{font-size:.81rem;line-height:1.3;color:var(--muted)}
.mode{display:grid;grid-template-columns:1fr 1fr;gap:9px}.mode a{padding:15px;border-radius:18px;border:1px solid var(--line);background:var(--panel);text-decoration:none;color:var(--text);font-weight:900}.mode small{display:block;color:var(--muted);font-weight:500;margin-top:4px}
.status{margin-top:22px;padding:14px 15px;border:1px solid #25342c;border-radius:16px;background:#101712;color:#aab8af;font-size:.82rem;line-height:1.45}.status b{color:var(--green)}
.bottom{position:fixed;left:50%;bottom:0;transform:translateX(-50%);width:min(760px,100%);display:grid;grid-template-columns:repeat(5,1fr);padding:8px 10px calc(8px + env(safe-area-inset-bottom));background:rgba(10,13,16,.96);backdrop-filter:blur(16px);border-top:1px solid var(--line);z-index:5}.bottom a{display:grid;gap:3px;place-items:center;text-decoration:none;color:var(--muted);font-size:.68rem;padding:7px 2px;border-radius:12px}.bottom a.active{color:var(--blue);background:#13202a}.bottom b{font-size:1.05rem}
@media(min-width:620px){.grid{grid-template-columns:repeat(4,1fr)}.card{min-height:136px}}
</style>
</head>
<body>
<main class="app">
<header class="top">
<a class="brand" href="/transport/ride"><span class="mark">OAP</span><span><strong>Rides</strong><small>From this postcode to the next.</small></span></a>
<a class="round" href="/transport/my" aria-label="My Transport">◎</a>
</header>
<section class="hero">
<div class="eyebrow">ON ANY POSTCODE · RIDES</div>
<h1>Move through<br>your world.</h1>
<p>One ride door powered by OAP Movement, OAP World, Guardian and SIKA.</p>
</section>
<section class="routebox">
<div class="route-line"><span class="dot"></span><a href="/oap-map">Choose pickup</a><span>OAP World</span></div>
<div class="route-line"><span class="dot to"></span><a href="/oap-map">Choose destination</a><span>Route</span></div>
<a class="go" href="/movement/workspace#book-title">Request a journey</a>
</section>
<div class="section-head"><h2>Journey tools</h2><a href="/transport/ride/current">Current journey</a></div>
<section class="grid">
<a class="card" href="/movement/workspace#book-title"><span class="emoji">🚗</span><div><strong>Request ride</strong><span>Create a governed journey request.</span></div></a>
<a class="card" href="/oap-map"><span class="emoji">🗺️</span><div><strong>Open map</strong><span>Plan pickup, destination and route.</span></div></a>
<a class="card" href="/transport/ride/current"><span class="emoji">🧭</span><div><strong>Current journey</strong><span>Journey state, code, receipt and feedback.</span></div></a>
<a class="card" href="/transport/ride/guardian/status"><span class="emoji">🛡️</span><div><strong>Guardian</strong><span>Safety controls and protected journey state.</span></div></a>
<a class="card" href="/pay/bank"><span class="emoji">🪙</span><div><strong>SIKA</strong><span>Open payment and value controls.</span></div></a>
<a class="card" href="/movement/workspace#bookings-title"><span class="emoji">🧾</span><div><strong>My journeys</strong><span>Review your movement history.</span></div></a>
<a class="card" href="/transport/ride/driver/earnings"><span class="emoji">📊</span><div><strong>Earnings</strong><span>Driver earnings software view.</span></div></a>
<a class="card" href="/eats"><span class="emoji">🍲</span><div><strong>Eats</strong><span>Switch to food and delivery.</span></div></a>
</section>
<div class="section-head"><h2>Choose mode</h2></div>
<div class="mode">
<a href="/transport/ride/rider">Rider<small>Request, match, journey, receipt</small></a>
<a href="/transport/ride/driver">Driver<small>Availability, jobs, drive, earnings</small></a>
</div>
<div class="status"><b>● Software surface active.</b> Journey requests, matching, Guardian and payment bindings are software capabilities. Physical vehicle operation and external dispatch remain outside this build.</div>
</main>
<nav class="bottom" aria-label="OAP Rides navigation">
<a class="active" href="/transport/ride"><b>⌂</b><span>Rides</span></a>
<a href="/oap-map"><b>◎</b><span>World</span></a>
<a href="/transport/ride/current"><b>↗</b><span>Journey</span></a>
<a href="/transport/ride/guardian/status"><b>⛨</b><span>Guardian</span></a>
<a href="/pay/bank"><b>◈</b><span>SIKA</span></a>
</nav>
</body>
</html>"""

@bp.get("/transport/ride")
def transport_ride():
    return _no_store(make_response(render_template_string(_RIDE_PAGE), 200))


@bp.get("/transport/ride/status")
def transport_ride_status():
    return _no_store(make_response(jsonify(oap_ride.status()), 200))


@bp.get("/transport/ride/app-config")
def transport_ride_app_config():
    return _no_store(make_response(jsonify({
        "product": "OAP Rides",
        "front_door": "/transport/ride",
        "navigation": {
            "rides": "/transport/ride",
            "world": "/oap-map",
            "journey": "/transport/ride/current",
            "guardian": "/transport/ride/guardian/status",
            "sika": "/pay/bank",
            "eats": "/eats",
        },
        "rider": "/transport/ride/rider",
        "driver": "/transport/ride/driver",
        "movement_workspace": "/movement/workspace",
        "physical_operations_in_scope": False,
        "human_authority_final": True,
    }), 200))


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
