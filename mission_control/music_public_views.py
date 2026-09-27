"""Public OAP Music front door and truth-mode open catalogue."""
from flask import Blueprint, jsonify, make_response, render_template, request

from . import entertainment_catalogue, music_public_catalogue, open_music_intake

bp = Blueprint("oap_music_public", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/music/manifest.webmanifest")
def music_manifest():
    """Dedicated first-party install identity for the public OAP Music app."""

    response = make_response(
        jsonify(
            {
                "name": "OAP Music",
                "short_name": "OAP Music",
                "description": "First-party OAP Music player, creator and radio surface.",
                "id": "/music",
                "start_url": "/music?source=oap-music-app",
                "scope": "/music",
                "display": "standalone",
                "display_override": ["standalone", "minimal-ui"],
                "orientation": "any",
                "background_color": "#080808",
                "theme_color": "#080808",
                "prefer_related_applications": False,
                "categories": ["music", "entertainment"],
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
                    {"name": "Player", "short_name": "Player", "url": "/music#player"},
                    {"name": "Radio", "short_name": "Radio", "url": "/music#radio"},
                    {"name": "Creator Studio", "short_name": "Create", "url": "/music#creators"},
                ],
            }
        )
    )
    response.headers["Content-Type"] = "application/manifest+json"
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/music")
def music_home():
    sources = open_music_intake.source_directory()
    return _no_store(
        make_response(
            render_template(
                "oap_music.html",
                player=entertainment_catalogue.universal_player_contract(),
                sources=sources["entries"],
                listener=music_public_catalogue.listener_contract(),
            )
        )
    )


@bp.get("/music/api/open-sources")
def music_open_sources():
    """Public discovery directory only; no licence or playback claim."""
    return _no_store(make_response(jsonify(open_music_intake.source_directory())))



@bp.get("/music/api/catalogue")
def music_catalogue():
    """Search canonical first-party OAP Music metadata only."""
    try:
        return _no_store(
            make_response(
                jsonify(
                    music_public_catalogue.catalogue(
                        query=request.args.get("q", ""),
                        limit=50,
                    )
                )
            )
        )
    except (ValueError, RuntimeError):
        return _no_store(
            make_response(
                jsonify(
                    {
                        "catalogue": "OAP Music",
                        "ownership": "first_party",
                        "items": [],
                        "item_count": 0,
                        "playback_enabled": False,
                        "external_catalogue_dependency": False,
                        "temporarily_unavailable": True,
                    }
                ),
                503,
            )
        )


@bp.get("/music/api/status")
def music_public_status():
    """Public truth-mode contract for the deployed Music front door."""
    sources = open_music_intake.source_directory()
    return _no_store(
        make_response(
            jsonify(
                {
                    "organ": "OAP Music",
                    "front_door_ready": True,
                    "install_app_contract_ready": True,
                    "install_manifest_url": "/music/manifest.webmanifest",
                    "install_mode": "PWA",
                    "signed_android_package_verified": False,
                    "device_install_verified": False,
                    "open_source_directory_ready": True,
                    "open_source_count": len(sources["entries"]),
                    "listener_contract": music_public_catalogue.listener_contract(),
                    "public_catalogue_track_count": 0,
                    "public_playback_enabled": False,
                    "public_radio_streaming_enabled": False,
                    "rights_verified_by_software": False,
                    "human_authority_final": True,
                }
            )
        )
    )
