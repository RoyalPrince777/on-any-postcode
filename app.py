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
    send_from_directory,
    session,
    url_for,
)

from mission_control import (
    approval_service,
    authority,
    carnival_intelligence,
    founder_activation,
    judgement,
    languages,
    linkup,
    location_intelligence,
    neon_auth,
    product_store,
    products,
    public_store,
    smi_chat_runtime,
    telemetry,
    web_security,
    workspaces,
)
from mission_control import init_app as _mc_init
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
FOUNDER_ONLY_PATH_PREFIXES = (
    "/api/infrastructure",
    "/infrastructure",
    "/mission",
    "/my-world",
    "/myworld",
)
CARNIVAL_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
    "form-action 'self'; object-src 'none'; img-src 'self' data:; "
    "media-src 'self'; connect-src 'self'; style-src 'self'; "
    "script-src 'self'; frame-src https://www.openstreetmap.org"
)
FOUNDER_ACTIVATED_SESSION_KEY = "oap_founder_activation_completed"


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


@app.before_request
def _protect_private_assets():
    if request.endpoint != "mission_control.static":
        return None
    try:
        user = web_security.current_authenticated_user()
    except neon_auth.AuthUnavailable:
        user = None
    if user is not None and web_security.private_authority_allowed(user):
        return None
    response = make_response("", 404)
    response.headers["Cache-Control"] = "no-store"
    return response


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
    telemetry.record_http_request(
        path=str(request.url_rule.rule) if request.url_rule else "unmatched",
        status_code=response.status_code,
        duration_ms=duration_ms,
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

LOCATION_LEVELS = (
    {
        "order": 1,
        "name": "Continent",
        "icon": "🌍",
        "purpose": "Connect every local community to its part of the world.",
    },
    {
        "order": 2,
        "name": "Country",
        "icon": "🏳️",
        "purpose": "National identity, culture, information and shared services.",
    },
    {
        "order": 3,
        "name": "County / Region",
        "icon": "🧭",
        "purpose": "Regional coordination without replacing local ownership.",
    },
    {
        "order": 4,
        "name": "Borough / District",
        "icon": "🏙️",
        "purpose": "The local authority and neighbourhood connection layer.",
    },
    {
        "order": 5,
        "name": "Postcode",
        "icon": "📍",
        "purpose": "The free front door into The Spot and local community life.",
    },
)

# Register read-only Mission Control routes and explicit CLI-only DB commands.
_mc_init(app)


@app.get("/assets/oap.css")
def public_stylesheet():
    """Serve shared presentation styles from a product-neutral public URL."""

    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "oap_public.css",
        max_age=3600,
    )


@app.get("/manifest.webmanifest")
def oap_os_manifest():
    """Expose the install contract for the public OAP Operating System shell."""

    response = send_from_directory(
        os.path.join(app.root_path, "static"),
        "manifest.webmanifest",
        mimetype="application/manifest+json",
        max_age=3600,
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@app.get("/service-worker.js")
def oap_os_service_worker():
    """Serve the public-only worker at the root scope with prompt updates."""

    response = send_from_directory(
        os.path.join(app.root_path, "static"),
        "oap-os-sw.js",
        mimetype="application/javascript",
        max_age=0,
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@app.get("/assets/oap-os.js")
def oap_os_install_controller():
    """Serve the bounded browser installation controller."""

    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "oap-os.js",
        mimetype="application/javascript",
        max_age=3600,
    )


@app.get("/assets/oap-os-icon-<int:size>.png")
def oap_os_icon(size):
    """Serve only the two reviewed install-icon sizes."""

    if size not in {192, 512}:
        response = make_response("", 404)
        response.headers["Cache-Control"] = "no-store"
        return response
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        f"oap-os-icon-{size}.png",
        mimetype="image/png",
        max_age=86400,
    )


@app.get("/offline")
def oap_os_offline():
    """Return a static public fallback without opening a session or private store."""

    response = send_from_directory(
        os.path.join(app.root_path, "static"),
        "oap-os-offline.html",
        mimetype="text/html",
        max_age=3600,
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


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
        location_levels=LOCATION_LEVELS,
        signal_posts=public["signal_posts"],
        team_messages=public["team_messages"],
        flag_counts=public["flag_counts"],
        public_persistence=public["durable"],
    )


