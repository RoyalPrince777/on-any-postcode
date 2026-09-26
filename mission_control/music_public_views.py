"""Public OAP Music front door. Public playback remains proof-gated."""
from flask import Blueprint, make_response, render_template

from . import entertainment_catalogue

bp = Blueprint("oap_music_public", __name__)


@bp.get("/music")
def music_home():
    response = make_response(
        render_template(
            "oap_music.html",
            player=entertainment_catalogue.universal_player_contract(),
        )
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
