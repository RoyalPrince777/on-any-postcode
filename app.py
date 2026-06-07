from flask import Flask, request, redirect, session
from datetime import datetime
import os
import sqlite3
from html import escape

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "OAP-CHANGE-THIS-777")
DB = "oap_architecture_v12.db"

SYSTEMS = {
    "world": ("🌍 OAP World", "One public front door."),
    "identity": ("👤 My World", "One identity hub."),
    "intelligence": ("🧠 Intelligence", "HRM, Review Core, Agents, Command."),
    "money": ("💎 Money / SIKA", "SIKA records, wallet readiness, finance readiness."),
    "communications": ("📧 Communications", "Mail, messenger, notifications."),
    "infrastructure": ("🗺 Infrastructure", "Weather, maps, navigation, connectivity, eSIM readiness."),
    "operations": ("🚚 Operations", "Bookings, delivery, riders, drivers, businesses, creators, experiences."),
    "culture": ("🎭 Culture", "Music, media, sports, education, countries, international song."),
    "trust": ("🛡 Trust", "Privacy, safety, compliance, verification, audit."),
}

MODULES = {
    "world": ["OAP Signals", "Experiences", "Explorer", "Country Spaces", "World Cup 2026", "Community Power", "OAP Movement", "Legacy Makers"],
    "identity": ["Join OAP", "Enter My World", "Profile", "Family Tree", "Awards", "Verification", "SIKA Records"],
    "intelligence": ["HRM", "Review Core", "Agents", "Neo Team", "Animal Team", "Command Center", "Risk Register", "Decision Log"],
    "money": ["SIKA Dashboard", "Contribution Records", "Trust Records", "Wallet Readiness", "Card Readiness", "Deposit Requests", "Finance Compliance"],
    "communications": ["Mail", "Messenger", "Inbox", "Contacts", "Notifications", "Broadcasts"],
    "infrastructure": ["Weather", "Navigation", "Maps", "OAP Connect", "eSIM Requests", "WiFi", "Coverage", "Devices"],
    "operations": ["Business Network", "Creator Hub", "Experiences", "Delivery Bookings", "Riders", "Drivers", "Dispatch", "Transport"],
    "culture": ["Music", "Media", "International Song", "Sports", "World Cup", "Real Education", "KORADASO", "Akan", "Begoro"],
    "trust": ["Privacy Promise", "Youth Safety", "Compliance Tracker", "Verification Badges", "Audit Logs", "Review Queue"],
}

TRANSPORT = [
    "Walking", "Bicycle", "E-Bike", "Scooter", "Motorcycle", "Car",
    "Taxi Request", "Van", "Truck", "Bus", "Tram", "Train",
    "Underground", "Ferry", "Ship", "Flight", "Helicopter"
]

AGENTS = [
    "Neo", "Morpheus", "Trinity", "Oracle", "Architect", "Keymaker",
    "Tank", "Dozer", "Seraph", "Bee", "Lion", "Tiger",
    "Elephant", "Owl", "Panther", "Dolphin", "Horse", "Stag"
]

TEAMS = [
("algeria","🇩🇿 Algeria"),
("argentina","🇦🇷 Argentina"),
("australia","🇦🇺 Australia"),
("belgium","🇧🇪 Belgium"),
("brazil","🇧🇷 Brazil"),
("cameroon","🇨🇲 Cameroon"),
("canada","🇨🇦 Canada"),
("colombia","🇨🇴 Colombia"),
("costa-rica","🇨🇷 Costa Rica"),
("croatia","🇭🇷 Croatia"),
("denmark","🇩🇰 Denmark"),
("ecuador","🇪🇨 Ecuador"),
("egypt","🇪🇬 Egypt"),
("england","🏴󠁧󠁢󠁥󠁮󠁧󠁿 England"),
("france","🇫🇷 France"),
("germany","🇩🇪 Germany"),
("ghana","🇬🇭 Ghana"),
("iran","🇮🇷 Iran"),
("iraq","🇮🇶 Iraq"),
("italy","🇮🇹 Italy"),
("ivory-coast","🇨🇮 Ivory Coast"),
("jamaica","🇯🇲 Jamaica"),
("japan","🇯🇵 Japan"),
("mali","🇲🇱 Mali"),
("mexico","🇲🇽 Mexico"),
("morocco","🇲🇦 Morocco"),
("netherlands","🇳🇱 Netherlands"),
("new-zealand","🇳🇿 New Zealand"),
("nigeria","🇳🇬 Nigeria"),
("panama","🇵🇦 Panama"),
("paraguay","🇵🇾 Paraguay"),
("poland","🇵🇱 Poland"),
("portugal","🇵🇹 Portugal"),
("qatar","🇶🇦 Qatar"),
("saudi-arabia","🇸🇦 Saudi Arabia"),
("senegal","🇸🇳 Senegal"),
("serbia","🇷🇸 Serbia"),
("south-africa","🇿🇦 South Africa"),
("south-korea","🇰🇷 South Korea"),
("spain","🇪🇸 Spain"),
("switzerland","🇨🇭 Switzerland"),
("tunisia","🇹🇳 Tunisia"),
("ukraine","🇺🇦 Ukraine"),
("uruguay","🇺🇾 Uruguay"),
("usa","🇺🇸 USA"),
("uzbekistan","🇺🇿 Uzbekistan"),
("venezuela","🇻🇪 Venezuela"),
]
CONTINENTS = [
("africa","🌍 Africa"),
("europe","🌍 Europe"),
("asia","🌏 Asia"),
("north-america","🌎 North America"),
("south-america","🌎 South America"),
("caribbean","🏝 Caribbean"),
("oceania","🌊 Oceania")
]
OAP_FLAG_NUMBER = 13
OAP_FLAG_LINE = "13 = OAP Flag / Crown Signal"

COUNCIL_AGENTS = [
    ("🙏 God Layer", "Highest values: truth, protection, dignity, purpose."),
    ("👑 Founder / Sovereign Veto", "Final decision maker. Approves or stops major moves."),
    ("📜 Chancellor", "Governance, lawful wording, rules, compliance and public claims."),
    ("🛡 Guardian", "Safety, privacy, youth protection, risk checks and trust."),
    ("🏗 Architect", "System structure, routes, tables, performance and clean code."),
    ("📚 Archivist", "History, records, decisions, lessons and long-term memory."),
    ("🧠 HRM", "Memory engine. Logs actions, risks, builds, fixes and learning."),
    ("🤖 Ollama / Local AI", "Private summariser. Reads HRM records and recommends next moves."),

    ("GPT", "Chief Architect and coding partner."),
    ("Claude", "Chancellor and governance reviewer."),
    ("Gemini", "Archivist and broad research memory."),
    ("Kimi", "Expansion strategist and long-context planner."),
    ("Grok", "Challenger and stress tester."),
    ("Edge / Copilot", "Web operator and browser workflow helper."),

    ("🕶 Neo", "Execution, action and build momentum."),
    ("🧠 Morpheus", "Strategy, belief and direction."),
    ("⚔️ Trinity", "Operations, precision and mission flow."),
    ("🔮 Oracle", "Insight, patterns and warnings."),
    ("🏗 Matrix Architect", "Deep structure, systems and route design."),
    ("🗝 Keymaker", "Access, links, routes and unlocks."),
    ("🛡 Seraph", "Security, privacy and protection."),
    ("📦 Tank", "Infrastructure, runtime and local systems."),
    ("🔧 Dozer", "Backup, recovery and support."),

    ("🐝 Bee", "Collects missing data, fixtures, players, tasks and source checks."),
    ("🐘 Elephant", "Memory, history, records and lessons."),
    ("🦉 Owl", "Wisdom, judgement, timing and review."),
    ("🦍 Gorilla", "Protection, resilience and strength."),
    ("🦁 Lion", "Leadership, standards and courage."),
    ("🐅 Tiger", "Focus, execution and next action."),
    ("🐆 Panther", "Adaptation, stealth and fast changes."),
    ("🦅 Eagle", "Vision, roadmap and future scanning."),
    ("🐬 Dolphin", "Communication, public wording and community signals."),
    ("🐎 Horse", "Movement, operations and momentum."),
    ("🦌 Stag", "Balance, harmony and long-term alignment.")
]
def now():
    return datetime.utcnow().isoformat(timespec="seconds")


