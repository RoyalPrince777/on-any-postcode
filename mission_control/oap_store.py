"""First-party OAP Store public catalogue and install surface.

The first installable release is the existing OAP World / OAP OS public PWA.
Native Android packages remain separately gated and are never inferred from PWA
installability.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import oap_store_registry, products

bp = Blueprint("oap_store", __name__, template_folder="templates")

OAP_WORLD = {
    "app_id": "oap.world",
    "name": "OAP World",
    "publisher": "ON ANY POSTCODE LTD",
    "distribution": "OAP Store",
    "first_party": True,
    "description": "The ON ANY POSTCODE public world and installable OAP OS shell.",
    "release_state": "install_ready",
    "install_enabled": True,
    "install_mode": "PWA",
    "manifest_url": "/manifest.webmanifest",
    "service_worker_url": "/service-worker.js",
    "start_url": "/",
    "open_url": "/",
    "category": "World",
    "install_url": "/?source=oap-store&install=1",
    "offline_url": "/offline",
    "native_apk": False,
    "native_package_available": False,
    "physical_device_certified": False,
    "human_authority_final": True,
}

LINK_UP = {
    "app_id": "oap.linkup",
    "name": "Link Up",
    "publisher": "ON ANY POSTCODE LTD",
    "distribution": "OAP Store",
    "first_party": True,
    "description": "Private OAP communication with Link Message, Link Call, Voice, Incoming, presence and sharing controls.",
    "release_state": "install_ready",
    "install_enabled": True,
    "install_mode": "PWA",
    "manifest_url": "/linkup/manifest.webmanifest",
    "service_worker_url": "/service-worker.js",
    "start_url": "/linkup?source=oap-store",
    "open_url": "/linkup",
    "category": "Communication",
    "install_url": "/linkup?source=oap-store&install=1",
    "offline_url": "/offline",
    "native_apk": False,
    "native_package_available": False,
    "physical_device_certified": False,
    "human_authority_final": True,
}



OAP_TRANSPORT = {
    "app_id": "oap.transport",
    "name": "OAP Transport",
    "publisher": "ON ANY POSTCODE LTD",
    "distribution": "OAP Store",
    "first_party": True,
    "description": "Rider, Driver and Travel in one installable OAP Transport app.",
    "release_state": "install_ready",
    "install_enabled": True,
    "install_mode": "PWA",
    "manifest_url": "/transport/manifest.webmanifest",
    "service_worker_url": "/service-worker.js",
    "start_url": "/transport?source=oap-store",
    "open_url": "/transport",
    "category": "Travel",
    "install_url": "/transport?source=oap-store&install=1",
    "offline_url": "/offline",
    "native_apk": False,
    "native_package_available": False,
    "physical_device_certified": False,
    "bundles": ("Rider", "Driver", "Travel"),
    "human_authority_final": True,
}


OAP_MUSIC = {
    "app_id": "oap.music",
    "name": "OAP Music",
    "publisher": "ON ANY POSTCODE LTD",
    "distribution": "OAP Store",
    "first_party": True,
    "description": "First-party music, Player, Radio and creator discovery.",
    "release_state": "install_ready",
    "install_enabled": True,
    "install_mode": "PWA",
    "manifest_url": "/music/manifest.webmanifest",
    "service_worker_url": "/service-worker.js",
    "start_url": "/music",
    "open_url": "/music",
    "category": "Media",
    "install_url": "/music",
    "offline_url": "/offline",
    "native_apk": False,
    "native_package_available": False,
    "physical_device_certified": False,
    "human_authority_final": True,
}


def _catalogue_placeholder(*, app_id: str, name: str, open_url: str, description: str, category: str) -> dict[str, object]:
    return {
        "app_id": app_id,
        "name": name,
        "publisher": "ON ANY POSTCODE LTD",
        "distribution": "OAP Store",
        "first_party": True,
        "description": description,
        "release_state": "open_ready",
        "install_enabled": False,
        "install_mode": "Web",
        "manifest_url": None,
        "service_worker_url": "/service-worker.js",
        "start_url": open_url,
        "open_url": open_url,
        "category": category,
        "install_url": None,
        "offline_url": "/offline",
        "native_apk": False,
        "native_package_available": False,
        "physical_device_certified": False,
        "human_authority_final": True,
    }



def _planned_app(*, app_id: str, name: str, description: str, category: str, internal_intelligence: tuple[str, ...] = ()) -> dict[str, object]:
    return {
        "app_id": app_id,
        "name": name,
        "publisher": "ON ANY POSTCODE LTD",
        "distribution": "OAP Store",
        "first_party": True,
        "description": description,
        "release_state": "planned",
        "install_enabled": False,
        "install_mode": "Planned",
        "manifest_url": None,
        "service_worker_url": None,
        "start_url": None,
        "open_url": None,
        "category": category,
        "install_url": None,
        "offline_url": None,
        "native_apk": False,
        "native_package_available": False,
        "physical_device_certified": False,
        "human_authority_final": True,
        "internal_intelligence": internal_intelligence,
    }


PLANNED_STORE_APPS = (
    _planned_app(
        app_id="oap.mail",
        name="OAP Mail",
        description="First-party OAP mail and account communications. Current active public route is not yet proven.",
        category="Communication",
    ),
    _planned_app(
        app_id="oap.vpn",
        name="OAP VPN",
        description="First-party privacy network layer. No VPN tunnel, DNS leak protection or device certification is claimed until runtime proof exists.",
        category="Privacy",
    ),
    _planned_app(
        app_id="oap.cyber-security",
        name="OAP Cyber Security",
        description="First-party security operations, threat detection, access control, incident response, recovery and audit.",
        category="Security",
        internal_intelligence=("Neo", "Trinity", "Morpheus", "Oracle", "Architect", "Keymaker", "Seraph", "Agent Smith"),
    ),
)


PUBLIC_STORE_APPS = (
    _catalogue_placeholder(app_id="oap.search", name="OAP Search", open_url="/search", description="First-party search across OAP public apps, places, Market, Library and media catalogue entries.", category="Discovery"),
    _catalogue_placeholder(app_id="oap.spot", name="The Spot", open_url="/the-spot", description="Public community activity, Pulse, Signal and Empire life.", category="Social"),
    _catalogue_placeholder(app_id="oap.link", name="The Link", open_url="/the-link", description="People, opportunities and the bridge into private Link Up.", category="Communication"),
    _catalogue_placeholder(app_id="oap.arena", name="OAP Arena", open_url="/arena", description="First-party games, challenges and Global Arena progression.", category="Games"),
    _catalogue_placeholder(app_id="oap.library", name="OAP Library", open_url="/library", description="One World. One Library. Unlimited Learning.", category="Learning"),
    _catalogue_placeholder(app_id="oap.place", name="On Any Place", open_url="/on-any-place", description="Maps, place search, routes, weather and movement intelligence.", category="Places"),
    _catalogue_placeholder(app_id="oap.movement", name="Movement", open_url="/movement", description="Travel, movement, route context and delivery awareness.", category="Movement"),
    _catalogue_placeholder(app_id="oap.booking", name="OAP Direct", open_url="/booking", description="First-party supplier and booking journey.", category="Travel"),
)

_PUBLIC_SPOT_CATEGORIES = {
    "pulse": "Social",
    "signal": "Social",
    "news": "News",
    "nature": "Nature",
    "postcode-rooms": "World",
    "events": "Events",
    "arena": "Games",
    "carnival-intelligence": "Events",
    "discovery": "Places",
    "businesses": "Business",
    "creators": "Creators",
    "community-power": "Community",
    "support": "Support",
    "infrastructure": "Places",
    "market": "Market",
    "music": "Media",
    "player": "Media",
    "radio": "Media",
    "distribution": "Creators",
    "sika": "Value",
    "safety": "Safety",
    "identity": "Identity",
    "tv-media": "Media",
    "membership": "Membership",
    "languages": "Learning",
}


def _spot_store_apps() -> tuple[dict[str, object], ...]:
    skip = {"arena", "music"}
    result = []
    for item in products.PUBLIC_SPOT_CAPABILITIES:
        source_id = str(item["source_id"])
        if source_id in skip:
            continue
        slug = str(item["slug"])
        result.append(
            _catalogue_placeholder(
                app_id=f"oap.{source_id}",
                name=str(item["name"]),
                open_url=f"/the-spot/{slug}",
                description=str(item["purpose"]),
                category=_PUBLIC_SPOT_CATEGORIES.get(source_id, "OAP"),
            )
        )
    return tuple(result)


def catalogue() -> tuple[dict[str, object], ...]:
    items = (
        dict(OAP_WORLD),
        dict(LINK_UP),
        dict(OAP_MUSIC),
        dict(OAP_TRANSPORT),
        *PUBLIC_STORE_APPS,
        *PLANNED_STORE_APPS,
        *_spot_store_apps(),
    )
    unique: dict[str, dict[str, object]] = {}
    for item in items:
        unique.setdefault(str(item["app_id"]), item)
    return tuple(unique.values())


def native_distribution_status() -> dict[str, object]:
    return oap_store_registry.native_install_status()


@bp.get("/store")
def store_home():
    response = make_response(render_template("oap_store.html", apps=catalogue()))
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/oap-store/apps")
def store_catalogue():
    response = make_response(jsonify(apps=catalogue()), 200)
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/oap-store/native/status")
def native_store_status():
    response = make_response(jsonify(native_distribution_status()), 200)
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/oap-store/apps/oap.world")
def oap_world_store_entry():
    response = make_response(jsonify(dict(OAP_WORLD)), 200)
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/linkup/manifest.webmanifest")
def link_up_manifest():
    payload = {
        "name": "Link Up · ON ANY POSTCODE",
        "short_name": "Link Up",
        "description": "Private first-party communication inside ON ANY POSTCODE.",
        "id": "/linkup",
        "start_url": "/linkup?source=oap-store",
        "scope": "/linkup",
        "display": "standalone",
        "display_override": ["standalone", "minimal-ui"],
        "orientation": "any",
        "background_color": "#050807",
        "theme_color": "#050807",
        "prefer_related_applications": False,
        "launch_handler": {"client_mode": "navigate-existing"},
        "categories": ["social", "communication"],
        "icons": [
            {
                "src": "/assets/oap-os-icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/assets/oap-os-icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ],
    }
    response = make_response(jsonify(payload), 200)
    response.headers["Content-Type"] = "application/manifest+json"
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@bp.get("/oap-store/apps/oap.linkup")
def link_up_store_entry():
    response = make_response(jsonify(dict(LINK_UP)), 200)
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/transport/manifest.webmanifest")
def transport_manifest():
    payload = {
        "name": "OAP Transport · ON ANY POSTCODE",
        "short_name": "OAP Transport",
        "description": "Rider, Driver and Travel inside ON ANY POSTCODE.",
        "id": "/transport",
        "start_url": "/transport?source=oap-store",
        "scope": "/",
        "display": "standalone",
        "display_override": ["standalone", "minimal-ui"],
        "orientation": "any",
        "background_color": "#050807",
        "theme_color": "#050807",
        "prefer_related_applications": False,
        "launch_handler": {"client_mode": "navigate-existing"},
        "categories": ["travel", "navigation", "utilities"],
        "icons": [
            {
                "src": "/assets/oap-os-icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/assets/oap-os-icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ],
        "shortcuts": [
            {
                "name": "Rider",
                "short_name": "Rider",
                "url": "/transport/ride/rider?source=oap-transport",
                "icons": [{"src": "/assets/oap-os-icon-192.png", "sizes": "192x192"}],
            },
            {
                "name": "Driver",
                "short_name": "Driver",
                "url": "/transport/ride/driver?source=oap-transport",
                "icons": [{"src": "/assets/oap-os-icon-192.png", "sizes": "192x192"}],
            },
            {
                "name": "Travel",
                "short_name": "Travel",
                "url": "/travel?source=oap-transport",
                "icons": [{"src": "/assets/oap-os-icon-192.png", "sizes": "192x192"}],
            },
        ],
    }
    response = make_response(jsonify(payload), 200)
    response.headers["Content-Type"] = "application/manifest+json"
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@bp.get("/oap-store/apps/oap.transport")
def transport_store_entry():
    response = make_response(jsonify(dict(OAP_TRANSPORT)), 200)
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/oap-store/apps/<app_id>")
def generic_store_entry(app_id: str):
    for item in catalogue():
        if item["app_id"] == app_id:
            response = make_response(jsonify(dict(item)), 200)
            response.headers["Cache-Control"] = "no-store"
            return response
    response = make_response(jsonify(error="app_not_found"), 404)
    response.headers["Cache-Control"] = "no-store"
    return response



def _search_public_apps(query: str) -> tuple[dict[str, object], ...]:
    needle = " ".join(str(query or "").casefold().split())
    if not needle:
        return ()
    ranked = []
    for app in catalogue():
        if not app.get("open_url"):
            continue
        haystack = " ".join(
            str(app.get(field) or "")
            for field in ("name", "description", "category", "app_id")
        ).casefold()
        if needle not in haystack:
            continue
        name = str(app.get("name") or "").casefold()
        score = 0 if name == needle else 1 if name.startswith(needle) else 2
        ranked.append((score, str(app.get("name") or ""), dict(app)))
    ranked.sort(key=lambda item: (item[0], item[1].casefold()))
    return tuple(item[2] for item in ranked)


@bp.get("/search")
def oap_search():
    query = str(request.args.get("q") or "").strip()[:120]
    results = _search_public_apps(query)
    response = make_response(
        render_template("oap_search.html", query=query, results=results),
        200,
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noarchive"
    return response
