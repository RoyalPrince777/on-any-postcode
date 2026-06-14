from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_business_network_secret"
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

LISTINGS = {
    "Free Listing": 0,
    "Featured Listing": 10,
    "Premium Listing": 25
}

BASE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Business Network</title>
<style>
body{margin:0;font-family:Arial;background:#07110b;color:#f5fff7}
header{padding:22px;background:#0d1f14;border-bottom:1px solid #1f4d2e}
nav a{color:#b8ffc8;margin-right:12px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:1120px;margin:auto}
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
.biz{background:#111f17;border-color:#3b8a4a}
</style>
</head>
<body>
<header>
<h1>🏪 OAP Business Network</h1>
<nav>
<a href="/">Home</a>
<a href="/business-network">Business Network</a>
<a href="/add-business">Add Business</a>
<a href="/proof">Proof</a>
<a href="/value-created">Value Created</a>
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
    <h2>🏪 Business Network</h2>
    <p>Step 5: First business signal. Local businesses join OAP through free, featured, or premium listings.</p>
    </div>

    <div class="grid">
      <div class="card"><h3>Free Listing</h3><p>£0/month</p></div>
      <div class="card"><h3>Featured Listing</h3><p>£10/month</p></div>
      <div class="card"><h3>Premium Listing</h3><p>£25/month</p></div>
    </div>
    """)

@app.route("/business-network")
def business_network():
    conn = db()
    rows = conn.execute("SELECT * FROM business_network ORDER BY id DESC").fetchall()
    conn.close()

    html = "<div class='card biz'><h2>🏪 Business Network</h2>"
    if not rows:
        html += "<p>No businesses listed yet.</p>"
    for r in rows:
        html += f"""
        <div class="card">
        <h3>{r['business_name']}</h3>
        <p><span class="badge">{r['listing_type']}</span> <span class="badge">£{r['monthly_value']}/month</span> <span class="badge">{r['status']}</span></p>
        <p><b>Owner:</b> {r['owner_name']}</p>
        <p><b>Category:</b> {r['category']}</p>
        <p>{r['postcode']} → {r['borough']} → {r['country']}</p>
        <p>{r['description']}</p>
        <p class="small">{r['created_at']}</p>
        </div>
        """
    html += "</div>"
    return page(html)

@app.route("/add-business", methods=["GET","POST"])
def add_business():
    if request.method == "POST":
        listing_type = request.form["listing_type"]
        monthly_value = LISTINGS.get(listing_type, 0)

        conn = db()
        conn.execute("""INSERT INTO business_network
        (business_name, owner_name, category, postcode, borough, country, listing_type, monthly_value, status, description, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
            request.form["business_name"],
            request.form["owner_name"],
            request.form["category"],
            request.form["postcode"],
            request.form["borough"],
            request.form["country"],
            listing_type,
            monthly_value,
            request.form["status"],
            request.form["description"],
            now()
        ))

        conn.execute("""INSERT INTO proof_of_contribution
        (member_name, contribution_type, proof_note, status, created_at)
        VALUES (?,?,?,?,?)""", (
            request.form["business_name"],
            "Business Network",
            f"Business listed as {listing_type}. {request.form['description']}",
            "Contribution Recorded",
            now()
        ))

        if monthly_value > 0:
            conn.execute("INSERT INTO value_created(source, amount, note, created_at) VALUES(?,?,?,?)", (
                "Business Network",
                monthly_value,
                f"{request.form['business_name']} joined as {listing_type}",
                now()
            ))

        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return page("""
    <div class="card biz">
    <h2>🏪 Add Business</h2>
    <form method="post">
    <input name="business_name" placeholder="Business name" required>
    <input name="owner_name" placeholder="Owner / contact name">
    <input name="category" placeholder="Category e.g. food, clothing, barber, music, delivery">
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
      <option>Paused</option>
    </select>
    <textarea name="description" placeholder="Business description / offer / proof note"></textarea>
    <button>Record Business</button>
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
        html += f"<p><span class='badge'>{r['source']}</span> £{r['amount']} — {r['note']} <span class='small'>{r['created_at']}</span></p>"
    html += "</div>"
    return page(html)

@app.route("/dashboard")
def dashboard():
    conn = db()
    businesses = count(conn, "business_network")
    proof = count(conn, "proof_of_contribution")
    value = total_value(conn)

    listing_rows = conn.execute("""
        SELECT listing_type, COUNT(*) as count, COALESCE(SUM(monthly_value),0) as total
        FROM business_network
        GROUP BY listing_type
    """).fetchall()

    conn.close()

    html = """
    <div class="card">
    <h2>👑 Sovereign Dashboard — Business Network</h2>
    <div class="grid">
    """
    html += f"<div class='card'><div class='big'>{businesses}</div><p>Businesses</p></div>"
    html += f"<div class='card'><div class='big'>{proof}</div><p>Proof of Contribution</p></div>"
    html += f"<div class='card'><div class='big'>£{value}</div><p>Value Created</p></div>"
    html += "</div></div>"

    html += "<div class='card'><h2>🚦 Mission Signals</h2>"
    html += "<p class='green'>✅ Explorer: built</p>"
    html += "<p class='green'>✅ Sovereign Dashboard: built</p>"
    html += "<p class='green'>✅ People’s Command: built</p>"
    html += "<p class='green'>✅ Postcode to Universe Circle: active</p>"
    html += "<p class='green'>✅ Business Network: active</p>"
    html += "<p class='red'>🔴 Creator Hub: next</p>"
    html += "</div>"

    html += "<div class='card'><h2>🏪 Listing Breakdown</h2>"
    if not listing_rows:
        html += "<p>No listing data yet.</p>"
    for l in listing_rows:
        html += f"<p><span class='badge'>{l['listing_type']}</span> {l['count']} business(es) — £{l['total']}/month</p>"
    html += "</div>"

    return page(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