def safe(v):
    return escape((v or "").strip())


def slug(v):
    return (
        v.lower()
        .replace("&", "and")
        .replace("/", "-")
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
    )


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init():
    con = db()

    con.execute("""
CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        postcode TEXT,
        borough TEXT,
        county TEXT,
        country TEXT,
        continent TEXT,
        circle TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system TEXT,
        module TEXT,
        title TEXT,
        name TEXT,
        location TEXT,
        category TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)
    con.execute("""
CREATE TABLE IF NOT EXISTS community_power(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member TEXT,
    mission TEXT,
    category TEXT,
    points INTEGER,
    created_at TEXT
)
""")
    con.execute("""
CREATE TABLE IF NOT EXISTS businesses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        location TEXT,
        contact TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS creators(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        country TEXT,
        link TEXT,
        bio TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS experiences(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        location TEXT,
        date_note TEXT,
        category TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS delivery_bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        pickup TEXT,
        dropoff TEXT,
        item TEXT,
        transport TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS riders_drivers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        role TEXT,
        vehicle TEXT,
        area TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS sika_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        record_type TEXT,
        value_note TEXT,
        points INTEGER,
        status TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS verification_badges(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        level TEXT,
        location TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS readiness_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT,
        request_type TEXT,
        applicant TEXT,
        location TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        detail TEXT,
        created_at TEXT
    )
    """)
    con.commit()
    con.close()

init()


def audit(action, detail):
    con = db()
    con.execute(
        "INSERT INTO audit(action,detail,created_at) VALUES(?,?,?)",
        (action, detail, now())
    )
    con.commit()
    con.close()


def nav():
    links = "<a href='/'>Home</a>"
    links += "".join([f"<a href='/{k}'>{v[0]}</a>" for k, v in SYSTEMS.items()])
    links += "<a href='/world-cup'>⚽ World Cup</a>"
    links += "<a href='/command'>🎛 Command</a>"
    return links


def layout(title, body):
    return f"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root {{
  --gold:#d4af37;
  --line:#6d5520;
  --text:#f7f0dd;
  --muted:#c9b987;
  --green:#52d98f;
  --blue:#00eaff;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  background:radial-gradient(circle at top,#161616,#050505 55%,#000);
  color:var(--text);
  font-family:Arial,Helvetica,sans-serif;
}}
header {{
  position:sticky;
  top:0;
  z-index:9;
  background:#050505ee;
  border-bottom:1px solid var(--gold);
  padding:14px;
}}
.brand {{
  font-family:Impact,Arial Black,sans-serif;
  color:var(--gold);
  font-size:26px;
  letter-spacing:3px;
  text-transform:uppercase;
}}
.tag {{
  color:var(--muted);
  font-size:13px;
  letter-spacing:1px;
}}
nav {{
  display:flex;
  gap:8px;
  overflow:auto;
  padding-top:10px;
}}
nav a,.btn {{
  white-space:nowrap;
  text-decoration:none;
  color:var(--text);
  background:#111;
  border:1px solid var(--line);
  border-radius:999px;
  padding:9px 12px;
  font-weight:900;
}}
main,footer {{
  max-width:1200px;
  margin:auto;
  padding:18px;
}}
.hero {{
  background:linear-gradient(135deg,#090909,#161616,#123c52);
  border:1px solid var(--gold);
  border-radius:26px;
  padding:26px;
  margin-bottom:16px;
  box-shadow:0 0 30px #d4af3738;
}}
.grid {{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:14px;
}}
.card {{
  display:block;
  background:linear-gradient(160deg,#090909,#111);
  border:1px solid var(--line);
  border-radius:20px;
  padding:18px;
  color:var(--text);
  text-decoration:none;
}}
.metric {{
  font-size:32px;
  color:var(--gold);
  font-weight:900;
}}
.green {{ color:var(--green); font-weight:900; }}
.neon {{ color:var(--blue); text-shadow:0 0 12px var(--blue); }}
input,select,textarea,button {{
  width:100%;
  padding:12px;
  margin:6px 0;
  border-radius:14px;
  border:1px solid var(--line);
  background:#050505;
  color:var(--text);
  font-size:15px;
}}
button {{
  background:#1d8f5f;
  font-weight:900;
}}
table {{
  width:100%;
  border-collapse:collapse;
  background:#101010;
  border-radius:18px;
  overflow:hidden;
  margin-top:14px;
}}
td,th {{
  border-bottom:1px solid var(--line);
  padding:10px;
  text-align:left;
  vertical-align:top;
}}
.warn {{
  background:#2c2108;
  border:1px solid var(--gold);
  border-radius:18px;
  padding:14px;
  margin:12px 0;
}}
</style>
</head>
<body>
<header>
  <div class="brand">ON ANY POSTCODE 🌍👑</div>
  <div class="tag">One Brand. One Front Door. One Identity. Born Local. Built Global.</div>
  <nav>{nav()}</nav>
</header>
<main>{body}</main>
<footer>
  🌍 ON ANY POSTCODE — Born Local. Built Global. EARTH IS OUR TURF. One Race. Human Race.
</footer>
</body>
</html>"""


def get_records(system=None, module=None):
    con = db()
    if system and module:
        rows = con.execute(
            "SELECT * FROM records WHERE system=? AND module=? ORDER BY id DESC LIMIT 50",
            (system, module)
        ).fetchall()
    elif system:
        rows = con.execute(
            "SELECT * FROM records WHERE system=? ORDER BY id DESC LIMIT 50",
            (system,)
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT * FROM records ORDER BY id DESC LIMIT 80"
        ).fetchall()
    con.close()
    return rows


def record_table(rows):
    if not rows:
        return "<div class='card'><h2>Open</h2><p>This space is live and ready for the first post.</p></div>"

    body = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['system']}</td><td>{r['module']}</td><td>{r['title']}</td><td>{r['status']}</td><td>{r['notes']}</td></tr>"
        for r in rows
    ])

    return f"""
<table>
<tr><th>Time</th><th>System</th><th>Module</th><th>Title</th><th>Status</th><th>Notes</th></tr>
{body}
</table>
"""

