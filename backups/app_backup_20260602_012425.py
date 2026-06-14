from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_operating_core_v1"
DB = "oap_world.db"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def qcount(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

def total_value(conn):
    return round(conn.execute("SELECT COALESCE(SUM(amount),0) FROM value_created").fetchone()[0], 2)

def init_db():
    conn = db()
    c = conn.cursor()

    tables = [
        """CREATE TABLE IF NOT EXISTS news(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,body TEXT,category TEXT,postcode TEXT,country TEXT,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS oap_experiences(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,description TEXT,location TEXT,postcode TEXT,country TEXT,event_date TEXT,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS explorer_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,query TEXT,results_count INTEGER,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS people_command(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,mission_type TEXT,assigned_to TEXT,postcode TEXT,country TEXT,priority TEXT,status TEXT,action_note TEXT,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS p2u_members(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,postcode TEXT,borough TEXT,county_region TEXT,country TEXT,tier TEXT,monthly_value REAL,status TEXT,contribution_note TEXT,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS family_tree(id INTEGER PRIMARY KEY AUTOINCREMENT,member_name TEXT,root_place TEXT,heritage_note TEXT,relationship_note TEXT,mentor_note TEXT,legacy_note TEXT,privacy_status TEXT,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS business_network(id INTEGER PRIMARY KEY AUTOINCREMENT,business_name TEXT,owner_name TEXT,category TEXT,postcode TEXT,borough TEXT,country TEXT,listing_type TEXT,monthly_value REAL,status TEXT,description TEXT,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS creator_hub(id INTEGER PRIMARY KEY AUTOINCREMENT,creator_name TEXT,skill TEXT,postcode TEXT,borough TEXT,country TEXT,profile_type TEXT,monthly_value REAL,status TEXT,bio TEXT,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS proof_of_contribution(id INTEGER PRIMARY KEY AUTOINCREMENT,member_name TEXT,contribution_type TEXT,proof_note TEXT,status TEXT,created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS value_created(id INTEGER PRIMARY KEY AUTOINCREMENT,source TEXT,amount REAL,note TEXT,created_at TEXT)"""
    ]

    for t in tables:
        c.execute(t)

    conn.commit()
    conn.close()

init_db()

P2U_TIERS = {"Postcode Founder": 5, "Borough Builder": 10, "Country Champion": 25}
BUSINESS_LISTINGS = {"Free Listing": 0, "Featured Listing": 10, "Premium Listing": 25}
CREATOR_PROFILES = {"Free Creator Profile": 0, "Featured Creator": 10, "Promotion Slot": 25}

BASE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Operating Core</title>
<style>
body{margin:0;font-family:Arial;background:#07110b;color:#f5fff7}
header{padding:22px;background:#0d1f14;border-bottom:1px solid #1f4d2e}
nav a{color:#b8ffc8;margin-right:10px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:1150px;margin:auto}
.card{background:#102417;border:1px solid #275b36;border-radius:18px;padding:18px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
input,textarea,select,button{width:100%;padding:13px;margin:7px 0;border-radius:12px;border:0}
button{background:#21c45a;color:#031006;font-weight:bold}
.badge{display:inline-block;background:#183b25;color:#b8ffc8;padding:7px 10px;border-radius:20px;margin:4px}
.big{font-size:34px;font-weight:bold;color:#ffd76b}
.gold{color:#ffd76b}.green{color:#9dffb3}.red{color:#ff8d8d}.small{opacity:.75;font-size:13px}
</style>
</head>
<body>
<header>
<h1>👑 OAP Operating Core</h1>
<nav>
<a href="/">Home</a>
<a href="/explorer">Explorer</a>
<a href="/dashboard">Dashboard</a>
<a href="/people-command">People’s Command</a>
<a href="/circle">Circle</a>
<a href="/family-tree">Family Tree</a>
<a href="/business-network">Business</a>
<a href="/creator-hub">Creator</a>
<a href="/proof">Proof</a>
<a href="/value-created">Value</a>
</nav>
</header>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def page(content):
    return render_template_string(BASE, content=content)

@app.route("/")
def home():
    return page("""
    <div class="card">
    <h2>🌍 From Building OAP to Operating OAP</h2>
    <p><b>Mission:</b> first member, first business, first OAP Experience, first Value Created.</p>
    <p><b>Master line:</b> People’s Command creates OAP Experiences, records Proof of Contribution, and tracks Value Created.</p>
    </div>
    <div class="grid">
      <div class="card"><h3>🔍 Explorer</h3><p>Search everything.</p></div>
      <div class="card"><h3>🐝 People’s Command</h3><p>Missions and action.</p></div>
      <div class="card"><h3>👑 Postcode to Universe Circle</h3><p>Membership journey.</p></div>
      <div class="card"><h3>🌳 Family Tree</h3><p>Roots and legacy.</p></div>
      <div class="card"><h3>🏪 Business Network</h3><p>Local value.</p></div>
      <div class="card"><h3>🎨 Creator Hub</h3><p>Creator promotion.</p></div>
    </div>
    """)

@app.route("/dashboard")
def dashboard():
    conn = db()
    metrics = {
        "News": qcount(conn, "news"),
        "OAP Experiences": qcount(conn, "oap_experiences"),
        "People’s Command": qcount(conn, "people_command"),
        "Circle Members": qcount(conn, "p2u_members"),
        "Family Roots": qcount(conn, "family_tree"),
        "Businesses": qcount(conn, "business_network"),
        "Creators": qcount(conn, "creator_hub"),
        "Proof Records": qcount(conn, "proof_of_contribution"),
        "Explorer Searches": qcount(conn, "explorer_logs"),
    }
    value = total_value(conn)
    conn.close()

    html = "<div class='card'><h2>👑 Sovereign Dashboard</h2><div class='grid'>"
    for k,v in metrics.items():
        html += f"<div class='card'><div class='big'>{v}</div><p>{k}</p></div>"
    html += f"<div class='card'><div class='big'>£{value}</div><p>Value Created</p></div></div></div>"
    html += "<div class='card'><h2>🚦 Mission Signals</h2>"
    html += f"<p class='{'green' if metrics['Circle Members'] else 'red'}'> {'✅' if metrics['Circle Members'] else '🔴'} First member</p>"
    html += f"<p class='{'green' if metrics['Businesses'] else 'red'}'> {'✅' if metrics['Businesses'] else '🔴'} First business</p>"
    html += f"<p class='{'green' if metrics['OAP Experiences'] else 'red'}'> {'✅' if metrics['OAP Experiences'] else '🔴'} First OAP Experience</p>"
    html += f"<p class='{'green' if value else 'red'}'> {'✅' if value else '🔴'} First Value Created</p></div>"
    return page(html)

@app.route("/explorer")
def explorer():
    q = request.args.get("q","").strip()
    results = []
    if q:
        like = f"%{q}%"
        conn = db()
        searches = [
            ("News","news","title","body"),
            ("OAP Experience","oap_experiences","title","description"),
            ("Business","business_network","business_name","description"),
            ("Creator","creator_hub","creator_name","bio"),
            ("Circle Member","p2u_members","name","contribution_note"),
        ]
        for label, table, title_col, body_col in searches:
            rows = conn.execute(f"""SELECT *, '{label}' as result_type FROM {table}
            WHERE {title_col} LIKE ? OR {body_col} LIKE ? OR postcode LIKE ? OR country LIKE ?
            ORDER BY id DESC""", (like,like,like,like)).fetchall()
            results.extend(rows)
        conn.execute("INSERT INTO explorer_logs(query,results_count,created_at) VALUES(?,?,?)", (q,len(results),now()))
        conn.commit()
        conn.close()

    html = f"""<div class='card'><h2>🔍 Explorer</h2>
    <form><input name='q' placeholder='Search news, experiences, businesses, creators, postcodes...' value='{q}'><button>Search OAP</button></form></div>"""
    if q:
        html += f"<div class='card'><h3>{len(results)} result(s) for <span class='gold'>{q}</span></h3></div>"
        for r in results:
            title = r["title"] if "title" in r.keys() else r["business_name"] if "business_name" in r.keys() else r["creator_name"] if "creator_name" in r.keys() else r["name"]
            body = r["body"] if "body" in r.keys() else r["description"] if "description" in r.keys() else r["bio"] if "bio" in r.keys() else r["contribution_note"]
            html += f"<div class='card'><span class='badge'>{r['result_type']}</span><h3>{title}</h3><p>{body}</p></div>"
    return page(html)

@app.route("/people-command")
def people_command():
    conn = db()
    rows = conn.execute("SELECT * FROM people_command ORDER BY id DESC").fetchall()
    conn.close()
    html = "<div class='card'><h2>🐝 People’s Command</h2><p>Missions, helpers, and community action.</p><p><a class='badge' href='/add-mission'>Add Mission</a></p></div>"
    for r in rows:
        html += f"<div class='card'><h3>{r['title']}</h3><p><span class='badge'>{r['mission_type']}</span><span class='badge'>{r['priority']}</span><span class='badge'>{r['status']}</span></p><p>{r['action_note']}</p></div>"
    return page(html)

@app.route("/add-mission", methods=["GET","POST"])
def add_mission():
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO people_command(title,mission_type,assigned_to,postcode,country,priority,status,action_note,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (request.form["title"],request.form["mission_type"],request.form["assigned_to"],request.form["postcode"],request.form["country"],request.form["priority"],request.form["status"],request.form["action_note"],now()))
        conn.commit(); conn.close()
        return redirect("/people-command")
    return page("""<div class='card'><h2>🐝 Add Mission</h2><form method='post'>
    <input name='title' placeholder='Mission title' required>
    <select name='mission_type'><option>First Member</option><option>First Business</option><option>First OAP Experience</option><option>First Value Created</option><option>Community Action</option></select>
    <input name='assigned_to' placeholder='Assigned to'><input name='postcode' placeholder='Postcode'><input name='country' placeholder='Country'>
    <select name='priority'><option>Low</option><option selected>Medium</option><option>High</option></select>
    <select name='status'><option>Open</option><option>In Progress</option><option>Done</option></select>
    <textarea name='action_note' placeholder='Action note'></textarea><button>Save Mission</button></form></div>""")

@app.route("/circle")
def circle():
    conn = db(); rows = conn.execute("SELECT * FROM p2u_members ORDER BY id DESC").fetchall(); conn.close()
    html = "<div class='card'><h2>👑 Postcode to Universe Circle</h2><p><a class='badge' href='/join-circle'>Join Circle</a></p></div>"
    for r in rows:
        html += f"<div class='card'><h3>{r['name']}</h3><p><span class='badge'>{r['tier']}</span><span class='badge'>£{r['monthly_value']}/month</span></p><p>{r['postcode']} → {r['borough']} → {r['country']}</p></div>"
    return page(html)

@app.route("/join-circle", methods=["GET","POST"])
def join_circle():
    if request.method == "POST":
        tier = request.form["tier"]; val = P2U_TIERS[tier]
        conn = db()
        conn.execute("""INSERT INTO p2u_members(name,postcode,borough,county_region,country,tier,monthly_value,status,contribution_note,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)""", (request.form["name"],request.form["postcode"],request.form["borough"],request.form["county_region"],request.form["country"],tier,val,request.form["status"],request.form["contribution_note"],now()))
        conn.execute("INSERT INTO value_created(source,amount,note,created_at) VALUES(?,?,?,?)", ("Postcode to Universe Circle",val,f"{request.form['name']} joined as {tier}",now()))
        conn.execute("INSERT INTO proof_of_contribution(member_name,contribution_type,proof_note,status,created_at) VALUES(?,?,?,?,?)", (request.form["name"],"Postcode to Universe Circle",f"Joined as {tier}","Contribution Recorded",now()))
        conn.commit(); conn.close()
        return redirect("/dashboard")
    return page("""<div class='card'><h2>👑 Join Circle</h2><form method='post'>
    <input name='name' placeholder='Name / username' required><input name='postcode' placeholder='Postcode'><input name='borough' placeholder='Borough'><input name='county_region' placeholder='County / Region'><input name='country' placeholder='Country'>
    <select name='tier'><option>Postcode Founder</option><option>Borough Builder</option><option>Country Champion</option></select>
    <select name='status'><option>Active</option><option>Pending</option></select>
    <textarea name='contribution_note' placeholder='Contribution note'></textarea><button>Record Circle Member</button></form></div>""")

@app.route("/family-tree")
def family_tree():
    conn = db(); rows = conn.execute("SELECT * FROM family_tree ORDER BY id DESC").fetchall(); conn.close()
    html = "<div class='card'><h2>🌳 Family Tree</h2><p>The Circle gives members their place. The Family Tree gives them roots.</p><p><a class='badge' href='/add-family-root'>Add Root</a></p></div>"
    for r in rows:
        html += f"<div class='card'><h3>{r['member_name']}</h3><p><span class='badge'>{r['root_place']}</span><span class='badge'>{r['privacy_status']}</span></p><p>{r['heritage_note']}</p></div>"
    return page(html)

@app.route("/add-family-root", methods=["GET","POST"])
def add_family_root():
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO family_tree(member_name,root_place,heritage_note,relationship_note,mentor_note,legacy_note,privacy_status,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (request.form["member_name"],request.form["root_place"],request.form["heritage_note"],request.form["relationship_note"],request.form["mentor_note"],request.form["legacy_note"],request.form["privacy_status"],now()))
        conn.execute("INSERT INTO proof_of_contribution(member_name,contribution_type,proof_note,status,created_at) VALUES(?,?,?,?,?)", (request.form["member_name"],"Family Tree",f"Root recorded: {request.form['root_place']}","Contribution Recorded",now()))
        conn.commit(); conn.close()
        return redirect("/family-tree")
    return page("""<div class='card'><h2>🌳 Add Family Root</h2><form method='post'>
    <input name='member_name' placeholder='Member name' required><input name='root_place' placeholder='Root place'>
    <textarea name='heritage_note' placeholder='Heritage note'></textarea><textarea name='relationship_note' placeholder='Relationship note'></textarea><textarea name='mentor_note' placeholder='Mentor note'></textarea><textarea name='legacy_note' placeholder='Legacy note'></textarea>
    <select name='privacy_status'><option>Private</option><option>Circle Only</option><option>Public</option></select><button>Save Root</button></form></div>""")

@app.route("/business-network")
def business_network():
    conn = db(); rows = conn.execute("SELECT * FROM business_network ORDER BY id DESC").fetchall(); conn.close()
    html = "<div class='card'><h2>🏪 Business Network</h2><p><a class='badge' href='/add-business'>Add Business</a></p></div>"
    for r in rows:
        html += f"<div class='card'><h3>{r['business_name']}</h3><p><span class='badge'>{r['listing_type']}</span><span class='badge'>£{r['monthly_value']}/month</span></p><p>{r['description']}</p></div>"
    return page(html)

@app.route("/add-business", methods=["GET","POST"])
def add_business():
    if request.method == "POST":
        lt = request.form["listing_type"]; val = BUSINESS_LISTINGS[lt]
        conn = db()
        conn.execute("""INSERT INTO business_network(business_name,owner_name,category,postcode,borough,country,listing_type,monthly_value,status,description,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (request.form["business_name"],request.form["owner_name"],request.form["category"],request.form["postcode"],request.form["borough"],request.form["country"],lt,val,request.form["status"],request.form["description"],now()))
        conn.execute("INSERT INTO proof_of_contribution(member_name,contribution_type,proof_note,status,created_at) VALUES(?,?,?,?,?)", (request.form["business_name"],"Business Network",f"Listed as {lt}","Contribution Recorded",now()))
        if val: conn.execute("INSERT INTO value_created(source,amount,note,created_at) VALUES(?,?,?,?)", ("Business Network",val,f"{request.form['business_name']} listed as {lt}",now()))
        conn.commit(); conn.close()
        return redirect("/dashboard")
    return page("""<div class='card'><h2>🏪 Add Business</h2><form method='post'>
    <input name='business_name' placeholder='Business name' required><input name='owner_name' placeholder='Owner'><input name='category' placeholder='Category'><input name='postcode' placeholder='Postcode'><input name='borough' placeholder='Borough'><input name='country' placeholder='Country'>
    <select name='listing_type'><option>Free Listing</option><option>Featured Listing</option><option>Premium Listing</option></select>
    <select name='status'><option>Active</option><option>Pending</option></select><textarea name='description' placeholder='Description'></textarea><button>Record Business</button></form></div>""")

@app.route("/creator-hub")
def creator_hub():
    conn = db(); rows = conn.execute("SELECT * FROM creator_hub ORDER BY id DESC").fetchall(); conn.close()
    html = "<div class='card'><h2>🎨 Creator Hub</h2><p><a class='badge' href='/add-creator'>Add Creator</a></p></div>"
    for r in rows:
        html += f"<div class='card'><h3>{r['creator_name']}</h3><p><span class='badge'>{r['profile_type']}</span><span class='badge'>£{r['monthly_value']}/month</span></p><p>{r['bio']}</p></div>"
    return page(html)

@app.route("/add-creator", methods=["GET","POST"])
def add_creator():
    if request.method == "POST":
        pt = request.form["profile_type"]; val = CREATOR_PROFILES[pt]
        conn = db()
        conn.execute("""INSERT INTO creator_hub(creator_name,skill,postcode,borough,country,profile_type,monthly_value,status,bio,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)""", (request.form["creator_name"],request.form["skill"],request.form["postcode"],request.form["borough"],request.form["country"],pt,val,request.form["status"],request.form["bio"],now()))
        conn.execute("INSERT INTO proof_of_contribution(member_name,contribution_type,proof_note,status,created_at) VALUES(?,?,?,?,?)", (request.form["creator_name"],"Creator Hub",f"Listed as {pt}","Contribution Recorded",now()))
        if val: conn.execute("INSERT INTO value_created(source,amount,note,created_at) VALUES(?,?,?,?)", ("Creator Hub",val,f"{request.form['creator_name']} joined as {pt}",now()))
        conn.commit(); conn.close()
        return redirect("/dashboard")
    return page("""<div class='card'><h2>🎨 Add Creator</h2><form method='post'>
    <input name='creator_name' placeholder='Creator name' required><input name='skill' placeholder='Skill'><input name='postcode' placeholder='Postcode'><input name='borough' placeholder='Borough'><input name='country' placeholder='Country'>
    <select name='profile_type'><option>Free Creator Profile</option><option>Featured Creator</option><option>Promotion Slot</option></select>
    <select name='status'><option>Active</option><option>Pending</option></select><textarea name='bio' placeholder='Bio'></textarea><button>Record Creator</button></form></div>""")

@app.route("/proof")
def proof():
    conn = db(); rows = conn.execute("SELECT * FROM proof_of_contribution ORDER BY id DESC").fetchall(); conn.close()
    html = "<div class='card'><h2>🌱 Proof of Contribution</h2></div>"
    for r in rows:
        html += f"<div class='card'><h3>{r['member_name']}</h3><p><span class='badge'>{r['contribution_type']}</span><span class='badge'>{r['status']}</span></p><p>{r['proof_note']}</p></div>"
    return page(html)

@app.route("/value-created")
def value_created():
    conn = db(); rows = conn.execute("SELECT * FROM value_created ORDER BY id DESC").fetchall(); val = total_value(conn); conn.close()
    html = f"<div class='card'><h2>💚 Value Created</h2><div class='big'>£{val}</div></div>"
    for r in rows:
        html += f"<div class='card'><p><span class='badge'>{r['source']}</span> £{r['amount']} — {r['note']}</p></div>"
    return page(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
