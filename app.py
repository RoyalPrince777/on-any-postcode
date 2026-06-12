from flask import Flask, request, redirect, session, jsonify
from datetime import datetime, timedelta
from functools import wraps
import os
import sqlite3
from html import escape
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import json
import urllib.request

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "OAP-CHANGE-THIS-777")
DB = "oap_architecture_v12.db"

# Session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get("FLASK_ENV") == "production" 
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Logging setup
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)

# Constants
SYSTEMS = {
    "world": ("🌍 OAP World", "One public front door."),
    "identity": ("👤 My World", "One identity hub."),
    "intelligence": ("🧠 Intelligence", "HRM, Review Core, Agents, Command."),
    "money": ("💎 Money / SIKA", "SIKA records, wallet readiness, finance readiness."),
    "communications": ("⚡ Community Power", "OAP Pulse, linkups, spaces, announcements and trust."),
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
    "communications": ["OAP Pulse", "Pulse Spaces", "Pulse Linkup", "Pulse Announcements", "Pulse Relay", "Pulse Trust"],
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

HRM_LOG_TYPES = ["Actions", "Risks", "Builds", "Fixes", "Learning"]
LOCAL_AI_SUMMARY_FIELDS = ["Insights", "Patterns", "Recommendations", "Warnings"]

ITEMS_PER_PAGE = 20
MAX_PAGINATION = 100

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def now():
    """Get current UTC timestamp"""
    return datetime.utcnow().isoformat(timespec="seconds")

def safe(v):
    """Safely escape and sanitize user input"""
    if v is None:
        return ""
    return escape(str(v).strip())

def slug(v):
    """Convert to URL-friendly slug"""
    return (
        v.lower()
        .replace("&", "and")
        .replace("/", "-")
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
    )

def db():
    """Get database connection with row factory"""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def get_pagination(request):
    """Extract and validate pagination parameters"""
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    
    limit = min(ITEMS_PER_PAGE, max(1, int(request.args.get('limit', ITEMS_PER_PAGE))))
    offset = (page - 1) * limit
    return page, limit, offset

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'member' not in session:
            return redirect('/enter')
        return f(*args, **kwargs)
    return decorated_function

def audit(action, detail, level="INFO"):
    """Log action to audit table"""
    try:
        con = db()
        con.execute(
            "INSERT INTO audit(action,detail,level,created_at) VALUES(?,?,?,?)",
            (action, detail, level, now())
        )
        con.commit()
        con.close()
        logger.info(f"AUDIT: {action} - {detail}")
    except Exception as e:
        logger.error(f"Audit logging failed: {str(e)}")

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init():
    """Initialize database with all tables and indexes"""
    con = db()
    
    # Members table
    con.execute("""
    CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password TEXT NOT NULL,
        postcode TEXT,
        borough TEXT,
        county TEXT,
        country TEXT,
        continent TEXT,
        circle TEXT,
        verified BOOLEAN DEFAULT 0,
        active BOOLEAN DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system TEXT NOT NULL,
        module TEXT NOT NULL,
        title TEXT NOT NULL,
        name TEXT,
        location TEXT,
        category TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS community_power(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member TEXT NOT NULL,
        mission TEXT NOT NULL,
        category TEXT NOT NULL,
        points INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS businesses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        location TEXT,
        contact TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS creators(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        country TEXT,
        link TEXT,
        bio TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS experiences(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        location TEXT,
        date_note TEXT,
        category TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS delivery_bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT NOT NULL,
        pickup TEXT NOT NULL,
        dropoff TEXT NOT NULL,
        item TEXT,
        transport TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS riders_drivers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        vehicle TEXT,
        area TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS sika_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        record_type TEXT NOT NULL,
        value_note TEXT,
        points INTEGER DEFAULT 1,
        status TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS verification_badges(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        level TEXT NOT NULL,
        location TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS readiness_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT NOT NULL,
        request_type TEXT NOT NULL,
        applicant TEXT,
        location TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        detail TEXT,
        level TEXT DEFAULT 'INFO',
        created_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS dispatch_jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT NOT NULL,
        pickup TEXT NOT NULL,
        dropoff TEXT NOT NULL,
        item TEXT,
        rider TEXT,
        status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS rider_status(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rider_name TEXT NOT NULL,
        vehicle TEXT,
        area TEXT,
        status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS mail_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT,
        folder TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        body TEXT,
        status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS navigation_routes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_point TEXT NOT NULL,
        destination TEXT NOT NULL,
        transport_type TEXT,
        status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS map_places(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        place_name TEXT NOT NULL,
        category TEXT,
        location TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS weather_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT NOT NULL,
        condition TEXT,
        temperature TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    # OAP Pulse / Human Communications Core
    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_spaces(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        purpose TEXT,
        space_type TEXT DEFAULT 'community',
        postcode TEXT,
        borough TEXT,
        country TEXT,
        visibility TEXT DEFAULT 'public',
        created_at TEXT NOT NULL
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_linkups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        linkup_type TEXT DEFAULT 'group',
        space_id INTEGER,
        created_by TEXT NOT NULL,
        status TEXT DEFAULT 'open',
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT NOT NULL,
        receiver_username TEXT,
        space_id INTEGER,
        linkup_id INTEGER,
        body TEXT NOT NULL,
        pulse_type TEXT DEFAULT 'normal',
        status TEXT DEFAULT 'sent',
        created_at TEXT NOT NULL,
        read_at TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_announcements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT NOT NULL,
        target TEXT NOT NULL,
        title TEXT,
        body TEXT NOT NULL,
        priority TEXT DEFAULT 'normal',
        created_at TEXT NOT NULL
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_relays(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT NOT NULL,
        from_space_id INTEGER,
        to_space_id INTEGER,
        title TEXT,
        body TEXT NOT NULL,
        relay_type TEXT DEFAULT 'community',
        verification_status TEXT DEFAULT 'unverified',
        created_at TEXT NOT NULL
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_inbox(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        record_id INTEGER,
        linkup_id INTEGER,
        inbox_status TEXT DEFAULT 'unread',
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_trust(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_username TEXT NOT NULL,
        record_id INTEGER,
        space_id INTEGER,
        issue_type TEXT NOT NULL,
        details TEXT,
        review_status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL,
        reviewed_at TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_directory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        display_name TEXT,
        role TEXT DEFAULT 'member',
        postcode TEXT,
        borough TEXT,
        country TEXT,
        contact_status TEXT DEFAULT 'open',
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_pins(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        space_id INTEGER,
        record_id INTEGER,
        pinned_by TEXT NOT NULL,
        reason TEXT,
        created_at TEXT NOT NULL
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_notices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        notice_type TEXT DEFAULT 'info',
        title TEXT,
        body TEXT NOT NULL,
        notice_status TEXT DEFAULT 'unread',
        created_at TEXT NOT NULL,
        read_at TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pulse_queue(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT NOT NULL,
        receiver_username TEXT,
        space_id INTEGER,
        linkup_id INTEGER,
        body TEXT NOT NULL,
        queue_status TEXT DEFAULT 'pending',
        retry_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        last_try_at TEXT
    )
    """)

    default_pulse_spaces = [
        ("community", "Main OAP community room", "community", None, None, None),
        ("command-center", "OAP operations and support room", "operations", None, None, None),
        ("members", "Member-to-member support and updates", "members", None, None, None),
        ("riders", "Rider coordination and delivery updates", "dispatch", None, None, None),
        ("merchants", "Merchant support and business requests", "merchant", None, None, None),
        ("announcements", "Official OAP community announcements", "announcement", None, None, None),
        ("crisis-support", "Verified support, needs and safety records", "support", None, None, None),
        ("postcode-pulse", "Postcode-level community heartbeat", "postcode", None, None, None),
        ("earth-is-our-turf", "Global OAP movement room", "global", None, None, None)
    ]

    for name, purpose, space_type, postcode, borough, country in default_pulse_spaces:
        con.execute(
            """
            INSERT OR IGNORE INTO pulse_spaces(
                name,purpose,space_type,postcode,borough,country,created_at
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (name, purpose, space_type, postcode, borough, country, now())
        )

    # Create indexes for performance
    indexes = [
        ("idx_members_username", "members", "username"),
        ("idx_members_email", "members", "email"),
        ("idx_members_country", "members", "country"),
        ("idx_records_system_module", "records", "system, module"),
        ("idx_records_created_at", "records", "created_at"),
        ("idx_community_power_member", "community_power", "member"),
        ("idx_community_power_created_at", "community_power", "created_at"),
        ("idx_businesses_category", "businesses", "category"),
        ("idx_dispatch_status", "dispatch_jobs", "status"),
        ("idx_delivery_status", "delivery_bookings", "status"),
        ("idx_mail_folder", "mail_items", "folder"),
        ("idx_audit_created_at", "audit", "created_at"),
        ("idx_pulse_spaces_name", "pulse_spaces", "name"),
        ("idx_pulse_spaces_type", "pulse_spaces", "space_type"),
        ("idx_pulse_linkups_space", "pulse_linkups", "space_id"),
        ("idx_pulse_linkups_created_by", "pulse_linkups", "created_by"),
        ("idx_pulse_records_receiver", "pulse_records", "receiver_username"),
        ("idx_pulse_records_sender", "pulse_records", "sender_username"),
        ("idx_pulse_records_space", "pulse_records", "space_id"),
        ("idx_pulse_records_linkup", "pulse_records", "linkup_id"),
        ("idx_pulse_announcements_created", "pulse_announcements", "created_at"),
        ("idx_pulse_relays_from", "pulse_relays", "from_space_id"),
        ("idx_pulse_relays_to", "pulse_relays", "to_space_id"),
        ("idx_pulse_inbox_username", "pulse_inbox", "username"),
        ("idx_pulse_trust_status", "pulse_trust", "review_status"),
        ("idx_pulse_directory_username", "pulse_directory", "username"),
        ("idx_pulse_pins_space", "pulse_pins", "space_id"),
        ("idx_pulse_notices_username", "pulse_notices", "username"),
        ("idx_pulse_queue_status", "pulse_queue", "queue_status"),
    ]
    
    for idx_name, table, columns in indexes:
        try:
            con.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({columns})")
        except sqlite3.Error:
            pass
    
    con.commit()
    con.close()
    logger.info("Database initialized successfully")

init()

# ============================================================================
# TEMPLATE & LAYOUT
# ============================================================================

def nav():
    """Generate navigation HTML"""
    links = "<a href='/'>Home</a>"
    links += "<a href='/world'>🌍 OAP World</a>"
    links += "<a href='/identity'>👤 My World</a>"
    links += "<a href='/community-power'>⚡ Community Power</a>"
    links += "<a href='/the-link'>💬 The Link</a>"
    links += "<a href='/my-card'>👤 My Card</a>"
    links += "<a href='/my-energy'>⚡ My Energy</a>"
    links += "<a href='/born-local'>🌍 Born Local</a>"
    links += "<a href='/signals'>📡 Signals</a>"
    links += "<a href='/oap-pulse/spaces'>💚 Pulse Spaces</a>"
    links += "<a href='/communications'>📧 Communications</a>"
    links += "<a href='/pulse-inbox'>📥 Pulse Inbox</a>"
    links += "<a href='/pulse-directory'>🧭 Pulse Directory</a>"
    links += "<a href='/infrastructure'>🗺 Infrastructure</a>"
    links += "<a href='/operations'>🚚 Operations</a>"
    links += "<a href='/culture'>🎭 Culture</a>"
    links += "<a href='/trust'>🛡 Trust</a>"
    links += "<a href='/world-cup'>⚽ World Cup</a>"
    links += "<a href='/command'>🎛 Command</a>"
    return links

def layout(title, body, breadcrumb=None):
    """Base HTML layout template"""
    breadcrumb_html = ""
    if breadcrumb:
        breadcrumb_html = f"<div class='breadcrumb'>{' / '.join(breadcrumb)}</div>"
    
    return f"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta charset="utf-8">
<title>{safe(title)} - OAP</title>
<style>
:root {{
  --gold:#d4af37;
  --line:#6d5520;
  --text:#f7f0dd;
  --muted:#c9b987;
  --green:#52d98f;
  --blue:#00eaff;
  --error:#ff6b6b;
  --warning:#ffa500;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  background:radial-gradient(circle at top,#161616,#050505 55%,#000);
  color:var(--text);
  font-family:Arial,Helvetica,sans-serif;
  line-height:1.6;
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
  cursor:pointer;
  transition:all 0.2s;
}}
nav a:hover,.btn:hover {{
  background:var(--gold);
  color:#000;
}}
.breadcrumb {{
  font-size:12px;
  color:var(--muted);
  padding:8px 0;
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
  transition:transform 0.2s;
}}
.card:hover {{
  transform:translateY(-4px);
}}
.metric {{
  font-size:32px;
  color:var(--gold);
  font-weight:900;
}}
.green {{ color:var(--green); font-weight:900; }}
.neon {{ color:var(--blue); text-shadow:0 0 12px var(--blue); }}
.error {{ color:var(--error); }}
.warning {{ color:var(--warning); }}
input,select,textarea,button {{
  width:100%;
  padding:12px;
  margin:6px 0;
  border-radius:14px;
  border:1px solid var(--line);
  background:#050505;
  color:var(--text);
  font-size:15px;
  font-family:inherit;
}}
button {{
  background:#1d8f5f;
  font-weight:900;
}}
button:hover {{
  background:#2aad7d;
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
th {{
  background:#1a1a1a;
  font-weight:900;
}}
.warn {{
  background:#2c2108;
  border:1px solid var(--gold);
  border-radius:18px;
  padding:14px;
  margin:12px 0;
}}
.error-box {{
  background:#3d1a1a;
  border:1px solid var(--error);
  border-radius:18px;
  padding:14px;
  margin:12px 0;
}}
.pagination {{
  display:flex;
  gap:8px;
  justify-content:center;
  margin:20px 0;
}}
.pagination a, .pagination span {{
  padding:8px 12px;
  border:1px solid var(--line);
  border-radius:6px;
  text-decoration:none;
  color:var(--text);
}}
.pagination a:hover {{
  background:var(--gold);
  color:#000;
}}
.pagination .active {{
  background:var(--gold);
  color:#000;
  font-weight:900;
}}
.form-group {{
  margin:12px 0;
}}
.form-group label {{
  display:block;
  margin-bottom:6px;
  font-weight:900;
}}
</style>
</head>
<body>
<header>
  <div class="brand">ON ANY POSTCODE 🌍👑</div>
  <div class="tag">One Brand. One Front Door. One Identity. Born Local. Built Global.</div>
  {breadcrumb_html}
  <nav>{nav()}</nav>
</header>
<main>{body}</main>
<footer>
  🌍 ON ANY POSTCODE — Born Local. Built Global. EARTH IS OUR TURF. One Race. Human Race.
</footer>
</body>
</html>"""

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return layout("Page Not Found", """
    <section class="hero error-box">
    <h1>404 - Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <p><a href="/" style="color:var(--green);">← Return Home</a></p>
    </section>
    """), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(error)}")
    audit("system_error", str(error), "ERROR")
    return layout("Server Error", """
    <section class="hero error-box">
    <h1>500 - Server Error</h1>
    <p>Something went wrong. Our team has been notified.</p>
    <p><a href="/" style="color:var(--green);">← Return Home</a></p>
    </section>
    """), 500

# ============================================================================
# DATA RETRIEVAL FUNCTIONS
# ============================================================================

def get_records(system=None, module=None, page=1, limit=ITEMS_PER_PAGE):
    """Get records with pagination"""
    con = db()
    offset = (page - 1) * limit
    
    try:
        if system and module:
            rows = con.execute(
                "SELECT * FROM records WHERE system=? AND module=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (system, module, limit, offset)
            ).fetchall()
            total = con.execute(
                "SELECT COUNT(*) as c FROM records WHERE system=? AND module=?",
                (system, module)
            ).fetchone()['c']
        elif system:
            rows = con.execute(
                "SELECT * FROM records WHERE system=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (system, limit, offset)
            ).fetchall()
            total = con.execute(
                "SELECT COUNT(*) as c FROM records WHERE system=?",
                (system,)
            ).fetchone()['c']
        else:
            rows = con.execute(
                "SELECT * FROM records ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            total = con.execute("SELECT COUNT(*) as c FROM records").fetchone()['c']
    finally:
        con.close()
    
    return list(rows), total

def record_table(rows, enable_links=False):
    """Generate HTML table for records"""
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

def pagination_links(page, total, limit, base_url):
    """Generate pagination links"""
    total_pages = (total + limit - 1) // limit
    if total_pages <= 1:
        return ""
    
    links = '<div class="pagination">'
    
    if page > 1:
        links += f'<a href="{base_url}?page=1">← First</a>'
        links += f'<a href="{base_url}?page={page-1}">← Prev</a>'
    
    for p in range(max(1, page-2), min(total_pages+1, page+3)):
        if p == page:
            links += f'<span class="active">{p}</span>'
        else:
            links += f'<a href="{base_url}?page={p}">{p}</a>'
    
    if page < total_pages:
        links += f'<a href="{base_url}?page={page+1}">Next →</a>'
        links += f'<a href="{base_url}?page={total_pages}">Last →</a>'
    
    links += '</div>'
    return links

# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route("/")
def home():
    """Homepage"""
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
    """System overview page"""
    if system == "command":
        return command()
    
    data = SYSTEMS.get(system)
    if not data:
        return not_found(None)
    
    modules = MODULES.get(system, [])
    cards = "".join([
        f"<a class='card' href='/{system}/{slug(m)}'><h2>{m}</h2><p>{data[0]} module.</p></a>"
        for m in modules
    ])
    
    return layout(
        data[0],
        f"<section class='hero'><h1>{data[0]}</h1><p>{data[1]}</p></section>"
        f"<section class='grid'>{cards}</section>",
        [data[0]]
    )

@app.route("/<system>/<module>")
def module_page(system, module):
    """Module details page"""
    title = module.replace("-", " ").title()
    system_data = SYSTEMS.get(system)
    
    if not system_data:
        return not_found(None)
    
    page, limit, offset = get_pagination(request)
    rows, total = get_records(system, title, page, limit)
    
    table_html = record_table(rows)
    pagination = pagination_links(page, total, limit, f"/{system}/{module}")
    
    return layout(
        title,
        f"<section class='hero'><h1>{title}</h1><p>{system_data[0]} module.</p></section>"
        f"{table_html}"
        f"{pagination}",
        [system_data[0], title]
    )

@app.route("/world/country-spaces")
def country_spaces():
    """Country spaces listing"""
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
        """,
        ["World", "Country Spaces"]
    )

@app.route("/world-cup")
def worldcup():
    """World Cup hub"""
    cards = "".join([
        f"<a class='card' href='/world-cup/team/{s}'><h2>{n}</h2><p>⚽ Team hub ready</p></a>"
        for s, n in TEAMS
    ])
    
    return layout(
        "World Cup",
        f"""
        <section class='hero'>
        <h1>⚽ World Cup 2026</h1>
        <p>48-team structure. Community voice. Watch parties. No gambling.</p>
        </section>
        <section class='grid'>{cards}</section>
        """,
        ["World Cup 2026"]
    )

@app.route("/world-cup/team/<team>")
def team(team):
    """Team details page"""
    team_name = dict(TEAMS).get(team, team.replace("-", " ").title())
    
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
        """,
        ["World Cup", team_name]
    )

@app.route("/hrm/local-ai")
def hrm_local_ai():
    """HRM Local AI hub"""
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
        """,
        ["Intelligence", "HRM", "Local AI"]
    )

@app.route("/world-cup/match/<home>/<away>")
def match_command(home, away):
    """Match command center"""
    home_name = dict(TEAMS).get(home, home.replace("-", " ").title())
    away_name = dict(TEAMS).get(away, away.replace("-", " ").title())
    
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
        """,
        ["World Cup", "Matches", f"{home_name} vs {away_name}"]
    )

