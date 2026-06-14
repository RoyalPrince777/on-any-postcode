from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_p2u_secret"
DB = "oap_world.db"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    c = conn.cursor()

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

    c.execute("""CREATE TABLE IF NOT EXISTS value_created(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        amount REAL,
        note TEXT,
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

    c.execute("""CREATE TABLE IF NOT EXISTS people_command(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        mission_type TEXT,
        assigned_to TEXT,
        status TEXT,
        created_at TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

TIERS = {
    "Postcode Founder": 5,
    "Borough Builder": 10,
    "Country Champion": 25
}

BASE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Postcode to Universe Circle</title>
<style>
body{margin:0;font-family:Arial;background:#07110b;color:#f5fff7}
header{padding:22px;background:#0d1f14;border-bottom:1px solid #1f4d2e}
nav a{color:#b8ffc8;margin-right:12px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:1100px;margin:auto}
.card{background:#102417;border:1px solid #275b36;border-radius:18px;padding:18px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
input,textarea,select,button{width:100%;padding:13px;margin:7px 0;border-radius:12px;border:0}
button{background:#21c45a;color:#031006;font-weight:bold}
.badge{display:inline-block;background:#183b25;color:#b8ffc8;padding:7px 10px;border-radius:20px;margin:4px}
.big{font-size:34px;font-weight:bold;color:#ffd76b}
.gold{color:#ffd76b}
.green{color:#9dffb3}
.red{color:#ff8d8d}
.small{opacity:.75;font-size:13px}
</style>
</head>
<body>
<header>
<h1>👑 Postcode to Universe Circle</h1>
<nav>
<a href="/">Home</a>
<a href="/circle">Circle</a>
<a href="/join-circle">Join Circle</a>
<a href="/proof">Proof of Contribution</a>
<a href="/add-proof">Add Proof</a>
<a href="/value-created">Value Created</a>
<a href="/add-value">Add Value</a>
<a href="/dashboard">Dashboard</a>
</nav>
</header>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def page(content):
    return render_template_string(BASE, content=content)

def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

def total_value(conn):
    return round(conn.execute("SELECT COALESCE(SUM(amount),0) FROM value_created").fetchone()[0], 2)

@app.route("/")
def home():
    return page("""
    <div class="card">
    <h2>🌍 From Postcode to Universe</h2>
    <p>This is not “support”. This is belonging, identity, status, contribution, and journey.</p>
    <p><b>Path:</b> Postcode → Borough → County/Region → Country → Continent → Global → Planet → Universe.</p>
    </div>
    <div class="grid">
      <div class="card"><h3>🏠 Postcode Founder</h3><p>£5/month</p></div>
      <div class="card"><h3>🏙 Borough Builder</h3><p>£10/month</p></div>
      <div class="card"><h3>🇬🇧 Country Champion</h3><p>£25/month</p></div>
    </div>
    """)

@app.route("/circle")
def circle():
    conn = db()
    rows = conn.execute("SELECT * FROM p2u_members ORDER BY id DESC").fetchall()
    conn.close()

    html = "<div class='card'><h2>👑 Circle Members</h2>"
    if not rows:
        html += "<p>No Circle members yet.</p>"
    for r in rows:
        html += f"""
        <div class="card">
        <h3>{r['name']}</h3>
        <p><span class="badge">{r['tier']}</span> <span class="badge">£{r['monthly_value']}/month</span> <span class="badge">{r['status']}</span></p>
        <p>{r['postcode']} → {r['borough']} → {r['county_region']} → {r['country']}</p>
        <p>{r['contribution_note']}</p>
        <p class="small">{r['created_at']}</p>
        </div>
        """
    html += "</div>"
    return page(html)

@app.route("/join-circle", methods=["GET","POST"])
def join_circle():
    if request.method == "POST":
        tier = request.form["tier"]
        monthly_value = TIERS.get(tier, 0)
        conn = db()
        conn.execute("""INSERT INTO p2u_members
        (name, postcode, borough, county_region, country, tier, monthly_value, status, contribution_note, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            request.form["name"],
            request.form["postcode"],
            request.form["borough"],
            request.form["county_region"],
            request.form["country"],
            tier,
            monthly_value,
            request.form["status"],
            request.form["contribution_note"],
            now()
        ))

        conn.execute("INSERT INTO value_created(source, amount, note, created_at) VALUES(?,?,?,?)", (
            "Postcode to Universe Circle",
            monthly_value,
            f"{request.form['name']} joined as {tier}",
            now()
        ))

        conn.execute("""INSERT INTO proof_of_contribution
        (member_name, contribution_type, proof_note, status, created_at)
        VALUES (?,?,?,?,?)""", (
            request.form["name"],
            "Circle Membership",
            f"Joined as {tier}. {request.form['contribution_note']}",
            "Contribution Recorded",
            now()
        ))

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
      <option>Paused</option>
    </select>
    <textarea name="contribution_note" placeholder="Contribution note / why they joined"></textarea>
    <button>Record Circle Member</button>
    </form>
    </div>
    """)

@app.route("/proof")
def proof():
    conn = db()
    rows = conn.execute("SELECT * FROM proof_of_contribution ORDER BY id DESC").fetchall()
    conn.close()

    html = "<div class='card'><h2>🌱 Proof of Contribution</h2>"
    if not rows:
        html += "<p>No contribution records yet.</p>"
    for r in rows:
        html += f"""
        <div class="card">
        <h3>{r['member_name']}</h3>
        <p><span class="badge">{r['contribution_type']}</span> <span class="badge">{r['status']}</span></p>
        <p>{r['proof_note']}</p>
        <p class="small">{r['created_at']}</p>
        </div>
        """
    html += "</div>"
    return page(html)

@app.route("/add-proof", methods=["GET","POST"])
def add_proof():
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO proof_of_contribution
        (member_name, contribution_type, proof_note, status, created_at)
        VALUES (?,?,?,?,?)""", (
            request.form["member_name"],
            request.form["contribution_type"],
            request.form["proof_note"],
            request.form["status"],
            now()
        ))
        conn.commit()
        conn.close()
        return redirect("/proof")

    return page("""
    <div class="card">
    <h2>🌱 Add Proof of Contribution</h2>
    <form method="post">
    <input name="member_name" placeholder="Member / person / business name" required>
    <select name="contribution_type">
      <option>Circle Membership</option>
      <option>People’s Command Mission</option>
      <option>OAP Experience</option>
      <option>Business Network</option>
      <option>Creator Hub</option>
      <option>Community Help</option>
    </select>
    <textarea name="proof_note" placeholder="What contribution was made?"></textarea>
    <select name="status">
      <option>Contribution Recorded</option>
      <option>Needs Review</option>
      <option>Verified</option>
    </select>
    <button>Save Proof</button>
    </form>
    </div>
    """)

@app.route("/value-created")
def value_created():
    conn = db()
    rows = conn.execute("SELECT * FROM value_created ORDER BY id DESC").fetchall()
    total = total_value(conn)
    conn.close()

    html = f"<div class='card'><h2>💚 Value Created</h2><div class='big'>£{total}</div><p>Total Value Created recorded.</p></div>"
    html += "<div class='card'>"
    if not rows:
        html += "<p>No value records yet.</p>"
    for r in rows:
        html += f"""
        <p><span class="badge">{r['source']}</span> £{r['amount']} — {r['note']} <span class="small">{r['created_at']}</span></p>
        """
    html += "</div>"
    return page(html)

@app.route("/add-value", methods=["GET","POST"])
def add_value():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO value_created(source, amount, note, created_at) VALUES(?,?,?,?)", (
            request.form["source"],
            float(request.form["amount"] or 0),
            request.form["note"],
            now()
        ))
        conn.commit()
        conn.close()
        return redirect("/value-created")

    return page("""
    <div class="card">
    <h2>💚 Add Value Created</h2>
    <form method="post">
    <select name="source">
      <option>Postcode to Universe Circle</option>
      <option>Business Network</option>
      <option>Creator Hub</option>
      <option>OAP Experience</option>
      <option>Product</option>
      <option>Other</option>
    </select>
    <input name="amount" placeholder="Amount e.g. 5.00" required>
    <textarea name="note" placeholder="Value note"></textarea>
    <button>Record Value Created</button>
    </form>
    </div>
    """)

@app.route("/dashboard")
def dashboard():
    conn = db()
    members = count(conn, "p2u_members")
    proof = count(conn, "proof_of_contribution")
    value = total_value(conn)

    tier_rows = conn.execute("""
        SELECT tier, COUNT(*) as count, COALESCE(SUM(monthly_value),0) as total
        FROM p2u_members
        GROUP BY tier
    """).fetchall()
    conn.close()

    html = """
    <div class="card">
    <h2>👑 Sovereign Dashboard — Circle Metrics</h2>
    <div class="grid">
    """
    html += f"<div class='card'><div class='big'>{members}</div><p>Circle Members</p></div>"
    html += f"<div class='card'><div class='big'>{proof}</div><p>Proof of Contribution</p></div>"
    html += f"<div class='card'><div class='big'>£{value}</div><p>Value Created</p></div>"
    html += "</div></div>"

    html += "<div class='card'><h2>🚦 Mission Signals</h2>"
    html += "<p class='green'>✅ Explorer: built</p>"
    html += "<p class='green'>✅ Sovereign Dashboard: built</p>"
    html += "<p class='green'>✅ People’s Command: built</p>"
    html += "<p class='green'>✅ Postcode to Universe Circle: active</p>"
    html += "<p class='red'>🔴 Business Network: next</p>"
    html += "<p class='red'>🔴 Creator Hub: after</p>"
    html += "</div>"

    html += "<div class='card'><h2>👑 Tier Breakdown</h2>"
    if not tier_rows:
        html += "<p>No tier data yet.</p>"
    for t in tier_rows:
        html += f"<p><span class='badge'>{t['tier']}</span> {t['count']} member(s) — £{t['total']}/month</p>"
    html += "</div>"

    return page(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