def contribution_form(system, module="General"):
    return ""

@app.route("/")
def home():
    cards = "".join([
        f"<a class='card' href='/{k}'><h2>{v[0]}</h2><p>{v[1]}</p></a>"
        for k, v in SYSTEMS.items()
    ])

    body = f"""
<section class="hero">
<h1>OAP Architecture v12 💎</h1>
<h2>One Brand. One Front Door. One Identity.</h2>
<p><b>Separate Intelligence.</b> Separate Money. Separate Communications. Separate Infrastructure. Separate Operations.</p>
<p><b>EARTH IS OUR TURF.</b> One Race. Human Race.</p>
<div class="warn">
Banking, deposits, cards, e-money, telecom/eSIM activation, taxi/private-hire and regulated payments are routed as readiness/request records until lawful authorisation or provider backing is confirmed.
</div>
</section>

<section class="grid">
<div class="card"><div class="metric">⚡</div><h2>Community</h2></div>
<div class="card"><div class="metric">💎</div><h2>Culture</h2></div>
<div class="card"><div class="metric">🤝</div><h2>Business</h2></div>
<div class="card"><div class="metric">🏆</div><h2>Events</h2></div>
<div class="card"><div class="metric">🚚</div><h2>Operations Ready</h2></div>
<div class="card"><div class="metric">📶</div><h2>Infrastructure Ready</h2></div>
<div class="card"><div class="metric">🧠</div><h2>Intelligence Ready</h2></div>
<div class="card"><div class="metric">🛡</div><h2>Review Protected</h2></div>
</section>

<h2>Systems</h2>
<section class="grid">{cards}</section>
"""
    return layout("OAP Architecture v12", body)

@app.route("/<system>")
def system_page(system):
    if system == "command":
        return command()

    data = SYSTEMS.get(system)
    if not data:
        return layout("Not Found", "<section class='hero'><h1>System not found</h1></section>")

    modules = MODULES.get(system, [])
    cards = "".join([
        f"<a class='card' href='/{system}/{slug(m)}'><h2>{m}</h2><p>{data[0]} module.</p></a>"
        for m in modules
    ])

    return layout(
        data[0],
        f"<section class='hero'><h1>{data[0]}</h1><p>{data[1]}</p></section>"
        f"<section class='grid'>{cards}</section>"
    )

@app.route("/<system>/<module>")
def module_page(system, module):
    title = module.replace("-", " ").title()
    return layout(
        title,
        f"<section class='hero'><h1>{title}</h1><p>{system.title()} module.</p></section>"
        f"<div class='card'><h2>Coming next</h2><p>This page is being shaped into a simple OAP experience.</p></div>"
)

def special_forms(system):
    forms = ""
    if system == "operations":
        forms += business_form()
        forms += creator_form()
        forms += experience_form()
        forms += delivery_form()
        forms += rider_driver_form()

    if system == "money":
        forms += sika_form()
        forms += readiness_form("Finance / Bank / Card / Deposit")

    if system == "infrastructure":
        forms += readiness_form("eSIM / Weather / Navigation / Connectivity")

    if system == "identity":
        forms += verification_form()

    return forms


def business_form():
    return """
<div class="card">
<h2>🏪 Add Business</h2>
<form method="post" action="/add-business">
<input name="name" placeholder="Business name" required>
<input name="category" placeholder="Category">
<input name="location" placeholder="Postcode / area">
<input name="contact" placeholder="Phone / email / link">
<select name="status">
<option>Request Recorded</option>
<option>Review</option>
<option>Approved</option>
</select>
<textarea name="notes" placeholder="Notes"></textarea>
<button>Business Connected</button>
</form>
</div>
"""


def creator_form():
    return """
<div class="card">
<h2>👤 Add Creator</h2>
<form method="post" action="/add-creator">
<input name="name" placeholder="Creator name" required>
<input name="category" placeholder="Music / comedy / sport / education">
<input name="country" placeholder="Country">
<input name="link" placeholder="Link">
<textarea name="bio" placeholder="Bio"></textarea>
<button>Creator Connected</button>
</form>
</div>
"""


def experience_form():
    return """
<div class="card">
<h2>🎪 Add Experience</h2>
<form method="post" action="/add-experience">
<input name="title" placeholder="Experience title">
<input name="location" placeholder="Location">
<input name="date_note" placeholder="Date / note">
<input name="category" placeholder="Watch party / comedy / meetup">
<textarea name="notes" placeholder="Notes"></textarea>
<button>Experience Created</button>
</form>
</div>
"""


def delivery_form():
    opts = "".join([f"<option>{t}</option>" for t in TRANSPORT])
    return f"""
<div class="card">
<h2>🚚 Delivery / Booking</h2>
<form method="post" action="/add-delivery">
<input name="customer" placeholder="Customer / request name">
<input name="pickup" placeholder="Pickup">
<input name="dropoff" placeholder="Dropoff">
<input name="item" placeholder="Item / booking">
<select name="transport">{opts}</select>
<select name="status">
<option>Request Recorded</option>
<option>Review</option>
<option>Accepted</option>
<option>Collected</option>
<option>In Transit</option>
<option>Delivered</option>
</select>
<textarea name="notes" placeholder="Notes"></textarea>
<button>Booking Recorded</button>
</form>
</div>
"""


def rider_driver_form():
    opts = "".join([f"<option>{t}</option>" for t in TRANSPORT])
    return f"""
<div class="card">
<h2>🛵 Rider / Driver</h2>
<form method="post" action="/add-rider-driver">
<input name="name" placeholder="Name">
<select name="role">
<option>Rider</option>
<option>Driver</option>
<option>Courier</option>
<option>Volunteer</option>
</select>
<select name="vehicle">{opts}</select>
<input name="area" placeholder="Area / postcode">
<select name="status">
<option>Request Recorded</option>
<option>Review</option>
<option>Available</option>
<option>Active</option>
</select>
<textarea name="notes" placeholder="Notes"></textarea>
<button>Rider / Driver Recorded</button>
</form>
</div>
"""


def sika_form():
    return """
<div class="card">
<h2>💎 SIKA Record</h2>
<form method="post" action="/add-sika">
<input name="name" placeholder="Name">
<select name="record_type">
<option>Contribution Recorded</option>
<option>Trust Earned</option>
<option>Value Manifested</option>
<option>Legacy Recorded</option>
</select>
<input name="value_note" placeholder="Value note">
<input name="points" type="number" value="1">
<select name="status">
<option>Recorded</option>
<option>Review</option>
<option>Approved</option>
</select>
<textarea name="notes"></textarea>
<button>SIKA Recorded</button>
</form>
</div>
"""


def verification_form():
    return """
<div class="card">
<h2>🏅 Verification Request</h2>
<form method="post" action="/add-verification">
<input name="name" placeholder="Name">
<select name="level">
<option>Postcode</option>
<option>Borough</option>
<option>County</option>
<option>Country</option>
<option>Continent</option>
<option>Global</option>
<option>Planet</option>
<option>Universe</option>
</select>
<input name="location" placeholder="Location">
<select name="status">
<option>Request Recorded</option>
<option>Review</option>
<option>Approved</option>
</select>
<textarea name="notes"></textarea>
<button>Verification Recorded</button>
</form>
</div>
"""