@app.route("/hrm/council")
def hrm_council():
    """HRM Council page"""
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
        """,
        ["Intelligence", "HRM Council"]
    )

@app.route("/oap-world")
def oap_world_hub():
    """OAP World hub"""
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
        """,
        ["World", "OAP World"]
    )

@app.route("/messenger", methods=["GET", "POST"])
def messenger():
    """Pulse Inbox replacing old Messenger"""
    if request.method == "POST":
        sender = safe(request.form.get("sender_username", session.get("member", "guest")))
        receiver = safe(request.form.get("receiver_username", ""))
        body = safe(request.form.get("body", ""))
        pulse_type = safe(request.form.get("pulse_type", "direct"))

        if sender and body:
            con = db()
            try:
                con.execute("""
                    INSERT INTO pulse_records(
                        sender_username, receiver_username, body, pulse_type, status, created_at
                    ) VALUES(?,?,?,?,?,?)
                """, (sender, receiver, body, pulse_type, "sent", now()))

                record_id = con.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

                if receiver:
                    con.execute("""
                        INSERT INTO pulse_inbox(
                            username, record_id, inbox_status, created_at, updated_at
                        ) VALUES(?,?,?,?,?)
                    """, (receiver, record_id, "unread", now(), now()))

                con.commit()
                audit("pulse_inbox_record_created", f"{sender} to {receiver or 'community'}")
            finally:
                con.close()

        return redirect("/messenger")

    
    q = safe(request.args.get("q", ""))

    con = db()
    try:
        if q:
            rows = con.execute("""
                SELECT * FROM pulse_records
                WHERE pulse_type IN ('direct','support','normal','need','story')
                AND (
                    body LIKE ?
                    OR sender_username LIKE ?
                )
                ORDER BY id DESC
                LIMIT 50
            """, (f"%{q}%", f"%{q}%")).fetchall()
        else:
            rows = con.execute("""
                SELECT * FROM pulse_records
                WHERE pulse_type IN ('direct','support','normal','need','story')
                ORDER BY id DESC
                LIMIT 50
            """).fetchall()
    finally:
        con.close()

    messages = "".join([
        f"""
        <div class='card'>
            <h2>💚 {safe(r['sender_username'])} ✨ Founder</h2>
            <p>{safe(r['body'])}</p>
            <small>To: {safe(r['receiver_username'] or 'community')} • {safe(r['pulse_type'])}</small>
        </div>
        """
        for r in rows
    ]) or "<div class='card'><h2>Pulse Inbox Open</h2><p>No Pulse records yet.</p></div>"

    return layout(
        "THE LINK",
        f"""
        <section class='hero'>
            <h1>💚 Pulse Inbox</h1>
            <p>Not Messenger. This is OAP Pulse — human records, support, linkups and community heartbeat.</p>
        </section>

        <div class='card'>
            <h2>🔍 Search Pulse</h2>
            <form method='get'>
                <input name='q' placeholder='Search Pulse...' value='{safe(request.args.get("q",""))}'>
                <button type='submit'>Search</button>
            </form>
        </div>

        <div class='card'>
            <h2>Send Pulse</h2>
            <form method='post'>
                <input name='sender_username' value='{safe(session.get("member", "guest"))}' placeholder='Your username' required>
                <input name='receiver_username' placeholder='Receiver username optional'>
                <select name='pulse_type'>
                    <option>direct</option>
                    <option>support</option>
                    <option>normal</option>
                    <option>need</option>
                    <option>story</option>
                </select>
                <textarea name='body' placeholder='Write your Pulse' required></textarea>
                <button type='submit'>Send Pulse</button>
            </form>
        </div>

        <h2>Latest Pulse Records</h2>
        <section class='grid'>{messages}</section>
        """,
        ["Community Power", "Pulse Inbox"]
    )

