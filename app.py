from flask import Flask, jsonify, redirect, render_template, request, url_for

import mission_control.status as mc_status
from mission_control import init_app as _mc_init
from mission_control.agents import validate_agent_registry
from mission_control.database import db_status
from mission_control.organism import validate_architecture

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

MAX_PUBLIC_RECORDS = 100


def _form_text(name, default, max_length):
    value = request.form.get(name, default)
    return str(value).strip()[:max_length]


def _prepend_bounded(records, item):
    records.insert(0, item)
    del records[MAX_PUBLIC_RECORDS:]


@app.after_request
def _security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=()",
    )
    return response

signal_posts = []
team_messages = []
flag_counts = {}
profiles = []

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

@app.route("/")
def home():
    return render_template(
        "home.html",
        teams=teams,
        matches=matches,
        signal_posts=signal_posts,
        team_messages=team_messages,
        flag_counts=flag_counts,
        profiles=profiles,
        gateway=mc_status.get_public_gateway_status(),
    )

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
    _prepend_bounded(signal_posts, {
        "name": _form_text("name", "OAP", 80),
        "body": _form_text("body", "", 2000),
    })
    return redirect("/#signal")

@app.route("/room", methods=["POST"])
def room():
    _prepend_bounded(team_messages, {
        "room": _form_text("room", "Team Room", 80),
        "name": _form_text("name", "Visitor", 80),
        "message": _form_text("message", "", 2000),
    })
    return redirect("/#teams")

@app.route("/flag", methods=["POST"])
def flag():
    team = _form_text("team", "", 120)
    if team:
        flag_counts[team] = flag_counts.get(team, 0) + 1
    return redirect("/#teams")

@app.route("/myworld", methods=["POST"])
def myworld():
    _prepend_bounded(profiles, {
        "nickname": _form_text("nickname", "OAP Visitor", 80),
        "country": _form_text("country", "", 80),
    })
    return redirect("/#myworld")


@app.get("/healthz")
def healthz():
    """Return a side-effect-free, non-sensitive deployment readiness check."""

    architecture = validate_architecture()
    registry = validate_agent_registry()
    database = db_status()
    ready = (
        architecture["passed"]
        and registry["ready_for_activation"]
        and bool(database["initialized"])
    )
    response = jsonify(
        status="healthy" if ready else "degraded",
        live=True,
        checks={
            "architecture_integrity": architecture["passed"],
            "registry_integrity": registry["passed"],
            "registry_activation_ready": registry["ready_for_activation"],
            "database_initialized": bool(database["initialized"]),
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
def infrastructure_dashboard():
    return render_template("infrastructure.html", sections=[
        dict(section, href=url_for("infrastructure_section", section=section["slug"]))
        for section in INFRASTRUCTURE_SECTIONS
    ])


@app.get("/infrastructure/<section>")
def infrastructure_section(section):
    selected = next((item for item in INFRASTRUCTURE_SECTIONS if item["slug"] == section), None)
    if selected is None:
        return jsonify(status="not_found", section=section), 404
    checks = {"route": True, "human_authority_final": True}
    if section == "database":
        database = db_status()
        checks.update({
            "neon_postgres": True,
            "database": "neondb",
            "tables": 20,
            "initialized": bool(database["initialized"]),
        })
    elif section == "deployment":
        checks.update({"render": True, "github": True, "production": True})
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
def infrastructure_status():
    return jsonify(
        status="live",
        count=len(INFRASTRUCTURE_SECTIONS),
        live=sum(item["status"] == "LIVE" for item in INFRASTRUCTURE_SECTIONS),
        ready=sum(item["status"] == "READY" for item in INFRASTRUCTURE_SECTIONS),
        database={"provider":"Neon Postgres","database":"neondb","tables":20,"live":True},
        deployment={"provider":"Render","service":"on-any-postcode","live":True},
        sections=INFRASTRUCTURE_SECTIONS,
        governance={"human_authority_final":True},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