def readiness_form(area):
    return f"""
<div class="card">
<h2>🛡 {area} Request</h2>
<form method="post" action="/add-readiness">
<input type="hidden" name="area" value="{area}">
<input name="request_type" placeholder="Deposit / card / eSIM / taxi / provider / compliance">
<input name="applicant" placeholder="Applicant / business / person">
<input name="location" placeholder="Location">
<select name="status">
<option>Request Recorded</option>
<option>Compliance Review</option>
<option>Provider Check</option>
<option>Manual Approval Needed</option>
<option>Blocked</option>
</select>
<textarea name="notes" placeholder="Legal/provider/compliance notes"></textarea>
<button>Request Recorded</button>
</form>
</div>
"""

@app.route("/world/country-spaces")
def country_spaces():
    cards = "".join([
        f"<a class='card' href='/world/country-spaces/{s}'><h2>{n}</h2><p>Country spaces, culture and World Cup links.</p></a>"
        for s, n in CONTINENTS
    ])

    return layout(
        "Country Spaces",
        f"""
<section class='hero'>
<h1>🌍 Country Spaces</h1>
<p>Postcode → Country → Continent → World.</p>
</section>
<section class='grid'>{cards}</section>
"""
)

@app.route("/world-cup")
def worldcup():
    cards = "".join([
        f"<a class='card' href='/world-cup/team/{s}'><h2>{n}</h2><p>⚽ Team hub ready</p></a>"
        for s, n in TEAMS
    ])

    return layout(
        "World Cup",
        f"""
<section class='hero'>
<h1>⚽ World Cup</h1>
<p>48-team structure. Community voice. Watch parties. No gambling.</p>
</section>
<section class='grid'>{cards}</section>
"""
    )


@app.route("/world-cup/team/<team>")
def team(team):
    team_name = dict(TEAMS).get(team, team)

    features = [
        "⚡ Match Signals",
        "🎵 National Anthem",
        "🎭 Culture",
        "🎪 Watch Parties",
        "🏪 Business Offers",
        "👤 Creator Reactions",
        "🏆 Awards",
        "📊 Fixtures / Results",
        "🧠 HRM Notes"
    ]

    cards = "".join([
        f"<div class='card'><h2>{f}</h2><p>{team_name} World Cup layer.</p></div>"
        for f in features
    ])

    return layout(
        team_name,
        f"""
<section class='hero'>
<h1>{team_name}</h1>
<p>World Cup 2026 team hub.</p>
</section>

<section class='grid'>
{cards}
</section>
"""
)

@app.route("/hrm/local-ai")
def hrm_local_ai():
    logs = "".join([
        f"<div class='card'><h2>{x}</h2><p>Ready for HRM records.</p></div>"
        for x in HRM_LOG_TYPES
    ])

    summary = "".join([
        f"<div class='card'><h2>{x}</h2><p>Waiting for real OAP records.</p></div>"
        for x in LOCAL_AI_SUMMARY_FIELDS
    ])

    return layout(
        "HRM Local AI",
        f"""
<section class='hero'>
<h1>🧠 HRM Local AI</h1>
<p>Memory first. Local AI summaries later. Human approval before action.</p>
</section>

<h2>🧠 HRM Logs</h2>
<section class='grid'>{logs}</section>

<h2>🤖 Local AI Summary</h2>
<section class='grid'>{summary}</section>
"""
)
@app.route("/world-cup/match/<home>/<away>")
def match_command(home, away):
    home_name = dict(TEAMS).get(home, home)
    away_name = dict(TEAMS).get(away, away)

    tabs = [
        "🏟 Stadium",
        "⚔️ Pitch",
        "⚽ Fixtures",
        "👔 Manager",
        "👥 Squad",
        "🎵 Anthem",
        "🎭 Culture",
        "🎪 Watch Parties",
        "🏪 Business",
        "👤 Creators",
        "🏆 Awards",
        "🧠 HRM"
    ]

    tab_cards = "".join([
        f"<div class='card'><h2>{tab}</h2><p>{home_name} vs {away_name} board.</p></div>"
        for tab in tabs
    ])

    pitch = f"""
<div class='card'>
<h2>⚔️ Versus Pitch Board</h2>
<pre style='white-space:pre-wrap;text-align:center;font-size:14px;line-height:1.45'>
{away_name}

      ST         ST

LW                     RW

      CM     CM

         CM

LB  CB   CB   RB

════════ VS ════════

LB  CB   CB   RB

         CM

      CM     CM

LW                     RW

         ST

{home_name}
</pre>
</div>
"""

    return layout(
        f"{home_name} vs {away_name}",
        f"""
<section class='hero'>
<h1>⚔️ {home_name} vs {away_name}</h1>
<p>Match Command Center. Stadium, pitch, fixtures, manager, squad, anthem, culture, business and HRM.</p>
</section>
{pitch}
<section class='grid'>{tab_cards}</section>
"""
)

@app.route("/hrm/council")
def hrm_council():
    cards = "".join([
        f"<div class='card'><h2>{name}</h2><p>{role}</p></div>"
        for name, role in COUNCIL_AGENTS
    ])

    return layout(
        "HRM Council",
        f"""
<section class='hero'>
<h1>👑 HRM Council</h1>
<p>God layer, founder approval, advice agents, Neo team, animal team, HRM memory and Local AI.</p>
</section>

<section class='grid'>
{cards}
</section>

<div class='card'>
<h2>Build Law</h2>
<p>Bee collects. HRM records. Local AI summarises. Council reviews. Founder approves.</p>
</div>
"""
    )

@app.route("/oap-world")
def oap_world_hub():
    links = [
        ("💬 Messenger", "/messenger", "Messages, inbox and community contact."),
        ("⚡ OAP Signals", "/world/oap-signals", "Community updates and movement signals."),
        ("🎪 Experiences", "/world/experiences", "Events, gatherings and matchday energy."),
        ("🏪 Business", "/operations/business-network", "Local business board."),
        ("👤 Creators", "/operations/creator-hub", "Creator activity and promotion."),
        ("⚽ World Cup", "/world-cup", "Teams, fixtures and match command."),
        ("🧠 HRM", "/hrm/local-ai", "Memory, learning and local AI summaries."),
        ("👑 Council", "/hrm/council", "Agents, council and build law.")
    ]

    cards = "".join([
        f"<a class='card' href='{url}'><h2>{title}</h2><p>{desc}</p></a>"
        for title, url, desc in links
    ])

    return layout(
        "OAP World",
        f"""
<section class='hero'>
<h1>🌍 OAP World</h1>
<p>Born Local. Built Global. Community, messages, signals, creators, business, World Cup and HRM.</p>
</section>
<section class='grid'>{cards}</section>
"""
    )


