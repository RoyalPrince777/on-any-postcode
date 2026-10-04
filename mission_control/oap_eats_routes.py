"""Public OAP Eats software surface."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template_string

from . import oap_eats

bp = Blueprint("oap_eats", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Eats</title></head>
<body><main>
<h1>OAP Eats</h1>
<p>Find it. Order it. Bring it.</p>
<nav>
<a href="/eats/status">Status</a>
<a href="/market">OAP Market</a>
<a href="/transport/ride">OAP Rides</a>
</nav>
<p>One World → one shared map → one identity → one movement engine → one SIKA transaction spine.</p>
<small>Software surface only. Live merchant, payment and courier execution stays evidence-gated.</small>
</main></body></html>"""


@bp.get("/eats")
def eats_home():
    return _no_store(make_response(render_template_string(_PAGE), 200))


@bp.get("/eats/status")
def eats_status():
    return _no_store(make_response(jsonify(oap_eats.status()), 200))


@bp.get("/eats/order-states")
def eats_order_states():
    return _no_store(make_response(jsonify({
        "states": [state.value for state in oap_eats.EatsOrderState],
        "human_authority_final": True,
    }), 200))
