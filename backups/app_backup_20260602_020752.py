from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_operating_core_v2"
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

    c.execute("""CREATE TABLE IF NOT EXISTS launch_actions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        action_type TEXT,
        assigned_to TEXT,
        status TEXT,
        proof_note TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS oap_experiences(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        experience_type TEXT,
        host_name TEXT,
        location TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        experience_date TEXT,
        status TEXT,
        ticket_value REAL,
        description TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS p2u_members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        postcode TEXT,
        borough TEXT,
        county_region TEXT,
        country TEXT,
        tier TEXT,
        monthly_value REAL,
        status TEXT,
        contribution_note TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS business_network(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT,
        owner_name TEXT,
        category TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        listing_type TEXT,
        monthly_value REAL,
        status TEXT,
        description TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS creator_hub(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_name TEXT,
        skill TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        profile_type TEXT,
        monthly_value REAL,
        status TEXT,
        bio TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS proof_of_contribution(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_name TEXT,
        contribution_type TEXT,
        proof_note TEXT,
        status TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS value_created(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        amount REAL,
        note TEXT,
        created_at TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

P2U_TIERS = {
    "Postcode Founder": 5,
    "Borough Builder": 10,
    "Country Champion": 25
}

BUSINESS_LISTINGS = {
    "Free Listing": 0,
    "Featured Listing": 10,
    "Premium Listing": 25
}

CREATOR_PROFILES = {
    "Free Creator Profile": 0,
    "Featured Creator": 10,
    "Promotion Slot": 25
}

BASE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Operating Core v2</title>
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
.launch{background:#1e1808;border-color:#f4c542}
</style>
</head>
<body>
<header>
<h1>👑 OAP Operating Core v2</h1>
<nav>
<a href="/">Home</a>
<a href="/launch-board">Launch Board</a>
<a href="/dashboard">Dashboard</a>
<a href="/join-circle">Circle</a>
<a href="/add-business">Business</a>
<a href="/add-creator">Creator</a>
<a href="/add-experience">Experience</a>
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
    <div class="card launch">
    <h2>🚦 OAP Launch Board v1</h2>
    <p><b>Mission:</b> first member, first business, first OAP Experience, first Value Created.</p>
    <p><b>Master line:</b> People’s Command creates OAP Experiences, records Proof of Contribution, and tracks Value Created.</p>
    </div>
    <div class="grid">
      <div class="card"><h3>👑 Circle</h3><p>Record first member.</p></div>
      <div class="card"><h3>🏪 Business</h3><p>Record first business.</p></div>
      <div class="card"><h3>🎨 Creator</h3><p>Record first creator.</p></div>
      <div class="card"><h3>🎪 Experience</h3><p>Record first live activity.</p></div>
      <div class="card"><h3>🌱 Proof</h3><p>Contribution recorded.</p></div>
      <div class="card"><h3>💚 Value</h3><p>Track Value Created.</p></div>
    </div>
    """)

@app.route("/launch-board")
def launch_board():
    conn = db()
    actions = conn.execute("SELECT * FROM launch_actions ORDER BY id DESC").fetchall()

    circle = qcount(conn, "p2u_members")
    business = qcount(conn, "business_network")
    creator = qcount(conn, "creator_hub")
    exp = qcount(conn, "oap_experiences")
    value = total_value(conn)
    conn.close()

    html = "<div class='card launch'><h2>🚦 Launch Board</h2>"
    html += "<p><a class='badge' href='/add-launch-action'>Add Launch Action</a></p>"
    html += "<div class='grid'>"
    html += signal_card("First Member", circle)
    html += signal_card("First Business", business)
    html += signal_card("First Creator", creator)
    html += signal_card("First OAP Experience", exp)
    html += signal_card("First Value Created", value)
    html += "</div></div>"

    html += "<div class='card'><h2>📌 Launch Actions</h2>"
    if not actions:
        html += "<p>No launch actions yet.</p>"
    for a in actions:
        html += f"""
        <div class="card">
        <h3>{a['title']}</h3>
        <p><span class="badge">{a['action_type']}</span> <span class="badge">{a['status']}</span></p>
        <p><b>Assigned:</b> {a['assigned_to']}</p>
        <p>{a['proof_note']}</p>
        <p class="small">{a['created_at']}</p>
        </div>
        """
    html += "</div>"
    return page(html)

def signal_card(label, value):
    if value:
        return f"<div class='card'><div class='big green'>✅</div><p>{label}</p></div>"
    return f"<div class='card'><div class='big red'>🔴</div><p>{label}</p></div>"

