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
    CREATE TABLE IF NOT EXISTS community_missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        mission_type TEXT,
        description TEXT,
        created_by TEXT,
        status TEXT DEFAULT 'Open',
        proof_note TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS mission_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mission_id INTEGER,
        member_name TEXT,
        joined_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS mission_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mission_id INTEGER,
        update_note TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def seed_data():
    conn = db()
    c = conn.cursor()

    if c.execute("SELECT COUNT(*) FROM explorer_index").fetchone()[0] == 0:
        items = [
            ("News", "OAP News", "Community updates, culture, sport and launch signals.", "/"),
            ("Experience", "First OAP Experience", "Plan one meetup, watch party or community session.", "/launch-board"),
            ("Business", "Business Network", "Invite one barber, food shop, clothing seller or local service.", "/launch-board"),
            ("Creator", "Creator Hub", "Invite one artist, musician, designer, comedian or storyteller.", "/launch-board"),
            ("Award", "OAP Awards", "Recognition for contribution, creativity, business and culture.", "/"),
            ("Community", "Postcode to Universe", "Postcode, borough, county, country, continent and global journey.", "/"),
            ("Contribution", "Value Created", "Record first £5, £10 or £25 value signal.", "/dashboard"),
            ("Community Power", "Community Power", "Missions, action, value created and contribution recorded.", "/community-power"),
        ]
        for item in items:
            c.execute("""
                INSERT INTO explorer_index
                (item_type, title, description, url, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (*item, now()))

    if c.execute("SELECT COUNT(*) FROM launch_actions").fetchone()[0] == 0:
        actions = [
            ("Invite first local business", "First Business", "OAP", "Open", "Ask one barber/shop/food business to join Business Network."),
            ("Create first OAP Experience", "First OAP Experience", "OAP", "Open", "Plan one small meetup/watch party/community session."),
            ("Invite first creator", "First Creator", "OAP", "Open", "Ask one artist/creator to join Creator Hub."),
            ("Record first Value Created", "First Value Created", "OAP", "Open", "Record first £5, £10, or £25 value signal."),
        ]
        for a in actions:
            c.execute("""
                INSERT INTO launch_actions
                (title, action_type, assigned_to, status, proof_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (*a, now()))

    if c.execute("SELECT COUNT(*) FROM community_missions").fetchone()[0] == 0:
        missions = [
            ("Invite First Business", "🏪 Business Mission", "Invite one real local business into OAP.", "OAP", "Open", "First business target."),
            ("Invite First Creator", "👤 Creator Mission", "Invite one real creator into OAP.", "OAP", "Open", "First creator target."),
            ("Create First Community Experience", "🎪 Experience Mission", "Plan one watch party, meetup or community session.", "OAP", "Open", "First experience target."),
            ("Record First £5 Value", "💚 Value Mission", "Record first £5, £10 or £25 value signal.", "OAP", "Open", "First value target."),
            ("Recruit First Community Member", "🌍 Community Mission", "Invite one person to join OAP as Community Member.", "OAP", "Open", "First member target."),
        ]
        for m in missions:
            c.execute("""
                INSERT INTO community_missions
                (title, mission_type, description, created_by, status, proof_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (*m, now()))

    conn.commit()
    conn.close()

def table_count(table):
    conn = db()
    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return total

def count_type(item_type):
    conn = db()
    total = conn.execute("SELECT COUNT(*) FROM explorer_index WHERE item_type=?", (item_type,)).fetchone()[0]
    conn.close()
    return total

def count_status(status):
    conn = db()
    total = conn.execute("SELECT COUNT(*) FROM community_missions WHERE status=?", (status,)).fetchone()[0]
    conn.close()
    return total

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
            .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
            .metric { background:#061009; border:1px solid #347a4d; border-radius:18px; padding:16px; text-align:center; }
            .metric h2 { margin:0; font-size:34px; color:#8dffb0; }
            input, select, textarea { width:100%; padding:13px; margin:8px 0; border-radius:12px; border:1px solid #347a4d; background:#061009; color:white; box-sizing:border-box; }
            button { width:100%; padding:14px; border:0; border-radius:12px; background:#31d36b; color:#041007; font-weight:bold; font-size:16px; }
            .tag { display:inline-block; padding:5px 9px; border-radius:999px; background:#244b32; color:#b8ffd0; font-size:13px; }
            .signal { color:#8dffb0; font-weight:bold; }
            .danger { color:#ffb3b3; }
        </style>
    </head>
    <body>
        <header>
            <h2>🌍 ON ANY POSTCODE</h2>
            <div class="nav">
                <a href="/">Home</a>
                <a href="/dashboard">📊 Dashboard</a>
                <a href="/explorer">🧭 Explorer</a>
                <a href="/community-power">⚡ Community Power</a>
                <a href="/create-mission">➕ Mission</a>
                <a href="/launch-board">🚦 Launch Board</a>
                <a href="/record-value">💚 Value</a>
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
        <p class="signal">Mission: first member, first founder, first business, first creator, first experience, first value record.</p>
    </div>
    <div class="card">
        <p><a href="/community-power">⚡ Open Community Power</a></p>
        <p><a href="/dashboard">📊 Open Dashboard</a></p>
        <p><a href="/explorer">🧭 Open Explorer</a></p>
        <p><a href="/launch-board">🚦 Open Launch Board</a></p>
    </div>
    """
    return layout("OAP World", body)

@app.route("/dashboard")
def dashboard():
    metrics = {
        "Explorer Items": table_count("explorer_index"),
        "Launch Actions": table_count("launch_actions"),
        "Value Records": table_count("value_records"),
        "Missions": table_count("community_missions"),
        "Mission Members": table_count("mission_members"),
        "Mission Updates": table_count("mission_updates"),
        "Open Missions": count_status("Open"),
        "Active Missions": count_status("Active"),
        "Completed Missions": count_status("Completed"),
        "Businesses": count_type("Business"),
        "Creators": count_type("Creator"),
        "Experiences": count_type("Experience"),
    }

    metric_html = ""
    for name, total in metrics.items():
        metric_html += f"<div class='metric'><h2>{total}</h2><p>{name}</p></div>"

    body = f"""
    <div class="card">
        <h1>📊 Sovereign Dashboard Metrics</h1>
        <p>Live OAP signal board.</p>
    </div>
    <div class="grid">{metric_html}</div>
    """
    return layout("Dashboard", body)

@app.route("/community-power")
def community_power():
    conn = db()
    missions = conn.execute("SELECT * FROM community_missions ORDER BY id DESC").fetchall()
    conn.close()

    cards = ""
    for m in missions:
        conn = db()
        members = conn.execute("SELECT * FROM mission_members WHERE mission_id=? ORDER BY id DESC", (m["id"],)).fetchall()
        updates = conn.execute("SELECT * FROM mission_updates WHERE mission_id=? ORDER BY id DESC LIMIT 3", (m["id"],)).fetchall()
        conn.close()

        member_html = "".join([f"<span class='tag'>{x['member_name']}</span> " for x in members]) or "<p>No members joined yet.</p>"
        update_html = "".join([f"<p>• {u['update_note']} <small>{u['created_at']}</small></p>" for u in updates]) or "<p>No updates yet.</p>"

        cards += f"""
        <div class="card">
            <span class="tag">{m['mission_type'] or 'Mission'}</span>
            <span class="tag">{m['status']}</span>
            <h3>{m['title']}</h3>
            <p>{m['description'] or ''}</p>
            <p><b>Created by:</b> {m['created_by'] or 'OAP'}</p>
            <p><b>Proof:</b> {m['proof_note'] or ''}</p>

            <h4>🤝 Joined Members</h4>
            {member_html}

            <form method="POST" action="/join-mission/{m['id']}">
                <input name="member_name" placeholder="Member name">
                <button type="submit">Join Mission</button>
            </form>

            <h4>📝 Mission Updates</h4>
            {update_html}

            <form method="POST" action="/add-update/{m['id']}">
                <textarea name="update_note" placeholder="Add proof/update note"></textarea>
                <button type="submit">Add Update</button>
            </form>

            <p><a href="/activate-mission/{m['id']}">Set Active</a> | <a href="/complete-mission/{m['id']}">Complete + Contribution Recorded</a></p>
        </div>
        """

    body = f"""
    <div class="card">
        <h1>⚡ Community Power</h1>
        <p>People → Missions → Action → Value Created → Contribution Recorded.</p>
        <p><a href="/create-mission">➕ Create New Mission</a></p>
    </div>
    {cards}
    """
    return layout("Community Power", body)

@app.route("/create-mission", methods=["GET", "POST"])
def create_mission():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        mission_type = request.form.get("mission_type", "").strip()
        description = request.form.get("description", "").strip()
        created_by = request.form.get("created_by", "").strip() or "OAP"
        proof_note = request.form.get("proof_note", "").strip()

        if title:
            conn = db()
            conn.execute("""
                INSERT INTO community_missions
                (title, mission_type, description, created_by, status, proof_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, mission_type, description, created_by, "Open", proof_note, now()))

            conn.execute("""
                INSERT INTO explorer_index
                (item_type, title, description, url, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("Community Power", title, description, "/community-power", now()))

            conn.commit()
            conn.close()

        return redirect(url_for("community_power"))

    body = """
    <div class="card">
        <h1>➕ Create Mission</h1>
        <form method="POST">
            <label>Mission Title</label>
            <input name="title" placeholder="Example: Invite first barber">

            <label>Mission Type</label>
            <select name="mission_type">
                <option>🏪 Business Mission</option>
                <option>👤 Creator Mission</option>
                <option>🎪 Experience Mission</option>
                <option>🌍 Community Mission</option>
                <option>👶 Youth Mission</option>
                <option>🧓 Elder Support Mission</option>
                <option>🌱 Environment Mission</option>
                <option>💚 Value Mission</option>
                <option>🌍 Humanitarian Community Power</option>
            </select>

            <label>Description</label>
            <textarea name="description" placeholder="What needs to happen?"></textarea>

            <label>Created By</label>
            <input name="created_by" placeholder="OAP / member name">

            <label>Proof Note</label>
            <textarea name="proof_note" placeholder="What proof is needed before completion?"></textarea>

            <button type="submit">Create Mission</button>
        </form>
    </div>
    """
    return layout("Create Mission", body)

@app.route("/join-mission/<int:mission_id>", methods=["POST"])
def join_mission(mission_id):
    member_name = request.form.get("member_name", "").strip()
    if member_name:
        conn = db()
        conn.execute("""
            INSERT INTO mission_members
            (mission_id, member_name, joined_at)
            VALUES (?, ?, ?)
        """, (mission_id, member_name, now()))
        conn.execute("UPDATE community_missions SET status=? WHERE id=? AND status='Open'", ("Active", mission_id))
        conn.commit()
        conn.close()
    return redirect(url_for("community_power"))

@app.route("/add-update/<int:mission_id>", methods=["POST"])
def add_update(mission_id):
    update_note = request.form.get("update_note", "").strip()
    if update_note:
        conn = db()
        conn.execute("""
            INSERT INTO mission_updates
            (mission_id, update_note, created_at)
            VALUES (?, ?, ?)
        """, (mission_id, update_note, now()))
        conn.commit()
        conn.close()
    return redirect(url_for("community_power"))

@app.route("/activate-mission/<int:mission_id>")
def activate_mission(mission_id):
    conn = db()
    conn.execute("UPDATE community_missions SET status=? WHERE id=?", ("Active", mission_id))
    conn.commit()
    conn.close()
    return redirect(url_for("community_power"))

@app.route("/complete-mission/<int:mission_id>")
def complete_mission(mission_id):
    conn = db()
    mission = conn.execute("SELECT * FROM community_missions WHERE id=?", (mission_id,)).fetchone()

    if mission:
        conn.execute("UPDATE community_missions SET status=? WHERE id=?", ("Completed", mission_id))

        conn.execute("""
            INSERT INTO value_records
            (title, value_type, amount, proof_note, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Contribution Recorded: " + mission["title"],
            "Community Power",
            "Proof / Value",
            mission["proof_note"] or mission["description"] or "Mission completed.",
            now()
        ))

        conn.execute("""
            INSERT INTO explorer_index
            (item_type, title, description, url, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Contribution",
            "Contribution Recorded: " + mission["title"],
            mission["description"] or "Mission completed.",
            "/dashboard",
            now()
        ))

    conn.commit()
    conn.close()
    return redirect(url_for("community_power"))

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

@app.route("/record-value", methods=["GET", "POST"])
def record_value():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        value_type = request.form.get("value_type", "").strip()
        amount = request.form.get("amount", "").strip()
        proof_note = request.form.get("proof_note", "").strip()

        if title:
            conn = db()
            conn.execute("""
                INSERT INTO value_records
                (title, value_type, amount, proof_note, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title, value_type, amount, proof_note, now()))
            conn.execute("""
                INSERT INTO explorer_index
                (item_type, title, description, url, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("Contribution", title, proof_note, "/dashboard", now()))
            conn.commit()
            conn.close()

        return redirect(url_for("dashboard"))

    body = """
    <div class="card">
        <h1>💚 Record Value Created</h1>
        <form method="POST">
            <input name="title" placeholder="Example: First £5 founder value">
            <select name="value_type">
                <option>Membership</option>
                <option>Business</option>
                <option>Creator</option>
                <option>Experience</option>
                <option>Sale</option>
                <option>Contribution</option>
            </select>
            <input name="amount" placeholder="£5 / £10 / £25 / proof only">
            <textarea name="proof_note" placeholder="What value was created?"></textarea>
            <button type="submit">Record Value</button>
        </form>
    </div>
    """
    return layout("Record Value", body)

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
            <p><a href="/complete-action/{r['id']}">Mark Contribution Recorded</a></p>
        </div>
        """

    if not cards:
        cards = "<div class='card'><p>No launch actions yet.</p></div>"

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
    action = conn.execute("SELECT * FROM launch_actions WHERE id=?", (action_id,)).fetchone()

    if action:
        conn.execute("UPDATE launch_actions SET status=? WHERE id=?", ("Contribution Recorded", action_id))
        conn.execute("""
            INSERT INTO value_records
            (title, value_type, amount, proof_note, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Contribution Recorded: " + action["title"],
            action["action_type"] or "Launch Action",
            "Proof / Value",
            action["proof_note"] or "",
            now()
        ))

    conn.commit()
    conn.close()
    return redirect(url_for("launch_board"))

if __name__ == "__main__":
    init_db()
    seed_data()
    app.run(host="0.0.0.0", port=5000)