@app.route("/messenger")
def messenger():
    con = db()
    rows = con.execute(
        "SELECT * FROM records WHERE system='communications' AND module='Messenger' ORDER BY id DESC LIMIT 20"
    ).fetchall()
    con.close()

    messages = "".join([
        f"""
<div class='card'>
<h2>{r['title']}</h2>
<p><b>From:</b> {r['name'] or 'OAP Member'}</p>
<p><b>Area:</b> {r['location'] or 'OAP World'}</p>
<p>{r['notes'] or ''}</p>
<p><small>{r['created_at']}</small></p>
</div>
"""
        for r in rows
    ]) or "<div class='card'><h2>Inbox Open</h2><p>No messages yet. First message starts the network.</p></div>"

    form = """
<div class='card'>
<h2>✉️ New Message</h2>
<form method='post' action='/add-record'>
<input type='hidden' name='system' value='communications'>
<input type='hidden' name='module' value='Messenger'>
<input name='title' placeholder='Subject' required>
<input name='name' placeholder='Your name / username'>
<input name='location' placeholder='Postcode / borough / country'>
<input type='hidden' name='category' value='Message'>
<select name='status'>
<option>Open</option>
<option>Important</option>
<option>Reply Needed</option>
</select>
<textarea name='notes' placeholder='Write message'></textarea>
<button type='submit'>Send Message</button>
</form>
</div>
"""

    return layout(
        "Messenger",
        f"""
<section class='hero'>
<h1>💬 OAP Messenger</h1>
<p>Simple member messaging board. Private inbox later. Community messages now.</p>
</section>
{form}
<h2>📥 Inbox</h2>
<section class='grid'>{messages}</section>
"""
)

@app.route("/world-cup/tournament")
def worldcup_tournament():
    sections = [
        ("📊 Group Tables", "12 groups. P W D L GF GA GD PTS."),
        ("⚽ Fixtures", "Upcoming, live and completed matches."),
        ("🔥 Knockout Stage", "Round of 32 to semi-finals."),
        ("🥉 Third Place", "Third place match board."),
        ("👑 Final", "World Cup final command board."),
        ("🏟 Stadiums", "Host cities, stadiums, capacity and weather."),
        ("🧠 HRM Notes", "Tournament signals, lessons, risks and memory.")
    ]

    cards = "".join([
        f"<div class='card'><h2>{title}</h2><p>{desc}</p></div>"
        for title, desc in sections
    ])

    return layout(
        "Tournament Center",
        f"""
<section class='hero'>
<h1>🏆 World Cup Tournament Center</h1>
<p>Groups, tables, fixtures, knockouts, stadiums, final and HRM tournament memory.</p>
</section>

<section class='grid'>
{cards}
</section>
"""
)

