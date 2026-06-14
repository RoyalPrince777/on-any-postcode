from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
ADMIN_USERNAME = "N24-7"
ADMIN_EMAIL = "oap@onanypostcode.local"
ADMIN_PASSWORD = "2525"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def h(x):
    return escape(str(x or ""))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def log(action, username="system"):
    conn = db()
    conn.execute("INSERT INTO audit_logs(action,username,created_at) VALUES(?,?,?)", (action, username, now()))
    conn.commit()
    conn.close()

def add_col(cur, table, col, typ):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        username TEXT UNIQUE,
        oap_email TEXT,
        password TEXT,
        postcode TEXT,
        borough TEXT,
        county_region TEXT,
        country TEXT,
        continent TEXT,
        weather_location TEXT,
        verification_level TEXT DEFAULT 'starter',
        role TEXT DEFAULT 'member',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        event_type TEXT,
        category TEXT,
        postcode TEXT,
        borough TEXT,
        county_region TEXT,
        country TEXT,
        continent TEXT,
        venue TEXT,
        event_date TEXT,
        event_time TEXT,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        recipient TEXT,
        subject TEXT,
        body TEXT,
        status TEXT DEFAULT 'unread',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sports_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        sport TEXT,
        tournament TEXT,
        country_space TEXT,
        title TEXT,
        prediction TEXT,
        swot TEXT,
        body TEXT,
        status TEXT DEFAULT 'approved',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS watch_parties(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        match_title TEXT,
        country_focus TEXT,
        postcode TEXT,
        borough TEXT,
        city TEXT,
        country TEXT,
        venue TEXT,
        event_date TEXT,
        event_time TEXT,
        capacity TEXT,
        ticket_price TEXT,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS country_spaces(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_name TEXT UNIQUE,
        continent TEXT,
        flag_note TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS ai_public_queries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        visitor_name TEXT,
        query TEXT,
        answer TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS personal_hrm_tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        mission TEXT,
        layer TEXT,
        priority TEXT,
        status TEXT DEFAULT 'open',
        swot_strength TEXT,
        swot_weakness TEXT,
        swot_opportunity TEXT,
        swot_threat TEXT,
        next_action TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS private_decision_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        decision_title TEXT,
        decision_body TEXT,
        reason TEXT,
        risk_note TEXT,
        approval_status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS hrm_memory_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_type TEXT,
        title TEXT,
        summary TEXT,
        lesson TEXT,
        next_action TEXT,
        visibility TEXT DEFAULT 'private',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )""")

    for c in ["England", "Ghana", "Nigeria", "Brazil", "Argentina", "France", "Morocco"]:
        cur.execute("INSERT OR IGNORE INTO country_spaces(country_name,continent,flag_note,description,status,created_at) VALUES(?,?,?,?,?,?)",
                    (c, "Global", c + " supporters", "Country space for OAP sports, culture, watch parties and community posts.", "active", now()))

    cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,))
    user = cur.fetchone()
    if user:
        cur.execute("UPDATE users SET nickname=?, oap_email=?, password=?, role=?, verification_level=? WHERE username=?",
                    ("N24-7", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", "founder", ADMIN_USERNAME))
    else:
        cur.execute("""INSERT INTO users(nickname,username,oap_email,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("N24-7", ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "CR4", "Merton", "Greater London", "UK", "Europe", "London", "founder", "admin", now()))

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
body{margin:0;background:#050505;color:white;font-family:Arial}
.top{background:#101010;padding:15px;border-bottom:1px solid #222;position:sticky;top:0;z-index:2}
.logo{font-size:22px;font-weight:900}
.wrap{padding:14px;max-width:1150px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:16px;margin:12px 0}
.hero{text-align:center;padding:30px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:13px;margin:8px 0;background:#0b0b0b;color:white;border:1px solid #333;border-radius:12px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:12px;padding:13px 18px;font-weight:900}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:bold;margin:3px}
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
<a href="/login">Login</a> <a href="/signup">Join</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/community">Community</a>
<a href="/sports">Sports</a>
<a href="/worldcup">World Cup</a>
<a href="/country_spaces">Countries</a>
<a href="/watch_parties">Watch Parties</a>
<a href="/assistant">Website AI</a>
<a href="/search">Search</a>
<a href="/explorer">Explorer</a>
<a href="/events">Events</a>
<a href="/messages">Messenger</a>
<a href="/personal_hrm">HRM</a>
<a href="/admin">Admin</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def save_memory(memory_type, title, summary, lesson, next_action, visibility="private"):
    conn = db()
    conn.execute("INSERT INTO hrm_memory_logs(memory_type,title,summary,lesson,next_action,visibility,created_at) VALUES(?,?,?,?,?,?,?)",
                 (memory_type, title, summary, lesson, next_action, visibility, now()))
    conn.commit()
    conn.close()

def public_ai_answer(query):
    q = (query or "").lower()
    if "world" in q or "cup" in q or "football" in q:
        return "OAP World Cup layer connects watch parties, country spaces, predictions, creators, business promos, sports news and HRM reports. The goal is not to compete with FIFA, but to build the community layer around football."
    if "postcode" in q or "borough" in q:
        return "OAP navigation is Postcode → Borough → County/Region → Country → Continent → Global → Planet → Universe. Trust starts local and expands through contribution."
    if "weather" in q:
        return "OAP Weather is for event planning, field operations, watch parties, riders and local navigation. Add a weather location at signup/profile."
    if "sika" in q:
        return "SIKA starts as contribution and trust records only. It is not legal tender, not e-money and not a bank account."
    if "business" in q:
        return "OAP Business will support listings, offers, promos, vendors and sponsors. Monetization comes from real value, not views."
    return "Welcome to ON ANY POSTCODE. Browse freely, join easily, build trust gradually, and monetize with proof."

@app.route("/")
def home():
    conn = db()
    stats = {
        "users": conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        "events": conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        "watch": conn.execute("SELECT COUNT(*) c FROM watch_parties").fetchone()["c"],
        "sports": conn.execute("SELECT COUNT(*) c FROM sports_posts").fetchone()["c"],
        "countries": conn.execute("SELECT COUNT(*) c FROM country_spaces").fetchone()["c"],
        "messages": conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"],
    }
    posts = conn.execute("SELECT * FROM sports_posts ORDER BY id DESC LIMIT 4").fetchall()
    parties = conn.execute("SELECT * FROM watch_parties ORDER BY id DESC LIMIT 4").fetchall()
    conn.close()
    content = f"""
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>Stable Master Menu + Sports / World Cup Restored</p>
    <p>Born Local 🔥💨🚀 Built Global 💎💦</p>
    </div>
    <div class='grid'>
    <div class='card'><h2>{stats['users']}</h2><p>Users</p></div>
    <div class='card'><h2>{stats['events']}</h2><p>Events</p></div>
    <div class='card'><h2>{stats['watch']}</h2><p>Watch Parties</p></div>
    <div class='card'><h2>{stats['sports']}</h2><p>Sports Posts</p></div>
    <div class='card'><h2>{stats['countries']}</h2><p>Country Spaces</p></div>
    <div class='card'><h2>{stats['messages']}</h2><p>Messages</p></div>
    </div>
    <div class='card'>
    <a class='badge' href='/worldcup'>World Cup</a>
    <a class='badge' href='/sports'>Sports Hub</a>
    <a class='badge' href='/watch_parties'>Watch Parties</a>
    <a class='badge' href='/country_spaces'>Country Spaces</a>
    <a class='badge' href='/assistant'>Ask Website AI</a>
    <a class='badge' href='/explorer'>Explorer</a>
    </div>
    <div class='card'><h2>Latest Sports Posts</h2>
    """
    for p in posts:
        content += f"<div class='card'><b>{h(p['title'])}</b><br>{h(p['sport'])} • {h(p['country_space'])}<p>{h(p['body'])}</p></div>"
    content += "</div><div class='card'><h2>Latest Watch Parties</h2>"
    for w in parties:
        content += f"<div class='card'><b>{h(w['title'])}</b><br>{h(w['postcode'])} • {h(w['country_focus'])}<p>{h(w['description'])}</p></div>"
    content += "</div>"
    return render(content)

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        conn = db()
        try:
            conn.execute("""INSERT INTO users(nickname,username,oap_email,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                request.form["nickname"], request.form["username"], request.form.get("oap_email",""),
                generate_password_hash(request.form["password"]),
                request.form.get("postcode",""), request.form.get("borough",""), request.form.get("county_region",""),
                request.form.get("country",""), request.form.get("continent",""), request.form.get("weather_location",""),
                "starter", "member", now()
            ))
            conn.commit()
            log("User signup", request.form["username"])
            return redirect("/login")
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()
    return render("""
    <div class='card hero'><h1>Join OAP</h1><p class='green'>Fast signup. Geography optional until verification or monetization.</p></div>
    <div class='card'><form method='POST'>
    <input name='nickname' placeholder='Nickname' required>
    <input name='username' placeholder='Username' required>
    <input name='oap_email' placeholder='OAP email optional later'>
    <input name='password' type='password' placeholder='Password' required>
    <input name='postcode' placeholder='Postcode optional'>
    <input name='borough' placeholder='Borough optional'>
    <input name='county_region' placeholder='County / Region optional'>
    <input name='country' placeholder='Country optional'>
    <input name='continent' placeholder='Continent optional'>
    <input name='weather_location' placeholder='Weather location optional'>
    <button>Join</button>
    </form></div>
    """)

@app.route("/login", methods=["GET","POST"])
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
    <div class='card'><h2>Login</h2><form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Login</button>
    </form><p class='small'>Default admin: N24-7 / 2525</p></div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/sports", methods=["GET","POST"])
def sports():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO sports_posts(username,sport,tournament,country_space,title,prediction,swot,body,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["sport"], request.form["tournament"], request.form["country_space"],
            request.form["title"], request.form["prediction"], request.form["swot"], request.form["body"],
            "approved", now()
        ))
        conn.commit()
        conn.close()
        save_memory("sports_post", request.form["title"], "Sports post created.", "Sports creates community energy.", "Connect to watch parties and creators.", "public")
        return redirect("/sports")
    conn = db()
    rows = conn.execute("SELECT * FROM sports_posts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>⚽ Sports Hub</h1><p class='green'>Football, World Cup, AFCON, boxing, Olympics and local sports.</p></div>
    <div class='card'><form method='POST'>
    <select name='sport'><option>Football</option><option>Boxing</option><option>Olympics</option><option>Basketball</option><option>Cricket</option><option>Local Sports</option></select>
    <input name='tournament' placeholder='Tournament e.g. World Cup'>
    <input name='country_space' placeholder='Country space e.g. Ghana'>
    <input name='title' placeholder='Title' required>
    <input name='prediction' placeholder='Prediction'>
    <textarea name='swot' placeholder='SWOT'></textarea>
    <textarea name='body' placeholder='Post body'></textarea>
    <button>Post Sports Update</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['sport'])} • {h(r['tournament'])} • {h(r['country_space'])}<p>{h(r['body'])}</p><p class='gold'>Prediction: {h(r['prediction'])}</p><pre>{h(r['swot'])}</pre></div>"
    return render(content)

@app.route("/worldcup")
def worldcup():
    conn = db()
    parties = conn.execute("SELECT * FROM watch_parties ORDER BY id DESC LIMIT 10").fetchall()
    posts = conn.execute("SELECT * FROM sports_posts WHERE tournament LIKE '%World%' OR tournament LIKE '%Cup%' ORDER BY id DESC LIMIT 10").fetchall()
    countries = conn.execute("SELECT * FROM country_spaces ORDER BY country_name").fetchall()
    conn.close()
    content = """
    <div class='card hero'>
    <h1>🏆 OAP World Cup Energy</h1>
    <p class='green'>Watch parties • country spaces • creator debates • business promos • HRM reports</p>
    </div>
    <div class='card'>
    <a class='badge' href='/watch_parties'>Create Watch Party</a>
    <a class='badge' href='/sports'>Post Prediction</a>
    <a class='badge' href='/country_spaces'>Country Spaces</a>
    </div>
    <div class='card'><h2>Country Spaces</h2><div class='grid'>
    """
    for c in countries:
        content += f"<div class='card'><h2>{h(c['country_name'])}</h2><p>{h(c['description'])}</p></div>"
    content += "</div></div><div class='card'><h2>Watch Parties</h2>"
    for w in parties:
        content += f"<div class='card'><b>{h(w['title'])}</b><br>{h(w['match_title'])} • {h(w['postcode'])} • {h(w['venue'])}</div>"
    content += "</div><div class='card'><h2>Sports Posts</h2>"
    for p in posts:
        content += f"<div class='card'><b>{h(p['title'])}</b><p>{h(p['body'])}</p></div>"
    content += "</div>"
    return render(content)

@app.route("/watch_parties", methods=["GET","POST"])
def watch_parties():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO watch_parties(username,title,match_title,country_focus,postcode,borough,city,country,venue,event_date,event_time,capacity,ticket_price,description,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["title"], request.form["match_title"], request.form["country_focus"],
            request.form["postcode"], request.form["borough"], request.form["city"], request.form["country"],
            request.form["venue"], request.form["event_date"], request.form["event_time"],
            request.form["capacity"], request.form["ticket_price"], request.form["description"], "pending", now()
        ))
        conn.commit()
        conn.close()
        save_memory("watch_party", request.form["title"], "Watch party created.", "Watch parties create community and monetization signals.", "Track RSVP, attendance, business offers.", "public")
        return redirect("/watch_parties")
    conn = db()
    rows = conn.execute("SELECT * FROM watch_parties ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>📅 Watch Parties</h1><p class='green'>Postcode-based sports gatherings.</p></div>
    <div class='card'><form method='POST'>
    <input name='title' placeholder='Watch party title' required>
    <input name='match_title' placeholder='Match e.g. Ghana vs England'>
    <input name='country_focus' placeholder='Country focus'>
    <input name='postcode' placeholder='Postcode'>
    <input name='borough' placeholder='Borough'>
    <input name='city' placeholder='City'>
    <input name='country' placeholder='Country'>
    <input name='venue' placeholder='Venue'>
    <input name='event_date' placeholder='Date'>
    <input name='event_time' placeholder='Time'>
    <input name='capacity' placeholder='Capacity'>
    <input name='ticket_price' placeholder='Ticket / entry price'>
    <textarea name='description' placeholder='Description'></textarea>
    <button>Create Watch Party</button>
    </form></div>
    """
    for w in rows:
        content += f"<div class='card'><b>{h(w['title'])}</b><br>{h(w['match_title'])} • {h(w['postcode'])} • {h(w['country_focus'])}<p>{h(w['description'])}</p>Status: {h(w['status'])}</div>"
    return render(content)

@app.route("/country_spaces", methods=["GET","POST"])
def country_spaces():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT OR IGNORE INTO country_spaces(country_name,continent,flag_note,description,status,created_at) VALUES(?,?,?,?,?,?)",
                     (request.form["country_name"], request.form["continent"], request.form["flag_note"], request.form["description"], "active", now()))
        conn.commit()
        conn.close()
        return redirect("/country_spaces")
    conn = db()
    rows = conn.execute("SELECT * FROM country_spaces ORDER BY country_name").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>🌍 Country Spaces</h1><p class='green'>Supporters, culture, predictions, events and community.</p></div>
    <div class='card'><form method='POST'>
    <input name='country_name' placeholder='Country name' required>
    <input name='continent' placeholder='Continent'>
    <input name='flag_note' placeholder='Flag / identity note'>
    <textarea name='description' placeholder='Description'></textarea>
    <button>Add Country Space</button>
    </form></div><div class='grid'>
    """
    for r in rows:
        content += f"<div class='card'><h2>{h(r['country_name'])}</h2><p>{h(r['continent'])}</p><p>{h(r['description'])}</p></div>"
    content += "</div>"
    return render(content)

@app.route("/community")
def community():
    return render("""
    <div class='card hero'><h1>📍 Community Navigation</h1><p class='green'>Postcode → Borough → County/Region → Country → Continent → Global → Planet → Universe</p></div>
    <div class='grid'>
    <div class='card'><h2>📍 Postcode</h2><p>Trust starts local.</p></div>
    <div class='card'><h2>🏙 Borough</h2><p>Neighbouring postcodes connect.</p></div>
    <div class='card'><h2>🗺 Region</h2><p>Regional intelligence and opportunity.</p></div>
    <div class='card'><h2>🇬🇧 Country</h2><p>National spaces and sports energy.</p></div>
    <div class='card'><h2>🌍 Continent</h2><p>Continental community and culture.</p></div>
    <div class='card'><h2>🌎 Global</h2><p>Born local. Built global.</p></div>
    <div class='card'><h2>🌱 Planet</h2><p>Humanity, nature, dignity.</p></div>
    <div class='card'><h2>✨ Universe</h2><p>Ideas, learning and future generations.</p></div>
    </div>
    """)

@app.route("/assistant", methods=["GET","POST"])
def assistant():
    answer = ""
    query = ""
    if request.method == "POST":
        query = request.form["query"]
        answer = public_ai_answer(query)
        conn = db()
        conn.execute("INSERT INTO ai_public_queries(visitor_name,query,answer,created_at) VALUES(?,?,?,?)",
                     (request.form.get("visitor_name","visitor"), query, answer, now()))
        conn.commit()
        conn.close()
    return render(f"""
    <div class='card hero'><h1>🤖 OAP Website AI</h1><p class='green'>Public assistant for OAP navigation.</p></div>
    <div class='card'><form method='POST'>
    <input name='visitor_name' placeholder='Name optional'>
    <textarea name='query' placeholder='Ask OAP...' required>{h(query)}</textarea>
    <button>Ask</button>
    </form></div>
    {"<div class='card'><h2>Answer</h2><p>" + h(answer) + "</p></div>" if answer else ""}
    """)

@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    content = f"<div class='card hero'><h1>🔎 Search</h1></div><div class='card'><form><input name='q' value='{h(q)}' placeholder='Search events, sports, countries'><button>Search</button></form></div>"
    if not q:
        return render(content)
    like = f"%{q}%"
    conn = db()
    sports_rows = conn.execute("SELECT * FROM sports_posts WHERE title LIKE ? OR sport LIKE ? OR tournament LIKE ? OR country_space LIKE ? ORDER BY id DESC LIMIT 30", (like,like,like,like)).fetchall()
    events_rows = conn.execute("SELECT * FROM events WHERE title LIKE ? OR postcode LIKE ? OR borough LIKE ? OR country LIKE ? ORDER BY id DESC LIMIT 30", (like,like,like,like)).fetchall()
    watch_rows = conn.execute("SELECT * FROM watch_parties WHERE title LIKE ? OR match_title LIKE ? OR country_focus LIKE ? OR postcode LIKE ? ORDER BY id DESC LIMIT 30", (like,like,like,like)).fetchall()
    conn.close()
    content += "<div class='card'><h2>Sports</h2>"
    for r in sports_rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><p>{h(r['body'])}</p></div>"
    content += "</div><div class='card'><h2>Events</h2>"
    for e in events_rows:
        content += f"<div class='card'><b>{h(e['title'])}</b><br>{h(e['postcode'])} {h(e['borough'])}</div>"
    content += "</div><div class='card'><h2>Watch Parties</h2>"
    for w in watch_rows:
        content += f"<div class='card'><b>{h(w['title'])}</b><br>{h(w['match_title'])} {h(w['postcode'])}</div>"
    content += "</div>"
    return render(content)

@app.route("/explorer")
def explorer():
    return redirect("/community")

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO events(username,title,event_type,category,postcode,borough,county_region,country,continent,venue,event_date,event_time,description,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["title"], request.form["event_type"], request.form["category"],
            request.form["postcode"], request.form["borough"], request.form["county_region"],
            request.form["country"], request.form["continent"], request.form["venue"],
            request.form["event_date"], request.form["event_time"], request.form["description"],
            "pending", now()
        ))
        conn.commit()
        conn.close()
        return redirect("/events")
    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Events</h1><form method='POST'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'><option>Watch Party</option><option>Community Event</option><option>Business Popup</option><option>Creator Meetup</option></select>
    <input name='category' value='Community'>
    <input name='postcode' placeholder='Postcode'>
    <input name='borough' placeholder='Borough'>
    <input name='county_region' placeholder='County / Region'>
    <input name='country' placeholder='Country'>
    <input name='continent' placeholder='Continent'>
    <input name='venue' placeholder='Venue'>
    <input name='event_date' placeholder='Date'>
    <input name='event_time' placeholder='Time'>
    <textarea name='description' placeholder='Description'></textarea>
    <button>Submit Event</button></form></div>
    """
    for e in rows:
        content += f"<div class='card'><b>{h(e['title'])}</b><br>{h(e['postcode'])} → {h(e['borough'])} → {h(e['country'])}<p>{h(e['description'])}</p></div>"
    return render(content)

@app.route("/messages", methods=["GET","POST"])
def messages():
    if request.method == "POST":
        sender = session.get("user", "guest")
        conn = db()
        conn.execute("INSERT INTO messages(sender,recipient,subject,body,status,created_at) VALUES(?,?,?,?,?,?)",
                     (sender, request.form["recipient"], request.form["subject"], request.form["body"], "unread", now()))
        conn.commit()
        conn.close()
        return redirect("/messages")
    user = session.get("user", "guest")
    conn = db()
    rows = conn.execute("SELECT * FROM messages WHERE recipient=? OR sender=? OR recipient='admin' ORDER BY id DESC LIMIT 100", (user,user)).fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Messenger</h1><form method='POST'>
    <input name='recipient' value='admin'>
    <input name='subject' placeholder='Subject'>
    <textarea name='body' placeholder='Message'></textarea>
    <button>Send</button></form></div>
    """
    for m in rows:
        content += f"<div class='card'><b>{h(m['subject'])}</b><br>{h(m['sender'])} → {h(m['recipient'])}<p>{h(m['body'])}</p></div>"
    return render(content)

@app.route("/personal_hrm", methods=["GET","POST"])
def personal_hrm():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO personal_hrm_tasks(username,title,mission,layer,priority,status,swot_strength,swot_weakness,swot_opportunity,swot_threat,next_action,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["title"], request.form["mission"], request.form["layer"], request.form["priority"], "open",
            request.form["swot_strength"], request.form["swot_weakness"], request.form["swot_opportunity"], request.form["swot_threat"], request.form["next_action"], now()
        ))
        conn.commit()
        conn.close()
        save_memory("personal_hrm_task", request.form["title"], request.form["mission"], "Private HRM review.", request.form["next_action"])
        return redirect("/personal_hrm")
    conn = db()
    rows = conn.execute("SELECT * FROM personal_hrm_tasks ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>🧠 Personal HRM</h1></div><div class='card'><form method='POST'>
    <input name='title' placeholder='Task title' required>
    <select name='layer'><option>Mind</option><option>Body</option><option>Soul</option><option>Sports</option><option>Commerce</option></select>
    <select name='priority'><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select>
    <textarea name='mission' placeholder='Mission'></textarea>
    <input name='swot_strength' placeholder='Strength'>
    <input name='swot_weakness' placeholder='Weakness'>
    <input name='swot_opportunity' placeholder='Opportunity'>
    <input name='swot_threat' placeholder='Threat'>
    <textarea name='next_action' placeholder='Next action'></textarea>
    <button>Save HRM Task</button></form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['layer'])} • {h(r['priority'])}<p>{h(r['mission'])}</p><p><b>Next:</b> {h(r['next_action'])}</p></div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 100").fetchall()
    watch = conn.execute("SELECT * FROM watch_parties ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>Admin</h1></div><div class='card'><h2>Users</h2>"
    for u in users:
        content += f"<div class='card'>@{h(u['username'])} — {h(u['verification_level'])}<br>{h(u['postcode'])} → {h(u['borough'])} → {h(u['country'])}</div>"
    content += "</div><div class='card'><h2>Watch Parties</h2>"
    for w in watch:
        content += f"<div class='card'><b>{h(w['title'])}</b> — {h(w['status'])}</div>"
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    content += "</div>"
    return render(content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
