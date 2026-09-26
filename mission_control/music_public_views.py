"""Public OAP Music front door and truth-mode open catalogue."""
from flask import Blueprint, jsonify, make_response, render_template

from . import entertainment_catalogue, open_music_intake

bp = Blueprint("oap_music_public", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
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
            )
        )
    )


@bp.get("/music/api/open-sources")
def music_open_sources():
    """Public discovery directory only; no licence or playback claim."""
    return _no_store(make_response(jsonify(open_music_intake.source_directory())))


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
                    "open_source_directory_ready": True,
                    "open_source_count": len(sources["entries"]),
                    "public_catalogue_track_count": 0,
                    "public_playback_enabled": False,
                    "public_radio_streaming_enabled": False,
                    "rights_verified_by_software": False,
                    "human_authority_final": True,
                }
            )
        )
    )
