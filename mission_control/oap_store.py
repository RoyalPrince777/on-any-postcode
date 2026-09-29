"""First-party OAP Store public catalogue and install surface.

The first installable release is the existing OAP World / OAP OS public PWA.
Native Android packages remain separately gated and are never inferred from PWA
installability.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import oap_store_registry

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
    "install_url": "/linkup?source=oap-store&install=1",
    "offline_url": "/offline",
    "native_apk": False,
    "native_package_available": False,
    "physical_device_certified": False,
    "human_authority_final": True,
}


def catalogue() -> tuple[dict[str, object], ...]:
    return (dict(OAP_WORLD), dict(LINK_UP))


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
