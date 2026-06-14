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

def add_col(cur, table, col, typ):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")

def log(action, username="system"):
    conn = db()
    conn.execute(
        "INSERT INTO audit_logs(action,username,created_at) VALUES(?,?,?)",
        (action, username, now())
    )
    conn.commit()
    conn.close()

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

    cur.execute("""CREATE TABLE IF NOT EXISTS public_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        category TEXT,
        area TEXT,
        body TEXT,
        status TEXT DEFAULT 'approved',
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

    cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,))
    user = cur.fetchone()
    if user:
        cur.execute("""UPDATE users SET nickname=?, oap_email=?, password=?, role=?, verification_level=?
        WHERE username=?""", ("N24-7", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", "founder", ADMIN_USERNAME))
    else:
        cur.execute("""INSERT INTO users(nickname,username,oap_email,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            "N24-7", ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD),
            "CR4", "Merton", "Greater London", "UK", "Europe", "London",
            "founder", "admin", now()
        ))

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
.wrap{padding:14px;max-width:1100px;margin:auto}
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
<a href="/assistant">Website AI</a>
<a href="/search">Search</a>
<a href="/explorer">Explorer</a>
<a href="/events">Events</a>
<a href="/messages">Messenger</a>
<a href="/personal_hrm">Personal HRM</a>
<a href="/decisions">Decisions</a>
<a href="/hrm_memory">HRM Memory</a>
<a href="/admin">Admin</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def current_user():
    return session.get("user", "guest")

def save_memory(memory_type, title, summary, lesson, next_action, visibility="private"):
    conn = db()
    conn.execute("""INSERT INTO hrm_memory_logs(memory_type,title,summary,lesson,next_action,visibility,created_at)
    VALUES(?,?,?,?,?,?,?)""", (memory_type, title, summary, lesson, next_action, visibility, now()))
    conn.commit()
    conn.close()

