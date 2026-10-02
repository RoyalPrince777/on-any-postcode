"""OAP Ride dashboard button surfaces."""
from __future__ import annotations
from flask import Blueprint, make_response, render_template_string

bp = Blueprint("oap_ride_dashboards", __name__)

RIDER = ("Request Journey","Plan Journey","My Journeys","Share Journey","Guardian","The Link","OAP Pay","Help")
DRIVER = ("Go Active","Go Quiet","Incoming Journey","Accept Journey","Decline","My Drive","Earnings","Journey History","Guardian","The Link")
MY = ("Rider","Driver","My Journeys","My Drive","Payments","Guardian","The Link","Settings")

PAGE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{margin:0;background:#080808;color:#fff;font-family:system-ui}main{max-width:720px;margin:auto;padding:18px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.btn{padding:20px 12px;border:1px solid #333;border-radius:18px;background:#121212;font-weight:800;text-align:center}
h1{margin:0 0 16px}.back{display:block;margin-bottom:12px;color:#aaa;text-decoration:none}
</style></head><body><main><a class="back" href="/transport">← Transport</a><h1>{{ title }}</h1><div class="grid">{% for label in buttons %}<div class="btn">{{ label }}</div>{% endfor %}</div></main></body></html>"""

def _page(title, buttons):
    response = make_response(render_template_string(PAGE, title=title, buttons=buttons))
    response.headers["Cache-Control"] = "no-store, private"
    return response

@bp.get("/transport/ride/rider")
def rider_dashboard():
    return _page("Rider", RIDER)

@bp.get("/transport/ride/driver")
def driver_dashboard():
    return _page("Driver", DRIVER)

@bp.get("/transport/my")
def my_transport_dashboard():
    return _page("My Transport", MY)
