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
    ("Payments", "/pay/bank"),
    ("Guardian", "/transport/guardian"),
    ("Book Delivery", "/movement/workspace?service=delivery#book-title"),
    ("Track Food Order", "/eats"),
    ("Travel & Tickets", "/travel"),
    ("Public Transport", "/transport"),
)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#090909">
{% if manifest_url %}<link rel="manifest" href="{{ manifest_url }}">{% endif %}
<title>{{ title }} · ON ANY POSTCODE</title>
<style>
:root{color-scheme:dark;--gold:#efcf73;--bg:#090909;--panel:#171717;--line:#39352a;--muted:#b9b9b9}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:#fff;font:16px/1.45 system-ui,-apple-system,sans-serif}
a{color:inherit;text-decoration:none}
main{max-width:850px;margin:auto;padding:calc(18px + env(safe-area-inset-top)) 16px calc(40px + env(safe-area-inset-bottom))}
nav{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
nav a{color:var(--gold);display:inline-flex;align-items:center;min-height:44px;font-weight:700}
.eyebrow{margin:24px 0 5px;color:var(--gold);font-size:.78rem;font-weight:900;letter-spacing:.08em}
h1{font-size:clamp(2rem,7vw,3rem);margin:0 0 8px;line-height:1.08}
.intro{margin:0 0 17px;color:var(--muted);max-width:650px}
.role-switch{display:flex;gap:9px;margin:16px 0 20px}
.role-switch a{flex:1;text-align:center;padding:13px 10px;min-height:48px;border:1px solid var(--line);border-radius:12px;background:var(--panel);font-weight:800}
.role-switch a[aria-current="page"]{background:var(--gold);border-color:var(--gold);color:#16120b}
.install-row{margin:12px 0 20px;display:flex;align-items:center;gap:11px;flex-wrap:wrap}
.install-row button{font:inherit;font-weight:850;padding:12px 17px;min-height:48px;border:0;border-radius:12px;background:var(--gold);color:#17130a;cursor:pointer}
.install-row button[hidden]{display:none}.install-row button:disabled{opacity:.65}
.install-row [role=status]{color:var(--muted);font-size:.85rem;line-height:1.45}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}
.btn{min-height:94px;min-width:0;padding:16px;border:1px solid var(--line);border-radius:16px;background:var(--panel);color:#f8f8f8;font-weight:750;display:flex;align-items:center;justify-content:flex-start;overflow-wrap:anywhere}
.btn:first-child{border-color:#b99b44;background:#231e13;color:#f9dd8a}
.note{margin:20px 0 0;padding:13px 15px;border-left:3px solid var(--gold);background:#1b1913;color:#d0cbc0;font-size:.85rem}
a:focus-visible,button:focus-visible{outline:3px solid #fff;outline-offset:3px}
@media(min-width:720px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:320px){.grid{grid-template-columns:1fr}.btn{min-height:64px}}
</style></head><body><main>
<nav aria-label="Transport navigation"><a href="/transport">← Global Transport</a><a href="/transport/my">My Transport</a></nav>
<p class="eyebrow">ON ANY POSTCODE · GLOBAL TRANSPORT</p>
<h1>{{ title }}</h1>
{% if title == "My Transport" %}
<p class="intro">Your customer journeys, delivery bookings and payment links in one place.</p>
{% else %}
<p class="intro">{{ "Plan journeys, request a ride and follow its progress." if title == "Rider" else "Manage availability, incoming requests and journey history." }}</p>
<div class="role-switch" aria-label="Choose transport role">
<a href="/transport/ride/rider" {% if title == "Rider" %}aria-current="page"{% endif %}>Rider</a>
<a href="/transport/ride/driver" {% if title == "Driver" %}aria-current="page"{% endif %}>Driver</a>
</div>
<div class="install-row">
<button type="button" data-oap-install hidden>{{ install_label }}</button>
<span data-oap-install-status role="status" aria-live="polite"></span>
<span data-oap-install-platform hidden></span>
</div>
{% endif %}
<section class="grid" aria-label="{{ title }} actions">
{% for label, href in buttons %}<a class="btn" href="{{ href }}">{{ label }}</a>{% endfor %}
</section>
<p class="note">{% if title == "Driver" %}Driver jobs and earnings require the appropriate signed-in account and approvals. {% else %}Personal bookings and account actions require sign-in. {% endif %}Live dispatch and payment remain evidence-gated; installing does not grant operating permission.</p>
</main>
{% if manifest_url %}<script src="/assets/oap-os.js" defer></script>{% endif %}
</body></html>"""


def _page(title, buttons):
    manifests = {
        "Rider": "/transport/ride/rider/manifest.webmanifest",
        "Driver": "/transport/ride/driver/manifest.webmanifest",
    }
    response = make_response(render_template_string(
        PAGE,
        title=title,
        buttons=buttons,
        manifest_url=manifests.get(title),
        install_label=f"Install OAP {title}" if title in manifests else "",
    ))
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
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