def public_ai_answer(query):
    q = (query or "").lower()
    conn = db()
    events = conn.execute("SELECT * FROM events WHERE status='approved' ORDER BY id DESC LIMIT 5").fetchall()
    posts = conn.execute("SELECT * FROM public_posts WHERE status='approved' ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    if "event" in q or "watch" in q or "party" in q:
        answer = "OAP event layer: check Events for watch parties, meetups, community events, sports events, and local activity. "
        if events:
            answer += "Latest events: " + ", ".join([e["title"] for e in events]) + "."
        else:
            answer += "No approved events yet. Create one after login."
        return answer

    if "postcode" in q or "borough" in q or "country" in q or "continent" in q:
        return "OAP navigation runs Postcode → Borough → County/Region → Country → Continent → Global → Planet → Universe. Start local, then expand outward through real trust records."

    if "weather" in q:
        return "OAP Weather is a planning layer for events, riders, watch parties, field operations, and local navigation. Add your preferred weather location at signup/profile."

    if "sika" in q:
        return "SIKA starts as contribution and trust records only. It is not legal tender, not e-money, not a bank account, and not an investment product."

    if "business" in q:
        return "OAP Business will support listings, offers, promotions, vendor spaces, sponsor packages, and local discovery. Monetization comes from real value, not views."

    if "creator" in q:
        return "OAP Creator layer will support profiles, debates, media, awards, country spaces, watch-party content, and business partnerships."

    if "bank" in q or "wallet" in q:
        return "OAP financial path is trust records first: community → commerce → audit logs → SIKA trust records → compliant payment partner later → bank-style UX later. No public bank claims before authorization."

    if posts:
        return "OAP can help you discover events, posts, areas, creators, businesses, weather notes, and community signals. Latest public post: " + posts[0]["title"]

    return "Welcome to ON ANY POSTCODE. Browse freely. Join easily. Build trust gradually. Monetize with proof. Start with Events, Search, Explorer, Messenger, and HRM records."

@app.route("/")
def home():
    conn = db()
    stats = {
        "users": conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        "events": conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        "messages": conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"],
        "tasks": conn.execute("SELECT COUNT(*) c FROM personal_hrm_tasks").fetchone()["c"],
        "decisions": conn.execute("SELECT COUNT(*) c FROM private_decision_logs").fetchone()["c"],
        "memories": conn.execute("SELECT COUNT(*) c FROM hrm_memory_logs").fetchone()["c"],
    }
    events = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = f"""
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>Personal HRM AI + Website AI Core</p>
    <p>Public AI helps visitors. Private HRM helps you build. Never mix private strategy with public assistant.</p>
    </div>

    <div class='grid'>
    <div class='card'><h2>{stats['users']}</h2><p>Users</p></div>
    <div class='card'><h2>{stats['events']}</h2><p>Events</p></div>
    <div class='card'><h2>{stats['messages']}</h2><p>Messages</p></div>
    <div class='card'><h2>{stats['tasks']}</h2><p>HRM Tasks</p></div>
    <div class='card'><h2>{stats['decisions']}</h2><p>Decisions</p></div>
    <div class='card'><h2>{stats['memories']}</h2><p>Memories</p></div>
    </div>

    <div class='card'>
    <h2>Quick Actions</h2>
    <a class='badge' href='/assistant'>Ask Website AI</a>
    <a class='badge' href='/personal_hrm'>Personal HRM</a>
    <a class='badge' href='/search'>Search</a>
    <a class='badge' href='/explorer'>Explorer</a>
    <a class='badge' href='/events'>Events</a>
    <a class='badge' href='/decisions'>Decision Log</a>
    </div>

    <div class='card red'>
    Public Website AI only uses public OAP guidance and public records. Personal HRM is private founder/build intelligence.
    </div>

    <div class='card'><h2>Latest Events</h2>
    """
    for e in events:
        content += f"<div class='card'><b>{h(e['title'])}</b><br>{h(e['postcode'])} → {h(e['borough'])} → {h(e['country'])}<p>{h(e['description'])}</p></div>"
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
    <div class='card hero'><h1>Join OAP</h1><p class='green'>Fast signup. Location fields optional until verification or monetization.</p></div>
    <div class='card'>
    <form method='POST'>
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
    </form>
    </div>
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
    <div class='card'><h2>Login</h2>
    <form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Login</button>
    </form>
    <p class='small'>Default admin: N24-7 / 2525</p>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

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
        log("Website AI query", request.form.get("visitor_name","visitor"))

    return render(f"""
    <div class='card hero'>
    <h1>🤖 OAP Website AI</h1>
    <p class='green'>Public assistant for events, search, explorer, weather, community, creators, business and SIKA guidance.</p>
    </div>
    <div class='card'>
    <form method='POST'>
    <input name='visitor_name' placeholder='Name optional'>
    <textarea name='query' placeholder='Ask OAP...' required>{h(query)}</textarea>
    <button>Ask</button>
    </form>
    </div>
    {"<div class='card'><h2>Answer</h2><p>" + h(answer) + "</p></div>" if answer else ""}
    """)

@app.route("/personal_hrm", methods=["GET","POST"])
def personal_hrm():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO personal_hrm_tasks(username,title,mission,layer,priority,status,swot_strength,swot_weakness,swot_opportunity,swot_threat,next_action,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["title"], request.form["mission"], request.form["layer"],
            request.form["priority"], "open", request.form["swot_strength"], request.form["swot_weakness"],
            request.form["swot_opportunity"], request.form["swot_threat"], request.form["next_action"], now()
        ))
        conn.commit()
        conn.close()
        save_memory("personal_hrm_task", request.form["title"], request.form["mission"], "Task created for private HRM review.", request.form["next_action"])
        log("Personal HRM task created", username)
        return redirect("/personal_hrm")

    conn = db()
    rows = conn.execute("SELECT * FROM personal_hrm_tasks ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>🧠 Personal HRM AI</h1><p class='green'>Private founder command layer.</p></div>
    <div class='card'>
    <form method='POST'>
    <input name='title' placeholder='Task title' required>
    <select name='layer'>
    <option>Mind</option><option>Body</option><option>Soul</option><option>Commerce</option><option>Sports</option><option>Messenger</option><option>SIKA</option><option>Compliance</option>
    </select>
    <select name='priority'><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select>
    <textarea name='mission' placeholder='Mission / problem / goal'></textarea>
    <input name='swot_strength' placeholder='Strength'>
    <input name='swot_weakness' placeholder='Weakness'>
    <input name='swot_opportunity' placeholder='Opportunity'>
    <input name='swot_threat' placeholder='Threat'>
    <textarea name='next_action' placeholder='Next action'></textarea>
    <button>Save HRM Task</button>
    </form>
    </div>
    """
    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['title'])}</b><br>
        {h(r['layer'])} • {h(r['priority'])} • {h(r['status'])}
        <p>{h(r['mission'])}</p>
        <p class='green'>Opportunity: {h(r['swot_opportunity'])}</p>
        <p class='red'>Threat: {h(r['swot_threat'])}</p>
        <p><b>Next:</b> {h(r['next_action'])}</p>
        <a href='/hrm_done/{r['id']}'>Mark Done</a>
        </div>
        """
    return render(content)

@app.route("/hrm_done/<int:id>")
def hrm_done(id):
    conn = db()
    row = conn.execute("SELECT * FROM personal_hrm_tasks WHERE id=?", (id,)).fetchone()
    conn.execute("UPDATE personal_hrm_tasks SET status='done' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    if row:
        save_memory("task_done", row["title"], "Task marked done.", "Execution completed or reviewed.", "Create next task if needed.")
    return redirect("/personal_hrm")

@app.route("/decisions", methods=["GET","POST"])
def decisions():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO private_decision_logs(username,decision_title,decision_body,reason,risk_note,approval_status,created_at)
        VALUES(?,?,?,?,?,?,?)""", (
            username, request.form["decision_title"], request.form["decision_body"], request.form["reason"],
            request.form["risk_note"], "approved" if request.form.get("approval_status") == "approved" else "pending", now()
        ))
        conn.commit()
        conn.close()
        save_memory("decision", request.form["decision_title"], request.form["decision_body"], request.form["reason"], "Follow approved next action only.")
        log("Decision logged", username)
        return redirect("/decisions")

    conn = db()
    rows = conn.execute("SELECT * FROM private_decision_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>Decision Log</h1><p class='green'>Human final approval layer.</p></div>
    <div class='card'>
    <form method='POST'>
    <input name='decision_title' placeholder='Decision title' required>
    <textarea name='decision_body' placeholder='Decision'></textarea>
    <textarea name='reason' placeholder='Why?'></textarea>
    <textarea name='risk_note' placeholder='Risk / boundary'></textarea>
    <select name='approval_status'><option>pending</option><option>approved</option></select>
    <button>Save Decision</button>
    </form>
    </div>
    """
    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['decision_title'])}</b> — {h(r['approval_status'])}
        <p>{h(r['decision_body'])}</p>
        <p><b>Reason:</b> {h(r['reason'])}</p>
        <p class='red'><b>Risk:</b> {h(r['risk_note'])}</p>
        </div>
        """
    return render(content)

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
        log("Event submitted", username)
        return redirect("/events")

    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Events</h1>
    <form method='POST'>
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
    <button>Submit Event</button>
    </form>
    </div>
    """
    for e in rows:
        content += f"<div class='card'><b>{h(e['title'])}</b><br>{h(e['postcode'])} → {h(e['borough'])} → {h(e['country'])} → {h(e['continent'])}<p>{h(e['description'])}</p>Status: {h(e['status'])}</div>"
    return render(content)

