"""Public OAP Music first-party listener front door."""
from flask import Blueprint, jsonify, make_response, render_template, request

from . import entertainment_catalogue, music_public_catalogue

bp = Blueprint("oap_music_public", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/music")
def music_home():
    return _no_store(
        make_response(
            render_template(
                "oap_music.html",
                player=entertainment_catalogue.universal_player_contract(),
                listener=music_public_catalogue.listener_contract(),
            )
        )
    )


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
    return _no_store(
        make_response(
            jsonify(
                {
                    "organ": "OAP Music",
                    "front_door_ready": True,
                    "first_party_catalogue_ready": True,
                    "first_party_discovery_ready": True,
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
