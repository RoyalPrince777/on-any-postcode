# ruff: noqa: I001
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
    ("Guardian", "/transport/ride/guardian/status"),
)

DRIVER = (
    ("Go Active / Quiet", "/movement/workspace#work-title"),
    ("Current Journey", "/transport/ride/current"),
    ("Incoming Journey", "/movement/workspace#assigned-title"),
    ("Accept Journey", "/movement/workspace#assigned-title"),
    ("My Drive", "/movement/workspace#work-title"),
    ("Earnings", "/transport/ride/driver/earnings"),
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

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{{ title }} · OAP Ride</title>
<style>
:root{color-scheme:dark;--bg:#090b0d;--panel:#151b20;--line:#303a42;--gold:#e9c66a;--muted:#b8c3ca}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:white;font-family:system-ui,sans-serif}
main{max-width:720px;margin:auto;padding:18px 16px 80px}.top{display:flex;align-items:center;justify-content:space-between;gap:12px}
a{color:inherit}.back{text-decoration:none;color:var(--muted)}h1{font-size:clamp(2rem,8vw,3.2rem);margin:22px 0 8px}
.lead{color:var(--muted);line-height:1.5}.hero{padding:22px;border:1px solid #68552b;border-radius:24px;background:linear-gradient(145deg,#262017,#13191d);margin:18px 0}
.eyebrow{color:var(--gold);font-weight:800;letter-spacing:.08em;font-size:.8rem}.primary{display:block;background:var(--gold);color:#17140b;text-decoration:none;padding:17px;border-radius:15px;font-weight:900;text-align:center;margin-top:18px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.btn{padding:18px 12px;border:1px solid var(--line);border-radius:18px;background:var(--panel);color:#fff;font-weight:750;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;min-height:76px}
.btn:focus-visible,.primary:focus-visible,.back:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
.note{color:var(--muted);font-size:.9rem;line-height:1.5;margin-top:22px}
</style></head><body><main>
<header class="top"><a class="back" href="/transport">← Transport</a><a class="back" href="/world">OAP World</a></header>
{% if title == "Rider" %}
<section class="hero"><div class="eyebrow">ON ANY POSTCODE · RIDE</div><h1>Where to?</h1>
<p class="lead">Choose your pickup and destination in the existing OAP Movement booking workspace.</p>
<a class="primary" href="/movement/workspace#book-title">Request a journey →</a></section>
<p class="lead">Manage your journey, matching and safety below.</p>
{% elif title == "Driver" %}
<section class="hero"><div class="eyebrow">OAP RIDE · DRIVER</div><h1>Ready to drive?</h1>
<p class="lead">Manage your certified availability and incoming journey proposals.</p>
<a class="primary" href="/movement/workspace#work-title">Manage availability →</a></section>
{% else %}
<h1>{{ title }}</h1><p class="lead">Your transport routes and journey tools.</p>
{% endif %}
<nav class="grid" aria-label="{{ title }} actions">{% for label, href in buttons %}<a class="btn" href="{{ href }}">{{ label }}</a>{% endfor %}</nav>
<p class="note">Booking requests and match proposals do not constitute physical dispatch. Live rides and payments remain subject to operational approval.</p>
</main></body></html>"""

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