@app.route("/messages", methods=["GET","POST"])
def messages():
    if request.method == "POST":
        sender = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO messages(sender,recipient,subject,body,status,created_at)
        VALUES(?,?,?,?,?,?)""", (sender, request.form["recipient"], request.form["subject"], request.form["body"], "unread", now()))
        conn.commit()
        conn.close()
        log("Message sent", sender)
        return redirect("/messages")

    user = session.get("user", "guest")
    conn = db()
    rows = conn.execute("SELECT * FROM messages WHERE recipient=? OR sender=? OR recipient='admin' ORDER BY id DESC LIMIT 100", (user, user)).fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Messenger</h1>
    <form method='POST'>
    <input name='recipient' value='admin'>
    <input name='subject' placeholder='Subject'>
    <textarea name='body' placeholder='Message'></textarea>
    <button>Send</button>
    </form>
    </div>
    """
    for m in rows:
        content += f"<div class='card'><b>{h(m['subject'])}</b><br>{h(m['sender'])} → {h(m['recipient'])}<p>{h(m['body'])}</p></div>"
    return render(content)

@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    content = f"""
    <div class='card hero'><h1>Search</h1><p class='green'>OAP-first search.</p></div>
    <div class='card'><form><input name='q' value='{h(q)}' placeholder='Search events, posts, areas'><button>Search</button></form></div>
    """
    if not q:
        return render(content)

    like = f"%{q}%"
    conn = db()
    events_rows = conn.execute("""SELECT * FROM events WHERE title LIKE ? OR category LIKE ? OR postcode LIKE ? OR borough LIKE ? OR country LIKE ? ORDER BY id DESC LIMIT 30""",
                               (like,like,like,like,like)).fetchall()
    posts = conn.execute("""SELECT * FROM public_posts WHERE title LIKE ? OR category LIKE ? OR area LIKE ? OR body LIKE ? ORDER BY id DESC LIMIT 30""",
                         (like,like,like,like)).fetchall()
    conn.close()

    content += "<div class='card'><h2>Events</h2>"
    for e in events_rows:
        content += f"<div class='card'><b>{h(e['title'])}</b><br>{h(e['postcode'])} {h(e['borough'])} {h(e['country'])}</div>"
    content += "</div><div class='card'><h2>Posts</h2>"
    for p in posts:
        content += f"<div class='card'><b>{h(p['title'])}</b><p>{h(p['body'])}</p></div>"
    content += "</div>"
    return render(content)

