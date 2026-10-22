# ruff: noqa: I001
"""OAP Ride dashboard button surfaces wired to existing Movement functions."""
from __future__ import annotations
from flask import Blueprint, make_response, render_template_string, request
from . import web_security

bp = Blueprint("oap_ride_dashboards", __name__)

RIDER = (
    ("Request Journey", "/transport/ride/rider"),
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
.ride-form{display:grid;gap:12px;margin-top:16px}.ride-form label{font-weight:700}.ride-form input{width:100%;padding:15px;border-radius:12px;border:1px solid var(--line);background:#10161b;color:white;font:inherit}.ride-form button{border:0;cursor:pointer;font:inherit}.ride-form input:focus-visible,.ride-form button:focus-visible{outline:3px solid var(--gold);outline-offset:3px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.btn{padding:18px 12px;border:1px solid var(--line);border-radius:18px;background:var(--panel);color:#fff;font-weight:750;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;min-height:76px}
.btn:focus-visible,.primary:focus-visible,.back:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
.note{color:var(--muted);font-size:.9rem;line-height:1.5;margin-top:22px}
</style></head><body><main>
<header class="top"><a class="back" href="/transport">← Transport</a><a class="back" href="/world">OAP World</a></header>
{% if title == "Rider" %}
<section class="hero"><div class="eyebrow">ON ANY POSTCODE · RIDE</div><h1>Where to?</h1>
<p class="lead">Enter pickup and destination here, then review and submit your request on the secure OAP Ride booking screen.</p>
<form class="ride-form" action="/transport/ride/book" method="get" aria-label="Start a ride booking"><input type="hidden" name="service" value="ride"><label for="ride-pickup">Pickup postcode or place</label><input id="ride-pickup" name="from" maxlength="120" autocomplete="street-address" required><label for="ride-destination">Destination postcode or place</label><input id="ride-destination" name="to" maxlength="120" autocomplete="off" required><button class="primary" type="submit">Continue to secure booking →</button></form></section>
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


@bp.get("/transport/ride/book")
@web_security.login_required()
def ride_booking_page():
    """Authenticated Ride booking entry; existing Movement API owns writes."""
    pickup = request.args.get("from", "")[:120]
    destination = request.args.get("to", "")[:120]
    response = make_response(render_template_string(RIDE_BOOK_PAGE, pickup=pickup, destination=destination, csrf=web_security.csrf_token()))
    response.headers["Cache-Control"] = "no-store, private"
    return response

RIDE_BOOK_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Book Ride · OAP</title></head><body><main><a href="/transport/ride/rider">← Rider</a><h1>Request a Ride</h1><p>Requests do not dispatch a driver or charge a payment.</p><form id="ride-book"><label for="pickup">Pickup</label><input id="pickup" maxlength="120" required value="{{ pickup }}"><label for="destination">Destination</label><input id="destination" maxlength="120" required value="{{ destination }}"><button type="submit">Request journey</button></form><p id="ride-result" role="status" aria-live="polite"></p><a href="/movement/workspace#bookings-title">My bookings and matching</a></main><script>const csrf={{ csrf|tojson }};const form=document.getElementById("ride-book");const result=document.getElementById("ride-result");let pending=false;let requestKey=null;form.addEventListener("submit",async event=>{event.preventDefault();if(pending)return;pending=true;if(!requestKey)requestKey="ride-"+crypto.randomUUID();const button=form.querySelector("button");button.disabled=true;result.textContent="Submitting request…";try{const response=await fetch("/movement/bookings",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify({service_type:"ride",pickup_query:document.getElementById("pickup").value.trim(),destination_query:document.getElementById("destination").value.trim(),scheduled_for:null,idempotency_key:requestKey})});const data=await response.json().catch(()=>({}));if(!response.ok)throw new Error(data.error?.message||"Booking unavailable");if(!data.booking?.booking_id)throw new Error("Booking confirmation is incomplete. Check My bookings before retrying.");result.textContent="Journey requested. Booking reference: "+data.booking.booking_id+". Status: "+(data.booking.state||"REQUESTED")+". This is not a driver dispatch.";form.reset();requestKey=null;}catch(error){result.textContent=error.message||"Request failed. Please retry.";}finally{pending=false;button.disabled=false;}});</script></body></html>"""
