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
    CREATE TABLE IF NOT EXISTS oap_circle_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        continent TEXT,
        tier TEXT DEFAULT 'Community Member',
        proof_note TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS founder_wall (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_name TEXT NOT NULL,
        tier TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS value_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        value_type TEXT,
        amount TEXT,
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

def add_explorer(item_type, title, description, url):
    conn = db()
    conn.execute("""
        INSERT INTO explorer_index
        (item_type, title, description, url, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (item_type, title, description, url, now()))
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
            body { margin:0; font-family:Arial,sans-serif; background:#07130d; color:#f4fff7; }
            header { padding:18px; background:#0d2417; border-bottom:1px solid #1f5c38; }
            .wrap { padding:18px; max-width:1050px; margin:auto; }
            a { color:#6fffa8; text-decoration:none; font-weight:bold; }
            .nav a { display:inline-block; margin:6px 8px 6px 0; padding:10px 12px; background:#163923; border-radius:12px; }
            .card { background:#10261a; border:1px solid #245c3b; border-radius:18px; padding:16px; margin:14px 0; }
            .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; }
            input, select, textarea { width:100%; padding:13px; margin:8px 0; border-radius:12px; border:1px solid #347a4d; background:#061009; color:white; box-sizing:border-box; }
            button { width:100%; padding:14px; border:0; border-radius:12px; background:#31d36b; color:#041007; font-weight:bold; font-size:16px; }
            .tag { display:inline-block; padding:5px 9px; border-radius:999px; background:#244b32; color:#b8ffd0; font-size:13px; }
            .price { font-size:32px; color:#8dffb0; font-weight:bold; }
            .signal { color:#8dffb0; font-weight:bold; }
        </style>
    </head>
    <body>
        <header>
            <h2>🌍 ON ANY POSTCODE</h2>
            <div class="nav">
                <a href="/">Home</a>
                <a href="/oap-circle">👑 OAP Circle</a>
                <a href="/join-circle">🌍 Join Circle</a>
                <a href="/founder-wall">👑 Founder Wall</a>
                <a href="/explorer">🧭 Explorer</a>
            </div>
        </header>
        <div class="wrap">{{ body|safe }}</div>
    </body>
    </html>
    """, title=title, body=body)

@app.route("/")
def home():
    body = """
    <div class="card">
        <h1>👑 OAP World</h1>
        <p>Born Local. Built Global. Earth is our turf.</p>
        <p class="signal">Next launch layer: OAP Circle — belonging, contribution, recognition.</p>
    </div>
    <div class="card">
        <p><a href="/oap-circle">👑 Open OAP Circle</a></p>
        <p><a href="/join-circle">🌍 Join Circle</a></p>
        <p><a href="/founder-wall">👑 Founder Wall</a></p>
    </div>
    """
    return layout("OAP World", body)

@app.route("/oap-circle")
def oap_circle():
    conn = db()
    members = conn.execute("SELECT * FROM oap_circle_members ORDER BY id DESC").fetchall()
    conn.close()

    member_html = ""
    for m in members:
        member_html += f"""
        <div class="card">
            <span class="tag">{m['tier']}</span>
            <h3>{m['name']}</h3>
            <p>@{m['username'] or 'no-username'}</p>
            <p>{m['postcode'] or ''} {m['borough'] or ''} {m['country'] or ''} {m['continent'] or ''}</p>
            <p>{m['proof_note'] or ''}</p>
        </div>
        """

    if not member_html:
        member_html = "<div class='card'><p>No Circle members yet. Add the first Community Member.</p></div>"

    body = f"""
    <div class="card">
        <h1>👑 OAP Circle</h1>
        <p>Community → Contribution → Trust → Recognition → Value.</p>
        <p><a href="/join-circle">🌍 Join OAP Circle</a></p>
    </div>

    <div class="grid">
        <div class="card">
            <h2>🆓 Community Member</h2>
            <div class="price">£0</div>
            <p>Free entry. Join OAP, create your place, access community missions.</p>
        </div>
        <div class="card">
            <h2>👑 Postcode Founder</h2>
            <div class="price">£5</div>
            <p>Founder badge, Founder Wall, early recognition.</p>
        </div>
        <div class="card">
            <h2>🏛 Borough Builder</h2>
            <div class="price">£10</div>
            <p>Borough badge, promotion support, builder recognition.</p>
        </div>
        <div class="card">
            <h2>🌍 Country Champion</h2>
            <div class="price">£25</div>
            <p>Champion badge, featured recognition, higher support signal.</p>
        </div>
    </div>

    <div class="card">
        <h2>🌍 Circle Members</h2>
    </div>
    {member_html}
    """
    return layout("OAP Circle", body)

@app.route("/join-circle", methods=["GET", "POST"])
def join_circle():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        postcode = request.form.get("postcode", "").strip()
        borough = request.form.get("borough", "").strip()
        country = request.form.get("country", "").strip()
        continent = request.form.get("continent", "").strip()
        tier = request.form.get("tier", "").strip()
        proof_note = request.form.get("proof_note", "").strip()

        if name:
            conn = db()
            conn.execute("""
                INSERT INTO oap_circle_members
                (name, username, postcode, borough, country, continent, tier, proof_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, username, postcode, borough, country, continent, tier, proof_note, now()))

            if tier != "🆓 Community Member £0":
                conn.execute("""
                    INSERT INTO founder_wall
                    (member_name, tier, message, created_at)
                    VALUES (?, ?, ?, ?)
                """, (name, tier, proof_note or "Joined OAP Circle.", now()))

                amount = "£0"
                if "£5" in tier:
                    amount = "£5"
                elif "£10" in tier:
                    amount = "£10"
                elif "£25" in tier:
                    amount = "£25"

                conn.execute("""
                    INSERT INTO value_records
                    (title, value_type, amount, proof_note, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, ("OAP Circle Joined: " + name, "OAP Circle", amount, proof_note, now()))

            conn.commit()
            conn.close()

            add_explorer("OAP Circle", name, tier + " " + proof_note, "/oap-circle")

        return redirect(url_for("oap_circle"))

    body = """
    <div class="card">
        <h1>🌍 Join OAP Circle</h1>
        <form method="POST">
            <label>Name / Nickname</label>
            <input name="name" placeholder="Example: Prince Lloyd">

            <label>Username</label>
            <input name="username" placeholder="example: earthisourturf777">

            <label>Postcode</label>
            <input name="postcode" placeholder="Example: SW16">

            <label>Borough</label>
            <input name="borough" placeholder="Example: Mitcham / Lambeth / Croydon">

            <label>Country</label>
            <input name="country" placeholder="Example: Ghana / UK">

            <label>Continent</label>
            <input name="continent" placeholder="Example: Africa / Europe">

            <label>Circle Tier</label>
            <select name="tier">
                <option>🆓 Community Member £0</option>
                <option>👑 Postcode Founder £5</option>
                <option>🏛 Borough Builder £10</option>
                <option>🌍 Country Champion £25</option>
            </select>

            <label>Proof / Message</label>
            <textarea name="proof_note" placeholder="Why are they joining? What value or contribution is recorded?"></textarea>

            <button type="submit">Join OAP Circle</button>
        </form>
    </div>
    """
    return layout("Join Circle", body)

@app.route("/founder-wall")
def founder_wall():
    conn = db()
    rows = conn.execute("SELECT * FROM founder_wall ORDER BY id DESC").fetchall()
    conn.close()

    cards = ""
    for r in rows:
        cards += f"""
        <div class="card">
            <span class="tag">{r['tier']}</span>
            <h3>{r['member_name']}</h3>
            <p>{r['message'] or ''}</p>
            <p><small>{r['created_at']}</small></p>
        </div>
        """

    if not cards:
        cards = "<div class='card'><p>No founders yet. First Founder is waiting.</p></div>"

    body = f"""
    <div class="card">
        <h1>👑 Founder Wall</h1>
        <p>Recognition for early OAP Circle members who helped build the movement.</p>
    </div>
    {cards}
    """
    return layout("Founder Wall", body)

@app.route("/explorer")
def explorer():
    q = request.args.get("q", "").strip()
    conn = db()

    if q:
        like = f"%{q}%"
        rows = conn.execute("""
            SELECT * FROM explorer_index
            WHERE title LIKE ? OR description LIKE ? OR item_type LIKE ?
            ORDER BY id DESC
        """, (like, like, like)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM explorer_index ORDER BY id DESC").fetchall()

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
        results = "<div class='card'><p>No results yet.</p></div>"

    body = f"""
    <div class="card">
        <h1>🧭 Explorer</h1>
        <form method="GET" action="/explorer">
            <input name="q" placeholder="Search OAP World..." value="{q}">
            <button type="submit">Search</button>
        </form>
    </div>
    {results}
    """
    return layout("Explorer", body)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