@app.route("/add-launch-action", methods=["GET","POST"])
def add_launch_action():
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO launch_actions
        (title, action_type, assigned_to, status, proof_note, created_at)
        VALUES (?,?,?,?,?,?)""", (
            request.form["title"],
            request.form["action_type"],
            request.form["assigned_to"],
            request.form["status"],
            request.form["proof_note"],
            now()
        ))
        conn.commit()
        conn.close()
        return redirect("/launch-board")

    return page("""
    <div class="card launch">
    <h2>🚦 Add Launch Action</h2>
    <form method="post">
    <input name="title" placeholder="Action title e.g. Ask first barber to join Business Network" required>
    <select name="action_type">
      <option>First Member</option>
      <option>First Business</option>
      <option>First Creator</option>
      <option>First OAP Experience</option>
      <option>First Value Created</option>
      <option>Content</option>
    </select>
    <input name="assigned_to" placeholder="Assigned to">
    <select name="status">
      <option>Open</option>
      <option>In Progress</option>
      <option>Done</option>
      <option>Blocked</option>
    </select>
    <textarea name="proof_note" placeholder="Proof / next step / result"></textarea>
    <button>Save Launch Action</button>
    </form>
    </div>
    """)

@app.route("/join-circle", methods=["GET","POST"])
def join_circle():
    if request.method == "POST":
        tier = request.form["tier"]
        val = P2U_TIERS[tier]
        conn = db()
        conn.execute("""INSERT INTO p2u_members
        (name, postcode, borough, county_region, country, tier, monthly_value, status, contribution_note, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            request.form["name"], request.form["postcode"], request.form["borough"],
            request.form["county_region"], request.form["country"], tier, val,
            request.form["status"], request.form["contribution_note"], now()
        ))
        conn.execute("INSERT INTO value_created(source,amount,note,created_at) VALUES(?,?,?,?)",
                     ("Postcode to Universe Circle", val, f"{request.form['name']} joined as {tier}", now()))
        conn.execute("INSERT INTO proof_of_contribution(member_name,contribution_type,proof_note,status,created_at) VALUES(?,?,?,?,?)",
                     (request.form["name"], "Postcode to Universe Circle", f"Joined as {tier}", "Contribution Recorded", now()))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return page("""
    <div class="card">
    <h2>👑 Join Postcode to Universe Circle</h2>
    <form method="post">
    <input name="name" placeholder="Name / username" required>
    <input name="postcode" placeholder="Postcode">
    <input name="borough" placeholder="Borough">
    <input name="county_region" placeholder="County / Region">
    <input name="country" placeholder="Country">
    <select name="tier">
      <option>Postcode Founder</option>
      <option>Borough Builder</option>
      <option>Country Champion</option>
    </select>
    <select name="status">
      <option>Active</option>
      <option>Pending</option>
    </select>
    <textarea name="contribution_note" placeholder="Contribution note"></textarea>
    <button>Record Circle Member</button>
    </form>
    </div>
    """)

@app.route("/add-business", methods=["GET","POST"])
def add_business():
    if request.method == "POST":
        lt = request.form["listing_type"]
        val = BUSINESS_LISTINGS[lt]
        conn = db()
        conn.execute("""INSERT INTO business_network
        (business_name,owner_name,category,postcode,borough,country,listing_type,monthly_value,status,description,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
            request.form["business_name"], request.form["owner_name"], request.form["category"],
            request.form["postcode"], request.form["borough"], request.form["country"],
            lt, val, request.form["status"], request.form["description"], now()
        ))
        conn.execute("INSERT INTO proof_of_contribution(member_name,contribution_type,proof_note,status,created_at) VALUES(?,?,?,?,?)",
                     (request.form["business_name"], "Business Network", f"Listed as {lt}", "Contribution Recorded", now()))
        if val:
            conn.execute("INSERT INTO value_created(source,amount,note,created_at) VALUES(?,?,?,?)",
                         ("Business Network", val, f"{request.form['business_name']} listed as {lt}", now()))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return page("""
    <div class="card">
    <h2>🏪 Add Business</h2>
    <form method="post">
    <input name="business_name" placeholder="Business name" required>
    <input name="owner_name" placeholder="Owner">
    <input name="category" placeholder="Category">
    <input name="postcode" placeholder="Postcode">
    <input name="borough" placeholder="Borough">
    <input name="country" placeholder="Country">
    <select name="listing_type">
      <option>Free Listing</option>
      <option>Featured Listing</option>
      <option>Premium Listing</option>
    </select>
    <select name="status">
      <option>Active</option>
      <option>Pending</option>
    </select>
    <textarea name="description" placeholder="Description"></textarea>
    <button>Record Business</button>
    </form>
    </div>
    """)

@app.route("/add-creator", methods=["GET","POST"])
def add_creator():
    if request.method == "POST":
        pt = request.form["profile_type"]
        val = CREATOR_PROFILES[pt]
        conn = db()
        conn.execute("""INSERT INTO creator_hub
        (creator_name,skill,postcode,borough,country,profile_type,monthly_value,status,bio,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            request.form["creator_name"], request.form["skill"], request.form["postcode"],
            request.form["borough"], request.form["country"], pt, val,
            request.form["status"], request.form["bio"], now()
        ))
        conn.execute("INSERT INTO proof_of_contribution(member_name,contribution_type,proof_note,status,created_at) VALUES(?,?,?,?,?)",
                     (request.form["creator_name"], "Creator Hub", f"Listed as {pt}", "Contribution Recorded", now()))
        if val:
            conn.execute("INSERT INTO value_created(source,amount,note,created_at) VALUES(?,?,?,?)",
                         ("Creator Hub", val, f"{request.form['creator_name']} joined as {pt}", now()))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return page("""
    <div class="card">
    <h2>🎨 Add Creator</h2>
    <form method="post">
    <input name="creator_name" placeholder="Creator name" required>
    <input name="skill" placeholder="Skill">
    <input name="postcode" placeholder="Postcode">
    <input name="borough" placeholder="Borough">
    <input name="country" placeholder="Country">
    <select name="profile_type">
      <option>Free Creator Profile</option>
      <option>Featured Creator</option>
      <option>Promotion Slot</option>
    </select>
    <select name="status">
      <option>Active</option>
      <option>Pending</option>
    </select>
    <textarea name="bio" placeholder="Bio"></textarea>
    <button>Record Creator</button>
    </form>
    </div>
    """)