def _world_languages_response():
    """Render only the validated, read-only OAP World learning projection."""

    validation = languages.validate_language_hub()
    if not validation["passed"]:
        response = jsonify(
            error={
                "code": "language_hub_unavailable",
                "message": "World Languages is temporarily unavailable.",
            }
        )
        response.status_code = 503
    else:
        response = make_response(
            render_template(
                "languages.html",
                hub=languages.get_public_language_hub(
                    continent_id=request.args.get("continent"),
                    lesson_id=request.args.get("lesson"),
                    drill_id=request.args.get("drill"),
                ),
            )
        )
    response.headers["Cache-Control"] = "no-store"
    return response


def _carnival_intelligence_response():
    """Render only the validated, source-scoped public event projection."""

    validation = carnival_intelligence.validate_carnival_hub()
    if not validation["passed"]:
        response = jsonify(
            error={
                "code": "carnival_intelligence_unavailable",
                "message": "Carnival Intelligence is temporarily unavailable.",
            }
        )
        response.status_code = 503
    else:
        response = make_response(
            render_template(
                "carnival.html",
                hub=carnival_intelligence.get_public_carnival_hub(),
            )
        )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        CARNIVAL_CONTENT_SECURITY_POLICY
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/languages")
@app.get("/world/languages")
def world_languages():
    """Open the phase-one public language-learning hub."""

    return _world_languages_response()


@app.get("/carnival")
@app.get("/world/carnival")
def world_carnival():
    """Open the read-only OAP Culture/Event Carnival hub."""

    return _carnival_intelligence_response()


