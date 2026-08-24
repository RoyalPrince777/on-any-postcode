import json
import logging
import os
import sys
import time
import uuid
from urllib import parse as urlparse

from flask import (
    Flask,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from mission_control import init_app as _mc_init
from mission_control import neon_auth, public_store, smi_chat_runtime, web_security
from mission_control.agents import validate_agent_registry
from mission_control.database import db_status
from mission_control.organism import validate_architecture

app = Flask(__name__)
REQUEST_LOGGER = logging.getLogger("oap.request")
if not REQUEST_LOGGER.handlers:
    request_log_handler = logging.StreamHandler(sys.stdout)
    request_log_handler.setFormatter(logging.Formatter("%(message)s"))
    REQUEST_LOGGER.addHandler(request_log_handler)
REQUEST_LOGGER.setLevel(logging.INFO)
REQUEST_LOGGER.propagate = False
SESSION_SECRET_CONFIGURED = bool(os.environ.get("OAP_SESSION_SECRET", "").strip())
app.config["SECRET_KEY"] = (
    os.environ.get("OAP_SESSION_SECRET", "").strip() or os.urandom(32)
)
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("OAP_LOCAL_MODE", "false").lower() != "true"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

MAX_PUBLIC_RECORDS = 100


def _form_text(name, default, max_length):
    value = request.form.get(name, default)
    return str(value).strip()[:max_length]


def _form_secret(name, max_length):
    """Read a bounded secret without silently changing valid whitespace."""

    return str(request.form.get(name, ""))[:max_length]


def _prepend_bounded(records, item):
    records.insert(0, item)
    del records[MAX_PUBLIC_RECORDS:]


@app.before_request
def _request_observability():
    g.oap_request_id = str(uuid.uuid4())
    g.oap_request_started = time.monotonic()


@app.context_processor
def _session_security_context():
    return {"oap_csrf_token": web_security.csrf_token()}


@app.after_request
def _security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(self), microphone=(self), geolocation=(), payment=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
        "form-action 'self'; object-src 'none'; img-src 'self' data: blob:; "
        "media-src 'self' blob:; connect-src 'self'; "
        "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'",
    )
    if os.environ.get("RENDER", "").lower() == "true":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    response.headers.setdefault("X-OAP-Request-ID", g.get("oap_request_id", ""))
    started = g.get("oap_request_started")
    duration_ms = round((time.monotonic() - started) * 1000, 2) if started else 0
    REQUEST_LOGGER.info(
        json.dumps(
            {
                "event": "http_request",
                "request_id": g.get("oap_request_id"),
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
            separators=(",", ":"),
        )
    )
    return response

signal_posts = []
team_messages = []
flag_counts = {}
# This identity-keyed collection is a deliberate local-development fallback.
# Production My World records are owned by verified UUIDs in Neon Postgres.
profiles = {}

teams = [
    ("A","🇲🇽","Mexico","El Tri","Flag meaning: hope, unity, sacrifice, and ancient identity."),
    ("A","🇿🇦","South Africa","Bafana Bafana","Flag meaning: unity after struggle and many histories joining together."),
    ("A","🇰🇷","South Korea","Taegeuk Warriors","Flag meaning: balance, heaven, earth, water and fire."),
    ("A","🇨🇿","Czechia","Národní tým","Flag meaning: Bohemian colours and historic Czechoslovak identity."),

    ("B","🇨🇦","Canada","The Canucks","Flag meaning: maple leaf, nature, identity, red and white."),
    ("B","🇧🇦","Bosnia and Herzegovina","The Dragons","Flag meaning: Europe, peace, continuity and stars."),
    ("B","🇶🇦","Qatar","The Maroons","Flag meaning: maroon heritage, white peace, nine-point edge."),
    ("B","🇨🇭","Switzerland","The Nati","Flag meaning: unity, neutrality, white cross on red."),

    ("C","🇧🇷","Brazil","Seleção","Flag meaning: nature, wealth, sky, stars, Order and Progress."),
    ("C","🇲🇦","Morocco","Atlas Lions","Flag meaning: courage, heritage, wisdom, peace and tradition."),
    ("C","🇭🇹","Haiti","Les Grenadiers","Flag meaning: unity, sacrifice, liberty and independence."),
    ("C","🏴","Scotland","Tartan Army","Flag meaning: Saint Andrew, loyalty and Scottish identity."),

    ("D","🇺🇸","United States","Stars and Stripes","Flag meaning: states, colonies, courage, purity and justice."),
    ("D","🇵🇾","Paraguay","La Albirroja","Flag meaning: courage, peace, liberty and independence."),
    ("D","🇦🇺","Australia","Socceroos","Flag meaning: history, federation and Southern Cross."),
    ("D","🇹🇷","Türkiye","Crescent-Stars","Flag meaning: Turkish identity, crescent, star and pride."),

    ("E","🇩🇪","Germany","Die Mannschaft","Flag meaning: unity, freedom and democratic identity."),
    ("E","🇨🇼","Curaçao","La Familia Azul","Flag meaning: sea, sky, sun and the island stars."),
    ("E","🇨🇮","Ivory Coast","The Elephants","Flag meaning: land, peace, hope and forests."),
    ("E","🇪🇨","Ecuador","La Tri","Flag meaning: resources, sky, sea and sacrifice."),

    ("F","🇳🇱","Netherlands","Oranje","Flag meaning: Dutch identity with orange football heritage."),
    ("F","🇯🇵","Japan","Samurai Blue","Flag meaning: rising sun and Japanese identity."),
    ("F","🇸🇪","Sweden","Blågult","Flag meaning: blue and yellow national heritage."),
    ("F","🇹🇳","Tunisia","Eagles of Carthage","Flag meaning: sacrifice, peace and cultural identity."),

    ("G","🇧🇪","Belgium","Red Devils","Flag meaning: national colours from Belgian history."),
    ("G","🇪🇬","Egypt","The Pharaohs","Flag meaning: revolution, peace, strength and power."),
    ("G","🇮🇷","Iran","Team Melli","Flag meaning: faith, peace, courage and national identity."),
    ("G","🇳🇿","New Zealand","All Whites","Flag meaning: Southern Cross, history and geography."),

    ("H","🇪🇸","Spain","La Roja","Flag meaning: Spanish kingdoms, unity and heritage."),
    ("H","🇨🇻","Cape Verde","Blue Sharks","Flag meaning: ocean, islands, peace, effort and hope."),
    ("H","🇸🇦","Saudi Arabia","Green Falcons","Flag meaning: faith, strength and justice."),
    ("H","🇺🇾","Uruguay","La Celeste","Flag meaning: historic regions and the Sun of May."),

    ("I","🇫🇷","France","Les Bleus","Flag meaning: liberty, equality and fraternity."),
    ("I","🇸🇳","Senegal","Lions of Teranga","Flag meaning: hope, wealth, sacrifice and unity."),
    ("I","🇮🇶","Iraq","Lions of Mesopotamia","Flag meaning: courage, peace, hope and Arab identity."),
    ("I","🇳🇴","Norway","The Lions","Flag meaning: Nordic identity, freedom and heritage."),

    ("J","🇦🇷","Argentina","La Albiceleste","Flag meaning: sky blue, white and independence."),
    ("J","🇩🇿","Algeria","Desert Foxes","Flag meaning: hope, peace and cultural identity."),
    ("J","🇦🇹","Austria","Das Team","Flag meaning: red-white-red Austrian identity."),
    ("J","🇯🇴","Jordan","The Chivalrous","Flag meaning: Arab heritage, unity and faith."),

    ("K","🇵🇹","Portugal","Seleção das Quinas","Flag meaning: hope, sacrifice, shields and discovery."),
    ("K","🇨🇩","DR Congo","The Leopards","Flag meaning: peace, sacrifice, wealth, hope and unity."),
    ("K","🇺🇿","Uzbekistan","White Wolves","Flag meaning: sky, peace, nature, moon and stars."),
    ("K","🇨🇴","Colombia","Los Cafeteros","Flag meaning: wealth, seas, sky and courage."),

    ("L","🏴","England","Three Lions","Flag meaning: Saint George, bravery and protection."),
    ("L","🇭🇷","Croatia","Vatreni","Flag meaning: Slavic colours and Croatian checkerboard heritage."),
    ("L","🇬🇭","Ghana","Black Stars","Flag meaning: sacrifice, gold, land and African unity."),
    ("L","🇵🇦","Panama","Los Canaleros","Flag meaning: peace, honesty and political balance."),
]

matches = [
    ("FT","11 Jun","A","🇲🇽 Mexico","🇿🇦 South Africa","2-0"),
    ("FT","11 Jun","A","🇰🇷 South Korea","🇨🇿 Czechia","2-1"),
    ("FT","12 Jun","B","🇨🇦 Canada","🇧🇦 Bosnia and Herzegovina","1-1"),
    ("FT","12 Jun","D","🇺🇸 United States","🇵🇾 Paraguay","4-1"),
    ("FT","13 Jun","C","🇧🇷 Brazil","🇲🇦 Morocco","1-1"),
    ("FT","13 Jun","C","🇭🇹 Haiti","🏴 Scotland","0-1"),
    ("FT","14 Jun","D","🇦🇺 Australia","🇹🇷 Türkiye","2-0"),
    ("NEXT","14 Jun","E","🇩🇪 Germany","🇨🇼 Curaçao","13:00"),
    ("NEXT","14 Jun","F","🇳🇱 Netherlands","🇯🇵 Japan","16:00"),
    ("NEXT","17 Jun","L","🏴 England","🇭🇷 Croatia","16:00"),
    ("NEXT","17 Jun","L","🇬🇭 Ghana","🇵🇦 Panama","19:00"),
]

# Register read-only Mission Control routes and explicit CLI-only DB commands.
_mc_init(app)


def _csrf_failure():
    return jsonify(
        error={
            "code": "csrf_failed",
            "message": "The secure session expired. Refresh the page and try again.",
        }
    ), 403


def _rate_failure():
    response = jsonify(
        error={
            "code": "rate_limited",
            "message": "Too many requests. Wait one minute and try again.",
        }
    )
    response.headers["Retry-After"] = "60"
    return response, 429


def _public_write_failure():
    return jsonify(
        error={
            "code": "public_store_unavailable",
            "message": "The durable community store is temporarily unavailable.",
        }
    ), 503


def _local_public_snapshot():
    return {
        "signal_posts": signal_posts,
        "team_messages": team_messages,
        "flag_counts": flag_counts,
        "durable": False,
    }


def _load_public_snapshot():
    if not public_store.status()["configured"]:
        return _local_public_snapshot()
    try:
        return public_store.snapshot()
    except public_store.PublicStoreUnavailable:
        app.logger.warning("durable_public_read_failed")
        return _local_public_snapshot()

@app.get("/")
@app.get("/world")
def home():
    public = _load_public_snapshot()
    return render_template(
        "home.html",
        teams=teams,
        matches=matches,
        signal_posts=public["signal_posts"],
        team_messages=public["team_messages"],
        flag_counts=public["flag_counts"],
        public_persistence=public["durable"],
    )


def _safe_next(value: object, default: str = "/my-world") -> str:
    candidate = str(value or "").strip()
    decoded = urlparse.unquote(candidate)
    parsed = urlparse.urlsplit(candidate)
    if (
        not candidate.startswith("/")
        or candidate.startswith("//")
        or decoded.startswith("//")
        or "\\" in decoded
        or bool(parsed.scheme)
        or bool(parsed.netloc)
        or "\r" in candidate
        or "\n" in candidate
        or len(candidate) > 500
    ):
        return default
    return candidate


def _auth_page_response(
    *,
    status_code: int = 200,
    error: str | None = None,
    notice: str | None = None,
    next_path: str = "/my-world",
):
    response = make_response(
        render_template(
            "auth.html",
            auth_configured=neon_auth.status()["valid"],
            auth_error=error,
            auth_notice=notice,
            next_path=_safe_next(next_path),
        ),
        status_code,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def _auth_rate_key() -> str:
    return f"auth:{request.remote_addr or 'unknown'}"


def _apply_auth_cookies(response, set_cookie_headers) -> bool:
    app_cookie_name = str(app.config.get("SESSION_COOKIE_NAME", "session"))
    upstream_names = neon_auth.cookie_names(set_cookie_headers)
    safe_names = tuple(name for name in upstream_names if name != app_cookie_name)
    if not safe_names:
        return False

    session.clear()
    session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = list(safe_names)
    session.permanent = True
    for header in set_cookie_headers:
        scoped = neon_auth.scoped_set_cookie(header)
        name = header.split("=", 1)[0].strip()
        if scoped and name in safe_names:
            response.headers.add("Set-Cookie", scoped)
    return True


@app.get("/auth")
@app.get("/enter-my-world")
def auth_page():
    next_path = _safe_next(request.args.get("next"))
    try:
        if web_security.current_authenticated_user() is not None:
            return redirect(next_path)
    except neon_auth.AuthUnavailable:
        pass
    error = None
    if request.args.get("auth_error") == "unavailable":
        error = "Secure identity verification is temporarily unavailable."
    return _auth_page_response(error=error, next_path=next_path)


@app.post("/auth/sign-in")
def auth_sign_in():
    next_path = _safe_next(request.form.get("next"))
    if not web_security.csrf_valid(request):
        return _auth_page_response(
            status_code=403,
            error="The secure session expired. Refresh and try again.",
            next_path=next_path,
        )
    if not web_security.AUTH_BURST_LIMITER.allow(_auth_rate_key()):
        return _auth_page_response(
            status_code=429,
            error="Too many sign-in attempts. Wait 15 minutes and try again.",
            next_path=next_path,
        )
    email = _form_text("email", "", 320).lower()
    password = _form_secret("password", 1024)
    if not email or not password:
        return _auth_page_response(
            status_code=400,
            error="Enter your email and password.",
            next_path=next_path,
        )
    try:
        result = neon_auth.sign_in(email, password)
    except neon_auth.AuthUnavailable:
        return _auth_page_response(
            status_code=503,
            error="Secure identity verification is temporarily unavailable.",
            next_path=next_path,
        )
    if not neon_auth.successful(result):
        return _auth_page_response(
            status_code=401,
            error="Email or password not recognised.",
            next_path=next_path,
        )
    response = redirect(next_path)
    if not _apply_auth_cookies(response, result.set_cookie_headers):
        return _auth_page_response(
            status_code=502,
            error="A secure session could not be established. Try again.",
            next_path=next_path,
        )
    return response


@app.post("/auth/sign-up")
def auth_sign_up():
    next_path = _safe_next(request.form.get("next"))
    if not web_security.csrf_valid(request):
        return _auth_page_response(
            status_code=403,
            error="The secure session expired. Refresh and try again.",
            next_path=next_path,
        )
    if not web_security.AUTH_BURST_LIMITER.allow(_auth_rate_key()):
        return _auth_page_response(
            status_code=429,
            error="Too many account attempts. Wait 15 minutes and try again.",
            next_path=next_path,
        )
    name = _form_text("name", "", 120)
    email = _form_text("email", "", 320).lower()
    password = _form_secret("password", 1024)
    confirmation = _form_secret("password_confirm", 1024)
    if not name or not email or len(password) < 8:
        return _auth_page_response(
            status_code=400,
            error="Enter a name, email, and password of at least 8 characters.",
            next_path=next_path,
        )
    if password != confirmation:
        return _auth_page_response(
            status_code=400,
            error="The passwords do not match.",
            next_path=next_path,
        )
    try:
        result = neon_auth.sign_up(name, email, password)
    except neon_auth.AuthUnavailable:
        return _auth_page_response(
            status_code=503,
            error="Secure account creation is temporarily unavailable.",
            next_path=next_path,
        )
    if not neon_auth.successful(result):
        return _auth_page_response(
            status_code=400,
            error="The account could not be created with those details.",
            next_path=next_path,
        )
    response = redirect(next_path)
    if _apply_auth_cookies(response, result.set_cookie_headers):
        return response
    return _auth_page_response(
        notice="Account created. Check your email if verification is requested, then sign in.",
        next_path=next_path,
    )


@app.post("/auth/sign-out")
def auth_sign_out():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    known_names = tuple(
        session.get(neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY, ())
        if isinstance(
            session.get(neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY), (list, tuple)
        )
        else ()
    )
    cookie_header = web_security.auth_cookie_header()
    upstream_headers = ()
    if cookie_header:
        try:
            upstream_headers = neon_auth.sign_out(cookie_header).set_cookie_headers
        except neon_auth.AuthUnavailable:
            app.logger.warning("neon_auth_sign_out_unavailable")
    session.clear()
    response = redirect(url_for("home"))
    for header in upstream_headers:
        scoped = neon_auth.scoped_set_cookie(header)
        if scoped:
            response.headers.add("Set-Cookie", scoped)
    for name in known_names:
        response.set_cookie(
            str(name),
            "",
            max_age=0,
            expires=0,
            path="/",
            secure=app.config["SESSION_COOKIE_SECURE"],
            httponly=True,
            samesite="Lax",
        )
    return response

@app.get("/the-spot")
def the_spot_front_door():
    """Open The Spot while keeping one canonical implementation route."""

    return redirect(url_for("mission_control.spot_dashboard"))


@app.get("/the-link")
def the_link_front_door():
    """Open The Link inside The Spot."""

    return redirect(url_for("mission_control.the_link_dashboard"))


@app.get("/linkup")
def linkup_front_door():
    """Open LinkUp inside The Link."""

    return redirect(url_for("mission_control.link_dashboard"))


@app.route("/signal", methods=["POST"])
def signal():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    identity_id = web_security.ensure_session_identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return _rate_failure()
    item = {
        "name": _form_text("name", "OAP", 80),
        "body": _form_text("body", "", 2000),
    }
    try:
        if public_store.status()["configured"]:
            public_store.add_signal(identity_id, **item)
        else:
            _prepend_bounded(signal_posts, item)
    except ValueError:
        return _rate_failure()
    except public_store.PublicStoreUnavailable:
        return _public_write_failure()
    return redirect("/#signal")

@app.route("/room", methods=["POST"])
def room():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    identity_id = web_security.ensure_session_identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return _rate_failure()
    item = {
        "room": _form_text("room", "Team Room", 80),
        "name": _form_text("name", "Visitor", 80),
        "message": _form_text("message", "", 2000),
    }
    if item["room"] not in {f"{team[2]} Team Room" for team in teams}:
        return jsonify(error={"code": "invalid_room"}), 400
    try:
        if public_store.status()["configured"]:
            public_store.add_room_message(identity_id, **item)
        else:
            _prepend_bounded(team_messages, item)
    except ValueError:
        return _rate_failure()
    except public_store.PublicStoreUnavailable:
        return _public_write_failure()
    return redirect("/#teams")

@app.route("/flag", methods=["POST"])
def flag():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    identity_id = web_security.ensure_session_identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return _rate_failure()
    team = _form_text("team", "", 120)
    if team not in {item[2] for item in teams}:
        return jsonify(error={"code": "invalid_team"}), 400
    try:
        if public_store.status()["configured"]:
            public_store.add_flag(identity_id, team=team)
        else:
            flag_counts[team] = flag_counts.get(team, 0) + 1
    except ValueError:
        return _rate_failure()
    except public_store.PublicStoreUnavailable:
        return _public_write_failure()
    return redirect("/#teams")

@app.get("/my-world")
@web_security.login_required()
def my_world():
    user = web_security.current_authenticated_user()
    if user is None:  # pragma: no cover - decorator is the fail-closed gate
        return redirect(url_for("auth_page"))
    identity_id = str(user["id"])
    profile = {
        "nickname": str(user["name"]),
        "country": "",
    }
    try:
        if public_store.status()["configured"]:
            public_store.ensure_authenticated_user(
                identity_id,
                email=str(user["email"]),
                display_name=str(user["name"]),
            )
            profile = public_store.get_profile(identity_id) or profile
        else:
            profile = profiles.get(identity_id, profile)
    except public_store.PublicStoreUnavailable:
        response = make_response(
            render_template(
                "my_world.html",
                auth_user=user,
                profile=profile,
                private_store_unavailable=True,
            ),
            503,
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    response = make_response(
        render_template(
            "my_world.html",
            auth_user=user,
            profile=profile,
            private_store_unavailable=False,
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return response


@app.get("/myworld")
@web_security.login_required()
def myworld_legacy_get():
    return redirect(url_for("my_world"))


@app.post("/myworld")
@web_security.login_required()
def myworld():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    user = web_security.current_authenticated_user()
    if user is None:  # pragma: no cover - decorator is the fail-closed gate
        return redirect(url_for("auth_page"))
    identity_id = str(user["id"])
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return _rate_failure()
    item = {
        "nickname": _form_text("nickname", "OAP Visitor", 80),
        "country": _form_text("country", "", 80),
    }
    try:
        if public_store.status()["configured"]:
            public_store.ensure_authenticated_user(
                identity_id,
                email=str(user["email"]),
                display_name=str(user["name"]),
            )
            public_store.update_profile(identity_id, **item)
        else:
            profiles[identity_id] = item
    except public_store.PublicStoreUnavailable:
        return _public_write_failure()
    return redirect(url_for("my_world"))


def _readiness_snapshot():
    architecture = validate_architecture()
    registry = validate_agent_registry()
    database = db_status()
    community = public_store.status()
    smi = smi_chat_runtime.health()
    auth = neon_auth.status()
    checks = {
        "architecture_integrity": architecture["passed"],
        "registry_integrity": registry["passed"],
        "registry_activation_ready": registry["ready_for_activation"],
        "database_initialized": bool(database.get("initialized")),
        "durable_public_store": bool(community["durable"]),
        "session_secret_configured": SESSION_SECRET_CONFIGURED,
        "neon_auth_configured": auth["valid"],
        "private_auth_required": os.environ.get(
            "OAP_AUTH_REQUIRED", "false"
        ).lower()
        == "true",
        "csrf_protection": True,
        "bounded_rate_controls": True,
        "smi_3x7_ready": smi["status"] == "green" and smi["green"] == smi["total"],
        "structured_request_logs": bool(REQUEST_LOGGER.handlers)
        and REQUEST_LOGGER.isEnabledFor(logging.INFO),
    }
    return {
        "checks": checks,
        "green": sum(checks.values()),
        "total": len(checks),
        "database": database,
        "community": community,
        "smi": smi,
        "auth": auth,
    }


@app.get("/livez")
def livez():
    response = jsonify(status="alive", live=True)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/healthz")
def healthz():
    """Return a side-effect-free, non-sensitive deployment readiness check."""

    readiness = _readiness_snapshot()
    checks = readiness["checks"]
    ready = all(checks.values())
    response = jsonify(
        status="healthy" if ready else "degraded",
        live=True,
        ready=ready,
        checks=checks,
        green=readiness["green"],
        total=readiness["total"],
        smi={
            "status": readiness["smi"]["status"],
            "green": readiness["smi"]["green"],
            "total": readiness["smi"]["total"],
        },
        governance={
            "human_authority_final": True,
            "execution_exposed": False,
        },
    )
    response.headers["Cache-Control"] = "no-store"
    return response


INFRASTRUCTURE_SECTIONS = [
    {"slug":"command","icon":"🏗️","name":"Infrastructure Command","status":"LIVE","features":["Overall status","Live services","System alerts","Infrastructure activity"]},
    {"slug":"database","icon":"🗄️","name":"Database","status":"LIVE","features":["Neon Postgres","SQLite local databases","Schema and migrations","Backups and recovery"]},
    {"slug":"deployment","icon":"🚀","name":"Hosting & Deployment","status":"LIVE","features":["Render services","GitHub deployments","Build status","Deployment history"]},
    {"slug":"network","icon":"🌐","name":"Network","status":"LIVE","features":["Service ports","API Gateway","NEXUS routing","DNS and connectivity"]},
    {"slug":"storage","icon":"💾","name":"Storage","status":"LIVE","features":["User files","Media storage","HRM memory","Backup storage"]},
    {"slug":"security","icon":"🛡️","name":"Security","status":"LIVE","features":["Identity checks","Permissions","Sessions and devices","Guardian audit"]},
    {"slug":"performance","icon":"📈","name":"Performance","status":"LIVE","features":["Clarity","Performance","Stability","Pace"]},
    {"slug":"services","icon":"🟢","name":"Service Health","status":"LIVE","features":["OAP World","My World","Link Up","HRM and SIKA"]},
    {"slug":"local","icon":"📱","name":"Local Infrastructure","status":"READY","features":["Termux","Flask services","Ollama","Offline local-first mode"]},
    {"slug":"cloud","icon":"☁️","name":"Cloud Infrastructure","status":"LIVE","features":["Neon Postgres","Render","GitHub","Datadog ready"]},
    {"slug":"monitoring","icon":"📊","name":"Logs & Monitoring","status":"LIVE","features":["Live logs","Errors","Route health","Agent and HRM activity"]},
    {"slug":"recovery","icon":"♻️","name":"Recovery & Maintenance","status":"READY","features":["Restore points","Database branches","Rollback","Incident history"]},
]


@app.get("/infrastructure")
@web_security.login_required()
def infrastructure_dashboard():
    return render_template("infrastructure.html", sections=[
        dict(section, href=url_for("infrastructure_section", section=section["slug"]))
        for section in INFRASTRUCTURE_SECTIONS
    ])


@app.get("/infrastructure/<section>")
@web_security.login_required(api=True)
def infrastructure_section(section):
    selected = next((item for item in INFRASTRUCTURE_SECTIONS if item["slug"] == section), None)
    if selected is None:
        return jsonify(status="not_found", section=section), 404
    checks = {"route": True, "human_authority_final": True}
    if section == "database":
        database = db_status()
        community = public_store.status()
        checks.update({
            "neon_postgres": database.get("backend") == "postgresql",
            "database": "neondb",
            "required_schema_verified": bool(database.get("initialized")),
            "community_data_durable": bool(community["durable"]),
        })
    elif section == "deployment":
        checks.update({
            "render": os.environ.get("RENDER", "").lower() == "true",
            "revision_present": bool(
                os.environ.get("RENDER_GIT_COMMIT")
                or os.environ.get("OAP_ENV_REVISION")
            ),
            "production": os.environ.get("OAP_LOCAL_MODE", "false").lower()
            != "true",
        })
    elif section == "services":
        architecture = validate_architecture()
        registry = validate_agent_registry()
        checks.update({
            "architecture": architecture["passed"],
            "agent_registry": registry["passed"],
            "activation_ready": registry["ready_for_activation"],
        })
    return jsonify(system="OAP Infrastructure", section=selected, checks=checks)


@app.get("/api/infrastructure/status")
@web_security.login_required(api=True)
def infrastructure_status():
    readiness = _readiness_snapshot()
    ready = all(readiness["checks"].values())
    return jsonify(
        status="live" if ready else "degraded",
        count=len(INFRASTRUCTURE_SECTIONS),
        live=sum(item["status"] == "LIVE" for item in INFRASTRUCTURE_SECTIONS),
        ready=sum(item["status"] == "READY" for item in INFRASTRUCTURE_SECTIONS),
        checks=readiness["checks"],
        database={
            "provider": "Neon Postgres",
            "database": "neondb",
            "initialized": bool(readiness["database"].get("initialized")),
            "community_data_durable": bool(readiness["community"]["durable"]),
        },
        deployment={
            "provider": "Render",
            "service": "on-any-postcode",
            "revision_present": bool(
                os.environ.get("RENDER_GIT_COMMIT")
                or os.environ.get("OAP_ENV_REVISION")
            ),
        },
        sections=INFRASTRUCTURE_SECTIONS,
        governance={"human_authority_final":True},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
