"""OAP Ride dashboard button surfaces wired to existing Movement functions."""
from __future__ import annotations
from flask import Blueprint, make_response, render_template_string

bp = Blueprint("oap_ride_dashboards", __name__)

RIDER = (
    ("Request Journey", "/movement/workspace#book-title"),
    ("Current Journey", "/transport/ride/current"),
    ("My Journeys", "/movement/workspace#bookings-title"),
    ("Find Match", "/movement/workspace#bookings-title"),
    ("My Matches", "/movement/workspace#member-matches-title"),
    ("OAP Pay", "/pay"),
    ("Guardian", "/transport/ride/runtime"),
)

DRIVER = (
    ("Go Active / Quiet", "/movement/workspace#work-title"),
    ("Current Journey", "/transport/ride/current"),
    ("Incoming Journey", "/movement/workspace#assigned-title"),
    ("Accept Journey", "/movement/workspace#assigned-title"),
    ("My Drive", "/movement/workspace#work-title"),
    ("Earnings", "/pay"),
    ("Journey History", "/movement/workspace#bookings-title"),
    ("Guardian", "/transport/ride/runtime"),
)

MY = (
    ("Rider", "/transport/ride/rider"),
    ("Driver", "/transport/ride/driver"),
    ("Current Journey", "/transport/ride/current"),
    ("My Journeys", "/movement/workspace#bookings-title"),
    ("My Drive", "/movement/workspace#work-title"),
    ("Payments", "/pay"),
    ("Guardian", "/transport/ride/runtime"),
)

PAGE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{margin:0;background:#080808;color:#fff;font-family:system-ui}main{max-width:720px;margin:auto;padding:18px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.btn{padding:20px 12px;border:1px solid #333;border-radius:18px;background:#121212;color:#fff;font-weight:800;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;min-height:72px}
h1{margin:0 0 16px}.back{display:block;margin-bottom:12px;color:#aaa;text-decoration:none}
</style></head><body><main><a class="back" href="/transport">← Transport</a><h1>{{ title }}</h1><div class="grid">{% for label, href in buttons %}<a class="btn" href="{{ href }}">{{ label }}</a>{% endfor %}</div></main></body></html>"""

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