@app.route("/add-experience", methods=["GET","POST"])
def add_experience():
    if request.method == "POST":
        val = float(request.form["ticket_value"] or 0)
        conn = db()
        conn.execute("""INSERT INTO oap_experiences
        (title,experience_type,host_name,location,postcode,borough,country,experience_date,status,ticket_value,description,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            request.form["title"], request.form["experience_type"], request.form["host_name"],
            request.form["location"], request.form["postcode"], request.form["borough"],
            request.form["country"], request.form["experience_date"], request.form["status"],
            val, request.form["description"], now()
        ))
        conn.execute("INSERT INTO proof_of_contribution(member_name,contribution_type,proof_note,status,created_at) VALUES(?,?,?,?,?)",
                     (request.form["host_name"], "OAP Experience", f"Created experience: {request.form['title']}", "Contribution Recorded", now()))
        if val:
            conn.execute("INSERT INTO value_created(source,amount,note,created_at) VALUES(?,?,?,?)",
                         ("OAP Experience", val, f"{request.form['title']} value recorded", now()))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return page("""
    <div class="card">
    <h2>🎪 Add OAP Experience</h2>
    <form method="post">
    <input name="title" placeholder="Experience title" required>
    <select name="experience_type">
      <option>Watch Party</option>
      <option>Music Night</option>
      <option>Comedy Night</option>
      <option>Business Showcase</option>
      <option>Creator Meetup</option>
      <option>Learning Session</option>
      <option>Community Day</option>
    </select>
    <input name="host_name" placeholder="Host / organiser">
    <input name="location" placeholder="Location">
    <input name="postcode" placeholder="Postcode">
    <input name="borough" placeholder="Borough">
    <input name="country" placeholder="Country">
    <input name="experience_date" placeholder="Date / time">
    <select name="status">
      <option>Planned</option>
      <option>Open</option>
      <option>Completed</option>
    </select>
    <input name="ticket_value" placeholder="Value e.g. 5.00">
    <textarea name="description" placeholder="Description"></textarea>
    <button>Record OAP Experience</button>
    </form>
    </div>
    """)

@app.route("/dashboard")
def dashboard():
    conn = db()
    circle = qcount(conn, "p2u_members")
    business = qcount(conn, "business_network")
    creator = qcount(conn, "creator_hub")
    exp = qcount(conn, "oap_experiences")
    proof = qcount(conn, "proof_of_contribution")
    actions = qcount(conn, "launch_actions")
    value = total_value(conn)
    conn.close()

    html = "<div class='card'><h2>👑 Sovereign Dashboard</h2><div class='grid'>"
    html += f"<div class='card'><div class='big'>{circle}</div><p>Circle Members</p></div>"
    html += f"<div class='card'><div class='big'>{business}</div><p>Businesses</p></div>"
    html += f"<div class='card'><div class='big'>{creator}</div><p>Creators</p></div>"
    html += f"<div class='card'><div class='big'>{exp}</div><p>OAP Experiences</p></div>"
    html += f"<div class='card'><div class='big'>{proof}</div><p>Proof Records</p></div>"
    html += f"<div class='card'><div class='big'>{actions}</div><p>Launch Actions</p></div>"
    html += f"<div class='card'><div class='big'>£{value}</div><p>Value Created</p></div>"
    html += "</div></div>"
    return page(html)

@app.route("/proof")
def proof():
    conn = db()
    rows = conn.execute("SELECT * FROM proof_of_contribution ORDER BY id DESC").fetchall()
    conn.close()
    html = "<div class='card'><h2>🌱 Proof of Contribution</h2></div>"
    for r in rows:
        html += f"<div class='card'><h3>{r['member_name']}</h3><p><span class='badge'>{r['contribution_type']}</span> <span class='badge'>{r['status']}</span></p><p>{r['proof_note']}</p></div>"
    return page(html)

@app.route("/value-created")
def value_created():
    conn = db()
    rows = conn.execute("SELECT * FROM value_created ORDER BY id DESC").fetchall()
    val = total_value(conn)
    conn.close()
    html = f"<div class='card'><h2>💚 Value Created</h2><div class='big'>£{val}</div></div>"
    for r in rows:
        html += f"<div class='card'><p><span class='badge'>{r['source']}</span> £{r['amount']} — {r['note']}</p></div>"
    return page(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
