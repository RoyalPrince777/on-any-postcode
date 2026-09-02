"""Public continent-first world hierarchy for ON ANY POSTCODE.

World Cup remains a Culture/Sport experience. Geography owns Continent → Country →
County/Region → Borough/District → Postcode. Public rooms reuse the existing durable
community-room ledger; private messages remain in LinkUp.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, redirect, render_template, request, url_for

from . import public_store, web_security

bp = Blueprint("world_geography", __name__)

CONTINENTS = (
    {"slug":"africa","name":"Africa","icon":"🌍","highlights":("Culture","Music","Food","History","Sport","Humour","Languages"),"countries":("Algeria","Cape Verde","DR Congo","Egypt","Ghana","Ivory Coast","Morocco","Senegal","South Africa","Tunisia")},
    {"slug":"asia","name":"Asia","icon":"🌏","highlights":("Culture","Food","Technology","History","Sport","Humour","Languages"),"countries":("Iran","Iraq","Japan","Jordan","Qatar","Saudi Arabia","South Korea","Uzbekistan")},
    {"slug":"europe","name":"Europe","icon":"🌍","highlights":("Culture","Music","History","Football","Humour","Languages","Travel"),"countries":("Austria","Belgium","Bosnia and Herzegovina","Croatia","Czechia","England","France","Germany","Netherlands","Norway","Portugal","Scotland","Spain","Sweden","Switzerland","Türkiye")},
    {"slug":"north-america","name":"North America & Caribbean","icon":"🌎","highlights":("Culture","Music","Carnival","Sport","Humour","Food","Community"),"countries":("Canada","Curaçao","Haiti","Mexico","Panama","United States")},
    {"slug":"south-america","name":"South America","icon":"🌎","highlights":("Culture","Music","Football","Carnival","Food","Humour","History"),"countries":("Argentina","Brazil","Colombia","Ecuador","Paraguay","Uruguay")},
    {"slug":"oceania","name":"Oceania","icon":"🌏","highlights":("Culture","Nature","Sport","Music","Humour","Travel","Community"),"countries":("Australia","New Zealand")},
)

# Anthem sections are country-owned cultural surfaces. Audio is deliberately not
# outsourced; a first-party certified media asset can be attached without changing
# this hierarchy contract.
COUNTRY_ANTHEM_TITLES = {
    "Ghana":"God Bless Our Homeland Ghana",
    "South Africa":"National Anthem of South Africa",
    "Morocco":"Cherifian Anthem",
    "Senegal":"Pincez Tous vos Koras, Frappez les Balafons",
    "Egypt":"Bilady, Bilady, Bilady",
    "Algeria":"Kassaman",
    "Tunisia":"Humat al-Hima",
    "Japan":"Kimigayo",
    "South Korea":"Aegukga",
    "Qatar":"As Salam al Amiri",
    "Saudi Arabia":"Aash Al Maleek",
    "United States":"The Star-Spangled Banner",
    "Canada":"O Canada",
    "Mexico":"Himno Nacional Mexicano",
    "Brazil":"Hino Nacional Brasileiro",
    "Argentina":"Himno Nacional Argentino",
    "Colombia":"Himno Nacional de la República de Colombia",
    "Uruguay":"Himno Nacional de Uruguay",
    "Paraguay":"Paraguayos, República o Muerte",
    "Australia":"Advance Australia Fair",
    "New Zealand":"God Defend New Zealand",
    "France":"La Marseillaise",
    "Germany":"Deutschlandlied",
    "Spain":"Marcha Real",
    "Portugal":"A Portuguesa",
    "Netherlands":"Wilhelmus",
    "Belgium":"La Brabançonne",
    "Switzerland":"Swiss Psalm",
    "Austria":"Land der Berge, Land am Strome",
    "Croatia":"Lijepa naša domovino",
    "Czechia":"Kde domov můj",
    "Norway":"Ja, vi elsker dette landet",
    "Sweden":"Du gamla, Du fria",
    "Türkiye":"İstiklâl Marşı",
    "England":"God Save the King",
    "Scotland":"National anthem / sporting anthem surface",
}

LEVELS = (
    ("continent","🌍","Continent"),
    ("country","🏳️","Country"),
    ("region","🧭","County / Region"),
    ("borough","🏙️","Borough / District"),
    ("postcode","📍","Postcode"),
)


def _snapshot_messages():
    try:
        return public_store.snapshot().get("team_messages", [])
    except public_store.PublicStoreUnavailable:
        return []


@bp.get("/world")
def world_index():
    return make_response(render_template("world_geography.html", continents=CONTINENTS, selected=None, messages=_snapshot_messages()), 200)


@bp.get("/world/<continent_slug>")
def continent(continent_slug: str):
    selected = next((item for item in CONTINENTS if item["slug"] == continent_slug), None)
    if selected is None:
        return make_response(jsonify(error={"code":"not_found","message":"That continent is unavailable."}), 404)
    return make_response(render_template("world_geography.html", continents=CONTINENTS, selected=selected, anthem_titles=COUNTRY_ANTHEM_TITLES, messages=_snapshot_messages()), 200)


@bp.post("/world/room")
def hierarchy_room():
    if not web_security.csrf_valid(request):
        return make_response(jsonify(error={"code":"csrf_failed","message":"Request verification failed."}), 403)
    identity_id = web_security.ensure_session_identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return make_response(jsonify(error={"code":"rate_limited","message":"Too many room posts. Try again shortly."}), 429)

    level = str(request.form.get("level", "")).strip().lower()
    place = " ".join(str(request.form.get("place", "")).split())[:120]
    name = " ".join(str(request.form.get("name", "Visitor")).split())[:80] or "Visitor"
    message = " ".join(str(request.form.get("message", "")).split())[:500]
    allowed_levels = {item[0]: item[2] for item in LEVELS}
    if level not in allowed_levels or not place or not message:
        return make_response(jsonify(error={"code":"invalid_room","message":"A valid geography level, place and message are required."}), 400)

    room = f"{place} · {allowed_levels[level]} Room"
    try:
        public_store.add_room_message(identity_id, room=room, name=name, message=message)
    except ValueError:
        return make_response(jsonify(error={"code":"rate_limited","message":"Too many room posts. Try again shortly."}), 429)
    except public_store.PublicStoreUnavailable:
        return make_response(jsonify(error={"code":"public_store_unavailable","message":"The public room ledger is temporarily unavailable."}), 503)

    next_url = request.form.get("next") or url_for("world_geography.world_index")
    if not str(next_url).startswith("/world"):
        next_url = url_for("world_geography.world_index")
    return redirect(str(next_url))
