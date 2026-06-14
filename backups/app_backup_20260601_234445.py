from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_dashboard_v2_secret"
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

    c.execute("""CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        postcode TEXT,
        country TEXT,
        membership_type TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS news(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT,
        category TEXT,
        postcode TEXT,
        country TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        location TEXT,
        postcode TEXT,
        country TEXT,
        event_date TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS creators(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        skill TEXT,
        postcode TEXT,
        country TEXT,
        bio TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS businesses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        postcode TEXT,
        country TEXT,
        description TEXT,
        listing_type TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        price TEXT,
        postcode TEXT,
        country TEXT,
        description TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS awards(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        recipient TEXT,
        category TEXT,
        status TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS trust_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_type TEXT,
        subject TEXT,
        proof_note TEXT,
        status TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS revenue(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        amount REAL,
        note TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS explorer_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        results_count INTEGER,
        created_at TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

BASE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Sovereign Dashboard v2</title>
<style>
body{margin:0;font-family:Arial;background:#07110b;color:#f5fff7}
header{padding:22px;background:#0d1f14;border-bottom:1px solid #1f4d2e}
nav a{color:#b8ffc8;margin-right:12px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:1100px;margin:auto}
.card{background:#102417;border:1px solid #275b36;border-radius:18px;padding:18px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
input,textarea,select,button{width:100%;padding:13px;margin:7px 0;border-radius:12px;border:0}
button{background:#21c45a;color:#031006;font-weight:bold}
.badge{display:inline-block;background:#183b25;color:#b8ffc8;padding:7px 10px;border-radius:20px;margin:4px}
.gold{color:#ffd76b}
.red{color:#ff8d8d}
.green{color:#9dffb3}
.small{opacity:.75;font-size:13px}
.big{font-size:34px;font-weight:bold;color:#ffd76b}
</style>
</head>
<body>
<header>
<h1>👑 OAP World — Operating Dashboard</h1>
<nav>
<a href="/">Home</a>
<a href="/explorer">Explorer</a>
<a href="/dashboard">Dashboard</a>
<a href="/add-member">Add Member</a>
<a href="/add-news">Add News</a>
<a href="/add-event">Add Event</a>
<a href="/add-business">Add Business</a>
<a href="/add-creator">Add Creator</a>
<a href="/add-revenue">Add Revenue</a>
</nav>
</header>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def page(content):
    return render_template_string(BASE, content=content)

def count_table(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

def sum_revenue(conn):
    value = conn.execute("SELECT COALESCE(SUM(amount),0) FROM revenue").fetchone()[0]
    return round(value, 2)

@app.route("/")
def home():
    return page("""
    <div class="card">
    <h2>👑 OAP Operating Phase</h2>
    <p><b>Mission:</b> first member, first business, first event, first revenue.</p>
    <p><b>Build order:</b> Explorer → Dashboard Metrics → Bee Coordination → Founder Membership → Business Listings → Creator Promotion.</p>
    </div>
    <div class="grid">
      <div class="card"><h3>🔍 Explorer</h3><p>Search everything.</p></div>
      <div class="card"><h3>📊 Metrics</h3><p>Track live OAP numbers.</p></div>
      <div class="card"><h3>🐝 Bee Coordination</h3><p>Next: tasks, missions, volunteers.</p></div>
      <div class="card"><h3>💰 Revenue</h3><p>Record real money signals.</p></div>
    </div>
    """)

@app.route("/dashboard")
def dashboard():
    conn = db()

    metrics = {
        "Members": count_table(conn, "members"),
        "News Posts": count_table(conn, "news"),
        "Events": count_table(conn, "events"),
        "Businesses": count_table(conn, "businesses"),
        "Creators": count_table(conn, "creators"),
        "Products": count_table(conn, "products"),
        "Awards": count_table(conn, "awards"),
        "Trust Records": count_table(conn, "trust_records"),
        "Explorer Searches": count_table(conn, "explorer_logs"),
    }

    revenue_total = sum_revenue(conn)

    latest_revenue = conn.execute("SELECT * FROM revenue ORDER BY id DESC LIMIT 5").fetchall()
    latest_searches = conn.execute("SELECT * FROM explorer_logs ORDER BY id DESC LIMIT 5").fetchall()

    conn.close()

    html = "<div class='card'><h2>👑 Sovereign Dashboard v2</h2><p>Live operating numbers for OAP.</p><div class='grid'>"

    for k, v in metrics.items():
        html += f"<div class='card'><div class='big'>{v}</div><p>{k}</p></div>"

    html += f"<div class='card'><div class='big'>£{revenue_total}</div><p>Total Revenue Recorded</p></div>"
    html += "</div></div>"

    html += "<div class='card'><h2>🚦 Mission Signals</h2>"
    html += signal_line("First Member", metrics["Members"] > 0)
    html += signal_line("First Business", metrics["Businesses"] > 0)
    html += signal_line("First Event", metrics["Events"] > 0)
    html += signal_line("First Revenue", revenue_total > 0)
    html += "</div>"

    html += "<div class='card'><h2>💰 Latest Revenue</h2>"
    if not latest_revenue:
        html += "<p>No revenue recorded yet.</p>"
    for r in latest_revenue:
        html += f"<p><span class='badge'>{r['source']}</span> £{r['amount']} — {r['note']} <span class='small'>{r['created_at']}</span></p>"
    html += "</div>"

    html += "<div class='card'><h2>🔍 Latest Searches</h2>"
    if not latest_searches:
        html += "<p>No searches yet.</p>"
    for s in latest_searches:
        html += f"<p><span class='badge'>{s['query']}</span> {s['results_count']} result(s) <span class='small'>{s['created_at']}</span></p>"
    html += "</div>"

    return page(html)

def signal_line(label, good):
    if good:
        return f"<p class='green'>✅ {label}: active</p>"
    return f"<p class='red'>🔴 {label}: missing</p>"

@app.route("/explorer")
def explorer():
    q = request.args.get("q","").strip()
    results = []
    total = 0

    if q:
        like = f"%{q}%"
        conn = db()
        searches = [
            ("News", "news", "title", "body"),
            ("Events", "events", "title", "description"),
            ("Creators", "creators", "name", "bio"),
            ("Businesses", "businesses", "name", "description"),
            ("Products", "products", "name", "description"),
        ]

        for label, table, title_col, body_col in searches:
            rows = conn.execute(f"""
                SELECT *, '{label}' as result_type FROM {table}
                WHERE {title_col} LIKE ?
                OR {body_col} LIKE ?
                OR postcode LIKE ?
                OR country LIKE ?
                ORDER BY id DESC
            """, (like, like, like, like)).fetchall()
            for r in rows:
                results.append(r)

        total = len(results)
        conn.execute("INSERT INTO explorer_logs(query, results_count, created_at) VALUES(?,?,?)", (q, total, now()))
        conn.commit()
        conn.close()

    html = f"""
    <div class="card">
    <h2>🔍 Explorer v1</h2>
    <form method="get">
      <input name="q" placeholder="Search news, events, creators, businesses, products, countries, postcodes..." value="{q}">
      <button>Search OAP</button>
    </form>
    </div>
    """

    if q:
        html += f"<div class='card'><h3>Results for <span class='gold'>{q}</span></h3><p>{total} result(s)</p></div>"
        if not results:
            html += "<div class='card'><p>No results yet. Add content first.</p></div>"

        for r in results:
            result_type = r["result_type"]
            title = r["title"] if "title" in r.keys() else r["name"]
            body = ""
            if "body" in r.keys(): body = r["body"]
            if "description" in r.keys(): body = r["description"]
            if "bio" in r.keys(): body = r["bio"]
            html += f"""
            <div class="card">
              <span class="badge">{result_type}</span>
              <h3>{title}</h3>
              <p>{body}</p>
              <p class="small">Postcode: {r['postcode']} | Country: {r['country']}</p>
            </div>
            """
    return page(html)

@app.route("/add-member", methods=["GET","POST"])
def add_member():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO members(name, postcode, country, membership_type, created_at) VALUES(?,?,?,?,?)", (
            request.form["name"], request.form["postcode"], request.form["country"], request.form["membership_type"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return page("""
    <div class="card"><h2>👤 Add Member</h2>
    <form method="post">
    <input name="name" placeholder="Member name / username" required>
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <select name="membership_type">
      <option>Free</option>
      <option>Founder</option>
      <option>Founder+</option>
      <option>Patron</option>
    </select>
    <button>Save Member</button>
    </form></div>
    """)

@app.route("/add-revenue", methods=["GET","POST"])
def add_revenue():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO revenue(source, amount, note, created_at) VALUES(?,?,?,?)", (
            request.form["source"], float(request.form["amount"] or 0), request.form["note"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return page("""
    <div class="card"><h2>💰 Add Revenue</h2>
    <form method="post">
    <select name="source">
      <option>Founder Membership</option>
      <option>Business Listing</option>
      <option>Creator Promotion</option>
      <option>Event</option>
      <option>Product</option>
      <option>Other</option>
    </select>
    <input name="amount" placeholder="Amount e.g. 5.00" required>
    <textarea name="note" placeholder="Revenue note"></textarea>
    <button>Save Revenue</button>
    </form></div>
    """)

@app.route("/add-news", methods=["GET","POST"])
def add_news():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO news(title, body, category, postcode, country, created_at) VALUES(?,?,?,?,?,?)", (
            request.form["title"], request.form["body"], request.form["category"], request.form["postcode"], request.form["country"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return page("""
    <div class="card"><h2>📰 Add News</h2>
    <form method="post">
    <input name="title" placeholder="News title" required>
    <textarea name="body" placeholder="News body" required></textarea>
    <input name="category" placeholder="Category">
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <button>Save News</button>
    </form></div>
    """)

@app.route("/add-event", methods=["GET","POST"])
def add_event():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO events(title, description, location, postcode, country, event_date, created_at) VALUES(?,?,?,?,?,?,?)", (
            request.form["title"], request.form["description"], request.form["location"], request.form["postcode"],
            request.form["country"], request.form["event_date"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return page("""
    <div class="card"><h2>🎪 Add Event</h2>
    <form method="post">
    <input name="title" placeholder="Event title" required>
    <textarea name="description" placeholder="Event description"></textarea>
    <input name="location" placeholder="Location">
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <input name="event_date" placeholder="Event date">
    <button>Save Event</button>
    </form></div>
    """)

@app.route("/add-business", methods=["GET","POST"])
def add_business():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO businesses(name, category, postcode, country, description, listing_type, created_at) VALUES(?,?,?,?,?,?,?)", (
            request.form["name"], request.form["category"], request.form["postcode"], request.form["country"],
            request.form["description"], request.form["listing_type"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return page("""
    <div class="card"><h2>🏪 Add Business</h2>
    <form method="post">
    <input name="name" placeholder="Business name" required>
    <input name="category" placeholder="Category">
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <select name="listing_type">
      <option>Free Listing</option>
      <option>Featured Listing</option>
      <option>Premium Listing</option>
    </select>
    <textarea name="description" placeholder="Business description"></textarea>
    <button>Save Business</button>
    </form></div>
    """)

@app.route("/add-creator", methods=["GET","POST"])
def add_creator():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO creators(name, skill, postcode, country, bio, created_at) VALUES(?,?,?,?,?,?)", (
            request.form["name"], request.form["skill"], request.form["postcode"], request.form["country"], request.form["bio"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return page("""
    <div class="card"><h2>🎨 Add Creator</h2>
    <form method="post">
    <input name="name" placeholder="Creator name" required>
    <input name="skill" placeholder="Skill / category">
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <textarea name="bio" placeholder="Creator bio"></textarea>
    <button>Save Creator</button>
    </form></div>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