@app.route("/explorer")
def explorer():
    return render("""
    <div class='card hero'><h1>Explorer</h1><p class='green'>Postcode → Borough → County/Region → Country → Continent → Global → Planet → Universe</p></div>
    <div class='grid'>
    <div class='card'><h2>📍 Postcode</h2><p>Local trust starts here.</p></div>
    <div class='card'><h2>🏙 Borough</h2><p>Neighbouring postcodes connect.</p></div>
    <div class='card'><h2>🗺 Region</h2><p>Regional activity and opportunity.</p></div>
    <div class='card'><h2>🇬🇧 Country</h2><p>Country spaces and national culture.</p></div>
    <div class='card'><h2>🌍 Continent</h2><p>Continental identity and connection.</p></div>
    <div class='card'><h2>🌎 Global</h2><p>Born local, built global.</p></div>
    <div class='card'><h2>🌱 Planet</h2><p>Humanity, nature, dignity.</p></div>
    <div class='card'><h2>✨ Universe</h2><p>Ideas, future, learning, possibility.</p></div>
    </div>
    """)

@app.route("/hrm_memory")
def hrm_memory():
    conn = db()
    rows = conn.execute("SELECT * FROM hrm_memory_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>HRM Memory</h1><p class='green'>Private and public lessons recorded locally.</p></div>"
    for m in rows:
        content += f"""
        <div class='card'>
        <b>{h(m['title'])}</b> — {h(m['memory_type'])} • {h(m['visibility'])}<br>
        <p>{h(m['summary'])}</p>
        <p><b>Lesson:</b> {h(m['lesson'])}</p>
        <p><b>Next:</b> {h(m['next_action'])}</p>
        </div>
        """
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 100").fetchall()
    queries = conn.execute("SELECT * FROM ai_public_queries ORDER BY id DESC LIMIT 50").fetchall()
    tasks = conn.execute("SELECT * FROM personal_hrm_tasks ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card hero'><h1>Admin</h1></div><div class='card'><h2>Users</h2>"
    for u in users:
        content += f"<div class='card'>@{h(u['username'])} — {h(u['verification_level'])}<br>{h(u['postcode'])} → {h(u['borough'])} → {h(u['county_region'])} → {h(u['country'])} → {h(u['continent'])}</div>"
    content += "</div><div class='card'><h2>Website AI Queries</h2>"
    for q in queries:
        content += f"<div class='card'><b>{h(q['query'])}</b><p>{h(q['answer'])}</p></div>"
    content += "</div><div class='card'><h2>Personal HRM Tasks</h2>"
    for t in tasks:
        content += f"<div class='card'><b>{h(t['title'])}</b> — {h(t['status'])}<p>{h(t['next_action'])}</p></div>"
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    content += "</div>"
    return render(content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
