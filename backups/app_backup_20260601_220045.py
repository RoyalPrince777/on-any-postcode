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

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def h(x): return escape(str(x or ""))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def add_col(cur, table, col, typ):
    cur.execute(f"PRAGMA table_info({table})")
    if col not in [r[1] for r in cur.fetchall()]:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")

def init_db():
    conn = db()
    cur = conn.cursor()
    tables = {
        "users":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("nickname","TEXT"),("username","TEXT UNIQUE"),("password","TEXT"),("postcode","TEXT"),("borough","TEXT"),("county_region","TEXT"),("country","TEXT"),("continent","TEXT"),("weather_location","TEXT"),("verification_level","TEXT DEFAULT 'Starter'"),("role","TEXT DEFAULT 'member'"),("created_at","TEXT")],
        "audit_logs":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("action","TEXT"),("username","TEXT"),("member","TEXT"),("created_at","TEXT")],
        "family_tree":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("node_name","TEXT"),("node_type","TEXT"),("connection_to","TEXT"),("relationship","TEXT"),("heritage_note","TEXT"),("contribution_note","TEXT"),("visibility","TEXT DEFAULT 'private'"),("status","TEXT DEFAULT 'active'"),("created_at","TEXT")],
        "affiliate_tree":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("affiliate_name","TEXT"),("affiliate_type","TEXT"),("referred_business","TEXT"),("sale_value","REAL DEFAULT 0"),("commission_value","REAL DEFAULT 0"),("currency","TEXT DEFAULT 'GBP'"),("proof_note","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "council_logs":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("council_role","TEXT"),("signal","TEXT"),("summary","TEXT"),("recommendation","TEXT"),("status","TEXT DEFAULT 'active'"),("created_at","TEXT")],
        "decision_logs":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("decision_title","TEXT"),("decision_type","TEXT"),("reason","TEXT"),("approved_by","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "risk_logs":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("risk_title","TEXT"),("risk_level","TEXT"),("risk_area","TEXT"),("risk_description","TEXT"),("mitigation","TEXT"),("status","TEXT DEFAULT 'open'"),("created_at","TEXT")],
        "build_logs":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("build_name","TEXT"),("version","TEXT"),("result","TEXT"),("backup_name","TEXT"),("lesson","TEXT"),("status","TEXT DEFAULT 'recorded'"),("created_at","TEXT")],
        "sovereign_veto_logs":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("veto_title","TEXT"),("veto_reason","TEXT"),("risk_level","TEXT"),("decision","TEXT"),("reviewer","TEXT"),("status","TEXT DEFAULT 'paused'"),("created_at","TEXT")],
        "sika_trust_records":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("record_type","TEXT"),("record_title","TEXT"),("linked_to","TEXT"),("value_note","TEXT"),("proof_note","TEXT"),("trust_points","INTEGER DEFAULT 0"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "awards":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("award_name","TEXT"),("award_type","TEXT"),("nominee_name","TEXT"),("linked_record","TEXT"),("reason","TEXT"),("proof_note","TEXT"),("sika_points","INTEGER DEFAULT 0"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "royal_archive":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("archive_title","TEXT"),("archive_type","TEXT"),("heritage_link","TEXT"),("stewardship_note","TEXT"),("legacy_note","TEXT"),("visibility","TEXT DEFAULT 'private'"),("status","TEXT DEFAULT 'active'"),("created_at","TEXT")],
        "country_spaces":[("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("country_name","TEXT"),("continent","TEXT"),("space_type","TEXT"),("culture_note","TEXT"),("community_note","TEXT"),("song_note","TEXT"),("status","TEXT DEFAULT 'active'"),("created_at","TEXT")]
    }
    for table, cols in tables.items():
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table}({', '.join([c+' '+t for c,t in cols])})")
        for c,t in cols:
            if c != "id": add_col(cur, table, c, t)

    found = cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,)).fetchone()
    if found:
        cur.execute("UPDATE users SET password=?, role=?, verification_level=? WHERE username=?", (generate_password_hash(ADMIN_PASSWORD), "admin", "Founder", ADMIN_USERNAME))
    else:
        cur.execute("""INSERT INTO users(nickname,username,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", ("N24-7", ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), "CR4", "Merton", "Greater London", "UK", "Europe", "London", "Founder", "admin", now()))
    conn.commit()
    conn.close()

def log(action, username="system"):
    conn=db()
    conn.execute("INSERT INTO audit_logs(action,username,member,created_at) VALUES(?,?,?,?)", (action, username, username, now()))
    conn.commit()
    conn.close()

init_db()

def user(): return session.get("user", "guest")

def count(table, where="", params=()):
    conn=db()
    try: return conn.execute(f"SELECT COUNT(*) c FROM {table} {where}", params).fetchone()["c"]
    except Exception: return 0
    finally: conn.close()

def sum_col(table, col, where="", params=()):
    conn=db()
    try: return conn.execute(f"SELECT COALESCE(SUM({col}),0) s FROM {table} {where}", params).fetchone()["s"]
    except Exception: return 0
    finally: conn.close()

def render(content): return render_template_string(BASE, content=content)

BASE = """
<!DOCTYPE html><html><head><title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#050505;color:white;font-family:Arial}
.top{background:#101010;padding:15px;border-bottom:1px solid #222;position:sticky;top:0;z-index:5}
.logo{font-size:22px;font-weight:900;margin-bottom:6px}.wrap{padding:14px;max-width:1150px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:16px;margin:12px 0}
.hero{text-align:center;padding:30px 10px}.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.nav a,.chip{background:#151515;border:1px solid #272727;border-radius:999px;padding:8px 12px;color:#00dd99;font-size:14px}
input,textarea,select{width:100%;padding:13px;margin:8px 0;background:#0b0b0b;color:white;border:1px solid #333;border-radius:12px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:12px;padding:13px 18px;font-weight:900}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.warn{background:#2b1600;border-color:#6b3b00}.danger{background:#300;border-color:#700}
.badge{display:inline-block;background:#00dd99;color:#000;padding:7px 11px;border-radius:999px;font-weight:900;font-size:12px;margin:3px}
.small{color:#aaa;font-size:13px}
</style></head><body>
<div class="top"><div class="logo">ON ANY POSTCODE</div>
<div>{% if session.get("user") %}@{{session.get("user")}} <a href="/leave">Leave My World</a>{% else %}<a href="/join">Join OAP</a> <a href="/enter">Enter My World</a>{% endif %}</div>
<div class="nav"><a href="/">Home</a><a href="/my_world">My World</a><a href="/prince">Prince</a><a href="/megaverse">Megaverse</a><a href="/countries">Countries</a><a href="/search">Search</a><a href="/command_center">Command Center</a><a href="/sika_trust">SIKA Trust</a><a href="/awards">Awards</a><a href="/hrm">HRM</a><a href="/menu">Menu</a></div>
</div><div class="wrap">{{content|safe}}</div></body></html>
"""

@app.route("/favicon.ico")
def favicon(): return ("",204)

@app.route("/")
def home():
    return render(f"""
    <div class='card hero'><h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>Record → Verify → Build</p>
    <p>Royalty protects legacy. HRM records truth. SIKA records trust. Country Spaces connect cultures.</p>
    <a class='badge' href='/join'>Join OAP</a><a class='badge' href='/enter'>Enter My World</a></div>
    <div class='grid'>
    <div class='card'><h2>{count("users")}</h2><p>Members</p></div>
    <div class='card'><h2>{count("country_spaces")}</h2><p>Country Spaces</p></div>
    <div class='card'><h2>{count("royal_archive")}</h2><p>Royal Archive</p></div>
    <div class='card'><h2>{count("sika_trust_records")}</h2><p>SIKA Trust</p></div>
    <div class='card'><h2>{count("awards")}</h2><p>Awards</p></div>
    <div class='card'><h2>{sum_col("sika_trust_records","trust_points")}</h2><p>SIKA Points</p></div>
    </div>
    """)

@app.route("/join", methods=["GET","POST"])
def join():
    if request.method=="POST":
        conn=db()
        try:
            conn.execute("""INSERT INTO users(nickname,username,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (request.form["nickname"],request.form["username"],generate_password_hash(request.form["password"]),request.form.get("postcode",""),request.form.get("borough",""),request.form.get("county_region",""),request.form.get("country",""),request.form.get("continent",""),request.form.get("weather_location",""),"Starter","member",now()))
            conn.commit(); log("Member joined OAP", request.form["username"])
            return redirect("/welcome")
        except sqlite3.IntegrityError:
            return render("<div class='card'><h1>Username exists</h1><a href='/join'>Try again</a></div>")
        finally: conn.close()
    return render("<div class='card hero'><h1>Join OAP</h1></div><div class='card'><form method='POST'><input name='nickname' placeholder='Nickname' required><input name='username' placeholder='Username' required><input name='password' type='password' placeholder='Password' required><input name='postcode' placeholder='Postcode optional'><input name='borough' placeholder='Borough optional'><input name='county_region' placeholder='County / Region optional'><input name='country' placeholder='Country optional'><input name='continent' placeholder='Continent optional'><input name='weather_location' placeholder='Weather location optional'><button>Join OAP</button></form></div>")

@app.route("/welcome")
def welcome(): return render("<div class='card hero'><h1>🌍 Your World Has Been Created</h1><a class='badge' href='/enter'>Enter My World</a></div>")

@app.route("/enter", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def enter():
    if request.method=="POST":
        conn=db(); row=conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone(); conn.close()
        if row and check_password_hash(row["password"], request.form["password"]):
            session["user"]=row["username"]; session["role"]=row["role"]; log("Entered My World", row["username"]); return redirect("/my_world")
        return render("<div class='card'><h1>Invalid entry</h1><a href='/enter'>Try again</a></div>")
    return render("<div class='card hero'><h1>Enter My World</h1></div><div class='card'><form method='POST'><input name='username' placeholder='Username' required><input name='password' type='password' placeholder='Password' required><button>Enter My World</button></form><p>Founder: N24-7 / 2525</p></div>")

@app.route("/leave")
@app.route("/logout")
def leave(): session.clear(); return redirect("/")

@app.route("/my_world")
def my_world():
    u=user()
    return render(f"""
    <div class='card hero'><h1>🌍 My World</h1><p class='green'>Every member has a World.</p></div>
    <div class='grid'>
    <div class='card'><h2>{count("country_spaces","WHERE username=?",(u,))}</h2><p>My Country Spaces</p><a href='/countries'>Open</a></div>
    <div class='card'><h2>{count("family_tree","WHERE username=?",(u,))}</h2><p>My Family Tree</p><a href='/family_tree'>Open</a></div>
    <div class='card'><h2>{count("sika_trust_records","WHERE username=?",(u,))}</h2><p>My SIKA Records</p><a href='/sika_trust'>Open</a></div>
    <div class='card'><h2>{count("awards","WHERE username=?",(u,))}</h2><p>My Awards</p><a href='/awards'>Open</a></div>
    <div class='card'><h2>{count("royal_archive","WHERE username=?",(u,))}</h2><p>Royal Archive</p><a href='/prince'>Open</a></div>
    </div>
    """)

@app.route("/countries", methods=["GET","POST"])
def countries():
    if request.method=="POST":
        conn=db()
        conn.execute("""INSERT INTO country_spaces(username,country_name,continent,space_type,culture_note,community_note,song_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (user(),request.form["country_name"],request.form["continent"],request.form["space_type"],request.form["culture_note"],request.form["community_note"],request.form["song_note"],"active",now()))
        conn.commit(); conn.close(); log("Country Space added", user()); return redirect("/countries")
    conn=db(); rows=conn.execute("SELECT * FROM country_spaces ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="""
    <div class='card hero'><h1>🌍 Country Spaces</h1><p class='green'>Culture, community, songs, events and heritage by country.</p></div>
    <div class='card warn'>Use safe country spaces first. No conflict spaces until mission layer is ready.</div>
    <div class='card'><form method='POST'>
    <input name='country_name' placeholder='Country name' required>
    <select name='continent'><option>Africa</option><option>Europe</option><option>South America</option><option>North America</option><option>Asia</option><option>Caribbean</option><option>Oceania</option><option>Global</option></select>
    <select name='space_type'><option>Culture</option><option>Music</option><option>Sports</option><option>Business</option><option>Heritage</option><option>Community</option></select>
    <textarea name='culture_note' placeholder='Culture note'></textarea>
    <textarea name='community_note' placeholder='Community note'></textarea>
    <textarea name='song_note' placeholder='International song / play-pause note'></textarea>
    <button>Add Country Space</button></form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['country_name'])}</b><br>{h(r['continent'])} • {h(r['space_type'])}<p>{h(r['culture_note'])}</p><p>{h(r['community_note'])}</p><p class='gold'>Song: {h(r['song_note'])}</p><p class='small'>@{h(r['username'])} • {h(r['created_at'])}</p></div>"
    return render(content)

@app.route("/prince", methods=["GET","POST"])
def prince():
    if request.method=="POST":
        conn=db()
        conn.execute("""INSERT INTO royal_archive(username,archive_title,archive_type,heritage_link,stewardship_note,legacy_note,visibility,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (user(),request.form["archive_title"],request.form["archive_type"],request.form["heritage_link"],request.form["stewardship_note"],request.form["legacy_note"],request.form["visibility"],"active",now()))
        conn.commit(); conn.close(); log("Royal Archive record added", user()); return redirect("/prince")
    conn=db(); rows=conn.execute("SELECT * FROM royal_archive ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="<div class='card hero'><h1>👑 Prince of KORADASO</h1><p class='green'>Royalty means service, stewardship, legacy, culture and protection.</p></div><div class='card warn'>Not government authority. Not banking authority. Not control over people.</div><div class='grid'><div class='card'><h2>🌍 Countries</h2><a href='/countries'>Open</a></div><div class='card'><h2>🪙 SIKA Trust</h2><a href='/sika_trust'>Open</a></div><div class='card'><h2>🏆 Awards</h2><a href='/awards'>Open</a></div></div><div class='card'><form method='POST'><input name='archive_title' placeholder='Royal archive title' required><select name='archive_type'><option>Heritage Record</option><option>Stewardship Note</option><option>Legacy Record</option><option>Culture Protection</option><option>Country Space</option></select><input name='heritage_link' placeholder='Linked record'><textarea name='stewardship_note' placeholder='Stewardship note'></textarea><textarea name='legacy_note' placeholder='Legacy note'></textarea><select name='visibility'><option>private</option><option>public</option></select><button>Add Royal Archive Record</button></form></div>"
    for r in rows:
        content += f"<div class='card'><b>{h(r['archive_title'])}</b><br>{h(r['archive_type'])}<p>{h(r['stewardship_note'])}</p><p>{h(r['legacy_note'])}</p></div>"
    return render(content)

@app.route("/megaverse")
def megaverse():
    return render(f"""
    <div class='card hero'><h1>🌌 Sovereign Megaverse Dashboard</h1><p class='green'>Human-first intelligence from real records.</p></div>
    <div class='grid'>
    <div class='card'><h2>85% 🟢</h2><p>Personal HRM</p></div>
    <div class='card'><h2>95% 🟢</h2><p>Sovereign Council</p></div>
    <div class='card'><h2>50% 🟡</h2><p>Royal Stewardship</p></div>
    <div class='card'><h2>75% 🟡</h2><p>Trust Intelligence</p></div>
    <div class='card'><h2>35% 🟡</h2><p>Country Intelligence</p></div>
    <div class='card'><h2>25% 🔴</h2><p>Commerce Intelligence</p></div>
    </div>
    <div class='card'><h2>Live Records</h2><p>Country Spaces: {count("country_spaces")}</p><p>Royal Archive: {count("royal_archive")}</p><p>SIKA Trust: {count("sika_trust_records")}</p><p>Awards: {count("awards")}</p></div>
    """)

@app.route("/sika_trust", methods=["GET","POST"])
def sika_trust():
    if request.method=="POST":
        points=int(request.form.get("trust_points") or 0)
        conn=db()
        conn.execute("""INSERT INTO sika_trust_records(username,record_type,record_title,linked_to,value_note,proof_note,trust_points,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (user(),request.form["record_type"],request.form["record_title"],request.form["linked_to"],request.form["value_note"],request.form["proof_note"],points,"pending",now()))
        conn.commit(); conn.close(); log("SIKA Trust record added", user()); return redirect("/sika_trust")
    conn=db(); rows=conn.execute("SELECT * FROM sika_trust_records ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="<div class='card hero'><h1>🪙 SIKA Trust Records</h1><p class='green'>Not money. Not a bank. Trust records only.</p></div><div class='card'><form method='POST'><select name='record_type'><option>Community Contribution</option><option>Country Space</option><option>Award Proof</option><option>Royal Archive</option></select><input name='record_title' placeholder='Record title' required><input name='linked_to' placeholder='Linked to'><textarea name='value_note' placeholder='Value note'></textarea><textarea name='proof_note' placeholder='Proof note'></textarea><input name='trust_points' placeholder='Trust points'><button>Add SIKA Trust Record</button></form></div>"
    for r in rows: content += f"<div class='card'><b>{h(r['record_title'])}</b><br>{h(r['record_type'])}<p>{h(r['value_note'])}</p><p class='gold'>{h(r['trust_points'])} points</p></div>"
    return render(content)

@app.route("/awards", methods=["GET","POST"])
def awards():
    if request.method=="POST":
        points=int(request.form.get("sika_points") or 0)
        conn=db()
        conn.execute("""INSERT INTO awards(username,award_name,award_type,nominee_name,linked_record,reason,proof_note,sika_points,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)""", (user(),request.form["award_name"],request.form["award_type"],request.form["nominee_name"],request.form["linked_record"],request.form["reason"],request.form["proof_note"],points,"pending",now()))
        conn.commit(); conn.close(); log("Award record added", user()); return redirect("/awards")
    conn=db(); rows=conn.execute("SELECT * FROM awards ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    content="<div class='card hero'><h1>🏆 OAP Awards</h1></div><div class='card'><form method='POST'><input name='award_name' placeholder='Award name' required><select name='award_type'><option>Community Champion</option><option>Culture Keeper</option><option>Country Space Award</option><option>Heritage Guardian</option></select><input name='nominee_name' placeholder='Nominee'><input name='linked_record' placeholder='Linked record'><textarea name='reason' placeholder='Reason'></textarea><textarea name='proof_note' placeholder='Proof note'></textarea><input name='sika_points' placeholder='Award points'><button>Add Award</button></form></div>"
    for r in rows: content += f"<div class='card'><b>{h(r['award_name'])}</b><br>{h(r['award_type'])}<p>{h(r['reason'])}</p><p class='gold'>{h(r['sika_points'])} points</p></div>"
    return render(content)

def log_page(table,title,fields):
    if request.method=="POST":
        cols=["username"]+list(fields.keys())+["created_at"]
        vals=[user()]+[request.form.get(k,"") for k in fields.keys()]+[now()]
        conn=db(); conn.execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join(['?']*len(vals))})", vals); conn.commit(); conn.close(); log(f"{title} added", user()); return redirect("/"+table)
    conn=db(); rows=conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 100").fetchall(); conn.close()
    form=f"<div class='card hero'><h1>{h(title)}</h1></div><div class='card'><form method='POST'>"
    for name,label in fields.items(): form += f"<textarea name='{h(name)}' placeholder='{h(label)}'></textarea>"
    form += f"<button>Add {h(title)}</button></form></div>"
    for r in rows: form += "<div class='card'>"+"".join([f"<p><b>{h(k)}:</b> {h(r[k])}</p>" for k in r.keys() if k!="id"])+"</div>"
    return render(form)

@app.route("/council_logs", methods=["GET","POST"])
def council_logs(): return log_page("council_logs","👑 Council Logs",{"council_role":"Council role","signal":"Signal","summary":"Summary","recommendation":"Recommendation","status":"Status"})
@app.route("/decision_logs", methods=["GET","POST"])
def decision_logs(): return log_page("decision_logs","✅ Decision Logs",{"decision_title":"Decision title","decision_type":"Decision type","reason":"Reason","approved_by":"Approved by","status":"Status"})
@app.route("/risk_logs", methods=["GET","POST"])
def risk_logs(): return log_page("risk_logs","⚠️ Risk Logs",{"risk_title":"Risk title","risk_level":"Risk level","risk_area":"Risk area","risk_description":"Risk description","mitigation":"Mitigation","status":"Status"})
@app.route("/build_logs", methods=["GET","POST"])
def build_logs(): return log_page("build_logs","🧱 Build Logs",{"build_name":"Build name","version":"Version","result":"Result","backup_name":"Backup name","lesson":"Lesson","status":"Status"})
@app.route("/sovereign_veto", methods=["GET","POST"])
def sovereign_veto(): return log_page("sovereign_veto_logs","👑 Sovereign Veto",{"veto_title":"Veto title","veto_reason":"Reason","risk_level":"Risk level","decision":"Decision","reviewer":"Reviewer","status":"Status"})

@app.route("/menu")
def menu(): return render("<div class='card hero'><h1>☰ OAP Menu</h1></div><div class='grid'><div class='card'><h2>Royal</h2><p><a href='/prince'>Prince</a></p><p><a href='/megaverse'>Megaverse</a></p><p><a href='/countries'>Countries</a></p></div><div class='card'><h2>My World</h2><p><a href='/my_world'>My World</a></p><p><a href='/sika_trust'>SIKA Trust</a></p><p><a href='/awards'>Awards</a></p></div><div class='card'><h2>HRM</h2><p><a href='/hrm'>HRM</a></p><p><a href='/decision_logs'>Decision Logs</a></p><p><a href='/risk_logs'>Risk Logs</a></p></div></div>")
@app.route("/privacy")
def privacy(): return render("<div class='card hero'><h1>🛡️ Privacy & Trust</h1></div><div class='card'><p>✅ Your data belongs to you.</p><p>✅ Your profile belongs to you.</p><p>✅ Your content belongs to you.</p><p>✅ Your messages belong to you.</p><p>✅ Your culture belongs to you.</p><p>✅ Your business belongs to you.</p></div>")
@app.route("/hrm")
def hrm(): return render("<div class='card hero'><h1>🧠 HRM Sovereign Core</h1><p class='green'>Record → Verify → Build</p></div><div class='card'><p>No memory = no intelligence.</p><p>No verification = no trust.</p><p>No audit = no automation.</p><p>No human approval = no real-world action.</p></div>")
@app.route("/family_tree")
def family_tree(): return render("<div class='card hero'><h1>🌳 Family Tree</h1></div>")
@app.route("/affiliate_tree")
def affiliate_tree(): return render("<div class='card hero'><h1>🌿 Affiliate Tree</h1></div>")
@app.route("/search")
def search(): return render("<div class='card hero'><h1>🔎 OAP Search</h1></div><div class='card'><form><input name='q' placeholder='Search OAP records'><button>Search</button></form></div>")
@app.route("/explorer")
def explorer(): return render("<div class='card hero'><h1>🧭 Explorer</h1></div><div class='grid'><div class='card'><h2>Countries</h2><a href='/countries'>Open</a></div><div class='card'><h2>Prince</h2><a href='/prince'>Open</a></div><div class='card'><h2>Megaverse</h2><a href='/megaverse'>Open</a></div></div>")
@app.route("/command_center")
@app.route("/dashboard")
def command_center(): return render(f"<div class='card hero'><h1>🎯 Command Center</h1></div><div class='grid'><div class='card'><h2>{count('country_spaces')}</h2><p>Country Spaces</p></div><div class='card'><h2>{count('royal_archive')}</h2><p>Royal Archive</p></div><div class='card'><h2>{count('sika_trust_records')}</h2><p>SIKA Trust</p></div><div class='card'><h2>{count('awards')}</h2><p>Awards</p></div></div>")
@app.route("/health")
def health():
    tables=["users","audit_logs","country_spaces","family_tree","affiliate_tree","sika_trust_records","awards","royal_archive","council_logs","decision_logs","risk_logs","build_logs","sovereign_veto_logs"]
    content="<div class='card hero'><h1>🧪 Health Check</h1></div>"; conn=db()
    for table in tables:
        try: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone(); status="OK"
        except Exception as e: status=str(e)
        content += f"<div class='card'><b>{h(table)}</b><br>{h(status)}</div>"
    conn.close(); return render(content)
@app.route("/routes")
def routes():
    links=sorted(set(str(r.rule) for r in app.url_map.iter_rules() if "GET" in r.methods))
    return render("<div class='card hero'><h1>🧪 Route Checker</h1></div><div class='card'>"+"".join([f"<p><a href='{h(link)}'>{h(link)}</a></p>" for link in links])+"</div>")
@app.route("/admin")
def admin(): return render("<div class='card hero'><h1>⚙ Admin</h1></div>")
@app.route("/community")
def community(): return render("<div class='card hero'><h1>🌍 Community</h1></div>")
@app.route("/culture")
def culture(): return render("<div class='card hero'><h1>🎵 Culture</h1></div>")
@app.route("/artists")
def artists(): return render("<div class='card hero'><h1>🎤 Artists</h1></div>")
@app.route("/events")
def events(): return render("<div class='card hero'><h1>📅 Events</h1></div>")
@app.route("/business")
def business(): return render("<div class='card hero'><h1>🏪 Business</h1></div>")
@app.route("/products")
def products(): return render("<div class='card hero'><h1>🛍 Products</h1></div>")
@app.route("/messages")
def messages(): return render("<div class='card hero'><h1>💬 Messenger</h1></div>")
@app.route("/trust_badge")
def trust_badge(): return render("<div class='card hero'><h1>⭐ Trust Badge</h1></div>")
@app.route("/opportunity_board")
def opportunity_board(): return render("<div class='card hero'><h1>💰 Opportunity Board</h1></div>")
@app.route("/payouts")
def payouts(): return render("<div class='card hero'><h1>💸 Payouts</h1></div>")
@app.route("/approvals")
def approvals(): return render("<div class='card hero'><h1>✅ Approvals</h1></div>")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