@app.route("/add-record", methods=["POST"])
def add_record():
    vals = (
        safe(request.form.get("system")),
        safe(request.form.get("module")),
        safe(request.form.get("title")),
        safe(request.form.get("name")),
        safe(request.form.get("location")),
        safe(request.form.get("category")),
        safe(request.form.get("status")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO records(system,module,title,name,location,category,status,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("record_added", f"{vals[0]} / {vals[2]}")
    return redirect("/" + (vals[0] or ""))


@app.route("/add-business", methods=["POST"])
def add_business():
    vals = (
        safe(request.form.get("name")),
        safe(request.form.get("category")),
        safe(request.form.get("location")),
        safe(request.form.get("contact")),
        safe(request.form.get("status")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO businesses(name,category,location,contact,status,notes,created_at) VALUES(?,?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("business_added", vals[0])
    return redirect("/operations")


@app.route("/add-creator", methods=["POST"])
def add_creator():
    vals = (
        safe(request.form.get("name")),
        safe(request.form.get("category")),
        safe(request.form.get("country")),
        safe(request.form.get("link")),
        safe(request.form.get("bio")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO creators(name,category,country,link,bio,created_at) VALUES(?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("creator_added", vals[0])
    return redirect("/operations")


@app.route("/add-experience", methods=["POST"])
def add_experience():
    vals = (
        safe(request.form.get("title")),
        safe(request.form.get("location")),
        safe(request.form.get("date_note")),
        safe(request.form.get("category")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO experiences(title,location,date_note,category,notes,created_at) VALUES(?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("experience_added", vals[0])
    return redirect("/operations")
    
@app.route("/add-delivery", methods=["POST"])
def add_delivery():
    vals = (
        safe(request.form.get("customer")),
        safe(request.form.get("pickup")),
        safe(request.form.get("dropoff")),
        safe(request.form.get("item")),
        safe(request.form.get("transport")),
        safe(request.form.get("status")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO delivery_bookings(customer,pickup,dropoff,item,transport,status,notes,created_at) VALUES(?,?,?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("delivery_added", vals[3])
    return redirect("/operations")


@app.route("/add-rider-driver", methods=["POST"])
def add_rider_driver():
    vals = (
        safe(request.form.get("name")),
        safe(request.form.get("role")),
        safe(request.form.get("vehicle")),
        safe(request.form.get("area")),
        safe(request.form.get("status")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO riders_drivers(name,role,vehicle,area,status,notes,created_at) VALUES(?,?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("rider_driver_added", vals[0])
    return redirect("/operations")


@app.route("/add-sika", methods=["POST"])
def add_sika():
    try:
        points = int(request.form.get("points") or 0)
    except ValueError:
        points = 0

    vals = (
        safe(request.form.get("name")),
        safe(request.form.get("record_type")),
        safe(request.form.get("value_note")),
        points,
        safe(request.form.get("status")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO sika_records(name,record_type,value_note,points,status,notes,created_at) VALUES(?,?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("sika_added", vals[0])
    return redirect("/money")


@app.route("/add-verification", methods=["POST"])
def add_verification():
    vals = (
        safe(request.form.get("name")),
        safe(request.form.get("level")),
        safe(request.form.get("location")),
        safe(request.form.get("status")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO verification_badges(name,level,location,status,notes,created_at) VALUES(?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("verification_added", vals[0])
    return redirect("/identity")


@app.route("/add-readiness", methods=["POST"])
def add_readiness():
    vals = (
        safe(request.form.get("area")),
        safe(request.form.get("request_type")),
        safe(request.form.get("applicant")),
        safe(request.form.get("location")),
        safe(request.form.get("status")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO readiness_requests(area,request_type,applicant,location,status,notes,created_at) VALUES(?,?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("readiness_added", f"{vals[0]} / {vals[1]}")
    return redirect("/command")


@app.route("/command")
def command():
    con = db()

    counts = {
        "Records": con.execute("SELECT COUNT(*) c FROM records").fetchone()["c"],
        "Businesses": con.execute("SELECT COUNT(*) c FROM businesses").fetchone()["c"],
        "Creators": con.execute("SELECT COUNT(*) c FROM creators").fetchone()["c"],
        "Experiences": con.execute("SELECT COUNT(*) c FROM experiences").fetchone()["c"],
        "Deliveries": con.execute("SELECT COUNT(*) c FROM delivery_bookings").fetchone()["c"],
        "Riders / Drivers": con.execute("SELECT COUNT(*) c FROM riders_drivers").fetchone()["c"],
        "SIKA": con.execute("SELECT COUNT(*) c FROM sika_records").fetchone()["c"],
        "Verification": con.execute("SELECT COUNT(*) c FROM verification_badges").fetchone()["c"],
        "Readiness": con.execute("SELECT COUNT(*) c FROM readiness_requests").fetchone()["c"],
    }

    audits = con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 50").fetchall()
    latest = con.execute("SELECT * FROM records ORDER BY id DESC LIMIT 30").fetchall()

    con.close()

    cards = "".join([
        f"<div class='card'><div class='metric'>{v}</div><h2>{k}</h2></div>"
        for k, v in counts.items()
    ])

    aud = "".join([
        f"<tr><td>{a['created_at']}</td><td>{a['action']}</td><td>{a['detail']}</td></tr>"
        for a in audits
    ]) or "<tr><td colspan='3'>No audit logs yet.</td></tr>"

    rec = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['system']}</td><td>{r['module']}</td><td>{r['title']}</td><td>{r['status']}</td></tr>"
        for r in latest
    ]) or "<tr><td colspan='5'>No records yet.</td></tr>"

    body = f"""
<section class="hero">
<h1>🎛 Command Center</h1>
<p>Master dashboard. Records, audit, readiness, operations and launch signals.</p>
</section>

<section class="grid">
{cards}
</section>

<h2>Latest Records</h2>
<table>
<tr><th>Time</th><th>System</th><th>Module</th><th>Title</th><th>Status</th></tr>
{rec}
</table>

<h2>Audit Logs</h2>
<table>
<tr><th>Time</th><th>Action</th><th>Detail</th></tr>
{aud}
</table>
"""

    return layout("Command Center", body)

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        vals = (
            safe(request.form.get("nickname")),
            safe(request.form.get("username")),
            safe(request.form.get("email")),
            safe(request.form.get("password")),
            safe(request.form.get("postcode")),
            safe(request.form.get("borough")),
            safe(request.form.get("county")),
            safe(request.form.get("country")),
            safe(request.form.get("continent")),
            safe(request.form.get("circle")),
            now(),
        )
        con = db()
        try:
            con.execute("""
                INSERT INTO members(
                    nickname, username, email, password, postcode, borough,
                    county, country, continent, circle, created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """, vals)
            con.commit()
            session["member"] = vals[1]
            audit("member_joined", vals[1])
            con.close()
            return redirect("/my-world")
        except sqlite3.IntegrityError:
            con.close()
            return layout("Username Taken", "<section class='hero'><h1>Username already exists</h1><p>Go back and choose another username.</p></section>")

    return layout("Join OAP", """
<section class="hero">
<h1>🌍 Join OAP</h1>
<p>Create My World. Become a Legacy Maker.</p>
</section>

<div class="card">
<form method="post">
<input name="nickname" placeholder="Nickname" required>
<input name="username" placeholder="Username" required>
<input name="email" placeholder="Email optional">
<input name="password" type="password" placeholder="Password" required>
<input name="postcode" placeholder="Postcode">
<input name="borough" placeholder="Borough">
<input name="county" placeholder="County / Region">
<input name="country" placeholder="Country">
<input name="continent" placeholder="Continent">
<select name="circle">
<option>Community Member - Free</option>
<option>Postcode Founder - £5</option>
<option>Borough Builder - £10</option>
<option>Country Champion - £25</option>
</select>
<button>Join OAP</button>
</form>
</div>
""")


@app.route("/enter", methods=["GET", "POST"])
def enter():
    if request.method == "POST":
        username = safe(request.form.get("username"))
        password = safe(request.form.get("password"))

        con = db()
        member = con.execute(
            "SELECT * FROM members WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        con.close()

        if member:
            session["member"] = username
            audit("member_entered", username)
            return redirect("/my-world")

        return layout("Enter Failed", "<section class='hero'><h1>Enter failed</h1><p>Check username or password.</p></section>")

    return layout("Enter My World", """
<section class="hero">
<h1>👤 Enter My World</h1>
<p>Return to your OAP identity hub.</p>
</section>

<div class="card">
<form method="post">
<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>
<button>Enter My World</button>
</form>
</div>
""")


@app.route("/leave")
def leave():
    session.clear()
    return redirect("/")


@app.route("/my-world")
def my_world():
    username = session.get("member")
    if not username:
        return redirect("/enter")

    con = db()
    member = con.execute("SELECT * FROM members WHERE username=?", (username,)).fetchone()
    con.close()

    if not member:
        session.clear()
        return redirect("/enter")

    return layout("My World", f"""
<section class="hero">
<h1>👤 My World</h1>
<p>Welcome, <b>{member['nickname']}</b>.</p>
<p>{member['postcode']} • {member['borough']} • {member['country']} • {member['continent']}</p>
</section>

<section class="grid">
<div class="card"><h2>🏆 Circle</h2><p>{member['circle']}</p></div>
<div class="card"><h2>⚡ Contribution Recorded</h2><p>Your actions become proof.</p></div>
<div class="card"><h2>💎 SIKA Records</h2><p>Trust and value layer.</p></div>
<div class="card"><h2>🌳 Family Tree</h2><p>Legacy and relationships.</p></div>
<a class="card" href="/leave"><h2>Leave My World</h2><p>Sign out safely.</p></a>
</section>
""")
con = db()
con.execute("""
CREATE TABLE IF NOT EXISTS dispatch_jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT,
    pickup TEXT,
    dropoff TEXT,
    item TEXT,
    rider TEXT,
    status TEXT,
    created_at TEXT
)
""")

con.execute("""
CREATE TABLE IF NOT EXISTS rider_status(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rider_name TEXT,
    vehicle TEXT,
    area TEXT,
    status TEXT,
    created_at TEXT
)
""")
con.commit()
con.close()
@app.route("/dispatch")
def dispatch():

    con = db()
    rows = con.execute(
        "SELECT * FROM dispatch_jobs ORDER BY id DESC LIMIT 100"
    ).fetchall()
    con.close()

    jobs = "".join([
        f"<tr><td>{r['customer']}</td><td>{r['pickup']}</td><td>{r['dropoff']}</td><td>{r['status']}</td></tr>"
        for r in rows
    ])

    return layout(
        "Dispatch Board",
        f"""
        <section class='hero'>
        <h1>🚚 Dispatch Board</h1>
        <p>Bookings, deliveries and operations.</p>
        </section>

        <div class='card'>
        <form method='post' action='/add-dispatch'>
        <input name='customer' placeholder='Customer'>
        <input name='pickup' placeholder='Pickup'>
        <input name='dropoff' placeholder='Dropoff'>
        <input name='item' placeholder='Item'>
        <input name='rider' placeholder='Assigned Rider'>
        <select name='status'>
            <option>Pending</option>
            <option>Assigned</option>
            <option>Collected</option>
            <option>Delivered</option>
        </select>
        <button>Create Booking</button>
        </form>
        </div>

        <table>
        <tr><th>Customer</th><th>Pickup</th><th>Dropoff</th><th>Status</th></tr>
        {jobs}
        </table>
        """
    )


@app.route("/add-dispatch", methods=["POST"])
def add_dispatch():

    vals = (
        safe(request.form.get("customer")),
        safe(request.form.get("pickup")),
        safe(request.form.get("dropoff")),
        safe(request.form.get("item")),
        safe(request.form.get("rider")),
        safe(request.form.get("status")),
        now(),
    )

    con = db()

    con.execute("""
    INSERT INTO dispatch_jobs(
        customer,pickup,dropoff,item,rider,status,created_at
    ) VALUES(?,?,?,?,?,?,?)
    """, vals)

    con.commit()
    con.close()

    return redirect("/dispatch")
@app.route("/messenger")
def messenger():
    con = db()
    rows = con.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 50").fetchall()
    con.close()

    table_rows = "".join([
        f"<tr><td>{m['created_at']}</td><td>{m['sender']}</td><td>{m['receiver']}</td><td>{m['subject']}</td><td>{m['status']}</td></tr>"
        for m in rows
    ]) or "<tr><td colspan='5'>No messages yet.</td></tr>"

    return layout("Messenger", f"""
<section class="hero">
<h1>💬 Messenger</h1>
<p>OAP communication records. Human-first. Private-first.</p>
</section>

<div class="card">
<form method="post" action="/send-message">
<input name="sender" placeholder="From">
<input name="receiver" placeholder="To">
<input name="subject" placeholder="Subject">
<textarea name="body" placeholder="Message"></textarea>
<select name="status">
<option>Draft</option>
<option>Sent</option>
<option>Review</option>
</select>
<button>Send Message</button>
</form>
</div>

<h2>Messages</h2>
<table>
<tr><th>Time</th><th>From</th><th>To</th><th>Subject</th><th>Status</th></tr>
{table_rows}
</table>
""")


@app.route("/send-message", methods=["POST"])
def send_message():
    vals = (
        safe(request.form.get("sender")),
        safe(request.form.get("receiver")),
        safe(request.form.get("subject")),
        safe(request.form.get("body")),
        safe(request.form.get("status")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO messages(sender,receiver,subject,body,status,created_at) VALUES(?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("message_sent", f"{vals[0]} to {vals[1]}")
    return redirect("/messenger")


@app.route("/mail")
def mail():
    con = db()
    rows = con.execute("SELECT * FROM mail_items ORDER BY id DESC LIMIT 50").fetchall()
    con.close()

    table_rows = "".join([
        f"<tr><td>{m['created_at']}</td><td>{m['folder']}</td><td>{m['sender']}</td><td>{m['receiver']}</td><td>{m['subject']}</td></tr>"
        for m in rows
    ]) or "<tr><td colspan='5'>No mail yet.</td></tr>"

    return layout("OAP Mail", f"""
<section class="hero">
<h1>📧 OAP Mail</h1>
<p>Inbox, sent, drafts and member communication records.</p>
</section>

<div class="card">
<form method="post" action="/send-mail">
<input name="sender" placeholder="From">
<input name="receiver" placeholder="To">
<input name="subject" placeholder="Subject">
<textarea name="body" placeholder="Mail body"></textarea>
<select name="folder">
<option>Inbox</option>
<option>Sent</option>
<option>Draft</option>
<option>Review</option>
</select>
<button>Record Mail</button>
</form>
</div>

<h2>Mail Items</h2>
<table>
<tr><th>Time</th><th>Folder</th><th>From</th><th>To</th><th>Subject</th></tr>
{table_rows}
</table>
""")


@app.route("/send-mail", methods=["POST"])
def send_mail():
    vals = (
        safe(request.form.get("sender")),
        safe(request.form.get("receiver")),
        safe(request.form.get("subject")),
        safe(request.form.get("body")),
        safe(request.form.get("folder")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO mail_items(sender,receiver,subject,body,folder,created_at) VALUES(?,?,?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("mail_recorded", f"{vals[0]} to {vals[1]}")
    return redirect("/mail")

@app.route("/community-power")
def community_power():

    con = db()

    rows = con.execute(
        """
        SELECT *
        FROM community_power
        ORDER BY id DESC
        LIMIT 100
        """
    ).fetchall()

    con.close()

    table_rows = "".join([
        f"""
        <tr>
            <td>{r['created_at']}</td>
            <td>{r['member']}</td>
            <td>{r['mission']}</td>
            <td>{r['category']}</td>
            <td>{r['points']}</td>
        </tr>
        """
        for r in rows
    ]) or "<tr><td colspan='5'>No contribution records yet.</td></tr>"

    return layout("Community Power", f"""
    <section class='hero'>
        <h1>⚡ Community Power</h1>
        <p>Community action. Contribution recorded.</p>
    </section>

    <div class='card'>
        <form method='post' action='/add-community-power'>
            <input name='member' placeholder='Member' required>
            <input name='mission' placeholder='Mission' required>

            <select name='category'>
                <option>Community</option>
                <option>Business</option>
                <option>Creator</option>
                <option>Events</option>
                <option>Sports</option>
                <option>Culture</option>
            </select>

            <input type='number'
                   name='points'
                   value='10'
                   required>

            <button>
                Record Contribution
            </button>

        </form>
    </div>

    <h2>Contribution Records</h2>

    <table>
        <tr>
            <th>Date</th>
            <th>Member</th>
            <th>Mission</th>
            <th>Category</th>
            <th>Points</th>
        </tr>

        {table_rows}

    </table>
    """)


@app.route("/add-community-power", methods=["POST"])
def add_community_power():

    vals = (
        safe(request.form.get("member")),
        safe(request.form.get("mission")),
        safe(request.form.get("category")),
        int(request.form.get("points")),
        now()
    )

    con = db()

    con.execute(
        """
        INSERT INTO community_power(
            member,
            mission,
            category,
            points,
            created_at
        )
        VALUES(?,?,?,?,?)
        """,
        vals
    )

    con.commit()
    con.close()

    audit(
        "community_power",
        vals[1]
    )

    return redirect(
        "/community-power"
)
@app.route("/notifications")
def notifications():
    con = db()
    rows = con.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 50").fetchall()
    con.close()

    table_rows = "".join([
        f"<tr><td>{n['created_at']}</td><td>{n['title']}</td><td>{n['status']}</td><td>{n['body']}</td></tr>"
        for n in rows
    ]) or "<tr><td colspan='4'>No notifications yet.</td></tr>"

    return layout("Notifications", f"""
<section class="hero">
<h1>🔔 Notifications</h1>
<p>OAP alerts, system updates and community notices.</p>
</section>

<div class="card">
<form method="post" action="/add-notification">
<input name="title" placeholder="Notification title">
<textarea name="body" placeholder="Notification body"></textarea>
<select name="status">
<option>Draft</option>
<option>Active</option>
<option>Review</option>
<option>Archived</option>
</select>
<button>Notification Recorded</button>
</form>
</div>

<h2>Notifications</h2>
<table>
<tr><th>Time</th><th>Title</th><th>Status</th><th>Body</th></tr>
{table_rows}
</table>
""")


@app.route("/add-notification", methods=["POST"])
def add_notification():
    vals = (
        safe(request.form.get("title")),
        safe(request.form.get("body")),
        safe(request.form.get("status")),
        now(),
    )

    con = db()
    con.execute(
        "INSERT INTO notifications(title,body,status,created_at) VALUES(?,?,?,?)",
        vals
    )
    con.commit()
    con.close()

    audit("notification_added", vals[0])
    return redirect("/notifications")
@app.route("/navigation-hub")
def navigation_hub():

    con = db()
    rows = con.execute(
        "SELECT * FROM navigation_routes ORDER BY id DESC LIMIT 100"
    ).fetchall()
    con.close()

    routes = "".join([
        f"<tr><td>{r['start_point']}</td><td>{r['destination']}</td><td>{r['transport_type']}</td><td>{r['status']}</td></tr>"
        for r in rows
    ])

    return layout(
        "Navigation Hub",
        f"""
<section class='hero'>
<h1>🧭 Navigation Hub</h1>
<p>Community routes, logistics and movement records.</p>
</section>

<div class='card'>
<form method='post' action='/add-route'>
<input name='start_point' placeholder='Start'>
<input name='destination' placeholder='Destination'>
<input name='transport_type' placeholder='Transport'>
<select name='status'>
<option>Planned</option>
<option>Active</option>
<option>Completed</option>
</select>
<button>Create Route</button>
</form>
</div>

<table>
<tr><th>Start</th><th>Destination</th><th>Transport</th><th>Status</th></tr>
{routes}
</table>
"""
    )


@app.route("/add-route", methods=["POST"])
def add_route():

    vals = (
        safe(request.form.get("start_point")),
        safe(request.form.get("destination")),
        safe(request.form.get("transport_type")),
        safe(request.form.get("status")),
        now(),
    )

    con = db()

    con.execute("""
    INSERT INTO navigation_routes(
        start_point,destination,transport_type,status,created_at
    ) VALUES(?,?,?,?,?)
    """, vals)

    con.commit()
    con.close()

    return redirect("/navigation-hub")@app.route("/maps-hub")
def maps_hub():

    con = db()
    rows = con.execute(
        "SELECT * FROM map_places ORDER BY id DESC LIMIT 100"
    ).fetchall()
    con.close()

    places = "".join([
        f"<tr><td>{r['place_name']}</td><td>{r['category']}</td><td>{r['location']}</td></tr>"
        for r in rows
    ])

    return layout(
        "Maps Hub",
        f"""
<section class='hero'>
<h1>🗺 Maps Hub</h1>
<p>Places, businesses, landmarks and communities.</p>
</section>

<div class='card'>
<form method='post' action='/add-place'>
<input name='place_name' placeholder='Place Name'>
<input name='category' placeholder='Category'>
<input name='location' placeholder='Location'>
<textarea name='notes'></textarea>
<button>Add Place</button>
</form>
</div>

<table>
<tr><th>Name</th><th>Category</th><th>Location</th></tr>
{places}
</table>
"""
    )


@app.route("/add-place-old", methods=["POST"])
def add_place_old():
    vals = (
        safe(request.form.get("place_name")),
        safe(request.form.get("category")),
        safe(request.form.get("location")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()

    con.execute("""
    INSERT INTO map_places(
        place_name,category,location,notes,created_at
    ) VALUES(?,?,?,?,?)
    """, vals)

    con.commit()
    con.close()

    return redirect("/maps-hub")
    
@app.route("/weather-hub")
def weather_hub():

    con = db()
    rows = con.execute(
        "SELECT * FROM weather_records ORDER BY id DESC LIMIT 50"
    ).fetchall()
    con.close()

    weather = "".join([
        f"<tr><td>{r['location']}</td><td>{r['condition']}</td><td>{r['temperature']}</td></tr>"
        for r in rows
    ])

    return layout(
        "Weather Hub",
        f"""
<section class='hero'>
<h1>🌦 Weather Hub</h1>
<p>Postcode → Borough → Country → Global weather records.</p>
</section>

<div class='card'>
<form method='post' action='/add-weather'>
<input name='location' placeholder='Location'>
<input name='condition' placeholder='Condition'>
<input name='temperature' placeholder='Temperature'>
<textarea name='notes'></textarea>
<button>Record Weather</button>
</form>
</div>

<table>
<tr><th>Location</th><th>Condition</th><th>Temperature</th></tr>
{weather}
</table>
"""
    )


@app.route("/add-weather", methods=["POST"])
def add_weather():

    vals = (
        safe(request.form.get("location")),
        safe(request.form.get("condition")),
        safe(request.form.get("temperature")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()

    con.execute("""
    INSERT INTO weather_records(
        location,condition,temperature,notes,created_at
    ) VALUES(?,?,?,?,?)
    """, vals)

    con.commit()
    con.close()

    return redirect("/weather-hub")

@app.route("/maps-hub")
def maps_hub():

    con = db()
    rows = con.execute(
        "SELECT * FROM map_places ORDER BY id DESC LIMIT 100"
    ).fetchall()
    con.close()

    places = "".join([
        f"<tr><td>{r['place_name']}</td><td>{r['category']}</td><td>{r['location']}</td></tr>"
        for r in rows
    ])

    return layout(
        "Maps Hub",
        f"""
<section class='hero'>
<h1>🗺 Maps Hub</h1>
<p>Places, landmarks, communities and businesses.</p>
</section>

<div class='card'>
<form method='post' action='/add-place'>
<input name='place_name' placeholder='Place'>
<input name='category' placeholder='Category'>
<input name='location' placeholder='Location'>
<textarea name='notes'></textarea>
<button>Add Place</button>
</form>
</div>

<table>
<tr>
<th>Name</th>
<th>Category</th>
<th>Location</th>
</tr>
{places}
</table>
"""
    )


@app.route("/add-place", methods=["POST"])
def add_place_2():
    vals = (
        safe(request.form.get("place_name")),
        safe(request.form.get("category")),
        safe(request.form.get("location")),
        safe(request.form.get("notes")),
        now(),
    )

    con = db()

    con.execute("""
    INSERT INTO map_places(
        place_name,category,location,notes,created_at
    ) VALUES(?,?,?,?,?)
    """, vals)

    con.commit()
    con.close()

    return redirect("/maps-hub")

@app.route("/navigation-hub")
def navigation_hub_2():
    con = db()
    rows = con.execute(
        "SELECT * FROM navigation_routes ORDER BY id DESC LIMIT 100"
    ).fetchall()
    con.close()

    routes = "".join([
        f"<tr><td>{r['start_point']}</td><td>{r['destination']}</td><td>{r['transport_type']}</td><td>{r['status']}</td></tr>"
        for r in rows
    ])

    return layout(
        "Navigation Hub",
        f"""
<section class='hero'>
<h1>🧭 Navigation Hub</h1>
<p>Community routes, logistics and movement records.</p>
</section>

<div class='card'>
<form method='post' action='/add-route'>
<input name='start_point' placeholder='Start'>
<input name='destination' placeholder='Destination'>
<input name='transport_type' placeholder='Transport'>
<select name='status'>
<option>Planned</option>
<option>Active</option>
<option>Completed</option>
</select>
<button>Create Route</button>
</form>
</div>

<table>
<tr><th>Start</th><th>Destination</th><th>Transport</th><th>Status</th></tr>
{routes}
</table>
"""
    )


@app.route("/add-route", methods=["POST"])
def add_route_2():
    vals = (
        safe(request.form.get("start_point")),
        safe(request.form.get("destination")),
        safe(request.form.get("transport_type")),
        safe(request.form.get("status")),
        now(),
    )

    con = db()

    con.execute("""
    INSERT INTO navigation_routes(
        start_point,destination,transport_type,status,created_at
    ) VALUES(?,?,?,?,?)
    """, vals)

    con.commit()
    con.close()

    return redirect("/navigation-hub")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
)
