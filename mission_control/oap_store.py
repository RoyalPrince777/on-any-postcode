"""First-party OAP Store public catalogue and install surface.

The first installable release is the existing OAP World / OAP OS public PWA.
Native Android packages remain separately gated and are never inferred from PWA
installability.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

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


def catalogue() -> tuple[dict[str, object], ...]:
    return (dict(OAP_WORLD),)


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


@bp.get("/oap-store/apps/oap.world")
def oap_world_store_entry():
    response = make_response(jsonify(dict(OAP_WORLD)), 200)
    response.headers["Cache-Control"] = "no-store"
    return response
