from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
ADMIN_USERNAME = "N24-7"
ADMIN_EMAIL = "earthisourturf777@gmail.com"
ADMIN_PASSWORD = "2525"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def h(x):
    return escape(str(x or ""))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def add_col(cur, table, col, coltype):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")

def log(action, username="system"):
    conn = db()
    conn.execute("INSERT INTO audit_logs(action,username,created_at) VALUES(?,?,?)", (action, username, now()))
    conn.commit()
    conn.close()

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'member',
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS news_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        category TEXT,
        summary TEXT,
        body TEXT,
        source_note TEXT,
        verification_status TEXT DEFAULT 'needs review',
        country TEXT DEFAULT 'Global',
        city TEXT DEFAULT '',
        postcode TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        status TEXT DEFAULT 'approved',
        created_at TEXT
    )
    """)

    for col, typ in [
        ("source_note", "TEXT"),
        ("verification_status", "TEXT DEFAULT 'needs review'"),
        ("country", "TEXT DEFAULT 'Global'"),
        ("city", "TEXT DEFAULT ''"),
        ("postcode", "TEXT DEFAULT ''"),
        ("views", "INTEGER DEFAULT 0"),
        ("status", "TEXT DEFAULT 'approved'")
    ]:
        add_col(cur, "news_posts", col, typ)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hrm_event_reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        event_title TEXT,
        event_category TEXT,
        event_type TEXT,
        location TEXT,
        date_note TEXT,
        status_note TEXT,
        source_note TEXT,
        observation TEXT,
        community_impact TEXT,
        economic_impact TEXT,
        safety_note TEXT,
        recommendation TEXT,
        swot_strength TEXT,
        swot_weakness TEXT,
        swot_opportunity TEXT,
        swot_threat TEXT,
        news_post_id INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        event_type TEXT,
        category TEXT,
        country_focus TEXT,
        postcode TEXT,
        city TEXT,
        country TEXT,
        venue TEXT,
        event_date TEXT,
        event_time TEXT,
        description TEXT,
        ticket_price TEXT,
        capacity TEXT,
        contact TEXT,
        status TEXT DEFAULT 'pending',
        views INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )
    """)

    cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,))
    user = cur.fetchone()
    if user:
        cur.execute(
            "UPDATE users SET email=?, password=?, role=? WHERE username=?",
            (ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", ADMIN_USERNAME)
        )
    else:
        cur.execute(
            "INSERT INTO users(username,email,password,role,created_at) VALUES(?,?,?,?,?)",
            (ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", now())
        )

    conn.commit()
    conn.close()

init_db()

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#080808;color:white;font-family:Arial}
.top{background:#111;padding:15px;border-bottom:1px solid #222}
.logo{font-size:22px;font-weight:900}
.wrap{padding:18px;max-width:1100px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:18px;margin:15px 0}
.hero{text-align:center;padding:35px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:12px;margin:8px 0;background:#0c0c0c;color:white;border:1px solid #333;border-radius:10px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:10px;padding:12px 18px;font-weight:800}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:5px 9px;border-radius:999px;font-size:12px;font-weight:bold}
pre{white-space:pre-wrap;font-family:Arial}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/hrm_event_scanner">HRM Event Scanner</a>
<a href="/quick_events">Quick Events</a>
<a href="/event_reports">Event Reports</a>
<a href="/news">News</a>
<a href="/events">Events</a>
<a href="/admin">HRM Admin</a>
</div>
</div>
<div class="wrap">
{{content|safe}}
</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def create_event_news(data, username="HRM"):
    body = f"""
EVENT:
{data['event_title']}

CATEGORY:
{data['event_category']}

TYPE:
{data['event_type']}

LOCATION:
{data['location']}

DATE / TIME NOTE:
{data['date_note']}

STATUS:
{data['status_note']}

OBSERVATION:
{data['observation']}

COMMUNITY IMPACT:
{data['community_impact']}

ECONOMIC IMPACT:
{data['economic_impact']}

SAFETY / VERIFICATION NOTE:
{data['safety_note']}

RECOMMENDATION:
{data['recommendation']}

HRM LAW:
Scan reality.
Record facts.
Create news.
Generate SWOT.
Store lessons.
Recommend next actions.
Humans approve decisions.

MONETIZATION LAW:
Views are observation, not monetization.
Value comes from participation, attendance, product clicks, orders, revenue, repeat engagement, trust records and real-world outcomes.

SWOT:
Strength: {data['swot_strength']}
Weakness: {data['swot_weakness']}
Opportunity: {data['swot_opportunity']}
Threat: {data['swot_threat']}
"""

    conn = db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO news_posts(username,title,category,summary,body,source_note,verification_status,country,city,postcode,views,status,created_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        username,
        data["headline"],
        data["event_category"],
        data["summary"],
        body,
        data["source_note"],
        "needs review",
        data["country"],
        data["city"],
        data["postcode"],
        0,
        "approved",
        now()
    ))

    news_id = cur.lastrowid

    cur.execute("""
    INSERT INTO hrm_event_reports(
        username,event_title,event_category,event_type,location,date_note,status_note,source_note,
        observation,community_impact,economic_impact,safety_note,recommendation,
        swot_strength,swot_weakness,swot_opportunity,swot_threat,news_post_id,created_at
    )
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        username,
        data["event_title"],
        data["event_category"],
        data["event_type"],
        data["location"],
        data["date_note"],
        data["status_note"],
        data["source_note"],
        data["observation"],
        data["community_impact"],
        data["economic_impact"],
        data["safety_note"],
        data["recommendation"],
        data["swot_strength"],
        data["swot_weakness"],
        data["swot_opportunity"],
        data["swot_threat"],
        news_id,
        now()
    ))

    conn.commit()
    conn.close()
    log("HRM generated multi-event news", username)
    return news_id

@app.route("/")
def home():
    conn = db()
    news = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 8").fetchall()
    reports = conn.execute("SELECT * FROM hrm_event_reports ORDER BY id DESC LIMIT 6").fetchall()
    events = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>HRM Multi-Event Intelligence Scanner</p>
    <p>Sports, culture, business, weather, transport, community and humanitarian-safe signals.</p>
    </div>
    <div class='card'>
    <h2>Quick Actions</h2>
    <a class='badge' href='/quick_events'>Quick Event Templates</a>
    <a class='badge' href='/hrm_event_scanner'>Open Event Scanner</a>
    </div>
    <div class='card'><h2>Latest News</h2>
    """

    for n in news:
        content += f"""
        <div class='card'>
        <b>{h(n['title'])}</b><br>
        <span class='gold'>{h(n['category'])}</span>
        <p>{h(n['summary'])}</p>
        <a href='/news/{n['id']}'>Read</a>
        </div>
        """

    content += "</div><div class='card'><h2>HRM Event Reports</h2>"

    for r in reports:
        content += f"""
        <div class='card'>
        <b>{h(r['event_title'])}</b><br>
        <span class='gold'>{h(r['event_category'])}</span>
        <p>{h(r['status_note'])}</p>
        <a href='/news/{r['news_post_id']}'>Open News Record</a>
        </div>
        """

    content += "</div><div class='card'><h2>Events</h2>"

    for e in events:
        content += f"""
        <div class='card'>
        <b>{h(e['title'])}</b><br>
        {h(e['event_date'])} {h(e['event_time'])} • {h(e['city'])}
        </div>
        """

    content += "</div>"
    return render(content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], request.form["password"]):
            session["user"] = user["username"]
            log("User login", user["username"])
            return redirect("/")
        return "Invalid login"

    return render("""
    <div class='card'>
    <h2>Login</h2>
    <form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Login</button>
    </form>
    <p class='small'>Default local admin: N24-7 / 2525</p>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/quick_events")
def quick_events():
    return render("""
    <div class='card hero'>
    <h1>⚡ Quick Event Templates</h1>
    <p class='green'>Generate HRM news records from major event categories.</p>
    </div>
    <div class='grid'>
    <div class='card'><h2>⚽ Sports</h2><a class='badge' href='/quick_event/sports'>Generate</a></div>
    <div class='card'><h2>🎭 Culture</h2><a class='badge' href='/quick_event/culture'>Generate</a></div>
    <div class='card'><h2>🏪 Business</h2><a class='badge' href='/quick_event/business'>Generate</a></div>
    <div class='card'><h2>🌦️ Weather</h2><a class='badge' href='/quick_event/weather'>Generate</a></div>
    <div class='card'><h2>🚆 Transport</h2><a class='badge' href='/quick_event/transport'>Generate</a></div>
    <div class='card'><h2>🤝 Community</h2><a class='badge' href='/quick_event/community'>Generate</a></div>
    <div class='card'><h2>🛡️ Humanitarian-safe</h2><a class='badge' href='/quick_event/humanitarian'>Generate</a></div>
    </div>
    """)

@app.route("/quick_event/<kind>")
def quick_event(kind):
    templates = {
        "sports": {
            "headline": "Major Sports Event Creates Community, Creator and Business Opportunity",
            "summary": "HRM records this sports event as a high-attention signal that can support news, events, local business, creators and community activity.",
            "event_title": "Major Sports Event",
            "event_category": "Sports Intelligence",
            "event_type": "Sports / Match / Tournament",
            "location": "Global / Local",
            "date_note": "Add event date",
            "status_note": "Observed / requires verification",
            "source_note": "Verify scores, fixtures and outcomes from official or trusted sports sources.",
            "observation": "Sport creates attention, emotion, debate and gathering potential.",
            "community_impact": "Watch parties, debates, local meetups, youth-safe sports interest and creator reactions.",
            "economic_impact": "Food, drink, merch, event tickets, business promos and retail drops.",
            "safety_note": "Avoid fake scores, copyright misuse, crowd-risk and unverified claims.",
            "recommendation": "Create news record, event page, creator prompt and business promo opportunity.",
            "country": "Global", "city": "", "postcode": "",
            "swot_strength": "High attention and emotional engagement.",
            "swot_weakness": "Attention does not equal revenue.",
            "swot_opportunity": "Convert sports attention into participation and local commerce.",
            "swot_threat": "Fake results, overclaiming and chasing vanity metrics."
        },
        "culture": {
            "headline": "Culture Event Can Strengthen Community Identity and Creator Economy",
            "summary": "HRM records this culture event as a signal for music, comedy, fashion, art, awards and community storytelling.",
            "event_title": "Major Culture Event",
            "event_category": "Culture Intelligence",
            "event_type": "Music / Comedy / Fashion / Festival",
            "location": "Local / Global",
            "date_note": "Add event date",
            "status_note": "Observed / planning opportunity",
            "source_note": "Verify event details, organisers, venue and rights before public claims.",
            "observation": "Culture creates identity, belonging, entertainment and creator opportunity.",
            "community_impact": "Brings people together through music, humour, fashion, storytelling and celebration.",
            "economic_impact": "Tickets, merch, creator promos, vendor stalls and business visibility.",
            "safety_note": "Protect youth, verify venues, avoid misleading claims and respect copyright.",
            "recommendation": "Create culture news, creator spotlight and event opportunity.",
            "country": "Global", "city": "", "postcode": "",
            "swot_strength": "Strong identity and creative energy.",
            "swot_weakness": "Needs real attendance and organisation.",
            "swot_opportunity": "Build OAP creator/culture economy.",
            "swot_threat": "Copyright misuse, weak moderation or unsafe events."
        },
        "business": {
            "headline": "Business Signal Shows Local Commerce Opportunity",
            "summary": "HRM records this business signal as a potential opportunity for local promotion, retail, partnerships and revenue.",
            "event_title": "Business / Retail Opportunity",
            "event_category": "Business Intelligence",
            "event_type": "Business Launch / Market / Product Drop",
            "location": "Local postcode / city",
            "date_note": "Add date",
            "status_note": "Opportunity observed",
            "source_note": "Verify business details, offer, ownership and contact before promotion.",
            "observation": "Local business activity can create community value and monetization routes.",
            "community_impact": "Supports local services, jobs, products and trusted commerce.",
            "economic_impact": "Promo slots, orders, referrals, vendor fees and repeat customers.",
            "safety_note": "Avoid fake income promises, pyramid pressure and unverified business claims.",
            "recommendation": "Create business profile, promo slot and HRM review.",
            "country": "UK", "city": "London", "postcode": "",
            "swot_strength": "Direct monetization potential.",
            "swot_weakness": "Requires trust and proof.",
            "swot_opportunity": "Turn OAP into local business discovery.",
            "swot_threat": "Low-quality offers or misleading promotions."
        },
        "weather": {
            "headline": "Weather Signal Creates Community Awareness and Operational Planning Need",
            "summary": "HRM records this weather signal as an environmental and operational awareness item.",
            "event_title": "Weather / Environmental Signal",
            "event_category": "Weather Intelligence",
            "event_type": "Weather / Environment",
            "location": "Local area",
            "date_note": "Add date/time",
            "status_note": "Observed / verify forecast",
            "source_note": "Use official weather sources before public alerts.",
            "observation": "Weather affects travel, events, health, business and community safety.",
            "community_impact": "Helps people plan journeys, events, clothing, outdoor activity and safety.",
            "economic_impact": "Affects attendance, delivery, market days and product demand.",
            "safety_note": "Do not panic-post. Verify before sharing. Avoid medical or emergency overclaims.",
            "recommendation": "Create practical awareness post and event planning note.",
            "country": "UK", "city": "London", "postcode": "",
            "swot_strength": "Useful practical intelligence.",
            "swot_weakness": "Forecasts can change.",
            "swot_opportunity": "Build trusted local awareness.",
            "swot_threat": "Panic, misinformation or outdated alerts."
        },
        "transport": {
            "headline": "Transport Signal Affects Local Movement and Event Planning",
            "summary": "HRM records this transport signal as important for events, business access, deliveries and community movement.",
            "event_title": "Transport / Infrastructure Signal",
            "event_category": "Transport Intelligence",
            "event_type": "Road / Rail / Bus / Infrastructure",
            "location": "Local area",
            "date_note": "Add date/time",
            "status_note": "Observed / needs verification",
            "source_note": "Verify with official transport or local authority sources.",
            "observation": "Transport changes affect access, attendance, delivery and local business traffic.",
            "community_impact": "Helps people avoid disruption and plan movement.",
            "economic_impact": "Impacts footfall, events, delivery and business operations.",
            "safety_note": "Avoid unverified disruption claims. Update when resolved.",
            "recommendation": "Create transport note linked to events/businesses.",
            "country": "UK", "city": "London", "postcode": "",
            "swot_strength": "High practical value.",
            "swot_weakness": "Requires current updates.",
            "swot_opportunity": "OAP can become useful local intelligence layer.",
            "swot_threat": "Outdated or inaccurate disruption info."
        },
        "community": {
            "headline": "Community Event Can Build Trust, Participation and Local Identity",
            "summary": "HRM records this community signal as important for belonging, participation and trust building.",
            "event_title": "Community Signal",
            "event_category": "Community Intelligence",
            "event_type": "Community Event / Local Story",
            "location": "Local postcode / city",
            "date_note": "Add date",
            "status_note": "Observed / planning opportunity",
            "source_note": "Verify organisers, location and purpose before promotion.",
            "observation": "Community activity creates belonging, trust and repeat participation.",
            "community_impact": "Strengthens local identity, connection and support.",
            "economic_impact": "Can support vendors, creators, memberships and local businesses.",
            "safety_note": "Protect youth, privacy, dignity and consent.",
            "recommendation": "Create community news and invite safe participation.",
            "country": "UK", "city": "London", "postcode": "",
            "swot_strength": "Strong trust-building potential.",
            "swot_weakness": "Needs real people and follow-through.",
            "swot_opportunity": "Grow OAP through meaningful participation.",
            "swot_threat": "Low attendance or poor moderation."
        },
        "humanitarian": {
            "headline": "Humanitarian-Safe Signal Requires Verification, Dignity and Care",
            "summary": "HRM records this humanitarian-safe signal for awareness, support routing and harm reduction without panic or exploitation.",
            "event_title": "Humanitarian-Safe Signal",
            "event_category": "Humanitarian-safe Intelligence",
            "event_type": "Community Need / Resource / Support",
            "location": "Local / global",
            "date_note": "Add date",
            "status_note": "Needs verification",
            "source_note": "Verify before sharing. Use trusted sources. Preserve dignity and privacy.",
            "observation": "Community needs must be handled carefully, lawfully and respectfully.",
            "community_impact": "Can connect people to resources and support without panic.",
            "economic_impact": "May require donation transparency, resource tracking and no misleading fundraising.",
            "safety_note": "No vigilante action, no target lists, no panic, no unverified fundraising, protect youth.",
            "recommendation": "Record, verify, classify need, connect to lawful support, review before publishing.",
            "country": "Global", "city": "", "postcode": "",
            "swot_strength": "Protects dignity and supports civilians.",
            "swot_weakness": "Sensitive, requires verification and care.",
            "swot_opportunity": "Build trusted humanitarian-safe awareness.",
            "swot_threat": "Misinformation, panic, exploitation or privacy harm."
        }
    }

    data = templates.get(kind, templates["community"])
    news_id = create_event_news(data, session.get("user", "HRM"))
    return redirect(f"/news/{news_id}")

@app.route("/hrm_event_scanner", methods=["GET", "POST"])
def hrm_event_scanner():
    if request.method == "POST":
        data = {
            "headline": request.form["headline"],
            "summary": request.form["summary"],
            "event_title": request.form["event_title"],
            "event_category": request.form["event_category"],
            "event_type": request.form["event_type"],
            "location": request.form["location"],
            "date_note": request.form["date_note"],
            "status_note": request.form["status_note"],
            "source_note": request.form["source_note"],
            "observation": request.form["observation"],
            "community_impact": request.form["community_impact"],
            "economic_impact": request.form["economic_impact"],
            "safety_note": request.form["safety_note"],
            "recommendation": request.form["recommendation"],
            "country": request.form["country"],
            "city": request.form["city"],
            "postcode": request.form["postcode"],
            "swot_strength": request.form["swot_strength"],
            "swot_weakness": request.form["swot_weakness"],
            "swot_opportunity": request.form["swot_opportunity"],
            "swot_threat": request.form["swot_threat"]
        }
        news_id = create_event_news(data, session.get("user", "HRM"))
        return redirect(f"/news/{news_id}")

    return render("""
    <div class='card hero'>
    <h1>🧠 HRM Multi-Event Scanner</h1>
    <p class='green'>Scan sports, culture, business, weather, transport, community and humanitarian-safe signals.</p>
    </div>

    <div class='card'>
    <form method='POST'>
    <input name='headline' value='Major Event Creates Community Intelligence Signal' required>
    <textarea name='summary'>HRM records this event as a real-world signal with community, economic, operational and safety relevance.</textarea>
    <input name='event_title' value='Major Event / Signal' required>
    <select name='event_category'>
    <option>Sports Intelligence</option>
    <option>Culture Intelligence</option>
    <option>Business Intelligence</option>
    <option>Weather Intelligence</option>
    <option>Transport Intelligence</option>
    <option>Community Intelligence</option>
    <option>Humanitarian-safe Intelligence</option>
    </select>
    <input name='event_type' value='Event / Signal'>
    <input name='location' value='Local / Global'>
    <input name='country' value='Global'>
    <input name='city' placeholder='City'>
    <input name='postcode' placeholder='Postcode'>
    <input name='date_note' value='Add date/time'>
    <input name='status_note' value='Observed / needs verification'>
    <textarea name='source_note'>Verify with trusted sources before publishing strong claims.</textarea>
    <textarea name='observation'>What happened, where it happened, who it affects, and why it matters.</textarea>
    <textarea name='community_impact'>How this affects people, belonging, safety, participation or local identity.</textarea>
    <textarea name='economic_impact'>How this may affect products, orders, attendance, local businesses, vendors or revenue.</textarea>
    <textarea name='safety_note'>Protect privacy, youth, dignity, accuracy and lawful action.</textarea>
    <textarea name='recommendation'>Create news record, review risks, identify opportunities, and wait for human approval before action.</textarea>
    <input name='swot_strength' value='High real-world relevance'>
    <input name='swot_weakness' value='Requires verification and follow-through'>
    <input name='swot_opportunity' value='Convert attention into community value'>
    <input name='swot_threat' value='Misinformation, panic, low participation or vanity metrics'>
    <button>Generate HRM Event News</button>
    </form>
    </div>
    """)

@app.route("/event_reports")
def event_reports():
    conn = db()
    rows = conn.execute("SELECT * FROM hrm_event_reports ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = "<div class='card hero'><h1>🌍 HRM Event Reports</h1></div>"

    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['event_title'])}</b><br>
        <span class='gold'>{h(r['event_category'])}</span>
        <p>{h(r['status_note'])}</p>
        <a href='/news/{r['news_post_id']}'>Open News Record</a>
        </div>
        """

    return render(content)

@app.route("/news", methods=["GET", "POST"])
def news():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""
        INSERT INTO news_posts(username,title,category,summary,body,source_note,verification_status,country,city,postcode,views,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            username,
            request.form["title"],
            request.form["category"],
            request.form["summary"],
            request.form["body"],
            request.form["source_note"],
            request.form["verification_status"],
            request.form["country"],
            request.form["city"],
            request.form["postcode"],
            0,
            "pending",
            now()
        ))
        conn.commit()
        conn.close()
        log("News submitted", username)
        return redirect("/news")

    conn = db()
    rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card'>
    <h1>📰 OAP News</h1>
    <form method='POST'>
    <input name='title' placeholder='Title' required>
    <input name='category' value='Community'>
    <input name='country' value='Global'>
    <input name='city' placeholder='City'>
    <input name='postcode' placeholder='Postcode'>
    <textarea name='summary' placeholder='Summary'></textarea>
    <textarea name='body' placeholder='Story'></textarea>
    <textarea name='source_note' placeholder='Source/proof note'></textarea>
    <select name='verification_status'>
    <option>needs review</option>
    <option>verified</option>
    <option>draft</option>
    </select>
    <button>Submit News</button>
    </form>
    </div>
    """

    for n in rows:
        content += f"""
        <div class='card'>
        <b>{h(n['title'])}</b><br>
        <span class='gold'>{h(n['category'])}</span>
        <p>{h(n['summary'])}</p>
        <a href='/news/{n['id']}'>Read</a>
        </div>
        """

    return render(content)

@app.route("/news/<int:id>")
def news_detail(id):
    conn = db()
    n = conn.execute("SELECT * FROM news_posts WHERE id=?", (id,)).fetchone()
    if not n:
        conn.close()
        return "News not found"

    conn.execute("UPDATE news_posts SET views=views+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return render(f"""
    <div class='card'>
    <h1>{h(n['title'])}</h1>
    <p class='gold'>{h(n['category'])}</p>
    <p class='small'>{h(n['country'])} {h(n['city'])} {h(n['postcode'])} • Views: {h(n['views'])}</p>
    <h2>{h(n['summary'])}</h2>
    <pre>{h(n['body'])}</pre>
    <div class='card'>
    <h2>Verification</h2>
    <p>{h(n['source_note'])}</p>
    <p>Status: {h(n['verification_status'])}</p>
    </div>
    </div>
    """)

@app.route("/events", methods=["GET", "POST"])
def events():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""
        INSERT INTO events(username,title,event_type,category,country_focus,postcode,city,country,venue,event_date,event_time,description,ticket_price,capacity,contact,status,views,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            username,
            request.form["title"],
            request.form["event_type"],
            request.form["category"],
            request.form["country_focus"],
            request.form["postcode"],
            request.form["city"],
            request.form["country"],
            request.form["venue"],
            request.form["event_date"],
            request.form["event_time"],
            request.form["description"],
            request.form["ticket_price"],
            request.form["capacity"],
            request.form["contact"],
            "pending",
            0,
            now()
        ))
        conn.commit()
        conn.close()
        log("Event submitted", username)
        return redirect("/events")

    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card'>
    <h1>Events / Watch Parties</h1>
    <form method='POST'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'>
    <option>Watch Party</option>
    <option>Creator Meetup</option>
    <option>Business Popup</option>
    <option>Community Event</option>
    <option>Awareness Event</option>
    </select>
    <input name='category' value='Community'>
    <input name='country_focus' value='Global'>
    <input name='postcode' placeholder='Postcode'>
    <input name='city' placeholder='City'>
    <input name='country' value='UK'>
    <input name='venue' placeholder='Venue'>
    <input name='event_date' placeholder='Date'>
    <input name='event_time' placeholder='Time'>
    <textarea name='description' placeholder='Description'></textarea>
    <input name='ticket_price' placeholder='Ticket price'>
    <input name='capacity' placeholder='Capacity'>
    <input name='contact' placeholder='Contact'>
    <button>Submit Event</button>
    </form>
    </div>
    """

    for e in rows:
        content += f"""
        <div class='card'>
        <b>{h(e['title'])}</b><br>
        <span class='gold'>{h(e['event_type'])} • {h(e['category'])}</span>
        <p>{h(e['event_date'])} {h(e['event_time'])} • {h(e['city'])}</p>
        <p>{h(e['description'])}</p>
        </div>
        """

    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    news = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 80").fetchall()
    events = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 80").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card'><h1>🧠 HRM Admin</h1></div><div class='card'><h2>News Review</h2>"

    for n in news:
        content += f"""
        <div class='card'>
        {h(n['title'])} — {h(n['status'])}
        <a href='/admin/news/{n['id']}/approved'>Approve</a>
        <a href='/admin/news/{n['id']}/rejected'>Reject</a>
        </div>
        """

    content += "</div><div class='card'><h2>Event Review</h2>"

    for e in events:
        content += f"""
        <div class='card'>
        {h(e['title'])} — {h(e['status'])}
        <a href='/admin/event/{e['id']}/approved'>Approve</a>
        <a href='/admin/event/{e['id']}/rejected'>Reject</a>
        </div>
        """

    content += "</div><div class='card'><h2>Audit Logs</h2>"

    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"

    content += "</div>"
    return render(content)

@app.route("/admin/news/<int:id>/<status>")
def admin_news(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE news_posts SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"News {status}", session.get("user", "admin"))
    return redirect("/admin")

@app.route("/admin/event/<int:id>/<status>")
def admin_event(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE events SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"Event {status}", session.get("user", "admin"))
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
