from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_explorer_secret"
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
<title>OAP World Explorer</title>
<style>
body{margin:0;font-family:Arial;background:#07110b;color:#f5fff7}
header{padding:22px;background:#0d1f14;border-bottom:1px solid #1f4d2e}
nav a{color:#b8ffc8;margin-right:12px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:1050px;margin:auto}
.card{background:#102417;border:1px solid #275b36;border-radius:18px;padding:18px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
input,textarea,select,button{width:100%;padding:13px;margin:7px 0;border-radius:12px;border:0}
button{background:#21c45a;color:#031006;font-weight:bold}
.badge{display:inline-block;background:#183b25;color:#b8ffc8;padding:7px 10px;border-radius:20px;margin:4px}
.small{opacity:.75;font-size:13px}
.gold{color:#ffd76b}
</style>
</head>
<body>
<header>
<h1>🌍 OAP World — Explorer v1</h1>
<nav>
<a href="/">Home</a>
<a href="/explorer">Explorer</a>
<a href="/add-news">Add News</a>
<a href="/add-event">Add Event</a>
<a href="/add-creator">Add Creator</a>
<a href="/add-business">Add Business</a>
<a href="/add-product">Add Product</a>
<a href="/dashboard">Dashboard</a>
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
    <h2>👑 OAP Operating Phase</h2>
    <p>Architecture is done. Now the mission is content, members, businesses, events, and revenue.</p>
    <p><b>Next order:</b> Explorer → Metrics → Bee Coordination → Founder Membership → Business Listings → Creator Promotion.</p>
    </div>

    <div class="grid">
      <div class="card"><h3>🔍 Explorer</h3><p>Search News, Events, Creators, Businesses, Products, Countries, Postcodes.</p></div>
      <div class="card"><h3>📰 News</h3><p>Community updates and useful local awareness.</p></div>
      <div class="card"><h3>🎪 Events</h3><p>Real events, watch parties, campaigns, meetups.</p></div>
      <div class="card"><h3>🏪 Businesses</h3><p>Local business discovery and future paid listings.</p></div>
      <div class="card"><h3>🎨 Creators</h3><p>Creator profiles and future promotion slots.</p></div>
      <div class="card"><h3>🛒 Products</h3><p>Market items and future revenue signals.</p></div>
    </div>
    """)

@app.route("/explorer", methods=["GET","POST"])
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

    html = """
    <div class="card">
    <h2>🔍 Explorer v1</h2>
    <form method="get">
      <input name="q" placeholder="Search news, events, creators, businesses, products, countries, postcodes..." value="{}">
      <button>Search OAP</button>
    </form>
    </div>
    """.format(q)

    if q:
        html += f"<div class='card'><h3>Results for: <span class='gold'>{q}</span></h3><p>{total} result(s)</p></div>"

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

@app.route("/dashboard")
def dashboard():
    conn = db()
    counts = {
        "News Posts": conn.execute("SELECT COUNT(*) FROM news").fetchone()[0],
        "Events": conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
        "Creators": conn.execute("SELECT COUNT(*) FROM creators").fetchone()[0],
        "Businesses": conn.execute("SELECT COUNT(*) FROM businesses").fetchone()[0],
        "Products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "Explorer Searches": conn.execute("SELECT COUNT(*) FROM explorer_logs").fetchone()[0],
    }
    conn.close()

    html = "<div class='card'><h2>👑 Sovereign Dashboard v1 Metrics</h2><div class='grid'>"
    for k,v in counts.items():
        html += f"<div class='card'><h3>{v}</h3><p>{k}</p></div>"
    html += "</div></div>"
    return page(html)

@app.route("/add-news", methods=["GET","POST"])
def add_news():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO news(title, body, category, postcode, country, created_at) VALUES(?,?,?,?,?,?)", (
            request.form["title"], request.form["body"], request.form["category"],
            request.form["postcode"], request.form["country"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/explorer")
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
            request.form["title"], request.form["description"], request.form["location"],
            request.form["postcode"], request.form["country"], request.form["event_date"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/explorer")
    return page("""
    <div class="card"><h2>🎪 Add Event</h2>
    <form method="post">
    <input name="title" placeholder="Event title" required>
    <textarea name="description" placeholder="Event description" required></textarea>
    <input name="location" placeholder="Location">
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <input name="event_date" placeholder="Event date">
    <button>Save Event</button>
    </form></div>
    """)

@app.route("/add-creator", methods=["GET","POST"])
def add_creator():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO creators(name, skill, postcode, country, bio, created_at) VALUES(?,?,?,?,?,?)", (
            request.form["name"], request.form["skill"], request.form["postcode"],
            request.form["country"], request.form["bio"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/explorer")
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

@app.route("/add-business", methods=["GET","POST"])
def add_business():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO businesses(name, category, postcode, country, description, created_at) VALUES(?,?,?,?,?,?)", (
            request.form["name"], request.form["category"], request.form["postcode"],
            request.form["country"], request.form["description"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/explorer")
    return page("""
    <div class="card"><h2>🏪 Add Business</h2>
    <form method="post">
    <input name="name" placeholder="Business name" required>
    <input name="category" placeholder="Category">
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <textarea name="description" placeholder="Business description"></textarea>
    <button>Save Business</button>
    </form></div>
    """)

@app.route("/add-product", methods=["GET","POST"])
def add_product():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO products(name, category, price, postcode, country, description, created_at) VALUES(?,?,?,?,?,?,?)", (
            request.form["name"], request.form["category"], request.form["price"],
            request.form["postcode"], request.form["country"], request.form["description"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/explorer")
    return page("""
    <div class="card"><h2>🛒 Add Product</h2>
    <form method="post">
    <input name="name" placeholder="Product name" required>
    <input name="category" placeholder="Category">
    <input name="price" placeholder="Price">
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <textarea name="description" placeholder="Product description"></textarea>
    <button>Save Product</button>
    </form></div>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