@app.get("/world-cup")
def world_cup():
    """Preserve football inside Culture instead of using it as OAP World."""

    public = _load_public_snapshot()
    response = make_response(
        render_template(
            "world_cup.html",
            teams=teams,
            matches=matches,
            team_messages=public["team_messages"],
            flag_counts=public["flag_counts"],
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response


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


def _founder_only_path(value: object) -> bool:
    """Classify only explicit private-control destinations as Founder-only."""

    candidate = _safe_next(value)
    path = urlparse.urlsplit(candidate).path.rstrip("/") or "/"
    return any(
        path == prefix or path.startswith(f"{prefix}/")
        for prefix in FOUNDER_ONLY_PATH_PREFIXES
    )


def _auth_page_response(
    *,
    status_code: int = 200,
    error: str | None = None,
    notice: str | None = None,
    next_path: str = "/my-world",
):
    founder_only = _founder_only_path(next_path)
    auth_ready = neon_auth.status()["valid"] and (
        not founder_only or bool(neon_auth.configured_founder_email())
    )
    response = make_response(
        render_template(
            "auth.html",
            auth_configured=auth_ready,
            auth_error=error,
            auth_notice=notice,
            next_path=_safe_next(next_path),
            founder_only=founder_only,
        ),
        status_code,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def _founder_activation_response(
    *, status_code: int = 200, error: str | None = None
):
    response = make_response(
        render_template("founder_activation.html", activation_error=error),
        status_code,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def _founder_activation_closed(status_code: int = 404):
    response = make_response("", status_code)
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
    founder_only = _founder_only_path(next_path)
    error = None
    try:
        user = web_security.current_authenticated_user()
        if user is not None:
            if not founder_only or web_security.private_authority_allowed(user):
                return redirect(next_path)
            error = "This signed-in account cannot open the private Founder space."
    except neon_auth.AuthUnavailable:
        pass
    if request.args.get("auth_error") == "unavailable":
        error = "Secure identity verification is temporarily unavailable."
    notice = None
    if session.pop(FOUNDER_ACTIVATED_SESSION_KEY, False):
        notice = (
            "Founder identity activated. Sign in with the private password "
            "you just chose."
        )
    return _auth_page_response(error=error, notice=notice, next_path=next_path)


@app.get("/activate-founder")
def founder_activation_page():
    activation_state = founder_activation.state()
    if activation_state in {"complete", "disabled"}:
        return _founder_activation_closed()
    if activation_state != "available":
        return _founder_activation_response(
            status_code=503,
            error="Founder activation is temporarily unavailable.",
        )
    return _founder_activation_response()


@app.post("/activate-founder")
def activate_founder():
    activation_state = founder_activation.state()
    if activation_state in {"complete", "disabled"}:
        return _founder_activation_closed()
    if activation_state != "available":
        return _founder_activation_response(
            status_code=503,
            error="Founder activation is temporarily unavailable.",
        )
    if not web_security.csrf_valid(request):
        return _founder_activation_response(
            status_code=403,
            error="The secure session expired. Refresh and try again.",
        )
    if not web_security.AUTH_BURST_LIMITER.allow(_auth_rate_key()):
        return _founder_activation_response(
            status_code=429,
            error="Too many activation attempts. Wait 15 minutes and try again.",
        )
    if not founder_activation.token_allowed(_form_secret("activation_code", 512)):
        return _founder_activation_response(
            status_code=403,
            error="The activation details were not recognised.",
        )

    password = _form_secret("password", 129)
    confirmation = _form_secret("password_confirmation", 129)
    if password != confirmation:
        return _founder_activation_response(
            status_code=400,
            error="The two private password entries do not match.",
        )
    if len(password) < 12 or len(password) > 128 or not password.strip():
        return _founder_activation_response(
            status_code=400,
            error="Choose a private password between 12 and 128 characters.",
        )

    try:
        result = founder_activation.activate(password)
    except founder_activation.ActivationUnavailable:
        return _founder_activation_response(
            status_code=503,
            error="Founder activation is temporarily unavailable.",
        )
    if result == "complete":
        return _founder_activation_closed()
    if result != "activated":
        return _founder_activation_response(
            status_code=400,
            error=(
                "Managed identity rejected those setup details. Use a unique "
                "password between 12 and 128 characters, then enter the same "
                "password twice."
            ),
        )

    session[FOUNDER_ACTIVATED_SESSION_KEY] = True
    session.permanent = True
    return redirect(url_for("auth_page", next="/my-world"))


@app.post("/auth/sign-in")
def auth_sign_in():
    next_path = _safe_next(request.form.get("next"))
    founder_only = _founder_only_path(next_path)
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
    password = _form_secret("password", 1024)
    if not password:
        return _auth_page_response(
            status_code=400,
            error=(
                "Enter your private password."
                if founder_only
                else "Enter your email and password."
            ),
            next_path=next_path,
        )
    email = (
        neon_auth.configured_founder_email()
        if founder_only
        else _form_text("email", "", 320).lower()
    )
    if not email:
        return _auth_page_response(
            status_code=503 if founder_only else 400,
            error=(
                "Private access is temporarily unavailable."
                if founder_only
                else "Enter your email and password."
            ),
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
            error=(
                "Private password not recognised."
                if founder_only
                else "Email or password not recognised."
            ),
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
    """Render the public postcode-community product without internal details."""

    response = make_response(
        render_template(
            "spot.html",
            hierarchy=products.get_public_product_hierarchy(),
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/the-spot/<capability_slug>")
def spot_capability_front_door(capability_slug):
    """Render one Spot experience and its bounded live function when available."""

    capability = products.get_public_spot_capability(capability_slug)
    if capability is None:
        response = jsonify(
            error={
                "code": "not_found",
                "message": "That Spot experience is unavailable.",
            }
        )
        response.status_code = 404
    elif capability_slug == "languages":
        return _world_languages_response()
    elif capability_slug == "carnival":
        return _carnival_intelligence_response()
    else:
        user = None
        try:
            user = web_security.current_authenticated_user()
        except neon_auth.AuthUnavailable:
            user = None
        context = {
            "location": None,
            "location_error": None,
            "market_products": [],
            "signal_posts": [],
            "room_messages": [],
            "sika": None,
            "workspace": None,
            "workspace_records": [],
            "private_unavailable": False,
        }
        if capability_slug == "maps-weather-travel" and request.args.get("location"):
            try:
                context["location"] = location_intelligence.lookup_with_weather(
                    request.args.get("location")
                )
            except ValueError as exc:
                context["location_error"] = str(exc)
            except location_intelligence.LocationUnavailable:
                context["location_error"] = "live_location_unavailable"
        if capability_slug in {"pulse", "signal", "postcode-rooms"}:
            public = _load_public_snapshot()
            context["signal_posts"] = public["signal_posts"]
            context["room_messages"] = public["team_messages"]
        if capability_slug in {"market", "businesses"} and public_store.status()["configured"]:
            try:
                context["market_products"] = product_store.list_products()
            except product_store.ProductStoreUnavailable:
                context["private_unavailable"] = True
        workspace_map = {
            "pulse": "signals",
            "signal": "signals",
            "postcode-rooms": "signals",
            "events": "ecosystem",
            "carnival": "ecosystem",
            "discovery": "maps",
            "businesses": "market",
            "creators": "tv",
            "community-progress": "signals",
            "support": "governance",
            "maps-weather-travel": "maps",
            "market": "market",
            "movement-delivery": "transport",
            "safety": "governance",
            "my-world": "identity",
            "tv-media": "tv",
            "membership": "ecosystem",
            "sika": "sika",
        }
        workspace_id = workspace_map.get(capability_slug)
        if user and public_store.status()["configured"]:
            try:
                public_store.ensure_authenticated_user(
                    str(user["id"]),
                    email=str(user["email"]),
                    display_name=str(user["name"]),
                )
                if capability_slug == "sika":
                    context["sika"] = product_store.sika_summary(str(user["id"]))
                if workspace_id:
                    context["workspace"] = workspaces.get(workspace_id)
                    context["workspace_records"] = workspaces.list_records(
                        str(user["id"]), workspace_id, limit=10
                    )
            except (
                public_store.PublicStoreUnavailable,
                product_store.ProductStoreUnavailable,
                workspaces.WorkspaceUnavailable,
            ):
                context["private_unavailable"] = True
        response = make_response(
            render_template(
                "spot_capability.html",
                capability=capability,
                auth_user=user,
                **context,
            )
        )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/the-link")
def the_link_front_door():
    """Open The Link inside The Spot."""

    response = make_response(render_template("the_link.html"))
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/linkup")
def linkup_front_door():
    """Open LinkUp inside The Link."""

    user = None
    dashboard = None
    unavailable = False
    try:
        user = web_security.current_authenticated_user()
    except neon_auth.AuthUnavailable:
        user = None
    if user and public_store.status()["configured"]:
        try:
            public_store.ensure_authenticated_user(
                str(user["id"]),
                email=str(user["email"]),
                display_name=str(user["name"]),
            )
            dashboard = product_store.linkup_dashboard(str(user["id"]))
        except (
            public_store.PublicStoreUnavailable,
            product_store.ProductStoreUnavailable,
        ):
            unavailable = True
    response = make_response(
        render_template(
            "linkup.html",
            link=linkup.get_public_link_dashboard(),
            auth_user=user,
            dashboard=dashboard,
            private_unavailable=unavailable,
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/linkup/send")
@web_security.login_required(api=True)
def linkup_send():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    user = web_security.current_authenticated_user()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(str(user["id"])):
        return _rate_failure()
    try:
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
        )
        product_store.send_message(
            str(user["id"]),
            request.form.get("recipient_id"),
            _form_text("body", "", 4000),
        )
    except ValueError as exc:
        return jsonify(error={"code": str(exc)}), 400
    except (
        public_store.PublicStoreUnavailable,
        product_store.ProductStoreUnavailable,
    ):
        return jsonify(error={"code": "linkup_unavailable"}), 503
    return redirect(url_for("linkup_front_door"))


@app.post("/linkup/messages/<message_id>/read")
@web_security.login_required(api=True)
def linkup_read(message_id):
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    user = web_security.current_authenticated_user()
    try:
        if not product_store.mark_message_read(str(user["id"]), message_id):
            return jsonify(error={"code": "message_not_found"}), 404
    except (ValueError, product_store.ProductStoreUnavailable):
        return jsonify(error={"code": "message_unavailable"}), 503
    return redirect(url_for("linkup_front_door"))


@app.post("/market/listings")
@web_security.login_required(api=True)
def market_listing_create():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    user = web_security.current_authenticated_user()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(str(user["id"])):
        return _rate_failure()
    try:
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
        )
        product_store.create_product(
            str(user["id"]),
            name=request.form.get("name"),
            description=request.form.get("description"),
            price=request.form.get("price"),
        )
    except ValueError as exc:
        return jsonify(error={"code": str(exc)}), 400
    except (
        public_store.PublicStoreUnavailable,
        product_store.ProductStoreUnavailable,
    ):
        return jsonify(error={"code": "market_unavailable"}), 503
    return redirect(url_for("spot_capability_front_door", capability_slug="market"))


@app.post("/sika/contributions")
@web_security.login_required(api=True)
def sika_contribution_request():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    user = web_security.current_authenticated_user()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(str(user["id"])):
        return _rate_failure()
    try:
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
        )
        workspaces.add_record(
            str(user["id"]),
            "sika",
            title=request.form.get("title"),
            body=request.form.get("body"),
            status="draft",
        )
    except ValueError as exc:
        return jsonify(error={"code": str(exc)}), 400
    except (public_store.PublicStoreUnavailable, workspaces.WorkspaceUnavailable):
        return jsonify(error={"code": "sika_unavailable"}), 503
    return redirect(url_for("spot_capability_front_door", capability_slug="sika"))


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
    return redirect("/world-cup#teams")


@app.post("/postcode-rooms")
def postcode_room():
    """Post to a bounded public postcode room without crossing My World."""

    if not web_security.csrf_valid(request):
        return _csrf_failure()
    identity_id = web_security.ensure_session_identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return _rate_failure()
    postcode = " ".join(_form_text("postcode", "", 16).upper().split())
    if len(postcode) < 2 or not postcode.replace(" ", "").isalnum():
        return jsonify(error={"code": "invalid_postcode_room"}), 400
    item = {
        "room": f"{postcode} Postcode Room",
        "name": _form_text("name", "Visitor", 80),
        "message": _form_text("message", "", 2000),
    }
    if not item["message"]:
        return jsonify(error={"code": "message_required"}), 400
    try:
        if public_store.status()["configured"]:
            public_store.add_room_message(identity_id, **item)
        else:
            _prepend_bounded(team_messages, item)
    except ValueError:
        return _rate_failure()
    except public_store.PublicStoreUnavailable:
        return _public_write_failure()
    query = urlparse.urlencode({"postcode": postcode})
    return redirect(f"/the-spot/postcode-rooms?{query}")

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
    return redirect("/world-cup#teams")

@app.get("/my-world")
@web_security.login_required(founder_only=True)
def my_world():
    user = web_security.current_authenticated_user()
    if user is None:  # pragma: no cover - decorator is the fail-closed gate
        return redirect(url_for("auth_page"))
    identity_id = str(user["id"])
    profile = {
        "nickname": str(user["name"]),
        "postcode": "",
        "borough": "",
        "county": "",
        "country": "",
        "continent": "",
    }
    try:
        if public_store.status()["configured"]:
            public_store.ensure_authenticated_user(
                identity_id,
                email=str(user["email"]),
                display_name=str(user["name"]),
                store_email=False,
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
                workspaces=workspaces.WORKSPACES,
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
            workspaces=workspaces.WORKSPACES,
            private_store_unavailable=False,
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return response


@app.get("/myworld")
@web_security.login_required(founder_only=True)
def myworld_legacy_get():
    return redirect(url_for("my_world"))


@app.post("/myworld")
@web_security.login_required(founder_only=True)
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
        "postcode": _form_text("postcode", "", 16).upper(),
        "borough": _form_text("borough", "", 120),
        "county": _form_text("county", "", 120),
        "country": _form_text("country", "", 80),
        "continent": _form_text("continent", "", 80),
    }
    try:
        if public_store.status()["configured"]:
            public_store.ensure_authenticated_user(
                identity_id,
                email=str(user["email"]),
                display_name=str(user["name"]),
                store_email=False,
            )
            public_store.update_profile(identity_id, **item)
        else:
            profiles[identity_id] = item
    except public_store.PublicStoreUnavailable:
        return _public_write_failure()
    return redirect(url_for("my_world"))


@app.get("/my-world/<workspace_id>")
@web_security.login_required(founder_only=True)
def my_world_workspace(workspace_id):
    workspace = workspaces.get(workspace_id)
    if workspace is None:
        return jsonify(error={"code": "workspace_not_found"}), 404
    user = web_security.current_authenticated_user()
    try:
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
            store_email=False,
        )
        records = workspaces.list_records(str(user["id"]), workspace_id)
    except (public_store.PublicStoreUnavailable, workspaces.WorkspaceUnavailable):
        return jsonify(error={"code": "workspace_unavailable"}), 503
    response = make_response(
        render_template(
            "workspace.html",
            workspace=workspace,
            records=records,
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return response


@app.post("/my-world/<workspace_id>/records")
@web_security.login_required(api=True, founder_only=True)
def my_world_workspace_record(workspace_id):
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    workspace = workspaces.get(workspace_id)
    if workspace is None:
        return jsonify(error={"code": "workspace_not_found"}), 404
    user = web_security.current_authenticated_user()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(str(user["id"])):
        return _rate_failure()
    try:
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
            store_email=False,
        )
        workspaces.add_record(
            str(user["id"]),
            workspace_id,
            title=_form_text("title", "", 160),
            body=_form_text("body", "", 5000),
            status=_form_text("status", "active", 16),
        )
    except ValueError as exc:
        return jsonify(error={"code": str(exc)}), 400
    except (public_store.PublicStoreUnavailable, workspaces.WorkspaceUnavailable):
        return jsonify(error={"code": "workspace_unavailable"}), 503
    return redirect(url_for("my_world_workspace", workspace_id=workspace_id))


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


def _platform_health_snapshot():
    """Return deploy health without conflating it with human/business gates."""

    database = db_status()
    auth = neon_auth.status()
    checks = {
        "database_reachable": bool(database.get("reachable")),
        "required_schema": bool(database.get("initialized")),
        "session_secret": SESSION_SECRET_CONFIGURED,
        "auth_configuration": bool(auth.get("valid")),
        "private_auth_gate": os.environ.get(
            "OAP_AUTH_REQUIRED", "false"
        ).lower()
        == "true",
    }
    return {"ready": all(checks.values()), "checks": checks}


@app.get("/livez")
def livez():
    response = jsonify(status="alive")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/healthz")
def healthz():
    """Return only the coarse health state needed by the platform."""

    platform = _platform_health_snapshot()
    response = jsonify(status="healthy" if platform["ready"] else "unavailable")
    response.headers["Cache-Control"] = "no-store"
    return response


INFRASTRUCTURE_SECTION_DEFINITIONS = (
    {"slug":"command","icon":"🏗️","name":"Infrastructure Command","features":["Overall status","Live services","System alerts","Infrastructure activity"]},
    {"slug":"database","icon":"🗄️","name":"Database","features":["Neon Postgres","Schema and migrations","HRM memory","Durable community data"]},
    {"slug":"deployment","icon":"🚀","name":"Hosting & Deployment","features":["Render service","GitHub revision","Build identity","Production mode"]},
    {"slug":"network","icon":"🌐","name":"Network","features":["Service port","API Gateway","NEXUS routing","Location providers"]},
    {"slug":"storage","icon":"💾","name":"Storage","features":["Owner-scoped workspaces","Conversation memory","Market records","SIKA ledger"]},
    {"slug":"security","icon":"🛡️","name":"Security","features":["Neon identity","Permissions","Human Authority","Guardian audit"]},
    {"slug":"performance","icon":"📈","name":"Performance","features":["Structured request timing","Bounded I/O","Rate controls","Telemetry delivery"]},
    {"slug":"services","icon":"🟢","name":"Service Health","features":["OAP World","My World","LinkUp","Market and SIKA"]},
    {"slug":"local","icon":"📱","name":"Local Infrastructure","features":["Termux","Flask services","Ollama","Offline local-first mode"]},
    {"slug":"cloud","icon":"☁️","name":"Cloud Infrastructure","features":["Neon Postgres","Render","GitHub revision","Datadog"]},
    {"slug":"monitoring","icon":"📊","name":"Logs & Monitoring","features":["Request logs","Errors","Route health","Datadog metrics"]},
    {"slug":"recovery","icon":"♻️","name":"Recovery & Maintenance","features":["Restore checkpoint","Database branches","Rollback","Incident history"]},
)


def _section_state(checks):
    values = tuple(bool(value) for value in checks.values())
    if values and all(values):
        return "LIVE"
    if any(values):
        return "DEGRADED"
    return "WAITING"


def _infrastructure_sections():
    readiness = _readiness_snapshot()
    authority_probe = authority.status()
    approval_probe = approval_service.status()
    judgement_probe = judgement.status()
    product_probe = product_store.status()
    workspace_probe = workspaces.status()
    location_probe = location_intelligence.status()
    datadog_probe = telemetry.status()
    render_live = os.environ.get("RENDER", "").lower() == "true"
    revision_present = bool(
        os.environ.get("RENDER_GIT_COMMIT")
        or os.environ.get("OAP_ENV_REVISION")
    )
    production_mode = os.environ.get("OAP_LOCAL_MODE", "false").lower() != "true"
    product_tables_ready = bool(product_probe.get("ready"))
    probe_sets = {
        "command": {
            "database": readiness["checks"]["database_initialized"],
            "identity": authority_probe["active_level_zero"],
            "judgement": judgement_probe["schema_ready"],
            "services": product_tables_ready,
        },
        "database": {
            "reachable": readiness["database"].get("reachable", False),
            "migration": readiness["checks"]["database_initialized"],
            "community": readiness["checks"]["durable_public_store"],
            "judgement_schema": judgement_probe["schema_ready"],
        },
        "deployment": {
            "render": render_live,
            "revision": revision_present,
            "production": production_mode,
        },
        "network": {
            "nexus": readiness["smi"]["checks"].get("nexus", False),
            "chat_route": readiness["smi"]["checks"].get("chat_route", False),
            "location_providers": location_probe["ready"],
        },
        "storage": {
            "workspaces": workspace_probe["ready"],
            "conversation_memory": readiness["smi"]["checks"].get("conversation_memory", False),
            "product_tables": product_tables_ready,
        },
        "security": {
            "auth": readiness["checks"]["neon_auth_configured"],
            "private_gate": readiness["checks"]["private_auth_required"],
            "human_authority": authority_probe["ready"],
            "approval_receipt": approval_probe["ready"],
            "audit": readiness["smi"]["checks"].get("audit", False),
        },
        "performance": {
            "request_logs": readiness["checks"]["structured_request_logs"],
            "rate_controls": readiness["checks"]["bounded_rate_controls"],
            "bounded_provider_io": True,
            "telemetry_delivery": datadog_probe["delivery_verified"],
        },
        "services": {
            "world": True,
            "my_world": workspace_probe["ready"],
            "linkup_market_sika": product_tables_ready,
            "smi": readiness["checks"]["smi_3x7_ready"],
        },
        "local": {
            "flask": True,
            "local_first_supported": True,
            "mode_declared": os.environ.get("OAP_LOCAL_MODE", "").lower()
            in {"true", "false"},
        },
        "cloud": {
            "neon": readiness["database"].get("reachable", False),
            "render": render_live,
            "revision": revision_present,
            "datadog": datadog_probe["ready"],
        },
        "monitoring": {
            "structured_logs": readiness["checks"]["structured_request_logs"],
            "request_ids": True,
            "datadog": datadog_probe["ready"],
        },
        "recovery": {
            "checkpoint": bool(os.environ.get("OAP_RECOVERY_CHECKPOINT", "").strip()),
            "rollback_revision": revision_present,
        },
    }
    sections = []
    for definition in INFRASTRUCTURE_SECTION_DEFINITIONS:
        checks = probe_sets[definition["slug"]]
        state = _section_state(checks)
        if state == "LIVE" and definition["slug"] in {"local", "recovery"}:
            state = "READY"
        sections.append(
            {
                **definition,
                "status": state,
                "checks": checks,
                "passed": sum(bool(value) for value in checks.values()),
                "total": len(checks),
            }
        )
    return sections


@app.get("/infrastructure")
@web_security.login_required(founder_only=True)
def infrastructure_dashboard():
    sections = _infrastructure_sections()
    return render_template("infrastructure.html", sections=[
        dict(section, href=url_for("infrastructure_section", section=section["slug"]))
        for section in sections
    ], green=sum(item["status"] in {"LIVE", "READY"} for item in sections), total=len(sections))


@app.get("/infrastructure/<section>")
@web_security.login_required(api=True, founder_only=True)
def infrastructure_section(section):
    selected = next((item for item in _infrastructure_sections() if item["slug"] == section), None)
    if selected is None:
        return jsonify(status="not_found", section=section), 404
    checks = {
        **selected["checks"],
        "route": True,
        "human_authority_final": True,
    }
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
@web_security.login_required(api=True, founder_only=True)
def infrastructure_status():
    readiness = _readiness_snapshot()
    sections = _infrastructure_sections()
    ready = all(item["status"] in {"LIVE", "READY"} for item in sections)
    return jsonify(
        status="live" if ready else "degraded",
        count=len(sections),
        live=sum(item["status"] == "LIVE" for item in sections),
        ready=sum(item["status"] == "READY" for item in sections),
        degraded=sum(item["status"] == "DEGRADED" for item in sections),
        waiting=sum(item["status"] == "WAITING" for item in sections),
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
        sections=sections,
        governance={"human_authority_final":True},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
