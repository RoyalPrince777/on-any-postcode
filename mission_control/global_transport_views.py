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

# Keep the routed nine-door destinations as compatibility metadata.
# They are not the visible navigation, and no underlying routes are removed.
LEGACY_PUBLIC_ROUTES = {
    "journey": "/travel",
    "move": "/movement/workspace",
    "ride": "/transport/ride",
    "transit": "/travel",
    "drive": "/oap-map?profile=driving",
    "fly": "/travel",
    "cargo": "/distribution",
    "deliver": "/movement/workspace#book-title",
    "fleet": "/transport/ride/driver",
}

PUBLIC_DOORS = (
    ("Journey", "End-to-end journey planning", "/travel"),
    ("Move", "Movement, maps and navigation", "/movement/workspace"),
    ("Ride", "OAP Rider and Driver", "/transport/ride"),
    ("Logistics", "Cargo, deliveries and fleet", "/transport/logistics"),
    ("Guardian", "Journey safety and protection", "/transport/guardian"),
    ("Operators", "Provider and shared-bike discovery", "/transport/operators"),
    ("Control Center", "Transport execution readiness", "/transport/control-center"),
)

DOOR_GROUPS = {
    "journey": ["journey", "walk", "cycle", "parking"],
    "move": ["move", "drive", "transit", "fly", "sail", "road", "terminal", "energy"],
    "ride": ["ride", "accessibility"],
    "logistics": ["cargo", "deliver", "fleet"],
    "guardian": ["guardian_transport"],
    "operators": ["transport_market"],
    "control_center": ["transport_intelligence", "transport_control_center"],
}

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
        "public_doors": [name.lower().replace(" ", "_") for name, _, _ in PUBLIC_DOORS],
        "public_routes": {name.lower().replace(" ", "_"): href for name, _, href in PUBLIC_DOORS},
        "legacy_public_routes": LEGACY_PUBLIC_ROUTES,
        "door_groups": DOOR_GROUPS,
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
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="manifest" href="/transport/manifest.webmanifest">
<meta name="theme-color" content="#090909">
<title>OAP Global Transport</title>
<style>
:root{color-scheme:dark;--bg:#090909;--panel:#161512;--edge:#353025;--gold:#efcf73;--muted:#bdb7aa}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#f7f7f7;font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:800px;margin:auto;padding:calc(18px + env(safe-area-inset-top)) 16px calc(36px + env(safe-area-inset-bottom))}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:28px;padding-bottom:14px;border-bottom:1px solid var(--edge)}
.brand{color:var(--gold);font-weight:800;font-size:.78rem;letter-spacing:.075em}
.return{color:var(--gold);text-decoration:none;font-weight:700;padding:10px 0;min-height:44px;display:inline-flex;align-items:center}
h1{font-size:clamp(2.15rem,7.5vw,3.3rem);line-height:1.08;letter-spacing:-.045em;margin:0 0 23px;font-weight:850}
.intro{color:var(--muted);margin:0 0 24px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.card{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:80px;min-width:0;
padding:16px;border-radius:17px;background:var(--panel);border:1px solid var(--edge);
text-decoration:none;color:inherit;transition:border-color .15s}
.card:hover,.card:focus-visible{border-color:var(--gold)}.card:active{background:#22201a}
.card:focus-visible,.return:focus-visible,button:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
.card strong{display:block;color:#f7f7f7;font-size:1rem;line-height:1.25;overflow-wrap:break-word;flex:1;font-weight:750}

.card .arrow{font-size:1.1rem;color:var(--gold);flex:none}.card .mark{width:34px;height:34px;flex:none;display:grid;place-items:center;border-radius:11px;background:#262116;font-size:1.2rem}
.card:last-child{grid-column:1/-1;min-height:80px}
footer{margin-top:21px;padding-top:15px;border-top:1px solid var(--edge);color:var(--muted);font-size:.82rem}
.customer{margin:18px 0 6px}.customer a{border-bottom:1px solid #6f5b33}.install{margin-top:12px;display:flex;flex-wrap:wrap;align-items:center;gap:10px}.install:has(> button[hidden]):has(> [role=status]:empty){display:none}
.install button{background:#2a2418;border:1px solid #927744;border-radius:12px;color:var(--gold);padding:12px 17px;min-height:48px;font:inherit;font-weight:750;cursor:pointer}
.install [role=status]{color:var(--muted);font-size:.82rem}
@media(max-width:390px){main{padding-inline:14px}.grid{gap:9px}.card{padding:12px;min-height:80px;gap:7px}.card strong{font-size:.91rem}.card .mark{width:28px;height:28px;font-size:1rem}.card .arrow{font-size:1rem}}
@media(max-width:320px){.grid{grid-template-columns:1fr}.card:last-child{grid-column:auto}}
@media(prefers-reduced-motion:reduce){.card{transition:none}}
</style>
</head>
<body><main>
<header><div class="brand">ON ANY POSTCODE</div><a class="return" href="/world">OAP World</a></header>
<h1>Global Transport</h1>

{% set icons = {"Journey":"🧭", "Move":"🗺️", "Ride":"🚗", "Logistics":"📦", "Guardian":"🛡️", "Operators":"🏢", "Control Center":"⚙️"} %}
<nav class="grid" aria-label="Global Transport main menu">
{% for name, description, href in doors %}
<a class="card" href="{{ href }}"><span class="mark" aria-hidden="true">{{ icons[name] }}</span><strong>{{ name }}</strong><b class="arrow" aria-hidden="true">›</b></a>
{% endfor %}
</nav>
<p class="customer"><a class="return" href="/transport/my">My Transport · Customer controls</a></p>
<div class="install"><button type="button" data-oap-install hidden>Install OAP Transport</button>
<span data-oap-install-status role="status" aria-live="polite"></span>
<span data-oap-install-platform hidden></span></div>
<footer>Live transport requires verified providers and authorisation.</footer>
<script src="/assets/oap-os.js" defer></script>
</main></body></html>"""


# Static, public-safe offline navigation. No session, personal location or write actions.
_TRANSPORT_OFFLINE_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#090909">
<title>Global Transport · Offline</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#090909;color:#f5f5f5;font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:760px;margin:auto;padding:20px 16px 48px}
h1{font-size:clamp(1.85rem,7vw,2.8rem);line-height:1.12;margin:8px 0 12px}
p{color:#c8c8c8;margin:0 0 18px}
.brand{color:#f0cf63;font-weight:800;font-size:.8rem;letter-spacing:.075em}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.tile{background:#161616;border:1px solid #353535;border-radius:16px;min-height:76px;
padding:14px;display:flex;align-items:center;font-weight:700;color:#dedede}
.tile:last-child{grid-column:1/-1}
.notice{border-left:3px solid #f0cf63;padding:12px 14px;margin:20px 0;background:#211d14}
.retry{display:inline-flex;align-items:center;min-height:44px;padding:10px 16px;border-radius:12px;
color:#090909;background:#f0cf63;text-decoration:none;font-weight:700}
.retry:focus-visible{outline:3px solid #fff;outline-offset:3px}
small{display:block;color:#bdbdbd;margin-top:16px}
@media(max-width:320px){.grid{grid-template-columns:1fr}.tile:last-child{grid-column:auto}}
</style></head><body><main>
<p class="brand">ON ANY POSTCODE</p><h1>Global Transport</h1>
<p role="status">Offline shell only · live transport data unavailable</p>
<section class="grid" aria-label="Seven transport doors, unavailable while the server is offline">
{% for name, description, href in doors %}<div class="tile">{{ name }}</div>{% endfor %}
</section>
<div class="notice">Bookings, payments, dispatch, tracking, vehicle control and private journeys
are unavailable. No actions are queued or executed offline. Guardian, HRM and
Founder Final restrictions remain in force. Unverified status: Unknown · blocked.</div>
<a class="retry" href="/transport">Retry Global Transport</a>
<small>If your first-party Termux Flask server is running on this device, the full local
interface can open without internet. Otherwise only this public offline shell is available.</small>
</main></body></html>"""


@bp.get("/transport/offline")
def transport_offline():
    """Bounded public snapshot only; service worker may precache this exact route."""
    response = make_response(render_template_string(_TRANSPORT_OFFLINE_PAGE, doors=PUBLIC_DOORS))
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


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


# Public-facing navigation only. Technical JSON contracts remain on their original URLs.
# No operator, payment, dispatch or evidence-writing action is exposed here.
_TRANSPORT_INSIDE_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#090909">
<title>{{ title }} · OAP Global Transport</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#090909;color:#f5f5f5;font:16px system-ui,-apple-system,sans-serif}
main{max-width:760px;margin:auto;padding:calc(18px + env(safe-area-inset-top)) 16px calc(36px + env(safe-area-inset-bottom))}
nav{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
a{color:inherit;text-decoration:none}
.back{color:#e7c764;font-weight:650;min-height:44px;display:inline-flex;align-items:center;font-size:.91rem}
h1{font-size:clamp(1.75rem,6vw,2.4rem);line-height:1.15;margin:18px 0 8px}
p{line-height:1.5;color:#bdbdbd;margin:0 0 20px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.card{background:#151515;border:1px solid #333;border-radius:16px;padding:14px;
min-height:84px;min-width:0;display:flex;flex-direction:column;justify-content:center;gap:5px}
.card strong{color:#efd06b;font-size:.98rem;line-height:1.25;overflow-wrap:anywhere}.card span{font-size:.8rem;line-height:1.35;color:#bdbdbd;overflow-wrap:anywhere}
a:focus-visible{outline:3px solid #e7c764;outline-offset:3px}.card:hover,.card:focus-visible{border-color:#efd06b}
.note{margin-top:18px;color:#a9a9a9;font-size:.82rem;line-height:1.4}
@media(max-width:380px){.grid{gap:9px}.card{padding:12px}.back{font-size:.87rem}}
@media(max-width:320px){.grid{grid-template-columns:1fr}}
</style></head><body><main>
<nav><a class="back" href="/transport">← Global Transport</a><a class="back" href="/transport/my">My Transport</a></nav>
<h1>{{ title }}</h1>
<section class="grid" aria-label="{{ title }} options">
{% for name, detail, href in items %}
<a class="card" href="{{ href }}"><strong>{{ name }}</strong><span>{{ detail }}</span></a>
{% endfor %}
</section>
<p class="note">Live services require verified availability and authorisation.</p>
</main></body></html>"""

_INSIDE_DOORS = {
    "logistics": (
        "Logistics", "Cargo, deliveries and fleet.",
        (
            ("Cargo", "Sign-in required · distribution status", "/distribution"),
            ("Deliver", "Sign-in required · Delivery booking", "/movement/workspace?service=delivery#book-title"),
            ("Fleet", "Driver workspace", "/transport/ride/driver"),
        ),
    ),
    "guardian": (
        "Guardian", "Safety tools for your journey.",
        (
            ("Journey safety", "Protected journey controls", "/transport/ride/current"),
            ("Guardian status", "Read journey safety status", "/transport/ride/guardian/status"),
            ("My journeys", "Return to your journeys", "/transport/my"),
        ),
    ),
    "operators": (
        "Operators", "Discover available transport information.",
        (
            ("Shared bikes", "Mitcham discovery information", "/transport/shared-bikes/mitcham"),
            ("Provider status", "Technical availability data", "/transport/shared-bikes/status"),
            ("Ride", "OAP Rider and Driver", "/transport/ride"),
        ),
    ),
    "control-center": (
        "Control Center", "Transport software status and readiness.",
        (
            ("Readiness", "Review execution requirements", "/transport/control-center/readiness"),
            ("Capabilities", "View the 21 capability groups", "/transport/control-center/capabilities"),
            ("Transport status", "Evidence-gated operational status", "/transport/control-center/status"),
        ),
    ),
}


def _inside_door(name: str):
    title, description, items = _INSIDE_DOORS[name]
    return _no_store(make_response(render_template_string(
        _TRANSPORT_INSIDE_PAGE, title=title, description=description, items=items,
    )))


# Human-readable views; the original JSON endpoints remain unchanged.
_TRANSPORT_CONTROL_SUMMARY_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#090909">
<title>{{ title }} · OAP Global Transport</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#090909;color:#f5f5f5;font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:760px;margin:auto;padding:calc(18px + env(safe-area-inset-top)) 16px calc(36px + env(safe-area-inset-bottom))}
a{color:#e7c764}.back{display:inline-flex;align-items:center;min-height:44px;text-decoration:none;font-weight:650}
h1{font-size:clamp(1.8rem,6vw,2.5rem);margin:18px 0}
h2{font-size:1rem;margin:0 0 8px;color:#efcf73}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.panel{background:#151515;border:1px solid #353535;border-radius:16px;padding:16px;min-width:0}
.panel p{margin:0;color:#c8c8c8;overflow-wrap:anywhere}
.notice{margin:18px 0 0;border-left:3px solid #efcf73;padding:12px 14px;background:#211d14}
.note{font-size:.85rem;color:#bdbdbd;margin-top:16px}
a:focus-visible{outline:3px solid #efcf73;outline-offset:3px}
@media(max-width:360px){.grid{grid-template-columns:1fr}}
</style></head><body><main>
<a class="back" href="/transport/control-center">← Control Center</a>
<h1>{{ title }}</h1>
{% if groups is defined %}
<section class="grid" aria-label="21 grouped transport capabilities">
{% for name, items in groups %}
<article class="panel"><h2>{{ name }}</h2>
<p>{{ items|join(", ") }}</p></article>
{% endfor %}
</section>
<p class="note">Capabilities describe the software catalogue, not permissions to operate transport services.</p>
{% else %}
<section class="grid" aria-label="Execution gate status">
<article class="panel"><h2>Software</h2><p>Configured contracts; no physical operations</p></article>
<article class="panel"><h2>Live execution</h2>
<p>{% if not readiness.evidence_store_reachable %}Unknown · blocked{% elif readiness.live_execution_authorised %}Evidence requirements recorded; external authenticity unverified{% else %}Not authorised{% endif %}</p></article>
{% for name, area in readiness.areas.items() %}
<article class="panel"><h2>{{ name.replace("_", " ").title() }}</h2>
<p>{% if not readiness.evidence_store_reachable %}Unknown · blocked{% elif area.live_execution_authorised %}Required references recorded; authenticity unverified{% else %}Not authorised · {{ area.missing|length }} requirements outstanding{% endif %}</p></article>
{% endfor %}
</section>
<div class="notice">Live bookings, payments, dispatch and vehicle control require independently verified authority and evidence. Guardian, HRM and Founder Final remain in force.</div>
<a class="back" href="/transport/control-center/readiness">Review required evidence</a>
<p class="note">Human Authority remains final. Recorded references alone do not verify external authenticity.</p>
{% endif %}
</main></body></html>"""


@bp.get("/transport/control-center/capabilities")
def transport_capabilities_page():
    """Human-readable 21-capability grouping, never a live service authorisation."""
    groups = [(name.replace("_", " ").title(), [item.replace("_", " ").title() for item in members])
              for name, members in DOOR_GROUPS.items()]
    return _no_store(make_response(render_template_string(
        _TRANSPORT_CONTROL_SUMMARY_PAGE, title="Capabilities", groups=groups,
    )))


@bp.get("/transport/control-center/status")
def transport_status_page():
    """Evidence-based human status; fail closed when runtime evidence is unknown."""
    return _no_store(make_response(render_template_string(
        _TRANSPORT_CONTROL_SUMMARY_PAGE, title="Transport Status",
        readiness=execution_readiness(),
    )))


# Founder-private oversight uses existing transport evidence; never creates
# a competing dispatch, approval, payments or booking backend.
_FOUNDER_TRANSPORT_CONTROLS = (
    ("🧠 SMI", "Mission coordination", "/mission/ollama"),
    ("⚔️ WAR ROOM", "Blockers and recovery", "/mission/war-room"),
    ("🚗 Movement", "Bookings and work", "/movement/workspace"),
    ("📦 Logistics", "Deliveries and cargo", "/distribution"),
    ("🛡️ Guardian", "Journey protection", "/transport/guardian"),
    ("🧾 Evidence", "Proof requirements", "/transport/control-center/readiness"),
    ("📜 HRM Receipts", "Decision receipts", "/mission/smi/brain/receipts"),
    ("👑 Founder Final", "Final authority", "/mission/judgement"),
)

_FOUNDER_TRANSPORT_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#090909">
<title>Transport Control · Founder My World</title>
<style>
:root{color-scheme:dark;--bg:#090909;--panel:#181712;--gold:#efd076;--edge:#393327;--muted:#c0b9a8}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:#fff;font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:940px;margin:auto;padding:calc(20px + env(safe-area-inset-top)) 16px calc(55px + env(safe-area-inset-bottom))}
a{color:inherit;text-decoration:none}
.top{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;border-bottom:1px solid var(--edge);padding-bottom:14px}
.top a{display:inline-flex;align-items:center;min-height:44px;color:var(--gold);font-weight:750}
.eyebrow{margin:23px 0 7px;font-size:.76rem;font-weight:900;color:var(--gold);letter-spacing:.09em}
h1{font-size:clamp(2.1rem,9vw,3.9rem);line-height:1.02;margin:0 0 10px;letter-spacing:-.045em}
.lead{max-width:700px;color:var(--muted);margin:0 0 20px}
.mission{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border:1px solid #87713f;border-radius:16px;background:#211c12;padding:15px 16px;margin:0 0 16px}
.mission strong{display:block;font-size:1rem;color:var(--gold)}
.mission span{display:block;font-size:.81rem;color:var(--muted);margin-top:4px}
.mission a{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:10px 14px;border-radius:12px;background:var(--gold);color:#16130b;font-size:.88rem;font-weight:850}
.summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:24px}
.panel,.control{border:1px solid var(--edge);border-radius:16px;background:var(--panel);padding:16px;min-width:0}
.panel span{color:var(--muted);font-size:.79rem}.panel strong{display:block;margin-top:6px;line-height:1.3;color:var(--gold);overflow-wrap:anywhere}
h2{margin:28px 0 12px;font-size:1.15rem}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}
.control{display:flex;flex-direction:column;justify-content:center;min-height:92px;gap:6px;transition:border-color .15s,background .15s}.control:hover{background:#242014}
.control strong{font-size:1rem;color:#f8e0a0}.control span{color:var(--muted);font-size:.83rem}
.control:first-child{border-color:#9c8040}
.gate{border-bottom:1px solid var(--edge);padding:12px 0;display:flex;justify-content:space-between;align-items:center;gap:12px}
.gate span{overflow-wrap:anywhere}.gate small{color:var(--muted);text-align:right}
.evidence{margin-top:23px;border:1px solid var(--edge);border-radius:16px;background:var(--panel);padding:0 16px}.evidence summary{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:60px;cursor:pointer;font-weight:750;list-style:none}.evidence summary::-webkit-details-marker{display:none}.evidence summary::after{content:"+";color:var(--gold);font-size:1.3rem}.evidence[open] summary::after{content:"−"}.evidence section{padding:0 0 12px}.notice{margin:21px 0 0;padding:13px 15px;background:#231e15;border-left:3px solid var(--gold);font-size:.84rem;color:#d9d1c2}
a:hover,a:focus-visible{border-color:var(--gold)}a:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
@media(min-width:700px){.grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:320px){.grid,.summary{grid-template-columns:1fr}.gate{align-items:flex-start;flex-direction:column}.gate small{text-align:left}}@media(prefers-reduced-motion:reduce){.control{transition:none}}
</style></head><body><main>
<nav class="top"><a href="/my-world">← My World</a><a href="/transport/my">My Transport · Customer</a></nav>
<p class="eyebrow">FOUNDER PRIVATE · SMI GOVERNED</p>
<h1>Global Transport<br>Control Room</h1>
<p class="lead">Private oversight. Customer and Driver access stay separate.</p>
<section class="mission" aria-label="SMI Mission Keeper">
<div><strong>🧠 SMI → ALL IN A.I.</strong><span data-mission-status role="status" aria-live="polite">Latest Founder mission · checking evidence</span></div>
<a href="/mission/all-in-ai/app">Open Mission Keeper</a>
</section>
<section class="summary" aria-label="Live proof position">
<div class="panel"><span>Software capabilities</span><strong>21 registered</strong></div>
<div class="panel"><span>Real-world transport execution</span>
<strong>{% if not evidence_reachable %}Unknown · blocked{% elif externally_verified %}Independent proof required{% elif recorded %}References recorded · not independently verified{% else %}Not authorised{% endif %}</strong></div>
</section>
<h2>Command</h2>
<nav class="grid" aria-label="Founder Transport command controls">
{% for name, detail, href in controls %}
<a class="control" href="{{ href }}"><strong>{{ name }}</strong><span>{{ detail }}</span></a>
{% endfor %}
</nav>
<details class="evidence"><summary>Execution gates · {{ areas|length }}</summary>
<section aria-label="Transport gate evidence">
{% for key, area in areas.items() %}
<div class="gate"><span>{{ key.replace("_", " ").title() }}</span>
<small>{% if not evidence_reachable %}Unknown · blocked{% elif area.live_execution_authorised %}References recorded · verify externally{% else %}Locked · {{ area.missing|length }} requirements outstanding{% endif %}</small></div>
{% endfor %}
</section></details>
<div class="notice">Live dispatch, payments and vehicle control remain gated by Guardian, HRM and Founder Final. Missing proof never becomes Green.</div>
</main>
<script>
(() => {
  "use strict";
  const label = document.querySelector("[data-mission-status]");
  if (!label) return;
  // One founder-authenticated, read-only request. No polling, POST, approvals or auto-execution.
  fetch("/mission/all-in-ai/mission/latest", {
    method: "GET", credentials: "same-origin", cache: "no-store",
    headers: {"Accept": "application/json"}
  }).then(response => {
    if (!response.ok) throw new Error("mission_evidence_unavailable");
    return response.json();
  }).then(data => {
    if (data.found === false) {
      label.textContent = "No verified Founder mission checkpoint";
    } else if (data.found === true &&
               ["planned", "stopped", "recovered"].includes(data.state) &&
               data.read_back_verified === true &&
               data.audit_verified === true &&
               data.hrm_verified === true &&
               data.execution_granted === false &&
               data.approval_granted === false) {
      label.textContent = "Latest Founder mission: " + data.state +
        " · HRM receipt verified · No execution authority";
    } else {
      label.textContent = "Mission proof incomplete · blocked";
    }
  }).catch(() => { label.textContent = "Mission evidence unavailable · blocked"; });
})();
</script>
</body></html>"""


@bp.get("/my-world/transport-control")
@web_security.login_required(founder_only=True)
def founder_transport_control_room():
    """Founder-only command links and evidence status, without execution bypass."""
    readiness = execution_readiness()
    return _no_store(make_response(render_template_string(
        _FOUNDER_TRANSPORT_PAGE,
        controls=_FOUNDER_TRANSPORT_CONTROLS,
        areas=readiness.get("areas") or {},
        evidence_reachable=readiness.get("evidence_store_reachable") is True,
        recorded=readiness.get("live_execution_authorised") is True,
        externally_verified=readiness.get("software_verified_external_authenticity") is True,
    )))


@bp.get("/transport/logistics")
def transport_logistics_home():
    """Public navigation only; distribution, booking and dispatch stay gated."""
    return _inside_door("logistics")


@bp.get("/transport/guardian")
def transport_guardian_home():
    return _inside_door("guardian")


@bp.get("/transport/operators")
def transport_operators_home():
    return _inside_door("operators")


@bp.get("/transport/control-center")
def transport_control_center_home():
    return _inside_door("control-center")


_EXECUTION_READINESS_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#090909">
<title>Execution Readiness · OAP Global Transport</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#090909;color:#f5f5f5;font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:800px;margin:auto;padding:20px 16px 48px}
.back{display:inline-flex;align-items:center;min-height:44px;color:#efce68;text-decoration:none;font-weight:650}
h1{font-size:clamp(1.8rem,7vw,2.6rem);line-height:1.1;margin:20px 0 8px}
.intro,.muted{color:#bbb}.intro{margin:0 0 20px}
.summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:18px 0}
.panel,details{border:1px solid #343434;background:#161616;border-radius:16px;padding:16px}
.label{display:block;color:#bcbcbc;font-size:.8rem}
.value{font-size:1rem;font-weight:700;margin-top:5px}
section h2{font-size:1.15rem;margin:24px 0 12px}
details{margin:10px 0;padding:0}
summary{display:flex;align-items:center;justify-content:space-between;gap:12px;cursor:pointer;padding:16px;min-height:64px;list-style:none}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";font-size:1.3rem;color:#efce68}
details[open] summary::after{content:"−"}
.name{font-weight:700}.state{display:block;color:#bdbdbd;font-size:.82rem}
.content{padding:0 16px 16px}
ul{padding-left:20px;margin:8px 0;color:#e0e0e0}
li{margin:7px 0}
small{color:#bdbdbd}
.notice{border-left:3px solid #e7c762;padding:10px 14px;background:#211c12;border-radius:6px}
a:focus-visible,summary:focus-visible{outline:3px solid #efce68;outline-offset:3px}
@media(max-width:350px){.summary{grid-template-columns:1fr}}
</style></head><body><main>
<nav><a class="back" href="/transport/control-center">← Control Center</a></nav>
<h1>Execution Readiness</h1>
<p class="intro">The evidence required before transport services can operate.</p>
<div class="summary">
<div class="panel"><span class="label">Software contracts</span>
<div class="value">{{ "Configured" if state.software_execution_layer_ready else "Not ready" }}</div></div>
<div class="panel"><span class="label">Live execution</span>
<div class="value">{% if not state.evidence_store_reachable %}Unknown · blocked{% elif state.live_execution_authorised %}Evidence requirements met{% else %}Not authorised{% endif %}</div></div>
</div>
<div class="notice">
{% if not state.evidence_store_reachable %}
Evidence store not reachable. Live execution is blocked; verified coverage is unknown.
{% elif not state.live_execution_authorised %}
Live execution is not authorised for all areas. Missing requirements are shown below.
{% else %}
All required evidence references are recorded as verified. External authenticity is not independently software-verified.
{% endif %}
</div>
<section aria-label="Execution evidence areas"><h2>Execution areas · {{ state.areas|length }}</h2>
{% for key, area in state.areas.items() %}
<details><summary><span><span class="name">{{ key.replace("_", " ").title() }}</span>
<span class="state">{% if not state.evidence_store_reachable %}Evidence unavailable{% elif area.live_execution_authorised %}Requirements recorded{% else %}Not authorised{% endif %}</span>
</span><span class="state">{{ area.verified|length }}/{{ area.requires|length }} recorded</span></summary>
<div class="content">
{% if state.evidence_store_reachable %}
<p class="muted">Required evidence</p>
<ul>{% for requirement in area.requires %}
<li>{{ requirement.replace("_", " ").capitalize() }} —
{% if requirement in area.verified %}Verified reference recorded{% else %}Missing{% endif %}</li>
{% endfor %}</ul>
{% else %}
<p class="muted">Evidence coverage cannot be checked. These are required proofs, not confirmed missing records.</p>
<ul>{% for requirement in area.requires %}
<li>{{ requirement.replace("_", " ").capitalize() }}</li>
{% endfor %}</ul>
{% endif %}
</div></details>
{% endfor %}
</section>
<p class="muted">A verified reference alone does not prove external authenticity. Human Authority remains final.</p>
</main></body></html>"""


@bp.get("/transport/control-center/readiness")
def transport_readiness_page():
    return _no_store(make_response(render_template_string(
        _EXECUTION_READINESS_PAGE, state=execution_readiness(),
    )))


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
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#090909">
<title>OAP Ride · Global Transport</title>
<style>
:root{color-scheme:dark;--bg:#090909;--panel:#181612;--edge:#3b3325;--gold:#efcf73;--muted:#bdb7aa}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:#fff;font:16px/1.45 system-ui,-apple-system,sans-serif}
main{max-width:820px;margin:auto;padding:calc(17px + env(safe-area-inset-top)) 16px calc(38px + env(safe-area-inset-bottom))}
a{color:inherit;text-decoration:none}
header{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--edge);padding-bottom:13px}
header a{color:var(--gold);font-weight:700;min-height:44px;display:inline-flex;align-items:center}
h1{font-size:clamp(2rem,8vw,3.2rem);line-height:1.1;letter-spacing:-.045em;margin:22px 0 15px}
.entry{background:var(--panel);border:1px solid var(--edge);border-radius:18px;padding:16px;display:grid;gap:11px}
.entry label{font-weight:750;font-size:.89rem;display:block}
.entry input{display:block;width:100%;min-width:0;margin-top:6px;padding:13px 14px;min-height:49px;background:#090909;color:#fff;border:1px solid #63543a;border-radius:11px;font:inherit}
.entry input::placeholder{color:#9d978a}
.entry button{min-height:49px;border:0;border-radius:12px;background:var(--gold);color:#1a1308;font:850 1rem system-ui;cursor:pointer}
.entry input:focus-visible,.entry button:focus-visible,a:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
.quick{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:14px}
.quick a{display:grid;place-items:center;min-height:53px;border:1px solid var(--edge);border-radius:12px;background:var(--panel);font-weight:750;font-size:.9rem;text-align:center}
.quick a:hover,.action:hover{border-color:var(--gold)}
h2{font-size:1rem;margin:25px 0 12px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
.action{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:14px;border:1px solid var(--edge);border-radius:15px;background:var(--panel);font-weight:750}
.action .arrow{color:var(--gold);font-size:1.2rem}
.note{font-size:.8rem;color:var(--muted);margin:17px 0 0}
@media(max-width:340px){.quick{grid-template-columns:1fr}.grid{grid-template-columns:1fr}}
</style></head><body><main>
<header><a href="/transport">← Global Transport</a><span style="color:var(--gold);font-size:.8rem;font-weight:800">OAP RIDE</span></header>
<h1>Where to?</h1>
<form class="entry" id="oap-ride-draft" action="/movement/workspace#book-title" method="get">
<label for="ride-pickup">Pickup<input id="ride-pickup" type="text" placeholder="Postcode or place" maxlength="120" autocomplete="street-address" required></label>
<label for="ride-destination">Destination<input id="ride-destination" type="text" placeholder="Where are you going?" maxlength="120" autocomplete="street-address" required></label>
<button type="submit">Continue to journey request</button>
</form>
<nav class="quick" aria-label="OAP Rides navigation">
<a href="/transport/ride/rider">Rider</a><a href="/transport/ride/driver">Driver</a><a href="/transport/my">My Transport</a>
</nav>
<h2>Journey tools</h2>
<section class="grid" aria-label="Ride actions">
<a class="action" href="/transport/ride/current">Current journey<span class="arrow" aria-hidden="true">›</span></a>
<a class="action" href="/movement/workspace#bookings-title">My journeys<span class="arrow" aria-hidden="true">›</span></a>
<a class="action" href="/oap-map">Map<span class="arrow" aria-hidden="true">›</span></a>
<a class="action" href="/pay/bank">SIKA<span class="arrow" aria-hidden="true">›</span></a>
<a class="action" href="/transport/ride/guardian/status">Guardian<span class="arrow" aria-hidden="true">›</span></a>
<a class="action" href="/eats">Eats<span class="arrow" aria-hidden="true">›</span></a>
</section>
<p class="note">Private journey operations require sign-in and verified providers.</p>
</main>
<script>
document.getElementById("oap-ride-draft").addEventListener("submit",function(event){
  const pickup=document.getElementById("ride-pickup").value.trim();
  const destination=document.getElementById("ride-destination").value.trim();
  if (!pickup || !destination) return;
  try {
    sessionStorage.setItem("oap_transport_ride_draft",JSON.stringify({
      pickup:pickup.slice(0,120),destination:destination.slice(0,120),
      created:Date.now()
    }));
  } catch (_) { /* Existing Movement form remains available. */ }
});
</script></body></html>"""


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
