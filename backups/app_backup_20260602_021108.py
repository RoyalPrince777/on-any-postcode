from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS launch_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        action_type TEXT,
        assigned_to TEXT,
        status TEXT DEFAULT 'Open',
        proof_note TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS explorer_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        url TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def seed_explorer():
    conn = db()
    c = conn.cursor()

    count = c.execute("SELECT COUNT(*) FROM explorer_index").fetchone()[0]
    if count == 0:
        items = [
            ("News", "OAP News", "Community updates, culture, sport, local intelligence and launch signals.", "/"),
            ("Experience", "First OAP Experience", "Plan one meetup, watch party, gathering or community session.", "/launch-board"),
            ("Business", "Business Network", "Invite one barber, food shop, clothing seller or local service.", "/launch-board"),
            ("Creator", "Creator Hub", "Invite one artist, musician, designer, comedian or storyteller.", "/launch-board"),
            ("Award", "OAP Awards", "Community recognition for contribution, creativity, business and culture.", "/"),
            ("Community", "Postcode to Universe", "Postcode, borough, county, country, continent and global community journey.", "/"),
            ("Contribution", "Value Created", "Record first £5, £10 or £25 value signal and proof note.", "/launch-board"),
        ]

        for item in items:
            c.execute("""
                INSERT INTO explorer_index
                (item_type, title, description, url, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (*item, now()))

    conn.commit()
    conn.close()

def layout(title, body):
    return render_template_string("""
    <!doctype html>
    <html>
    <head>
        <title>{{ title }}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #07130d;
                color: #f4fff7;
            }
            header {
                padding: 18px;
                background: #0d2417;
                border-bottom: 1px solid #1f5c38;
            }
            h1, h2, h3 { margin: 0 0 12px; }
            .wrap { padding: 18px; max-width: 950px; margin: auto; }
            .card {
                background: #10261a;
                border: 1px solid #245c3b;
                border-radius: 18px;
                padding: 16px;
                margin: 14px 0;
                box-shadow: 0 0 18px rgba(0,0,0,0.25);
            }
            a {
                color: #6fffa8;
                text-decoration: none;
                font-weight: bold;
            }
            .nav a {
                display: inline-block;
                margin: 6px 8px 6px 0;
                padding: 10px 12px;
                background: #163923;
                border-radius: 12px;
            }
            input, select, textarea {
                width: 100%;
                padding: 13px;
                margin: 8px 0;
                border-radius: 12px;
                border: 1px solid #347a4d;
                background: #061009;
                color: #fff;
                box-sizing: border-box;
            }
            button {
                width: 100%;
                padding: 14px;
                border: 0;
                border-radius: 12px;
                background: #31d36b;
                color: #041007;
                font-weight: bold;
                font-size: 16px;
            }
            .tag {
                display: inline-block;
                padding: 5px 9px;
                border-radius: 999px;
                background: #244b32;
                color: #b8ffd0;
                font-size: 13px;
            }
            .signal { color: #8dffb0; font-weight: bold; }
        </style>
    </head>
    <body>
        <header>
            <h2>🌍 ON ANY POSTCODE</h2>
            <div class="nav">
                <a href="/">Home</a>
                <a href="/explorer">🧭 Explorer</a>
                <a href="/launch-board">🚦 Launch Board</a>
                <a href="/add-explorer">➕ Add Explorer Item</a>
            </div>
        </header>
        <div class="wrap">
            {{ body|safe }}
        </div>
    </body>
    </html>
    """, title=title, body=body)

@app.route("/")
def home():
    body = """
    <div class="card">
        <h1>👑 OAP World</h1>
        <p>Born Local. Built Global. Earth is our turf.</p>
        <p class="signal">Current Mission: first member, first business, first creator, first experience, first value created.</p>
    </div>
    <div class="card">
        <h2>Quick Launch</h2>
        <p><a href="/explorer">Open Explorer</a></p>
        <p><a href="/launch-board">Open Launch Board</a></p>
    </div>
    """
    return layout("OAP World", body)

@app.route("/explorer")
def explorer():
    q = request.args.get("q", "").strip()
    conn = db()
    c = conn.cursor()

    if q:
        like = f"%{q}%"
        rows = c.execute("""
            SELECT * FROM explorer_index
            WHERE title LIKE ?
            OR description LIKE ?
            OR item_type LIKE ?
            ORDER BY id DESC
        """, (like, like, like)).fetchall()
    else:
        rows = c.execute("SELECT * FROM explorer_index ORDER BY id DESC").fetchall()

    conn.close()

    results = ""
    for r in rows:
        results += f"""
        <div class="card">
            <span class="tag">{r['item_type']}</span>
            <h3>{r['title']}</h3>
            <p>{r['description'] or ''}</p>
            <p><a href="{r['url'] or '#'}">Open</a></p>
        </div>
        """

    if not results:
        results = "<div class='card'><p>No results yet. Add the first Explorer item.</p></div>"

    body = f"""
    <div class="card">
        <h1>🧭 Explorer</h1>
        <p>Search OAP World: News, Experiences, Creators, Businesses, Awards, Communities and Value Created.</p>
        <form method="GET" action="/explorer">
            <input name="q" placeholder="Search OAP World..." value="{q}">
            <button type="submit">Search</button>
        </form>
    </div>
    {results}
    """
    return layout("Explorer", body)

@app.route("/add-explorer", methods=["GET", "POST"])
def add_explorer():
    if request.method == "POST":
        item_type = request.form.get("item_type", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        url = request.form.get("url", "").strip() or "/explorer"

        if title and item_type:
            conn = db()
            c = conn.cursor()
            c.execute("""
                INSERT INTO explorer_index
                (item_type, title, description, url, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (item_type, title, description, url, now()))
            conn.commit()
            conn.close()

        return redirect(url_for("explorer"))

    body = """
    <div class="card">
        <h1>➕ Add Explorer Item</h1>
        <form method="POST">
            <label>Type</label>
            <select name="item_type">
                <option>News</option>
                <option>Experience</option>
                <option>Creator</option>
                <option>Business</option>
                <option>Award</option>
                <option>Community</option>
                <option>Contribution</option>
                <option>Product</option>
                <option>Postcode</option>
                <option>Country</option>
            </select>

            <label>Title</label>
            <input name="title" placeholder="Example: Mitcham Barber">

            <label>Description</label>
            <textarea name="description" placeholder="Short proof/value note"></textarea>

            <label>URL</label>
            <input name="url" placeholder="/launch-board">

            <button type="submit">Add to Explorer</button>
        </form>
    </div>
    """
    return layout("Add Explorer Item", body)

@app.route("/launch-board")
def launch_board():
    conn = db()
    rows = conn.execute("SELECT * FROM launch_actions ORDER BY id DESC").fetchall()
    conn.close()

    cards = ""
    for r in rows:
        cards += f"""
        <div class="card">
            <span class="tag">{r['action_type'] or 'Action'}</span>
            <h3>{r['title']}</h3>
            <p><b>Assigned:</b> {r['assigned_to'] or 'OAP'}</p>
            <p><b>Status:</b> {r['status'] or 'Open'}</p>
            <p><b>Proof Note:</b> {r['proof_note'] or ''}</p>
            <p><small>{r['created_at'] or ''}</small></p>
            <p><a href="/complete-action/{r['id']}">Mark Contribution Recorded</a></p>
        </div>
        """

    if not cards:
        cards = "<div class='card'><p>No launch actions yet. Run seed_launch.py.</p></div>"

    body = f"""
    <div class="card">
        <h1>🚦 Launch Board</h1>
        <p>Real action board for first business, first creator, first experience and first value created.</p>
    </div>
    {cards}
    """
    return layout("Launch Board", body)

@app.route("/complete-action/<int:action_id>")
def complete_action(action_id):
    conn = db()
    conn.execute("UPDATE launch_actions SET status=? WHERE id=?", ("Contribution Recorded", action_id))
    conn.commit()
    conn.close()
    return redirect(url_for("launch_board"))

if __name__ == "__main__":
    init_db()
    seed_explorer()
    app.run(host="0.0.0.0", port=5000)
