from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
ADMIN_USERNAME = "N24-7"
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

def init_db():
    conn = db()
    cur = conn.cursor()

    tables = {
        "users": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("nickname","TEXT"),("username","TEXT UNIQUE"),("password","TEXT"),("postcode","TEXT"),("borough","TEXT"),("county_region","TEXT"),("country","TEXT"),("continent","TEXT"),("weather_location","TEXT"),("verification_level","TEXT DEFAULT 'Starter'"),("role","TEXT DEFAULT 'member'"),("created_at","TEXT")],
        "audit_logs": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("action","TEXT"),("username","TEXT"),("member","TEXT"),("created_at","TEXT")],
        "culture_posts": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("title","TEXT"),("category","TEXT"),("country","TEXT"),("body","TEXT"),("created_at","TEXT")],
        "artists": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("artist_name","TEXT"),("genre","TEXT"),("country","TEXT"),("bio","TEXT"),("link","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "events": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("title","TEXT"),("event_type","TEXT"),("postcode","TEXT"),("borough","TEXT"),("country","TEXT"),("venue","TEXT"),("event_date","TEXT"),("description","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "messages": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("sender","TEXT"),("recipient","TEXT"),("subject","TEXT"),("body","TEXT"),("status","TEXT DEFAULT 'unread'"),("created_at","TEXT")],
        "trust_badges": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("requested_level","TEXT"),("proof","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "opportunities": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("source","TEXT"),("description","TEXT"),("amount","REAL DEFAULT 0"),("currency","TEXT DEFAULT 'GBP'"),("status","TEXT DEFAULT 'recorded'"),("created_at","TEXT")],
        "payouts": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("recipient_name","TEXT"),("reason","TEXT"),("amount","REAL DEFAULT 0"),("currency","TEXT DEFAULT 'GBP'"),("status","TEXT DEFAULT 'pending'"),("approved_by","TEXT"),("paid_date","TEXT"),("created_at","TEXT")],
        "approvals": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("approval_type","TEXT"),("record_id","INTEGER"),("status","TEXT DEFAULT 'pending'"),("reviewer","TEXT"),("notes","TEXT"),("created_at","TEXT")],
        "businesses": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("business_name","TEXT"),("category","TEXT"),("postcode","TEXT"),("borough","TEXT"),("country","TEXT"),("description","TEXT"),("contact","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "products": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("business_name","TEXT"),("product_name","TEXT"),("category","TEXT"),("price","REAL DEFAULT 0"),("currency","TEXT DEFAULT 'GBP'"),("description","TEXT"),("status","TEXT DEFAULT 'draft'"),("created_at","TEXT")],
        "family_tree": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("node_name","TEXT"),("node_type","TEXT"),("connection_to","TEXT"),("relationship","TEXT"),("heritage_note","TEXT"),("contribution_note","TEXT"),("visibility","TEXT DEFAULT 'private'"),("status","TEXT DEFAULT 'active'"),("created_at","TEXT")],
        "affiliate_tree": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("affiliate_name","TEXT"),("affiliate_type","TEXT"),("referred_business","TEXT"),("sale_value","REAL DEFAULT 0"),("commission_value","REAL DEFAULT 0"),("currency","TEXT DEFAULT 'GBP'"),("proof_note","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "council_logs": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("council_role","TEXT"),("signal","TEXT"),("summary","TEXT"),("recommendation","TEXT"),("status","TEXT DEFAULT 'active'"),("created_at","TEXT")],
        "decision_logs": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("decision_title","TEXT"),("decision_type","TEXT"),("reason","TEXT"),("approved_by","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "risk_logs": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("risk_title","TEXT"),("risk_level","TEXT"),("risk_area","TEXT"),("risk_description","TEXT"),("mitigation","TEXT"),("status","TEXT DEFAULT 'open'"),("created_at","TEXT")],
        "build_logs": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("build_name","TEXT"),("version","TEXT"),("result","TEXT"),("backup_name","TEXT"),("lesson","TEXT"),("status","TEXT DEFAULT 'recorded'"),("created_at","TEXT")],
        "sovereign_veto_logs": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("veto_title","TEXT"),("veto_reason","TEXT"),("risk_level","TEXT"),("decision","TEXT"),("reviewer","TEXT"),("status","TEXT DEFAULT 'paused'"),("created_at","TEXT")]
    }

    for table, cols in tables.items():
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table}({', '.join([c+' '+t for c,t in cols])})")
        for c, t in cols:
            if c != "id":
                add_col(cur, table, c, t)

    found = cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,)).fetchone()
    if found:
        cur.execute("UPDATE users SET password=?, role=?, verification_level=? WHERE username=?",
                    (generate_password_hash(ADMIN_PASSWORD), "admin", "Founder", ADMIN_USERNAME))
    else:
        cur.execute("""INSERT INTO users(nickname,username,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("N24-7", ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), "CR4", "Merton", "Greater London", "UK", "Europe", "London", "Founder", "admin", now()))

    conn.commit()
    conn.close()

def log(action, username="system"):
    conn = db()
    conn.execute("INSERT INTO audit_logs(action,username,member,created_at) VALUES(?,?,?,?)", (action, username, username, now()))
    conn.commit()
    conn.close()

init_db()

def user():
    return session.get("user", "guest")

def render(content):
    return render_template_string(BASE, content=content)

BASE = """
<!DOCTYPE html><html><head><title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#050505;color:white;font-family:Arial}
.top{background:#101010;padding:15px;border-bottom:1px solid #222;position:sticky;top:0;z-index:5}
.logo{font-size:22px;font-weight:900;margin-bottom:6px}
.wrap{padding:14px;max-width:1150px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:16px;margin:12px 0}
.hero{text-align:center;padding:30px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.nav a,.chip{background:#151515;border:1px solid #272727;border-radius:999px;padding:8px 12px;color:#00dd99;font-size:14px}
input,textarea,select{width:100%;padding:13px;margin:8px 0;background:#0b0b0b;color:white;border:1px solid #333;border-radius:12px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:12px;padding:13px 18px;font-weight:900}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.warn{background:#2b1600;border-color:#6b3b00}
.danger{background:#300;border-color:#700}
.badge{display:inline-block;background:#00dd99;color:#000;padding:7px 11px;border-radius:999px;font-weight:900;font-size:12px;margin:3px}
.small{color:#aaa;font-size:13px}
</style></head><body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/leave">Leave My World</a>
{% else %}
<a href="/join">Join OAP</a> <a href="/enter">Enter My World</a>
{% endif %}
</div>
<div class="nav">
<a href="/">Home</a>
<a href="/my_world">My World</a>
<a href="/explorer">Explorer</a>
<a href="/search">Search</a>
<a href="/command_center">Command Center</a>
<a href="/hrm">HRM</a>
<a href="/menu">Menu</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div></body></html>
"""

@app.route("/favicon.ico")
def favicon():
    return ("", 204)

@app.route("/")
def home():
    conn=db()
    stats={
        "members":conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        "family":conn.execute("SELECT COUNT(*) c FROM family_tree").fetchone()["c"],
        "affiliate":conn.execute("SELECT COUNT(*) c FROM affiliate_tree").fetchone()["c"],
        "council":conn.execute("SELECT COUNT(*) c FROM council_logs").fetchone()["c"],
        "decisions":conn.execute("SELECT COUNT(*) c FROM decision_logs").fetchone()["c"],
        "risks":conn.execute("SELECT COUNT(*) c FROM risk_logs").fetchone()["c"],
        "builds":conn.execute("SELECT COUNT(*) c FROM build_logs").fetchone()["c"],
        "veto":conn.execute("SELECT COUNT(*) c FROM sovereign_veto_logs").fetchone()["c"]
    }
    conn.close()
    return render(f"""
    <div class='card hero'><h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>Record → Verify → Build</p>
    <p>Clarity first. Speed second. Accuracy always.</p>
    <a class='badge' href='/join'>Join OAP</a><a class='badge' href='/enter'>Enter My World</a></div>
    <div class='grid'>
    <div class='card'><h2>{stats['members']}</h2><p>Members</p></div>
    <div class='card'><h2>{stats['family']}</h2><p>Family Tree</p></div>
    <div class='card'><h2>{stats['affiliate']}</h2><p>Affiliate Tree</p></div>
    <div class='card'><h2>{stats['council']}</h2><p>Council Logs</p></div>
    <div class='card'><h2>{stats['decisions']}</h2><p>Decision Logs</p></div>
    <div class='card'><h2>{stats['risks']}</h2><p>Risk Logs</p></div>
    <div class='card'><h2>{stats['builds']}</h2><p>Build Logs</p></div>
    <div class='card'><h2>{stats['veto']}</h2><p>Sovereign Veto Logs</p></div>
    </div>
    """)

@app.route("/menu")
def menu():
    return render("""
    <div class='card hero'><h1>☰ OAP Menu</h1><p class='green'>Same power, less clutter.</p></div>
    <div class='grid'>
      <div class='card'><h2>🌍 World</h2>
      <p><a href='/community'>Community</a></p><p><a href='/culture'>Culture</a></p><p><a href='/artists'>Artists</a></p><p><a href='/events'>Events</a></p></div>
      <div class='card'><h2>🌍 My World</h2>
      <p><a href='/my_world'>My World</a></p><p><a href='/messages'>Messenger</a></p><p><a href='/trust_badge'>Trust Badge</a></p><p><a href='/family_tree'>Family Tree</a></p><p><a href='/affiliate_tree'>Affiliate Tree</a></p></div>
      <div class='card'><h2>🏪 Commerce</h2>
      <p><a href='/business'>Business</a></p><p><a href='/products'>Products</a></p><p><a href='/opportunity_board'>Opportunity Board</a></p><p><a href='/approvals'>Approvals</a></p></div>
      <div class='card'><h2>🧠 HRM Sovereign</h2>
      <p><a href='/hrm'>HRM</a></p><p><a href='/council_logs'>Council Logs</a></p><p><a href='/decision_logs'>Decision Logs</a></p><p><a href='/risk_logs'>Risk Logs</a></p><p><a href='/build_logs'>Build Logs</a></p><p><a href='/sovereign_veto'>Sovereign Veto</a></p></div>
      <div class='card'><h2>🛡️ System</h2>
      <p><a href='/privacy'>Privacy</a></p><p><a href='/health'>Health</a></p><p><a href='/routes'>Routes</a></p><p><a href='/admin'>Admin</a></p></div>
    </div>
    """)

@app.route("/join", methods=["GET","POST"])
@app.route("/signup", methods=["GET","POST"])
def join():
    if request.method=="POST":
        conn=db()
        try:
            conn.execute("""INSERT INTO users(nickname,username,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (request.form["nickname"],request.form["username"],generate_password_hash(request.form["password"]),
             request.form.get("postcode",""),request.form.get("borough",""),request.form.get("county_region",""),
             request.form.get("country",""),request.form.get("continent",""),request.form.get("weather_location",""),
             "Starter","member",now()))
            conn.commit(); log("Member joined OAP", request.form["username"])
            return redirect("/welcome")
        except sqlite3.IntegrityError:
            return render("<div class='card'><h1>Username exists</h1><a href='/join'>Try again</a></div>")
        finally:
            conn.close()
    return render("""
    <div class='card hero'><h1>Join OAP</h1><p class='green'>Fast signup. More proof only needed for Trust Badge or monetization.</p></div>
    <div class='card'><form method='POST'>
    <input name='nickname' placeholder='Nickname' required><input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required><input name='postcode' placeholder='Postcode optional'>
    <input name='borough' placeholder='Borough optional'><input name='county_region' placeholder='County / Region optional'>
    <input name='country' placeholder='Country optional'><input name='continent' placeholder='Continent optional'>
    <input name='weather_location' placeholder='Weather location optional'><button>Join OAP</button></form></div>
    """)

@app.route("/welcome")
def welcome():
    return render("<div class='card hero'><h1>🌍 Your World Has Been Created</h1><p class='green'>Welcome to OAP.</p><a class='badge' href='/enter'>Enter My World</a><a class='badge' href='/menu'>Open Menu</a></div>")

@app.route("/enter", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def enter():
    if request.method=="POST":
        conn=db(); row=conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone(); conn.close()
        if row and check_password_hash(row["password"], request.form["password"]):
            session["user"]=row["username"]; session["role"]=row["role"]; log("Entered My World", row["username"])
            return redirect("/my_world")
        return render("<div class='card'><h1>Invalid entry</h1><a href='/enter'>Try again</a></div>")
    return render("<div class='card hero'><h1>Enter My World</h1></div><div class='card'><form method='POST'><input name='username' placeholder='Username' required><input name='password' type='password' placeholder='Password' required><button>Enter My World</button></form><p>Founder: N24-7 / 2525</p></div>")

@app.route("/leave")
@app.route("/logout")
def leave():
    session.clear()
    return redirect("/")

@app.route("/privacy")
@app.route("/trust")
def privacy():
    return render("""
    <div class='card hero'><h1>🛡️ OAP Privacy & Trust Promise</h1><p class='green'>Human-first. Private-first. Community-first.</p></div>
    <div class='card'><p>✅ Your data belongs to you.</p><p>✅ Your profile belongs to you.</p><p>✅ Your content belongs to you.</p><p>✅ Your messages belong to you.</p><p>✅ Your culture belongs to you.</p><p>✅ Your business belongs to you.</p></div>
    <div class='card warn'>OAP owns the core. We collaborate only where it fits the mission.</div>
    """)

@app.route("/hrm")
def hrm():
    return render("""
    <div class='card hero'><h1>🧠 HRM Sovereign Core</h1><p class='green'>Record → Verify → Build</p></div>
    <div class='card'>
    <h2>Sovereign Law</h2>
    <p>No memory = no intelligence.</p>
    <p>No verification = no trust.</p>
    <p>No audit = no automation.</p>
    <p>No human approval = no real-world action.</p>
    <p>No record = no sovereign veto.</p>
    </div>
    <div class='grid'>
    <div class='card'><h2>GPT Architect</h2><p>Architecture</p></div>
    <div class='card'><h2>Claude Chancellor</h2><p>Privacy / governance</p></div>
    <div class='card'><h2>Gemini Archivist</h2><p>Memory / history</p></div>
    <div class='card'><h2>Kimi Expansion</h2><p>Roadmap / scaling</p></div>
    <div class='card'><h2>Grok Challenger</h2><p>Risk / stress test</p></div>
    <div class='card'><h2>HRM</h2><p>Record keeper</p></div>
    </div>
    """)

@app.route("/council_logs", methods=["GET","POST"])
def council_logs():
    if request.method=="POST":
        conn=db()
        conn.execute("INSERT INTO council_logs(username,council_role,signal,summary,recommendation,status,created_at) VALUES(?,?,?,?,?,?,?)",
        (user(),request.form["council_role"],request.form["signal"],request.form["summary"],request.form["recommendation"],"active",now()))
        conn.commit(); conn.close(); log("Council log added", user())
        return redirect("/council_logs")
    conn=db(); rows=conn.execute("SELECT * FROM council_logs ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="<div class='card hero'><h1>👑 Council Logs</h1></div><div class='card'><form method='POST'><select name='council_role'><option>GPT Architect</option><option>Claude Chancellor</option><option>Gemini Archivist</option><option>Kimi Expansion</option><option>Grok Challenger</option><option>HRM</option><option>Founder</option></select><select name='signal'><option>Green</option><option>Yellow</option><option>Red</option></select><textarea name='summary' placeholder='Signal summary'></textarea><textarea name='recommendation' placeholder='Recommendation'></textarea><button>Add Council Log</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['council_role'])}</b> • {h(r['signal'])}<p>{h(r['summary'])}</p><p>{h(r['recommendation'])}</p><p class='small'>{h(r['created_at'])}</p></div>"
    return render(content)

@app.route("/decision_logs", methods=["GET","POST"])
def decision_logs():
    if request.method=="POST":
        conn=db()
        conn.execute("INSERT INTO decision_logs(username,decision_title,decision_type,reason,approved_by,status,created_at) VALUES(?,?,?,?,?,?,?)",
        (user(),request.form["decision_title"],request.form["decision_type"],request.form["reason"],request.form["approved_by"],request.form["status"],now()))
        conn.commit(); conn.close(); log("Decision log added", user())
        return redirect("/decision_logs")
    conn=db(); rows=conn.execute("SELECT * FROM decision_logs ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="<div class='card hero'><h1>✅ Decision Logs</h1></div><div class='card'><form method='POST'><input name='decision_title' placeholder='Decision title' required><select name='decision_type'><option>Build</option><option>Privacy</option><option>Commerce</option><option>Community</option><option>Safety</option><option>Roadmap</option></select><textarea name='reason' placeholder='Reason'></textarea><input name='approved_by' placeholder='Approved by'><select name='status'><option>approved</option><option>pending</option><option>rejected</option><option>paused</option></select><button>Add Decision</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['decision_title'])}</b><br>{h(r['decision_type'])} • {h(r['status'])}<p>{h(r['reason'])}</p><p>Approved by: {h(r['approved_by'])}</p></div>"
    return render(content)

@app.route("/risk_logs", methods=["GET","POST"])
def risk_logs():
    if request.method=="POST":
        conn=db()
        conn.execute("INSERT INTO risk_logs(username,risk_title,risk_level,risk_area,risk_description,mitigation,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (user(),request.form["risk_title"],request.form["risk_level"],request.form["risk_area"],request.form["risk_description"],request.form["mitigation"],request.form["status"],now()))
        conn.commit(); conn.close(); log("Risk log added", user())
        return redirect("/risk_logs")
    conn=db(); rows=conn.execute("SELECT * FROM risk_logs ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="<div class='card hero'><h1>⚠️ Risk Logs</h1></div><div class='card'><form method='POST'><input name='risk_title' placeholder='Risk title' required><select name='risk_level'><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select><select name='risk_area'><option>Privacy</option><option>Security</option><option>Finance</option><option>Youth Safety</option><option>Community</option><option>Technical</option><option>Reputation</option></select><textarea name='risk_description' placeholder='Risk description'></textarea><textarea name='mitigation' placeholder='Mitigation'></textarea><select name='status'><option>open</option><option>monitoring</option><option>fixed</option><option>paused</option></select><button>Add Risk</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['risk_title'])}</b><br>{h(r['risk_level'])} • {h(r['risk_area'])} • {h(r['status'])}<p>{h(r['risk_description'])}</p><p>{h(r['mitigation'])}</p></div>"
    return render(content)

@app.route("/build_logs", methods=["GET","POST"])
def build_logs():
    if request.method=="POST":
        conn=db()
        conn.execute("INSERT INTO build_logs(username,build_name,version,result,backup_name,lesson,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (user(),request.form["build_name"],request.form["version"],request.form["result"],request.form["backup_name"],request.form["lesson"],"recorded",now()))
        conn.commit(); conn.close(); log("Build log added", user())
        return redirect("/build_logs")
    conn=db(); rows=conn.execute("SELECT * FROM build_logs ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="<div class='card hero'><h1>🧱 Build Logs</h1></div><div class='card'><form method='POST'><input name='build_name' placeholder='Build name' required><input name='version' placeholder='Version e.g. v4.2'><textarea name='result' placeholder='Result'></textarea><input name='backup_name' placeholder='Gold backup name'><textarea name='lesson' placeholder='Lesson learned'></textarea><button>Add Build Log</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['build_name'])}</b> • {h(r['version'])}<p>{h(r['result'])}</p><p>{h(r['lesson'])}</p><p class='small'>{h(r['backup_name'])}</p></div>"
    return render(content)

@app.route("/sovereign_veto", methods=["GET","POST"])
def sovereign_veto():
    if request.method=="POST":
        conn=db()
        conn.execute("INSERT INTO sovereign_veto_logs(username,veto_title,veto_reason,risk_level,decision,reviewer,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (user(),request.form["veto_title"],request.form["veto_reason"],request.form["risk_level"],request.form["decision"],request.form["reviewer"],request.form["status"],now()))
        conn.commit(); conn.close(); log("Sovereign veto recorded", user())
        return redirect("/sovereign_veto")
    conn=db(); rows=conn.execute("SELECT * FROM sovereign_veto_logs ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="<div class='card hero'><h1>👑 Sovereign Veto</h1><p class='green'>Pause → Review → Verify → Decide → Record</p></div><div class='card danger'>Veto is not power. Veto is responsibility. It exists to prevent harm.</div><div class='card'><form method='POST'><input name='veto_title' placeholder='Veto title' required><textarea name='veto_reason' placeholder='Reason'></textarea><select name='risk_level'><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select><textarea name='decision' placeholder='Decision / action'></textarea><input name='reviewer' placeholder='Reviewer / final approval'><select name='status'><option>paused</option><option>approved</option><option>rejected</option><option>monitoring</option></select><button>Record Veto</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['veto_title'])}</b><br>{h(r['risk_level'])} • {h(r['status'])}<p>{h(r['veto_reason'])}</p><p>{h(r['decision'])}</p><p>Reviewer: {h(r['reviewer'])}</p></div>"
    return render(content)

@app.route("/family_tree")
def family_tree():
    return render("<div class='card hero'><h1>🌳 Family Tree</h1><p class='green'>Roots are heritage. Branches are relationships. Leaves are communities. Fruit is contribution.</p></div>")

@app.route("/affiliate_tree")
def affiliate_tree():
    return render("<div class='card hero'><h1>🌿 Affiliate Tree</h1><p class='green'>Rewards follow real value, not recruitment.</p></div><div class='card warn'>Direct commission only. No pyramid. No pressure. No fake income promises.</div>")

@app.route("/community")
def community():
    return render("<div class='card hero'><h1>🌍 Community</h1></div>")

@app.route("/culture")
def culture():
    return render("<div class='card hero'><h1>🎵 Culture</h1></div>")

@app.route("/artists")
def artists():
    return render("<div class='card hero'><h1>🎤 Artists</h1></div>")

@app.route("/events")
def events():
    return render("<div class='card hero'><h1>📅 Events</h1></div>")

@app.route("/business")
def business():
    return render("<div class='card hero'><h1>🏪 Business</h1></div>")

@app.route("/products")
def products():
    return render("<div class='card hero'><h1>🛍 Products</h1></div>")

@app.route("/messages")
def messages():
    return render("<div class='card hero'><h1>💬 Messenger</h1></div>")

@app.route("/trust_badge")
def trust_badge():
    return render("<div class='card hero'><h1>⭐ Trust Badge</h1></div>")

@app.route("/opportunity_board")
def opportunity():
    return render("<div class='card hero'><h1>💰 Opportunity Board</h1></div>")

@app.route("/payouts")
def payouts():
    return render("<div class='card hero'><h1>💸 Payouts</h1></div>")

@app.route("/approvals")
def approvals():
    return render("<div class='card hero'><h1>✅ Approvals</h1></div>")

@app.route("/search")
def search():
    q=request.args.get("q","").strip()
    return render(f"<div class='card hero'><h1>🔎 OAP Search</h1></div><div class='card'><form method='GET'><input name='q' value='{h(q)}' placeholder='Search OAP records'><button>Search</button></form></div>")

@app.route("/explorer")
def explorer():
    return render("<div class='card hero'><h1>🧭 Explorer</h1></div><div class='grid'><div class='card'><h2>🧠 HRM</h2><a href='/hrm'>Open</a></div><div class='card'><h2>👑 Sovereign Veto</h2><a href='/sovereign_veto'>Open</a></div><div class='card'><h2>🌳 Family Tree</h2><a href='/family_tree'>Open</a></div><div class='card'><h2>🌿 Affiliate Tree</h2><a href='/affiliate_tree'>Open</a></div></div>")

@app.route("/command_center")
@app.route("/dashboard")
def command_center():
    conn=db()
    council=conn.execute("SELECT COUNT(*) c FROM council_logs").fetchone()["c"]
    decisions=conn.execute("SELECT COUNT(*) c FROM decision_logs").fetchone()["c"]
    risks=conn.execute("SELECT COUNT(*) c FROM risk_logs").fetchone()["c"]
    builds=conn.execute("SELECT COUNT(*) c FROM build_logs").fetchone()["c"]
    veto=conn.execute("SELECT COUNT(*) c FROM sovereign_veto_logs").fetchone()["c"]
    conn.close()
    return render(f"<div class='card hero'><h1>🎯 Command Center</h1></div><div class='grid'><div class='card'><h2>{council}</h2><p>Council Logs</p></div><div class='card'><h2>{decisions}</h2><p>Decision Logs</p></div><div class='card'><h2>{risks}</h2><p>Risk Logs</p></div><div class='card'><h2>{builds}</h2><p>Build Logs</p></div><div class='card'><h2>{veto}</h2><p>Sovereign Veto Logs</p></div></div>")

@app.route("/health")
def health():
    conn=db(); checks=[]
    for table in ["users","audit_logs","family_tree","affiliate_tree","council_logs","decision_logs","risk_logs","build_logs","sovereign_veto_logs"]:
        try:
            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            checks.append((table,"OK"))
        except Exception as e:
            checks.append((table,str(e)))
    conn.close()
    content="<div class='card hero'><h1>🧪 Health Check</h1></div>"
    for table,status in checks:
        content+=f"<div class='card'><b>{h(table)}</b><br>{h(status)}</div>"
    return render(content)

@app.route("/routes")
def routes():
    links=sorted(set(str(r.rule) for r in app.url_map.iter_rules() if "GET" in r.methods))
    content="<div class='card hero'><h1>🧪 Route Checker</h1></div><div class='card'>"
    for link in links: content+=f"<p><a href='{h(link)}'>{h(link)}</a></p>"
    return render(content+"</div>")

@app.route("/admin")
def admin():
    conn=db(); logs=conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>⚙ Admin</h1></div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content+=f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    return render(content+"</div>")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