@app.route("/world-cup/tournament")
def worldcup_tournament():
    """World Cup tournament center"""
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
        """,
        ["World Cup", "Tournament"]
    )

# ==# ============================================================================
# OAP MOVEMENT / COMMUNITY POWER / OAP PULSE ROUTES
# ============================================================================
@app.route("/pulse-directory", methods=["GET", "POST"])
def pulse_directory_page():
    """Pulse Directory - members, riders, merchants, creators, businesses and support"""
    if request.method == "POST":
        username = safe(request.form.get("username", ""))
        display_name = safe(request.form.get("display_name", ""))
        role = safe(request.form.get("role", "member"))
        postcode = safe(request.form.get("postcode", ""))
        borough = safe(request.form.get("borough", ""))
        country = safe(request.form.get("country", ""))
        contact_status = safe(request.form.get("contact_status", "open"))

        if username and display_name:
            con = db()
            try:
                con.execute("""
                    INSERT INTO pulse_directory(
                        username, display_name, role, postcode, borough, country,
                        contact_status, created_at, updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                """, (username, display_name, role, postcode, borough, country, contact_status, now(), now()))
                con.commit()
                audit("pulse_directory_added", f"{username} as {role}")
            finally:
                con.close()

        return redirect("/pulse-directory")

    role_filter = safe(request.args.get("role", ""))
    con = db()
    try:
        if role_filter:
            rows = con.execute("""
                SELECT * FROM pulse_directory
                WHERE role=?
                ORDER BY id DESC
                LIMIT 100
            """, (role_filter,)).fetchall()
        else:
            rows = con.execute("""
                SELECT * FROM pulse_directory
                ORDER BY id DESC
                LIMIT 100
            """).fetchall()
    finally:
        con.close()

    cards = "".join([
        f"""
        <div class='card'>
          <h2>💚 {safe(r['display_name'])}</h2>
          <p><b>@{safe(r['username'])}</b></p>
          <p>Role: {safe(r['role'])}</p>
          <p>{safe(r['postcode'])} {safe(r['borough'])} {safe(r['country'])}</p>
          <small>Status: {safe(r['contact_status'])}</small>
        </div>
        """
        for r in rows
    ]) or "<div class='card'><h2>Directory Open</h2><p>No Pulse Directory records yet.</p></div>"

    return layout(
        "Pulse Directory",
        f"""
        <section class='hero'>
        <h1>🧭 Pulse Directory</h1>
        <p>Find members, riders, merchants, creators, businesses and support contacts inside Community Power.</p>
        </section>

        <section class='grid'>
          <a class='card' href='/pulse-directory'><h2>All</h2><p>Everyone listed.</p></a>
          <a class='card' href='/pulse-directory?role=member'><h2>Members</h2><p>Community members.</p></a>
          <a class='card' href='/pulse-directory?role=rider'><h2>Riders</h2><p>Field movement.</p></a>
          <a class='card' href='/pulse-directory?role=merchant'><h2>Merchants</h2><p>Local business support.</p></a>
          <a class='card' href='/pulse-directory?role=creator'><h2>Creators</h2><p>Artists and media.</p></a>
          <a class='card' href='/pulse-directory?role=support'><h2>Support</h2><p>Community support.</p></a>
        </section>

        <div class='card'>
        <h2>Add Directory Record</h2>
        <form method='post'>
          <input name='username' placeholder='username' required>
          <input name='display_name' placeholder='display name' required>
          <select name='role'>
            <option>member</option>
            <option>rider</option>
            <option>merchant</option>
            <option>creator</option>
            <option>business</option>
            <option>support</option>
          </select>
          <input name='postcode' placeholder='postcode optional'>
          <input name='borough' placeholder='borough optional'>
          <input name='country' placeholder='country optional'>
          <select name='contact_status'>
            <option>open</option>
            <option>limited</option>
            <option>private</option>
          </select>
          <button type='submit'>Add to Directory</button>
        </form>
        </div>

        <h2>Directory Records</h2>
        <section class='grid'>{cards}</section>
        """,
        ["Community Power", "Pulse Directory"]
    )
@app.route("/community-power")
def community_power_hub():
    """Community Power hub"""
    con = db()
    try:
        counts = {
            "Spaces": con.execute("SELECT COUNT(*) c FROM pulse_spaces").fetchone()["c"],
            "Linkups": con.execute("SELECT COUNT(*) c FROM pulse_linkups").fetchone()["c"],
            "Records": con.execute("SELECT COUNT(*) c FROM pulse_records").fetchone()["c"],
            "Announcements": con.execute("SELECT COUNT(*) c FROM pulse_announcements").fetchone()["c"],
            "Relays": con.execute("SELECT COUNT(*) c FROM pulse_relays").fetchone()["c"],
            "Trust": con.execute("SELECT COUNT(*) c FROM pulse_trust").fetchone()["c"],
        }
        spaces = con.execute("SELECT * FROM pulse_spaces ORDER BY id ASC LIMIT 20").fetchall()
        latest = con.execute("SELECT * FROM pulse_records ORDER BY id DESC LIMIT 10").fetchall()
    finally:
        con.close()

    count_cards = "".join([
        f"<div class='card'><div class='metric'>{v}</div><h2>{k}</h2></div>"
        for k, v in counts.items()
    ])

    space_cards = "".join([
        f"<a class='card' href='/oap-pulse/space/{s['id']}'><h2>💚 {safe(s['name'])}</h2><p>{safe(s['purpose'])}</p><small>{safe(s['space_type'])}</small></a>"
        for s in spaces
    ])

    latest_html = "".join([
        f"<div class='card'><h2>{safe(r['pulse_type'])}</h2><p>{safe(r['body'])}</p><small>{safe(r['sender_username'])} • {safe(r['created_at'])}</small></div>"
        for r in latest
    ]) or "<div class='card'><h2>First Pulse Waiting</h2><p>No records yet. Start the heartbeat.</p></div>"

    return layout("Community Power", f"""
    <section class='hero'>
    <h1>⚡ Community Power</h1>
    <h2>OAP Movement is the mission. Community Power is the engine. OAP Pulse is the heartbeat.</h2>
    <p><b>Earth Is Our Turf.</b> Link up, support, organise, announce, and record what matters.</p>
    </section>

    <section class='grid'>
      <a class='card' href='/oap-pulse/spaces'><h2>🌍 Pulse Spaces</h2><p>Community rooms and postcode spaces.</p></a>
      <a class='card' href='/oap-pulse/linkup'><h2>🔗 Pulse Linkup</h2><p>Start a human connection thread.</p></a>
      <a class='card' href='/oap-pulse/announcement'><h2>📣 Announce</h2><p>Share public movement notices.</p></a>
      <a class='card' href='/oap-pulse/relay'><h2>🔁 Relay</h2><p>Pass urgent updates across spaces.</p></a>
      <a class='card' href='/oap-pulse/trust'><h2>🛡 Trust</h2><p>Report, verify and protect the movement.</p></a>
    </section>

    <h2>Pulse Metrics</h2>
    <section class='grid'>{count_cards}</section>

    <h2>Pulse Spaces</h2>
    <section class='grid'>{space_cards}</section>

    <h2>Latest Pulse Records</h2>
    <section class='grid'>{latest_html}</section>
    """, ["OAP Movement", "Community Power"])

@app.route("/the-link")
def the_link():
    return layout(
        "The Link",
        """
        <section class='hero'>
            <h1>💬 The Link</h1>
            <p>Simple chat. Talk local. Build global.</p>
        </section>

        <section class='grid'>
            <a class='card' href='/pulse-directory'>
                <h2>🧭 Directory</h2>
                <p>Find people and businesses.</p>
            </a>

            <a class='card' href='/pulse-inbox'>
                <h2>📥 Inbox</h2>
                <p>View direct records.</p>
            </a>

            <a class='card' href='/community-power'>
                <h2>⚡ Community Power</h2>
                <p>Return to the movement hub.</p>
            </a>
        </section>

        <div class='card'>
            <h2>The Link is Live</h2>
            <p>Quick chat arrives next. This is the front door.</p>
        </div>
        """,
        ["Community Power", "The Link"]
    )

@app.route("/my-energy")
def my_energy():
    energies = [
        "🔥 Building",
        "🚀 Launching",
        "🏪 In Business",
        "🎨 Creating",
        "🤝 Connecting",
        "💚 Supporting",
        "🌍 Exploring",
        "🛡 On Duty",
        "🎯 Focused",
        "🔕 Quiet Mode",
        "😴 Recharging",
        "🎉 Celebrating",
        "🚚 On The Move",
        "📚 Learning"
    ]

    cards = "".join([
        f"<div class='card'><h2>{energy}</h2></div>"
        for energy in energies
    ])

    return layout(
        "My Energy",
        f"""
        <section class='hero'>
            <h1>⚡ My Energy</h1>
            <p>How you're showing up today.</p>
            <p><b>Born Local. Built Global.</b></p>
        </section>

        <section class='grid'>
            {cards}
        </section>
        """,
        ["Community Power", "My Energy"]
    )
@app.route("/signals")
def signals():
    signal_cards = [
        ("📡 Community Signal", "Community updates and announcements."),
        ("🏪 Business Signal", "Business offers and opportunities."),
        ("🎨 Creator Signal", "Creator drops and promotions."),
        ("🎪 Event Signal", "Upcoming gatherings and experiences."),
        ("🛡 Trust Signal", "Verification and trust notices."),
        ("⚠️ Important Signal", "Priority alerts."),
        ("🚚 Operations Signal", "Field and delivery updates."),
        ("🧠 HRM Signal", "Memory, lessons and reviews.")
    ]

    cards = "".join([
        f"""
        <div class='card'>
            <h2>{title}</h2>
            <p>{desc}</p>
        </div>
        """
        for title, desc in signal_cards
    ])

    return layout(
        "Signals",
        f"""
        <section class='hero'>
            <h1>📡 Signals</h1>
            <p>The heartbeat of OAP.</p>
            <p><b>Born Local. Built Global.</b></p>
        </section>

        <section class='grid'>
            {cards}
        </section>
        """,
        ["Community Power", "Signals"]
    )
@app.route("/oap-pulse")
def oap_pulse():
    """OAP Pulse main page"""
    return redirect("/community-power")

@app.route("/born-local")
def born_local_feed():
    cards = "".join([
        """
        <div class='card'>
            <h2>🌍 Born Local</h2>
            <p>Stories from postcodes around the world.</p>
        </div>
        """,
        """
        <div class='card'>
            <h2>🏪 Local Business</h2>
            <p>Support businesses in your area.</p>
        </div>
        """,
        """
        <div class='card'>
            <h2>🎨 Local Creators</h2>
            <p>Discover creators and culture.</p>
        </div>
        """
    ])

    return layout(
        "Born Local",
        f"""
        <section class='hero'>
            <h1>🌍 Born Local</h1>
            <p>Every postcode has a story.</p>
            <p><b>Born Local. Built Global.</b></p>
        </section>

        <section class='grid'>
            {cards}
        </section>
        """,
        ["Community Power", "Born Local"]
    )

@app.route("/oap-pulse/spaces", methods=["GET", "POST"])
def pulse_spaces():
    """Create and view Pulse Spaces"""
    if request.method == "POST":
        name = safe(request.form.get("name", ""))
        purpose = safe(request.form.get("purpose", ""))
        space_type = safe(request.form.get("space_type", "community"))
        postcode = safe(request.form.get("postcode", ""))
        borough = safe(request.form.get("borough", ""))
        country = safe(request.form.get("country", ""))

        if name and purpose:
            con = db()
            try:
                con.execute("""
                    INSERT OR IGNORE INTO pulse_spaces(
                        name,purpose,space_type,postcode,borough,country,created_at
                    ) VALUES(?,?,?,?,?,?,?)
                """, (name, purpose, space_type, postcode, borough, country, now()))
                con.commit()
                audit("pulse_space_created", name)
            finally:
                con.close()
        return redirect("/oap-pulse/spaces")

    con = db()
    try:
        rows = con.execute("SELECT * FROM pulse_spaces ORDER BY id DESC").fetchall()
    finally:
        con.close()

    cards = "".join([
        f"<a class='card' href='/oap-pulse/space/{r['id']}'><h2>🌍 {safe(r['name'])}</h2><p>{safe(r['purpose'])}</p><small>{safe(r['space_type'])} • {safe(r['postcode'])} {safe(r['borough'])} {safe(r['country'])}</small></a>"
        for r in rows
    ]) or "<div class='card'><h2>No spaces yet</h2><p>Create the first Pulse Space.</p></div>"

    return layout("Pulse Spaces", f"""
    <section class='hero'>
    <h1>🌍 Pulse Spaces</h1>
    <p>Postcode rooms, borough rooms, rider spaces, merchant spaces and support spaces.</p>
    </section>

    <div class='card'>
    <h2>Create Pulse Space</h2>
    <form method='post'>
      <input name='name' placeholder='space name' required>
      <input name='purpose' placeholder='purpose' required>
      <select name='space_type'>
        <option>community</option>
        <option>postcode</option>
        <option>borough</option>
        <option>country</option>
        <option>riders</option>
        <option>merchants</option>
        <option>support</option>
        <option>announcement</option>
      </select>
      <input name='postcode' placeholder='postcode optional'>
      <input name='borough' placeholder='borough optional'>
      <input name='country' placeholder='country optional'>
      <button>Create Space</button>
    </form>
    </div>

    <section class='grid'>{cards}</section>
    """, ["Community Power", "Pulse Spaces"])


@app.route("/oap-pulse/space/<int:space_id>", methods=["GET", "POST"])
def pulse_space(space_id):
    """Single Pulse Space"""
    if request.method == "POST":
        sender = safe(request.form.get("sender_username", session.get("member", "guest")))
        body = safe(request.form.get("body", ""))
        pulse_type = safe(request.form.get("pulse_type", "normal"))

        if sender and body:
            con = db()
            try:
                con.execute("""
                    INSERT INTO pulse_records(
                        sender_username, space_id, body, pulse_type, status, created_at
                    ) VALUES(?,?,?,?,?,?)
                """, (sender, space_id, body, pulse_type, "sent", now()))
                con.commit()
                audit("pulse_record_created", f"{sender} in space {space_id}")
            finally:
                con.close()
        return redirect(f"/oap-pulse/space/{space_id}")

    con = db()
    try:
        space = con.execute("SELECT * FROM pulse_spaces WHERE id=?", (space_id,)).fetchone()
        records = con.execute("SELECT * FROM pulse_records WHERE space_id=? ORDER BY id DESC LIMIT 50", (space_id,)).fetchall()
    finally:
        con.close()

    if not space:
        return not_found(None)

    records_html = "".join([
        f"<div class='card'><h2>{safe(r['sender_username'])}</h2><p>{safe(r['body'])}</p><small>{safe(r['pulse_type'])} • {safe(r['created_at'])}</small></div>"
        for r in records
    ]) or "<div class='card'><h2>Open Space</h2><p>No Pulse Records yet.</p></div>"

    return layout(safe(space["name"]), f"""
    <section class='hero'>
    <h1>💚 {safe(space['name'])}</h1>
    <p>{safe(space['purpose'])}</p>
    <small>{safe(space['space_type'])} • {safe(space['postcode'])} {safe(space['borough'])} {safe(space['country'])}</small>
    </section>

    <div class='card'>
    <h2>Send Pulse Record</h2>
    <form method='post'>
      <input name='sender_username' value='{safe(session.get("member", "guest"))}' placeholder='username' required>
      <select name='pulse_type'>
        <option>normal</option>
        <option>support</option>
        <option>need</option>
        <option>story</option>
        <option>rider-update</option>
        <option>merchant-update</option>
        <option>verified-safety</option>
      </select>
      <textarea name='body' placeholder='Write what matters' required></textarea>
      <button>Record Pulse</button>
    </form>
    </div>

    <section class='grid'>{records_html}</section>
    """, ["Community Power", "Pulse Spaces", safe(space["name"])])


@app.route("/oap-pulse/linkup", methods=["GET", "POST"])
def pulse_linkup():
    """Pulse Linkup threads"""
    if request.method == "POST":
        title = safe(request.form.get("title", ""))
        created_by = safe(request.form.get("created_by", session.get("member", "guest")))
        linkup_type = safe(request.form.get("linkup_type", "group"))
        space_id = request.form.get("space_id") or None

        con = db()
        try:
            con.execute("""
                INSERT INTO pulse_linkups(title,linkup_type,space_id,created_by,status,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)
            """, (title, linkup_type, space_id, created_by, "open", now(), now()))
            con.commit()
            audit("pulse_linkup_created", title)
        finally:
            con.close()
        return redirect("/oap-pulse/linkup")

    con = db()
    try:
        spaces = con.execute("SELECT * FROM pulse_spaces ORDER BY name ASC").fetchall()
        linkups = con.execute("SELECT * FROM pulse_linkups ORDER BY id DESC LIMIT 50").fetchall()
    finally:
        con.close()

    options = "".join([f"<option value='{s['id']}'>{safe(s['name'])}</option>" for s in spaces])
    rows = "".join([
        f"<div class='card'><h2>🔗 {safe(l['title'])}</h2><p>{safe(l['linkup_type'])} • {safe(l['status'])}</p><small>Created by {safe(l['created_by'])}</small></div>"
        for l in linkups
    ]) or "<div class='card'><h2>No Linkups</h2><p>Start the first Pulse Linkup.</p></div>"

    return layout("Pulse Linkup", f"""
    <section class='hero'>
    <h1>🔗 Pulse Linkup</h1>
    <p>Human connection threads for members, riders, merchants and support.</p>
    </section>

    <div class='card'>
    <form method='post'>
      <input name='title' placeholder='linkup title' required>
      <input name='created_by' value='{safe(session.get("member", "guest"))}' required>
      <select name='linkup_type'>
        <option>group</option>
        <option>direct</option>
        <option>support</option>
        <option>rider</option>
        <option>merchant</option>
      </select>
      <select name='space_id'>
        <option value=''>No space</option>
        {options}
      </select>
      <button>Create Linkup</button>
    </form>
    </div>

    <section class='grid'>{rows}</section>
    """, ["Community Power", "Pulse Linkup"])


@app.route("/oap-pulse/announcement", methods=["GET", "POST"])
def pulse_announcement():
    """Pulse announcements"""
    if request.method == "POST":
        sender = safe(request.form.get("sender_username", session.get("member", "guest")))
        target = safe(request.form.get("target", "community"))
        title = safe(request.form.get("title", ""))
        body = safe(request.form.get("body", ""))
        priority = safe(request.form.get("priority", "normal"))

        con = db()
        try:
            con.execute("""
                INSERT INTO pulse_announcements(sender_username,target,title,body,priority,created_at)
                VALUES(?,?,?,?,?,?)
            """, (sender, target, title, body, priority, now()))
            con.commit()
            audit("pulse_announcement_created", title)
        finally:
            con.close()
        return redirect("/oap-pulse/announcement")

    con = db()
    try:
        rows = con.execute("SELECT * FROM pulse_announcements ORDER BY id DESC LIMIT 50").fetchall()
    finally:
        con.close()

    cards = "".join([
        f"<div class='card'><h2>📣 {safe(r['title'])}</h2><p>{safe(r['body'])}</p><small>{safe(r['target'])} • {safe(r['priority'])} • {safe(r['created_at'])}</small></div>"
        for r in rows
    ]) or "<div class='card'><h2>No announcements</h2><p>Share the first movement notice.</p></div>"

    return layout("Pulse Announcements", f"""
    <section class='hero'>
    <h1>📣 Pulse Announcements</h1>
    <p>Public community notices and OAP Movement updates.</p>
    </section>

    <div class='card'>
    <form method='post'>
      <input name='sender_username' value='{safe(session.get("member", "guest"))}' required>
      <input name='target' placeholder='community / riders / merchants / country' value='community' required>
      <input name='title' placeholder='announcement title' required>
      <select name='priority'>
        <option>normal</option>
        <option>important</option>
        <option>urgent</option>
      </select>
      <textarea name='body' placeholder='announcement body' required></textarea>
      <button>Post Announcement</button>
    </form>
    </div>

    <section class='grid'>{cards}</section>
    """, ["Community Power", "Announcements"])


@app.route("/oap-pulse/relay", methods=["GET", "POST"])
def pulse_relay():
    """Pulse Relay"""
    if request.method == "POST":
        sender = safe(request.form.get("sender_username", session.get("member", "guest")))
        from_space_id = request.form.get("from_space_id") or None
        to_space_id = request.form.get("to_space_id") or None
        title = safe(request.form.get("title", ""))
        body = safe(request.form.get("body", ""))
        relay_type = safe(request.form.get("relay_type", "community"))

        con = db()
        try:
            con.execute("""
                INSERT INTO pulse_relays(
                    sender_username,from_space_id,to_space_id,title,body,relay_type,verification_status,created_at
                ) VALUES(?,?,?,?,?,?,?,?)
            """, (sender, from_space_id, to_space_id, title, body, relay_type, "unverified", now()))
            con.commit()
            audit("pulse_relay_created", title)
        finally:
            con.close()
        return redirect("/oap-pulse/relay")

    con = db()
    try:
        spaces = con.execute("SELECT * FROM pulse_spaces ORDER BY name ASC").fetchall()
        relays = con.execute("SELECT * FROM pulse_relays ORDER BY id DESC LIMIT 50").fetchall()
    finally:
        con.close()

    options = "".join([f"<option value='{s['id']}'>{safe(s['name'])}</option>" for s in spaces])
    cards = "".join([
        f"<div class='card'><h2>🔁 {safe(r['title'])}</h2><p>{safe(r['body'])}</p><small>{safe(r['relay_type'])} • {safe(r['verification_status'])} • {safe(r['created_at'])}</small></div>"
        for r in relays
    ]) or "<div class='card'><h2>No relays</h2><p>Relay important updates across the movement.</p></div>"

    return layout("Pulse Relay", f"""
    <section class='hero'>
    <h1>🔁 Pulse Relay</h1>
    <p>Urgent updates passed from space to space. Verify before crisis sharing.</p>
    </section>

    <div class='card'>
    <form method='post'>
      <input name='sender_username' value='{safe(session.get("member", "guest"))}' required>
      <select name='from_space_id'><option value=''>From Space</option>{options}</select>
      <select name='to_space_id'><option value=''>To Space</option>{options}</select>
      <input name='title' placeholder='relay title' required>
      <select name='relay_type'>
        <option>community</option>
        <option>event</option>
        <option>rider</option>
        <option>merchant</option>
        <option>support</option>
        <option>safety</option>
      </select>
      <textarea name='body' placeholder='relay update' required></textarea>
      <button>Create Relay</button>
    </form>
    </div>

    <section class='grid'>{cards}</section>
    """, ["Community Power", "Pulse Relay"])


@app.route("/oap-pulse/trust", methods=["GET", "POST"])
def pulse_trust():
    """Pulse Trust and safety reports"""
    if request.method == "POST":
        reporter = safe(request.form.get("reporter_username", session.get("member", "guest")))
        issue_type = safe(request.form.get("issue_type", "review"))
        details = safe(request.form.get("details", ""))
        record_id = request.form.get("record_id") or None
        space_id = request.form.get("space_id") or None

        con = db()
        try:
            con.execute("""
                INSERT INTO pulse_trust(
                    reporter_username,record_id,space_id,issue_type,details,review_status,created_at
                ) VALUES(?,?,?,?,?,?,?)
            """, (reporter, record_id, space_id, issue_type, details, "pending", now()))
            con.commit()
            audit("pulse_trust_report_created", issue_type)
        finally:
            con.close()
        return redirect("/oap-pulse/trust")

    con = db()
    try:
        rows = con.execute("SELECT * FROM pulse_trust ORDER BY id DESC LIMIT 50").fetchall()
    finally:
        con.close()

    cards = "".join([
        f"<div class='card'><h2>🛡 {safe(r['issue_type'])}</h2><p>{safe(r['details'])}</p><small>{safe(r['review_status'])} • {safe(r['created_at'])}</small></div>"
        for r in rows
    ]) or "<div class='card'><h2>No trust reports</h2><p>Pulse Trust is clean.</p></div>"

    return layout("Pulse Trust", f"""
    <section class='hero'>
    <h1>🛡 Pulse Trust</h1>
    <p>Report, verify and protect the OAP Movement. Human review before real-world action.</p>
    </section>

    <div class='card'>
    <form method='post'>
      <input name='reporter_username' value='{safe(session.get("member", "guest"))}' required>
      <input name='record_id' placeholder='record id optional'>
      <input name='space_id' placeholder='space id optional'>
      <select name='issue_type'>
        <option>review</option>
        <option>misuse</option>
        <option>privacy</option>
        <option>youth-safety</option>
        <option>crisis-verification</option>
        <option>spam</option>
      </select>
      <textarea name='details' placeholder='details' required></textarea>
      <button>Send Trust Report</button>
    </form>
    </div>

    <section class='grid'>{cards}</section>
    """, ["Community Power", "Pulse Trust"])
       
#=============================================================================
# COMMAND & ADMIN ROUTES
# ============================================================================

@app.route("/command")
def command():
    """Master command center"""
    con = db()
    
    try:
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
    finally:
        con.close()
    
    cards = "".join([
        f"<div class='card'><div class='metric'>{v}</div><h2>{k}</h2></div>"
        for k, v in counts.items()
    ])
    
    aud = "".join([
        f"<tr><td>{a['created_at']}</td><td>{a['action']}</td><td>{a['level']}</td><td>{a['detail']}</td></tr>"
        for a in audits
    ]) or "<tr><td colspan='4'>No audit logs yet.</td></tr>"
    
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
    <tr><th>Time</th><th>Action</th><th>Level</th><th>Detail</th></tr>
    {aud}
    </table>
    """
    
    return layout("Command Center", body, ["Control", "Command Center"])

# ============================================================================
# MEMBER AUTHENTICATION ROUTES
# ============================================================================

@app.route("/join", methods=["GET", "POST"])
def join():
    """Join OAP - Member registration"""
    if request.method == "POST":
        nickname = safe(request.form.get("nickname", ""))
        username = safe(request.form.get("username", ""))
        email = safe(request.form.get("email", ""))
        password = request.form.get("password", "")
        
        # Validation
        errors = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        if email and "@" not in email:
            errors.append("Invalid email address")
        
        if errors:
            error_html = "".join([f"<p class='error'>❌ {e}</p>" for e in errors])
            return layout("Join OAP - Errors", f"{error_html}", ["Identity", "Join"])
        
        vals = (
            nickname,
            username,
            email,
            generate_password_hash(password),
            safe(request.form.get("postcode", "")),
            safe(request.form.get("borough", "")),
            safe(request.form.get("county", "")),
            safe(request.form.get("country", "")),
            safe(request.form.get("continent", "")),
            safe(request.form.get("circle", "Community Member - Free")),
            now(),
            now(),
        )
        
        con = db()
        try:
            con.execute("""
                INSERT INTO members(
                    nickname, username, email, password, postcode, borough,
                    county, country, continent, circle, created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, vals)
            con.commit()
            session.permanent = True
            session["member"] = username
            audit("member_joined", username)
            logger.info(f"New member registered: {username}")
            return redirect("/my-world")
        except sqlite3.IntegrityError as e:
            con.close()
            if "username" in str(e):
                error_msg = "Username already exists. Choose another."
            elif "email" in str(e):
                error_msg = "Email already registered."
            else:
                error_msg = "Registration error. Please try again."
            return layout("Registration Error", f"<section class='hero error-box'><h1>Error</h1><p>{error_msg}</p></section>", ["Identity", "Join"])
        except Exception as e:
            con.close()
            logger.error(f"Join error: {str(e)}")
            audit("member_join_error", str(e), "ERROR")
            return server_error(e)
    
    return layout("Join OAP", """
    <section class="hero">
    <h1>🌍 Join OAP</h1>
    <p>Create My World. Become a Legacy Maker.</p>
    </section>
    
    <div class="card">
    <form method="post">
    <div class="form-group">
      <label>Nickname *</label>
      <input name="nickname" placeholder="Your nickname" required>
    </div>
    <div class="form-group">
      <label>Username *</label>
      <input name="username" placeholder="Unique username (3+ characters)" required>
    </div>
    <div class="form-group">
      <label>Email</label>
      <input name="email" type="email" placeholder="Email (optional)">
    </div>
    <div class="form-group">
      <label>Password *</label>
      <input name="password" type="password" placeholder="Password (8+ characters)" required>
    </div>
    <div class="form-group">
      <label>Postcode</label>
      <input name="postcode" placeholder="Postcode">
    </div>
    <div class="form-group">
      <label>Borough</label>
      <input name="borough" placeholder="Borough">
    </div>
    <div class="form-group">
      <label>County / Region</label>
      <input name="county" placeholder="County / Region">
    </div>
    <div class="form-group">
      <label>Country</label>
      <input name="country" placeholder="Country">
    </div>
    <div class="form-group">
      <label>Continent</label>
      <input name="continent" placeholder="Continent">
    </div>
    <div class="form-group">
      <label>Circle</label>
      <select name="circle">
      <option>Community Member - Free</option>
      <option>Postcode Founder - £5</option>
      <option>Borough Builder - £10</option>
      <option>Country Champion - £25</option>
      </select>
    </div>
    <button>Join OAP</button>
    </form>
    </div>
    """, ["Identity", "Join"])

@app.route("/enter", methods=["GET", "POST"])
def enter():
    """Enter My World - Member login"""
    if request.method == "POST":
        username = safe(request.form.get("username", ""))
        password = request.form.get("password", "")
        
        con = db()
        try:
            member = con.execute(
                "SELECT * FROM members WHERE username=? AND active=1",
                (username,)
            ).fetchone()
            con.close()
            
            if member and check_password_hash(member['password'], password):
                session.permanent = True
                session["member"] = username
                session["member_id"] = member['id']
                audit("member_login", username)
                logger.info(f"Member logged in: {username}")
                return redirect("/my-world")
            else:
                audit("member_login_failed", username, "WARNING")
                return layout("Login Failed", "<section class='hero error-box'><h1>Login Failed</h1><p>Check username or password.</p></section>", ["Identity", "Enter"])
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return server_error(e)
    
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
    <p><small>Don't have an account? <a href="/join" style="color:var(--green);">Join OAP</a></small></p>
    </div>
    """, ["Identity", "Enter"])

@app.route("/leave")
def leave():
    """Logout"""
    username = session.get("member", "unknown")
    session.clear()
    audit("member_logout", username)
    logger.info(f"Member logged out: {username}")
    return redirect("/")

@app.route("/my-world")
@login_required
def my_world():
    """Member dashboard"""
    username = session.get("member")
    
    con = db()
    try:
        member = con.execute("SELECT * FROM members WHERE username=? AND active=1", (username,)).fetchone()
        con.close()
        
        if not member:
            session.clear()
            return redirect("/enter")
        
        return layout("My World", f"""
        <section class="hero">
        <h1>👤 My World</h1>
        <p>Welcome, <b>{member['nickname']}</b>.</p>
        <p>{member['postcode'] or 'Postcode'} • {member['borough'] or 'Borough'} • {member['country'] or 'Country'} • {member['continent'] or 'Continent'}</p>
        </section>
        
        <section class="grid">
        <div class="card"><h2>🏆 Circle</h2><p>{member['circle']}</p></div>
        <div class="card"><h2>⚡ Contribution Recorded</h2><p>Your actions become proof.</p></div>
        <div class="card"><h2>💎 SIKA Records</h2><p>Trust and value layer.</p></div>
        <div class="card"><h2>🌳 Family Tree</h2><p>Legacy and relationships.</p></div>
        <a class="card" href="/leave"><h2>Leave My World</h2><p>Sign out safely.</p></a>
        </section>
        """, ["Identity", "My World"])
    except Exception as e:
        logger.error(f"My World error: {str(e)}")
        return server_error(e)

# ============================================================================
# DATA ENTRY ROUTES
# ============================================================================

@app.route("/add-record", methods=["POST"])
def add_record():
    """Add generic record"""
    try:
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
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO records(system,module,title,name,location,category,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("record_added", f"{vals[0]}/{vals[1]}: {vals[2]}")
        return redirect("/" + (vals[0] or ""))
    except Exception as e:
        logger.error(f"Add record error: {str(e)}")
        audit("record_add_error", str(e), "ERROR")
        return server_error(e)

@app.route("/add-business", methods=["POST"])
def add_business():
    """Add business"""
    try:
        vals = (
            safe(request.form.get("name")),
            safe(request.form.get("category")),
            safe(request.form.get("location")),
            safe(request.form.get("contact")),
            safe(request.form.get("status")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO businesses(name,category,location,contact,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("business_added", vals[0])
        return redirect("/operations")
    except Exception as e:
        logger.error(f"Add business error: {str(e)}")
        return server_error(e)

@app.route("/add-creator", methods=["POST"])
def add_creator():
    """Add creator"""
    try:
        vals = (
            safe(request.form.get("name")),
            safe(request.form.get("category")),
            safe(request.form.get("country")),
            safe(request.form.get("link")),
            safe(request.form.get("bio")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO creators(name,category,country,link,bio,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("creator_added", vals[0])
        return redirect("/operations")
    except Exception as e:
        logger.error(f"Add creator error: {str(e)}")
        return server_error(e)

@app.route("/add-experience", methods=["POST"])
def add_experience():
    """Add experience"""
    try:
        vals = (
            safe(request.form.get("title")),
            safe(request.form.get("location")),
            safe(request.form.get("date_note")),
            safe(request.form.get("category")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO experiences(title,location,date_note,category,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("experience_added", vals[0])
        return redirect("/operations")
    except Exception as e:
        logger.error(f"Add experience error: {str(e)}")
        return server_error(e)

@app.route("/add-delivery", methods=["POST"])
def add_delivery():
    """Add delivery booking"""
    try:
        vals = (
            safe(request.form.get("customer")),
            safe(request.form.get("pickup")),
            safe(request.form.get("dropoff")),
            safe(request.form.get("item")),
            safe(request.form.get("transport")),
            safe(request.form.get("status")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO delivery_bookings(customer,pickup,dropoff,item,transport,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("delivery_added", vals[3])
        return redirect("/operations")
    except Exception as e:
        logger.error(f"Add delivery error: {str(e)}")
        return server_error(e)

@app.route("/add-rider-driver", methods=["POST"])
def add_rider_driver():
    """Add rider/driver"""
    try:
        vals = (
            safe(request.form.get("name")),
            safe(request.form.get("role")),
            safe(request.form.get("vehicle")),
            safe(request.form.get("area")),
            safe(request.form.get("status")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO riders_drivers(name,role,vehicle,area,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("rider_driver_added", vals[0])
        return redirect("/operations")
    except Exception as e:
        logger.error(f"Add rider/driver error: {str(e)}")
        return server_error(e)

@app.route("/add-sika", methods=["POST"])
def add_sika():
    """Add SIKA record"""
    try:
        try:
            points = int(request.form.get("points") or 1)
        except ValueError:
            points = 1
        
        vals = (
            safe(request.form.get("name")),
            safe(request.form.get("record_type")),
            safe(request.form.get("value_note")),
            points,
            safe(request.form.get("status")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO sika_records(name,record_type,value_note,points,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("sika_added", vals[0])
        return redirect("/money")
    except Exception as e:
        logger.error(f"Add SIKA error: {str(e)}")
        return server_error(e)

@app.route("/add-verification", methods=["POST"])
def add_verification():
    """Add verification badge"""
    try:
        vals = (
            safe(request.form.get("name")),
            safe(request.form.get("level")),
            safe(request.form.get("location")),
            safe(request.form.get("status")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO verification_badges(name,level,location,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("verification_added", vals[0])
        return redirect("/identity")
    except Exception as e:
        logger.error(f"Add verification error: {str(e)}")
        return server_error(e)

@app.route("/add-readiness", methods=["POST"])
def add_readiness():
    """Add readiness request"""
    try:
        vals = (
            safe(request.form.get("area")),
            safe(request.form.get("request_type")),
            safe(request.form.get("applicant")),
            safe(request.form.get("location")),
            safe(request.form.get("status")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO readiness_requests(area,request_type,applicant,location,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("readiness_added", f"{vals[0]}/{vals[1]}")
        return redirect("/command")
    except Exception as e:
        logger.error(f"Add readiness error: {str(e)}")
        return server_error(e)

@app.route("/add-dispatch", methods=["POST"])
def add_dispatch():
    """Add dispatch job"""
    try:
        vals = (
            safe(request.form.get("customer")),
            safe(request.form.get("pickup")),
            safe(request.form.get("dropoff")),
            safe(request.form.get("item")),
            safe(request.form.get("rider")),
            safe(request.form.get("status")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO dispatch_jobs(customer,pickup,dropoff,item,rider,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        return redirect("/dispatch")
    except Exception as e:
        logger.error(f"Add dispatch error: {str(e)}")
        return server_error(e)

@app.route("/add-community-power", methods=["POST"])
def add_community_power():
    """Record community contribution"""
    try:
        vals = (
            safe(request.form.get("member")),
            safe(request.form.get("mission")),
            safe(request.form.get("category")),
            int(request.form.get("points", 1)),
            now()
        )
        
        con = db()
        con.execute(
            "INSERT INTO community_power(member,mission,category,points,created_at) VALUES(?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("community_power", vals[1])
        return redirect("/community-power")
    except Exception as e:
        logger.error(f"Add community power error: {str(e)}")
        return server_error(e)

@app.route("/send-mail", methods=["POST"])
def send_mail():
    """Send mail"""
    try:
        vals = (
            safe(request.form.get("sender")),
            safe(request.form.get("receiver")),
            safe(request.form.get("subject")),
            safe(request.form.get("body")),
            safe(request.form.get("folder")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO mail_items(sender,receiver,subject,body,folder,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("mail_sent", f"{vals[0]} to {vals[1]}")
        return redirect("/mail")
    except Exception as e:
        logger.error(f"Send mail error: {str(e)}")
        return server_error(e)

@app.route("/add-notification", methods=["POST"])
def add_notification():
    """Add notification"""
    try:
        vals = (
            safe(request.form.get("title")),
            safe(request.form.get("body")),
            safe(request.form.get("status")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO notifications(title,body,status,created_at,updated_at) VALUES(?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        audit("notification_added", vals[0])
        return redirect("/notifications")
    except Exception as e:
        logger.error(f"Add notification error: {str(e)}")
        return server_error(e)

@app.route("/add-place", methods=["POST"])
def add_place():
    """Add map place"""
    try:
        vals = (
            safe(request.form.get("place_name")),
            safe(request.form.get("category")),
            safe(request.form.get("location")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO map_places(place_name,category,location,notes,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        return redirect("/maps-hub")
    except Exception as e:
        logger.error(f"Add place error: {str(e)}")
        return server_error(e)

@app.route("/add-route", methods=["POST"])
def add_route():
    """Add navigation route"""
    try:
        vals = (
            safe(request.form.get("start_point")),
            safe(request.form.get("destination")),
            safe(request.form.get("transport_type")),
            safe(request.form.get("status")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO navigation_routes(start_point,destination,transport_type,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        return redirect("/navigation-hub")
    except Exception as e:
        logger.error(f"Add route error: {str(e)}")
        return server_error(e)

@app.route("/add-weather", methods=["POST"])
def add_weather():
    """Add weather record"""
    try:
        vals = (
            safe(request.form.get("location")),
            safe(request.form.get("condition")),
            safe(request.form.get("temperature")),
            safe(request.form.get("notes")),
            now(),
            now(),
        )
        
        con = db()
        con.execute(
            "INSERT INTO weather_records(location,condition,temperature,notes,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            vals
        )
        con.commit()
        con.close()
        
        return redirect("/weather-hub")
    except Exception as e:
        logger.error(f"Add weather error: {str(e)}")
        return server_error(e)

# ============================================================================
# DISPLAY ROUTES
# ============================================================================

@app.route("/dispatch")
def dispatch():
    """Dispatch board"""
    page, limit, offset = get_pagination(request)
    con = db()
    
    try:
        rows = con.execute(
            "SELECT * FROM dispatch_jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = con.execute("SELECT COUNT(*) as c FROM dispatch_jobs").fetchone()['c']
    finally:
        con.close()
    
    jobs = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['customer']}</td><td>{r['pickup']}</td><td>{r['dropoff']}</td><td>{r['status']}</td></tr>"
        for r in rows
    ]) or "<tr><td colspan='5'>No dispatch jobs yet.</td></tr>"
    
    pagination = pagination_links(page, total, limit, "/dispatch")
    
    return layout(
        "Dispatch Board",
        f"""
        <section class='hero'>
        <h1>🚚 Dispatch Board</h1>
        <p>Bookings, deliveries and operations.</p>
        </section>
        
        <div class='card'>
        <h2>Create Booking</h2>
        <form method='post' action='/add-dispatch'>
        <input name='customer' placeholder='Customer' required>
        <input name='pickup' placeholder='Pickup' required>
        <input name='dropoff' placeholder='Dropoff' required>
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
        <tr><th>Time</th><th>Customer</th><th>Pickup</th><th>Dropoff</th><th>Status</th></tr>
        {jobs}
        </table>
        {pagination}
        """,
        ["Operations", "Dispatch"]
    )

@app.route("/community-power")
def community_power():
    """Community power tracking"""
    page, limit, offset = get_pagination(request)
    con = db()
    
    try:
        rows = con.execute(
            "SELECT * FROM community_power ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = con.execute("SELECT COUNT(*) as c FROM community_power").fetchone()['c']
    finally:
        con.close()
    
    table_rows = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['member']}</td><td>{r['mission']}</td><td>{r['category']}</td><td>{r['points']}</td></tr>"
        for r in rows
    ]) or "<tr><td colspan='5'>No contributions yet.</td></tr>"
    
    pagination = pagination_links(page, total, limit, "/community-power")
    
    return layout(
        "Community Power",
        f"""
        <section class='hero'>
            <h1>⚡ Community Power</h1>
            <p>Community action. Contribution recorded.</p>
        </section>
        
        <div class='card'>
            <h2>Record Contribution</h2>
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
                
                <input type='number' name='points' value='10' min='1'>
                
                <button>Record Contribution</button>
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
        {pagination}
    """,
        ["Operations", "Community Power"]
    )

@app.route("/mail")
def mail():
    """Mail system"""
    page, limit, offset = get_pagination(request)
    con = db()
    
    try:
        rows = con.execute(
            "SELECT * FROM mail_items ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = con.execute("SELECT COUNT(*) as c FROM mail_items").fetchone()['c']
    finally:
        con.close()
    
    table_rows = "".join([
        f"<tr><td>{m['created_at']}</td><td>{m['folder']}</td><td>{m['sender']}</td><td>{m['receiver']}</td><td>{m['subject']}</td></tr>"
        for m in rows
    ]) or "<tr><td colspan='5'>No mail yet.</td></tr>"
    
    pagination = pagination_links(page, total, limit, "/mail")
    
    return layout("OAP Mail", f"""
    <section class="hero">
         <h1>📧 OAP Mail</h1>
         <p>Inbox, sent, drafts and member communication records.</p>
    </section>
    
    <div class="card">
    <h2>Send Mail</h2>
    <form method="post" action="/send-mail">
    <input name="sender" placeholder="From" required>
    <input name="receiver" placeholder="To" required>
    <input name="subject" placeholder="Subject" required>
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
    {pagination}
    """,
        ["Communications", "Mail"]
    )

@app.route("/notifications")
def notifications():
    """Notifications hub"""
    page, limit, offset = get_pagination(request)
    con = db()
    
    try:
        rows = con.execute(
            "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = con.execute("SELECT COUNT(*) as c FROM notifications").fetchone()['c']
    finally:
        con.close()
    
    table_rows = "".join([
        f"<tr><td>{n['created_at']}</td><td>{n['title']}</td><td>{n['status']}</td><td>{n['body']}</td></tr>"
        for n in rows
    ]) or "<tr><td colspan='4'>No notifications yet.</td></tr>"
    
    pagination = pagination_links(page, total, limit, "/notifications")
    
    return layout("Notifications", f"""
    <section class="hero">
        <h1>🔔 Notifications</h1>
        <p>OAP alerts, system updates and community notices.</p>
    </section>
    
    <div class="card">
    <h2>Create Notification</h2>
    <form method="post" action="/add-notification">
    <input name="title" placeholder="Notification title" required>
    <textarea name="body" placeholder="Notification body"></textarea>
    <select name="status">
    <option>Draft</option>
    <option>Active</option>
    <option>Review</option>
    <option>Archived</option>
    </select>
    <button>Record Notification</button>
    </form>
    </div>
    
    <h2>Notifications</h2>
    <table>
    <tr><th>Time</th><th>Title</th><th>Status</th><th>Body</th></tr>
    {table_rows}
    </table>
    {pagination}
    """,
        ["Communications", "Notifications"]
    )

@app.route("/maps-hub")
def maps_hub():
    """Maps hub"""
    page, limit, offset = get_pagination(request)
    con = db()
    
    try:
        rows = con.execute(
            "SELECT * FROM map_places ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = con.execute("SELECT COUNT(*) as c FROM map_places").fetchone()['c']
    finally:
        con.close()
    
    places = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['place_name']}</td><td>{r['category']}</td><td>{r['location']}</td></tr>"
        for r in rows
    ]) or "<tr><td colspan='4'>No places yet.</td></tr>"
    
    pagination = pagination_links(page, total, limit, "/maps-hub")
    
    return layout(
        "Maps Hub",
        f"""
        <section class='hero'>
            <h1>🗺 Maps Hub</h1>
            <p>Places, businesses, landmarks and communities.</p>
        </section>
        
        <div class='card'>
            <h2>Add Place</h2>
            <form method='post' action='/add-place'>
                <input name='place_name' placeholder='Place Name' required>
                <input name='category' placeholder='Category'>
                <input name='location' placeholder='Location' required>
                <textarea name='notes' placeholder='Notes'></textarea>
                <button>Add Place</button>
            </form>
        </div>
        
        <table>
            <tr><th>Time</th><th>Name</th><th>Category</th><th>Location</th></tr>
            {places}
        </table>
        {pagination}
        """,
        ["Infrastructure", "Maps"]
    )

@app.route("/navigation-hub")
def navigation_hub():
    """Navigation hub"""
    page, limit, offset = get_pagination(request)
    con = db()
    
    try:
        rows = con.execute(
            "SELECT * FROM navigation_routes ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = con.execute("SELECT COUNT(*) as c FROM navigation_routes").fetchone()['c']
    finally:
        con.close()
    
    routes = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['start_point']}</td><td>{r['destination']}</td><td>{r['transport_type']}</td><td>{r['status']}</td></tr>"
        for r in rows
    ]) or "<tr><td colspan='5'>No routes yet.</td></tr>"
    
    pagination = pagination_links(page, total, limit, "/navigation-hub")
    
    return layout(
        "Navigation Hub",
        f"""
        <section class='hero'>
            <h1>🧭 Navigation Hub</h1>
            <p>Community routes, logistics and movement records.</p>
        </section>
        
        <div class='card'>
            <h2>Create Route</h2>
            <form method='post' action='/add-route'>
                <input name='start_point' placeholder='Start' required>
                <input name='destination' placeholder='Destination' required>
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
            <tr><th>Time</th><th>Start</th><th>Destination</th><th>Transport</th><th>Status</th></tr>
            {routes}
        </table>
        {pagination}
        """,
        ["Infrastructure", "Navigation"]
    )

@app.route("/weather-hub")
def weather_hub():
    """Weather hub"""
    page, limit, offset = get_pagination(request)
    con = db()
    
    try:
        rows = con.execute(
            "SELECT * FROM weather_records ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = con.execute("SELECT COUNT(*) as c FROM weather_records").fetchone()['c']
    finally:
        con.close()
    
    weather = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['location']}</td><td>{r['condition']}</td><td>{r['temperature']}</td></tr>"
        for r in rows
    ]) or "<tr><td colspan='4'>No weather records yet.</td></tr>"
    
    pagination = pagination_links(page, total, limit, "/weather-hub")
    
    return layout(
        "Weather Hub",
        f"""
        <section class='hero'>
        <h1>🌦 Weather Hub</h1>
        <p>Postcode → Borough → Country → Global weather records.</p>
        </section>
        
        <div class='card'>
        <h2>Record Weather</h2>
        <form method='post' action='/add-weather'>
        <input name='location' placeholder='Location' required>
        <input name='condition' placeholder='Condition' required>
        <input name='temperature' placeholder='Temperature'>
        <textarea name='notes' placeholder='Notes'></textarea>
        <button>Record Weather</button>
        </form>
        </div>
        
        <table>
        <tr><th>Time</th><th>Location</th><th>Condition</th><th>Temperature</th></tr>
        {weather}
        </table>
        {pagination}
        """,
        ["Infrastructure", "Weather"]
    )

# ============================================================================
# HRM SOVEREIGN MEGAVERSE INTELLIGENCE - PUBLIC AI
# ============================================================================

@app.route("/world-watch/ai-sync")
def world_watch_ai_sync():
    """HRM World Watch Intelligence: public AI summaries from verified facts only"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return layout(
            "HRM World Watch Intelligence",
            """
            <section class='hero'>
                <h1>🧠🌍👑 HRM Sovereign Megaverse Intelligence</h1>
                <p>OPENAI_API_KEY is missing in Render environment.</p>
            </section>
            <div class='card'>
                <h2>Setup Needed</h2>
                <p>Add OPENAI_API_KEY in Render Environment, then redeploy.</p>
            </div>
            """,
            ["World Watch", "AI Sync"]
        )

    verified_facts = """
    Mexico 2-0 South Africa. Group A. Finished.
    South Korea 2-1 Czechia. Group A. Finished.
    Canada vs Bosnia and Herzegovina. Group B. Upcoming.
    USA vs Paraguay. Group D. Upcoming.
    """

    prompt = f"""
You are HRM Sovereign Megaverse Intelligence for ON ANY POSTCODE.

Master doctrine:
Born Local. Built Global.
Human First. AI Assisted.
Protect life. Preserve dignity.
Facts first. Stories connect.
Humanity decides.

Use ONLY the verified facts below.
Do not invent scores, players, times, venues, injuries, cards, or standings.

Output in short public OAP style:
1. World Watch Summary
2. What Changed
3. Next Watch Points
4. HRM Lesson
5. Humanitarian / Community Note

VERIFIED FACTS:
{verified_facts}
"""

    payload = json.dumps({
        "model": "gpt-4o-mini",
        "input": prompt
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode("utf-8"))
            
# ===text = data.get("output_text", "No summary returned.")
    except Exception as e:
        text = f"AI sync failed: {str(e)}"

# ============================================================================
# HEALTH CHECK & API ENDPOINTS
# ============================================================================
@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        con = db()
        con.execute("SELECT 1")
        con.close()
        return jsonify({"status": "healthy", "timestamp": now()}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route("/api/stats")
def api_stats():
    """API stats endpoint"""
    con = db()
    try:
        stats = {
            "members": con.execute("SELECT COUNT(*) c FROM members").fetchone()["c"],
            "records": con.execute("SELECT COUNT(*) c FROM records").fetchone()["c"],
            "businesses": con.execute("SELECT COUNT(*) c FROM businesses").fetchone()["c"],
            "timestamp": now()
        }
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        con.close()

# ============================================================================
# APP STARTUP
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("FLASK_ENV") != "production"
    )
