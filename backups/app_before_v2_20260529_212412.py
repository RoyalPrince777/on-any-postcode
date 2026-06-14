from flask import Flask, request, redirect, url_for, render_template_string, g, flash, session, send_file
import sqlite3
from pathlib import Path
from datetime import datetime
import os
import secrets
import html
import json
import shutil
from functools import wraps

APP_NAME = "OAP AI Research Kernel v0.3"
DB_PATH = Path("oap_research_kernel.db")
SECRET_PATH = Path(".oap_secret")
PIN_PATH = Path(".oap_pin")
BACKUP_DIR = Path("backups")
EXPORT_DIR = Path("exports")

BACKUP_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

if not SECRET_PATH.exists():
    SECRET_PATH.write_text(secrets.token_hex(32))
app.secret_key = SECRET_PATH.read_text().strip()


def clean(value):
    if value is None:
        return ""
    return html.escape(str(value).strip())


def now_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def pin_is_set():
    return PIN_PATH.exists() and PIN_PATH.read_text().strip()


def save_pin(pin):
    PIN_PATH.write_text(pin.strip())


def check_pin(pin):
    return pin_is_set() and PIN_PATH.read_text().strip() == pin.strip()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db:
        db.close()


def execute(sql, params=()):
    db = get_db()
    db.execute(sql, params)
    db.commit()


def query(sql, params=(), one=False):
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows[0] if one and rows else rows if not one else None


def audit(action, details=""):
    execute("INSERT INTO audit_log (action, details) VALUES (?, ?)", (clean(action), clean(details)))


def memory(event_type, title, lesson="", next_action="", importance="Medium"):
    execute(
        """
        INSERT INTO hrm_memory_log (event_type, title, lesson, next_action, importance)
        VALUES (?, ?, ?, ?, ?)
        """,
        (clean(event_type), clean(title), clean(lesson), clean(next_action), clean(importance))
    )
    audit("HRM_MEMORY_ADDED", f"{event_type}: {title}")


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not pin_is_set() and request.endpoint != "setup":
            return redirect(url_for("setup"))
        if not session.get("unlocked") and request.endpoint not in ["login", "setup", "static"]:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def column_exists(table, column):
    rows = query(f"PRAGMA table_info({table})")
    return any(r["name"] == column for r in rows)


def add_column_if_missing(table, column, definition):
    if not column_exists(table, column):
        execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS research_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'General',
        summary TEXT NOT NULL DEFAULT '',
        source_note TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Research',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS risk_register (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER,
        risk_type TEXT NOT NULL,
        risk_level TEXT NOT NULL DEFAULT 'Medium',
        description TEXT NOT NULL,
        mitigation TEXT NOT NULL DEFAULT '',
        review_status TEXT NOT NULL DEFAULT 'Open',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS decision_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        decision TEXT NOT NULL,
        reason TEXT NOT NULL DEFAULT '',
        rejected_options TEXT NOT NULL DEFAULT '',
        approval_status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS prediction_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction TEXT NOT NULL,
        reason TEXT NOT NULL DEFAULT '',
        expected_date TEXT NOT NULL DEFAULT '',
        result TEXT NOT NULL DEFAULT 'Not reviewed yet',
        confidence TEXT NOT NULL DEFAULT 'Low',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS permission_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        allowed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        purpose TEXT NOT NULL DEFAULT '',
        safety_limit TEXT NOT NULL DEFAULT '',
        result TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Planned',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        details TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source_type TEXT NOT NULL DEFAULT 'Note',
        author TEXT NOT NULL DEFAULT '',
        link_or_reference TEXT NOT NULL DEFAULT '',
        reliability TEXT NOT NULL DEFAULT 'Unknown',
        summary TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS review_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL,
        item_title TEXT NOT NULL,
        reason TEXT NOT NULL DEFAULT '',
        priority TEXT NOT NULL DEFAULT 'Medium',
        status TEXT NOT NULL DEFAULT 'Needs review',
        reviewer_note TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS hrm_memory_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        title TEXT NOT NULL,
        lesson TEXT NOT NULL DEFAULT '',
        next_action TEXT NOT NULL DEFAULT '',
        importance TEXT NOT NULL DEFAULT 'Medium',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    for table, cols in {
        "risk_register": [("review_status", "TEXT NOT NULL DEFAULT 'Open'")],
        "research_topics": [("review_status", "TEXT NOT NULL DEFAULT 'Not reviewed'")],
        "prediction_log": [("review_status", "TEXT NOT NULL DEFAULT 'Not reviewed'")],
        "experiments": [("review_status", "TEXT NOT NULL DEFAULT 'Not reviewed'")],
    }.items():
        for col, definition in cols:
            add_column_if_missing(table, col, definition)

    c = db.execute("SELECT COUNT(*) AS c FROM permission_rules").fetchone()["c"]
    if c == 0:
        rules = [
            ("Level 0", "Research only", "Research, summarize, compare, map ideas. No real-world action.", 1),
            ("Level 1", "Suggestion only", "Recommend safe next steps and options.", 1),
            ("Level 2", "Draft only", "Draft plans, posts, code, reports for review.", 1),
            ("Level 3", "Human-approved action", "Only act after explicit approval and audit.", 0),
            ("Level 4", "Restricted automation later", "Only after testing, rollback, logs, limits.", 0),
            ("Level 5", "No-go zone for now", "No money, banking, legal, health, surveillance, deployment, private data movement, irreversible action.", 0),
        ]
        db.executemany("INSERT INTO permission_rules (level,name,description,allowed) VALUES (?,?,?,?)", rules)
        db.execute("INSERT INTO audit_log (action,details) VALUES (?,?)", ("SYSTEM_INIT", "Default permission rules created"))
    db.commit()


def stats():
    tables = ["research_topics", "risk_register", "decision_log", "prediction_log", "experiments", "audit_log", "sources", "review_queue", "hrm_memory_log"]
    out = {}
    for t in tables:
        out[t] = query(f"SELECT COUNT(*) AS c FROM {t}", one=True)["c"]
    out["high_risks"] = query("SELECT COUNT(*) AS c FROM risk_register WHERE risk_level='High'", one=True)["c"]
    out["needs_review"] = query("SELECT COUNT(*) AS c FROM review_queue WHERE status='Needs review'", one=True)["c"]
    return out


BASE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{{ app_name }}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#050505;color:#f5f5f5;font-family:Arial,sans-serif;line-height:1.5}
.wrap{max-width:1180px;margin:auto;padding:18px}
.hero,.card{background:#111;border:1px solid #2a2a2a;border-radius:18px;padding:16px;margin-bottom:14px}
.hero{background:linear-gradient(135deg,rgba(34,197,94,.16),rgba(250,204,21,.1))}
h1,h2,h3{margin-top:0}
nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
a{color:#22c55e;text-decoration:none;font-weight:800}
nav a,.tag{border:1px solid #333;border-radius:999px;padding:8px 10px;color:#f5f5f5;background:#151515}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}
.col-3{grid-column:span 3}.col-4{grid-column:span 4}.col-6{grid-column:span 6}.col-8{grid-column:span 8}.col-12{grid-column:span 12}
@media(max-width:850px){.col-3,.col-4,.col-6,.col-8{grid-column:span 12}}
input,textarea,select{width:100%;padding:12px;border-radius:12px;border:1px solid #333;background:#070707;color:white;margin:6px 0 12px}
textarea{min-height:95px}
button,.button{background:#22c55e;color:#001b08;border:0;border-radius:999px;padding:10px 14px;font-weight:900;cursor:pointer}
.danger{background:#ef4444;color:white}.bluebtn{background:#38bdf8;color:#001018}.goldbtn{background:#facc15;color:#1a1200}
.gold{color:#facc15}.muted{color:#aaa;font-size:14px}.stat{font-size:30px;font-weight:900;color:#22c55e}
.flash{background:rgba(34,197,94,.15);border:1px solid #22c55e;border-radius:12px;padding:10px;margin-bottom:12px}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #333;padding:9px;text-align:left;vertical-align:top}th{color:#facc15}
.tag-green{color:#22c55e}.tag-red{color:#ef4444}.tag-gold{color:#facc15}.tag-blue{color:#38bdf8}
.law{border-left:4px solid #facc15;background:#080808;border-radius:10px;padding:10px;margin-top:10px;font-weight:800}
.row-actions{display:flex;gap:6px;flex-wrap:wrap}
</style>
</head>
<body>
<div class="wrap">
<section class="hero">
<h1>👑 {{ app_name }}</h1>
<p class="muted">ON ANY POSTCODE — Research has no ceiling. Deployment has boundaries.</p>
<div class="law">AI can research, reason, recommend and draft — but real-world action needs human approval, safety checks and audit.</div>
</section>

{% if session.get("unlocked") %}
<nav>
<a href="/">Dashboard</a><a href="/topics">Research</a><a href="/sources">Sources</a><a href="/risks">Risks</a><a href="/review">Review</a>
<a href="/decisions">Decisions</a><a href="/predictions">Predictions</a><a href="/permissions">Permissions</a><a href="/experiments">Experiments</a>
<a href="/memory">HRM Memory</a><a href="/audit">Audit</a><a href="/tools">Tools</a><a href="/seed">Seed</a><a href="/logout">Lock</a>
</nav>
{% endif %}

{% with messages=get_flashed_messages() %}
{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}
{% endwith %}

{{ content|safe }}
<p class="muted">Human-first. Private-first. Reliable-first. Local-first. Audit before automation. 🌍💚</p>
</div>
</body>
</html>
"""


def page(content):
    return render_template_string(BASE, app_name=APP_NAME, content=content)


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if pin_is_set():
        return redirect(url_for("login"))
    if request.method == "POST":
        pin = request.form.get("pin", "").strip()
        pin2 = request.form.get("pin2", "").strip()
        if len(pin) < 4:
            flash("PIN must be at least 4 digits/characters.")
        elif pin != pin2:
            flash("PINs do not match.")
        else:
            save_pin(pin)
            session["unlocked"] = True
            audit("PIN_CREATED", "Local app PIN created")
            memory("Security", "PIN created", "Kernel now has local gate protection.", "Keep PIN private.", "High")
            return redirect(url_for("index"))
    return page("""
    <div class="card">
    <h2>🔐 Create Local PIN</h2>
    <form method="post">
    <label>New PIN</label><input name="pin" type="password" required>
    <label>Repeat PIN</label><input name="pin2" type="password" required>
    <button>Create PIN</button>
    </form>
    </div>
    """)


@app.route("/login", methods=["GET", "POST"])
def login():
    if not pin_is_set():
        return redirect(url_for("setup"))
    if request.method == "POST":
        if check_pin(request.form.get("pin", "")):
            session["unlocked"] = True
            audit("LOGIN", "Kernel unlocked")
            return redirect(url_for("index"))
        flash("Wrong PIN.")
    return page("""
    <div class="card">
    <h2>🔐 Unlock OAP Kernel</h2>
    <form method="post"><label>PIN</label><input name="pin" type="password" autofocus required><button>Unlock</button></form>
    </div>
    """)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    s = stats()
    latest_memory = query("SELECT * FROM hrm_memory_log ORDER BY id DESC LIMIT 6")
    latest_review = query("SELECT * FROM review_queue ORDER BY id DESC LIMIT 6")
    content = render_template_string("""
    <div class="grid">
    <div class="card col-3"><div class="stat">{{s.research_topics}}</div><div class="muted">Research</div></div>
    <div class="card col-3"><div class="stat">{{s.sources}}</div><div class="muted">Sources</div></div>
    <div class="card col-3"><div class="stat">{{s.needs_review}}</div><div class="muted">Needs Review</div></div>
    <div class="card col-3"><div class="stat">{{s.hrm_memory_log}}</div><div class="muted">HRM Memories</div></div>
    </div>

    <div class="grid">
    <div class="card col-6"><h2>🧠 Kernel Status</h2>
    <p><b>Public:</b> OAP AI Research Kernel v0.3</p>
    <p><b>Private:</b> HRM Kernel Seed v0.3</p>
    <p><b>Now active:</b> research, sources, review queue, risk register, decisions, prediction log, HRM memory, PIN, export, backup.</p>
    <p><b>Blocked:</b> autonomous money, deployment, surveillance, private data movement, health/legal decisions.</p>
    </div>
    <div class="card col-6"><h2>⚖️ Signals</h2>
    <p><b>High risks:</b> {{s.high_risks}}</p>
    <p><b>Open reviews:</b> {{s.needs_review}}</p>
    <p><b>Audit records:</b> {{s.audit_log}}</p>
    <p><b>Experiments:</b> {{s.experiments}}</p>
    </div>
    </div>

    <div class="grid">
    <div class="card col-6"><h2>🧬 Latest HRM Memory</h2>
    {% for r in latest_memory %}
    <p><b>{{r.title}}</b><br><span class="muted">{{r.event_type}} / {{r.importance}} — {{r.created_at}}</span><br>{{r.lesson}}</p>
    {% else %}<p class="muted">No memory yet.</p>{% endfor %}
    </div>

    <div class="card col-6"><h2>👁️ Latest Review Queue</h2>
    {% for r in latest_review %}
    <p><b>{{r.item_title}}</b><br><span class="muted">{{r.item_type}} / {{r.priority}} / {{r.status}}</span><br>{{r.reason}}</p>
    {% else %}<p class="muted">No review items yet.</p>{% endfor %}
    </div>
    </div>
    """, s=s, latest_memory=latest_memory, latest_review=latest_review)
    return page(content)


@app.route("/topics", methods=["GET", "POST"])
@login_required
def topics():
    if request.method == "POST":
        title = clean(request.form.get("title"))
        execute("INSERT INTO research_topics (title,category,summary,source_note,status,review_status) VALUES (?,?,?,?,?,?)",
                (title, clean(request.form.get("category")) or "General",
                 clean(request.form.get("summary")), clean(request.form.get("source_note")),
                 clean(request.form.get("status")) or "Research", clean(request.form.get("review_status")) or "Not reviewed"))
        audit("TOPIC_CREATED", title)
        memory("Research", title, "New research topic added to library.", "Review source quality and risk.", "Medium")
        return redirect(url_for("topics"))
    rows = query("SELECT * FROM research_topics ORDER BY id DESC")
    return page(render_template_string("""
    <div class="grid"><div class="card col-4"><h2>➕ Add Research</h2>
    <form method="post">
    <label>Title</label><input name="title" required>
    <label>Category</label><select name="category">
    <option>AI Reasoning</option><option>Agents</option><option>World Models</option><option>Robotics</option><option>Cybersecurity</option>
    <option>Privacy</option><option>Governance</option><option>Finance / Ledger</option><option>Community Operations</option>
    <option>Media / News</option><option>Health / Wellbeing</option><option>Humanitarian</option><option>Hardware / Wearables</option><option>General</option>
    </select>
    <label>Summary</label><textarea name="summary"></textarea>
    <label>Source Note</label><textarea name="source_note"></textarea>
    <label>Status</label><select name="status"><option>Research</option><option>Review</option><option>Approved for planning</option><option>Delayed</option><option>Rejected</option></select>
    <label>Review Status</label><select name="review_status"><option>Not reviewed</option><option>Needs review</option><option>Reviewed</option><option>Approved</option><option>Rejected</option></select>
    <button>Add</button></form></div>
    <div class="card col-8"><h2>📚 Research Library</h2><table>
    <tr><th>Topic</th><th>Category</th><th>Status</th><th>Review</th><th>Summary</th><th></th></tr>
    {% for r in rows %}<tr><td><b>{{r.title}}</b><br><span class="muted">{{r.created_at}}</span></td><td>{{r.category}}</td><td>{{r.status}}</td><td>{{r.review_status}}</td><td>{{r.summary}}</td>
    <td class="row-actions">
    <form method="post" action="/queue/research/{{r.id}}"><button class="goldbtn">Review</button></form>
    <form method="post" action="/delete/research_topics/{{r.id}}"><button class="danger">Delete</button></form>
    </td></tr>
    {% endfor %}</table></div></div>""", rows=rows))


@app.route("/sources", methods=["GET", "POST"])
@login_required
def sources():
    if request.method == "POST":
        title = clean(request.form.get("title"))
        execute("INSERT INTO sources (title,source_type,author,link_or_reference,reliability,summary) VALUES (?,?,?,?,?,?)",
                (title, clean(request.form.get("source_type")), clean(request.form.get("author")),
                 clean(request.form.get("link_or_reference")), clean(request.form.get("reliability")), clean(request.form.get("summary"))))
        audit("SOURCE_CREATED", title)
        memory("Source", title, "New source added. Reliability should guide deployment decisions.", "Use source only after verification.", "Medium")
        return redirect(url_for("sources"))

    rows = query("SELECT * FROM sources ORDER BY id DESC")
    return page(render_template_string("""
    <div class="grid"><div class="card col-4"><h2>🔗 Add Source</h2>
    <form method="post">
    <label>Title</label><input name="title" required>
    <label>Source Type</label><select name="source_type"><option>Paper</option><option>Official docs</option><option>Book</option><option>News</option><option>Video</option><option>Personal note</option><option>Field observation</option><option>Other</option></select>
    <label>Author / Publisher</label><input name="author">
    <label>Link or Reference</label><textarea name="link_or_reference"></textarea>
    <label>Reliability</label><select name="reliability"><option>Unknown</option><option>Low</option><option>Medium</option><option>High</option><option>Primary source</option><option>Needs verification</option></select>
    <label>Summary</label><textarea name="summary"></textarea>
    <button>Add Source</button></form></div>
    <div class="card col-8"><h2>📎 Source Library</h2><table>
    <tr><th>Source</th><th>Type</th><th>Reliability</th><th>Summary</th><th></th></tr>
    {% for r in rows %}
    <tr><td><b>{{r.title}}</b><br><span class="muted">{{r.author}}<br>{{r.link_or_reference}}</span></td><td>{{r.source_type}}</td><td>{{r.reliability}}</td><td>{{r.summary}}</td>
    <td><form method="post" action="/delete/sources/{{r.id}}"><button class="danger">Delete</button></form></td></tr>
    {% endfor %}
    </table></div></div>""", rows=rows))


@app.route("/risks", methods=["GET", "POST"])
@login_required
def risks():
    if request.method == "POST":
        execute("INSERT INTO risk_register (topic_id,risk_type,risk_level,description,mitigation,review_status) VALUES (?,?,?,?,?,?)",
                (request.form.get("topic_id") or None, clean(request.form.get("risk_type")), clean(request.form.get("risk_level")),
                 clean(request.form.get("description")), clean(request.form.get("mitigation")), clean(request.form.get("review_status")) or "Open"))
        audit("RISK_CREATED", request.form.get("risk_type", ""))
        memory("Risk", request.form.get("risk_type", ""), "New risk added to register.", "Mitigate before deployment.", "High" if request.form.get("risk_level") == "High" else "Medium")
        return redirect(url_for("risks"))
    rows = query("SELECT r.*,t.title AS topic_title FROM risk_register r LEFT JOIN research_topics t ON r.topic_id=t.id ORDER BY r.id DESC")
    topics_rows = query("SELECT id,title FROM research_topics ORDER BY title")
    return page(render_template_string("""
    <div class="grid"><div class="card col-4"><h2>🛡️ Add Risk</h2><form method="post">
    <label>Topic</label><select name="topic_id"><option value="">None</option>{% for t in topics_rows %}<option value="{{t.id}}">{{t.title}}</option>{% endfor %}</select>
    <label>Type</label><select name="risk_type"><option>Legal risk</option><option>Privacy risk</option><option>Security risk</option><option>Community harm risk</option><option>Financial risk</option><option>Overbuilding risk</option><option>Fake claim risk</option><option>Youth safety risk</option></select>
    <label>Level</label><select name="risk_level"><option>Low</option><option selected>Medium</option><option>High</option></select>
    <label>Description</label><textarea name="description" required></textarea>
    <label>Mitigation</label><textarea name="mitigation"></textarea>
    <label>Review Status</label><select name="review_status"><option>Open</option><option>Mitigated</option><option>Accepted</option><option>Blocked</option></select>
    <button>Add</button></form></div>
    <div class="card col-8"><h2>⚠️ Risk Register</h2><table><tr><th>Risk</th><th>Level</th><th>Description</th><th>Mitigation</th><th>Status</th><th></th></tr>
    {% for r in rows %}<tr><td><b>{{r.risk_type}}</b><br><span class="muted">{{r.topic_title or "No topic"}}</span></td><td>{{r.risk_level}}</td><td>{{r.description}}</td><td>{{r.mitigation}}</td><td>{{r.review_status}}</td>
    <td><form method="post" action="/delete/risk_register/{{r.id}}"><button class="danger">Delete</button></form></td></tr>{% endfor %}
    </table></div></div>""", rows=rows, topics_rows=topics_rows))


@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    if request.method == "POST":
        execute("INSERT INTO review_queue (item_type,item_title,reason,priority,status,reviewer_note) VALUES (?,?,?,?,?,?)",
                (clean(request.form.get("item_type")), clean(request.form.get("item_title")), clean(request.form.get("reason")),
                 clean(request.form.get("priority")), clean(request.form.get("status")), clean(request.form.get("reviewer_note"))))
        audit("REVIEW_CREATED", request.form.get("item_title", ""))
        memory("Review", request.form.get("item_title", ""), "Item added to human review queue.", "Resolve review before deployment.", "High")
        return redirect(url_for("review"))

    rows = query("SELECT * FROM review_queue ORDER BY id DESC")
    return page(render_template_string("""
    <div class="grid"><div class="card col-4"><h2>👁️ Add Review Item</h2><form method="post">
    <label>Item Type</label><select name="item_type"><option>Research</option><option>Risk</option><option>Decision</option><option>Prediction</option><option>Experiment</option><option>Deployment</option><option>Legal</option><option>Privacy</option></select>
    <label>Item Title</label><input name="item_title" required>
    <label>Reason</label><textarea name="reason"></textarea>
    <label>Priority</label><select name="priority"><option>Low</option><option selected>Medium</option><option>High</option><option>Critical</option></select>
    <label>Status</label><select name="status"><option>Needs review</option><option>Approved</option><option>Rejected</option><option>Blocked</option><option>Done</option></select>
    <label>Reviewer Note</label><textarea name="reviewer_note"></textarea>
    <button>Add Review</button></form></div>
    <div class="card col-8"><h2>👁️ Review Queue</h2><table><tr><th>Item</th><th>Reason</th><th>Priority</th><th>Status</th><th></th></tr>
    {% for r in rows %}
    <tr><td><b>{{r.item_title}}</b><br><span class="muted">{{r.item_type}} — {{r.created_at}}</span></td><td>{{r.reason}}<br><span class="muted">{{r.reviewer_note}}</span></td><td>{{r.priority}}</td><td>{{r.status}}</td>
    <td class="row-actions">
    <form method="post" action="/review/{{r.id}}/status/Approved"><button>Approve</button></form>
    <form method="post" action="/review/{{r.id}}/status/Blocked"><button class="danger">Block</button></form>
    <form method="post" action="/delete/review_queue/{{r.id}}"><button class="danger">Delete</button></form>
    </td></tr>
    {% endfor %}</table></div></div>""", rows=rows))


@app.route("/review/<int:item_id>/status/<status>", methods=["POST"])
@login_required
def review_status(item_id, status):
    allowed = {"Approved", "Blocked", "Rejected", "Done", "Needs review"}
    if status not in allowed:
        flash("Status blocked.")
        return redirect(url_for("review"))
    execute("UPDATE review_queue SET status=? WHERE id=?", (status, item_id))
    audit("REVIEW_STATUS_UPDATED", f"id={item_id} status={status}")
    memory("Review Status", f"Review item {item_id}", f"Status changed to {status}.", "Use status before action.", "High")
    return redirect(url_for("review"))


@app.route("/queue/research/<int:item_id>", methods=["POST"])
@login_required
def queue_research(item_id):
    row = query("SELECT * FROM research_topics WHERE id=?", (item_id,), one=True)
    if row:
        execute("INSERT INTO review_queue (item_type,item_title,reason,priority,status) VALUES (?,?,?,?,?)",
                ("Research", row["title"], "Research topic sent for human review.", "Medium", "Needs review"))
        audit("RESEARCH_QUEUED", row["title"])
        flash("Research sent to review queue.")
    return redirect(url_for("topics"))


@app.route("/decisions", methods=["GET", "POST"])
@login_required
def decisions():
    if request.method == "POST":
        title = clean(request.form.get("title"))
        execute("INSERT INTO decision_log (title,decision,reason,rejected_options,approval_status) VALUES (?,?,?,?,?)",
                (title, clean(request.form.get("decision")), clean(request.form.get("reason")),
                 clean(request.form.get("rejected_options")), clean(request.form.get("approval_status"))))
        audit("DECISION_CREATED", title)
        memory("Decision", title, "Decision logged for future reasoning and audit.", "Review outcome later.", "High")
        return redirect(url_for("decisions"))
    rows = query("SELECT * FROM decision_log ORDER BY id DESC")
    return page(render_template_string("""
    <div class="grid"><div class="card col-4"><h2>⚖️ Add Decision</h2><form method="post">
    <label>Title</label><input name="title" required><label>Decision</label><textarea name="decision" required></textarea>
    <label>Reason</label><textarea name="reason"></textarea><label>Rejected Options</label><textarea name="rejected_options"></textarea>
    <label>Status</label><select name="approval_status"><option>Pending</option><option>Approved</option><option>Rejected</option><option>Needs review</option></select>
    <button>Log</button></form></div>
    <div class="card col-8"><h2>📜 Decision Log</h2><table><tr><th>Title</th><th>Decision</th><th>Status</th><th></th></tr>
    {% for r in rows %}<tr><td><b>{{r.title}}</b><br><span class="muted">{{r.created_at}}</span></td><td>{{r.decision}}<br><span class="muted">{{r.reason}}</span></td><td>{{r.approval_status}}</td>
    <td><form method="post" action="/delete/decision_log/{{r.id}}"><button class="danger">Delete</button></form></td></tr>{% endfor %}</table></div></div>""", rows=rows))


@app.route("/predictions", methods=["GET", "POST"])
@login_required
def predictions():
    if request.method == "POST":
        prediction = clean(request.form.get("prediction"))
        execute("INSERT INTO prediction_log (prediction,reason,expected_date,result,confidence,review_status) VALUES (?,?,?,?,?,?)",
                (prediction, clean(request.form.get("reason")), clean(request.form.get("expected_date")),
                 clean(request.form.get("result")) or "Not reviewed yet", clean(request.form.get("confidence")) or "Low",
                 clean(request.form.get("review_status")) or "Not reviewed"))
        audit("PREDICTION_CREATED", prediction[:120])
        memory("Prediction", prediction[:120], "Prediction recorded for later reality check.", "Review against real outcome.", "Medium")
        return redirect(url_for("predictions"))
    rows = query("SELECT * FROM prediction_log ORDER BY id DESC")
    return page(render_template_string("""
    <div class="grid"><div class="card col-4"><h2>🔮 Add Prediction</h2><form method="post">
    <label>Prediction</label><textarea name="prediction" required></textarea><label>Reason</label><textarea name="reason"></textarea>
    <label>Expected Date</label><input name="expected_date"><label>Result</label><select name="result"><option>Not reviewed yet</option><option>Correct</option><option>Partly correct</option><option>Wrong</option><option>Needs more data</option></select>
    <label>Confidence</label><select name="confidence"><option>Low</option><option>Medium</option><option>High</option></select>
    <label>Review Status</label><select name="review_status"><option>Not reviewed</option><option>Needs review</option><option>Reviewed</option></select>
    <button>Log</button></form></div>
    <div class="card col-8"><h2>📈 Prediction Log</h2><table><tr><th>Prediction</th><th>Reason</th><th>Review</th><th></th></tr>
    {% for r in rows %}<tr><td><b>{{r.prediction}}</b><br>{{r.confidence}} / {{r.result}}</td><td>{{r.reason}}</td><td>{{r.expected_date}}<br><span class="muted">{{r.review_status}} / {{r.created_at}}</span></td>
    <td><form method="post" action="/delete/prediction_log/{{r.id}}"><button class="danger">Delete</button></form></td></tr>{% endfor %}</table></div></div>""", rows=rows))


@app.route("/permissions", methods=["GET", "POST"])
@login_required
def permissions():
    if request.method == "POST":
        execute("UPDATE permission_rules SET allowed=? WHERE id=?", (1 if request.form.get("allowed") == "1" else 0, request.form.get("rule_id")))
        audit("PERMISSION_UPDATED", f"rule={request.form.get('rule_id')}")
        memory("Permission", f"Rule {request.form.get('rule_id')}", "Permission changed.", "Keep Level 3+ blocked until real safety exists.", "High")
        return redirect(url_for("permissions"))
    rows = query("SELECT * FROM permission_rules ORDER BY id")
    return page(render_template_string("""
    <div class="card"><h2>🔐 Permissions</h2><table><tr><th>Level</th><th>Name</th><th>Description</th><th>Allowed</th><th></th></tr>
    {% for r in rows %}<tr><td>{{r.level}}</td><td><b>{{r.name}}</b></td><td>{{r.description}}</td><td>{{"Allowed" if r.allowed else "Blocked"}}</td>
    <td><form method="post"><input type="hidden" name="rule_id" value="{{r.id}}"><button name="allowed" value="1">Allow</button> <button class="danger" name="allowed" value="0">Block</button></form></td></tr>{% endfor %}
    </table></div>""", rows=rows))


@app.route("/experiments", methods=["GET", "POST"])
@login_required
def experiments():
    if request.method == "POST":
        title = clean(request.form.get("title"))
        execute("INSERT INTO experiments (title,purpose,safety_limit,result,status,review_status) VALUES (?,?,?,?,?,?)",
                (title, clean(request.form.get("purpose")), clean(request.form.get("safety_limit")),
                 clean(request.form.get("result")), clean(request.form.get("status")), clean(request.form.get("review_status")) or "Not reviewed"))
        audit("EXPERIMENT_CREATED", title)
        memory("Experiment", title, "Experiment logged with safety limits.", "Never run without checking limits.", "Medium")
        return redirect(url_for("experiments"))
    rows = query("SELECT * FROM experiments ORDER BY id DESC")
    return page(render_template_string("""
    <div class="grid"><div class="card col-4"><h2>🧪 Add Experiment</h2><form method="post">
    <label>Title</label><input name="title" required><label>Purpose</label><textarea name="purpose"></textarea>
    <label>Safety Limit</label><textarea name="safety_limit"></textarea><label>Result</label><textarea name="result"></textarea>
    <label>Status</label><select name="status"><option>Planned</option><option>Running</option><option>Completed</option><option>Paused</option><option>Rejected</option></select>
    <label>Review Status</label><select name="review_status"><option>Not reviewed</option><option>Needs review</option><option>Reviewed</option></select>
    <button>Add</button></form></div>
    <div class="card col-8"><h2>🧬 Experiments</h2><table><tr><th>Title</th><th>Purpose</th><th>Limit</th><th>Status</th><th></th></tr>
    {% for r in rows %}<tr><td><b>{{r.title}}</b><br><span class="muted">{{r.created_at}}</span></td><td>{{r.purpose}}</td><td>{{r.safety_limit}}</td><td>{{r.status}} / {{r.review_status}}</td>
    <td><form method="post" action="/delete/experiments/{{r.id}}"><button class="danger">Delete</button></form></td></tr>{% endfor %}</table></div></div>""", rows=rows))


@app.route("/memory", methods=["GET", "POST"])
@login_required
def memory_page():
    if request.method == "POST":
        memory(request.form.get("event_type"), request.form.get("title"), request.form.get("lesson"), request.form.get("next_action"), request.form.get("importance"))
        flash("HRM memory added.")
        return redirect(url_for("memory_page"))
    rows = query("SELECT * FROM hrm_memory_log ORDER BY id DESC")
    return page(render_template_string("""
    <div class="grid"><div class="card col-4"><h2>🧠 Add HRM Memory</h2><form method="post">
    <label>Event Type</label><select name="event_type"><option>Research</option><option>Risk</option><option>Decision</option><option>Prediction</option><option>Experiment</option><option>Security</option><option>Build</option><option>Lesson</option></select>
    <label>Title</label><input name="title" required>
    <label>Lesson</label><textarea name="lesson"></textarea>
    <label>Next Action</label><textarea name="next_action"></textarea>
    <label>Importance</label><select name="importance"><option>Low</option><option selected>Medium</option><option>High</option><option>Critical</option></select>
    <button>Add Memory</button></form></div>
    <div class="card col-8"><h2>🧬 HRM Memory Log</h2><table><tr><th>Memory</th><th>Lesson</th><th>Next Action</th><th></th></tr>
    {% for r in rows %}<tr><td><b>{{r.title}}</b><br><span class="muted">{{r.event_type}} / {{r.importance}} / {{r.created_at}}</span></td><td>{{r.lesson}}</td><td>{{r.next_action}}</td>
    <td><form method="post" action="/delete/hrm_memory_log/{{r.id}}"><button class="danger">Delete</button></form></td></tr>{% endfor %}
    </table></div></div>""", rows=rows))


@app.route("/audit")
@login_required
def audit_page():
    rows = query("SELECT * FROM audit_log ORDER BY id DESC LIMIT 300")
    return page(render_template_string("""
    <div class="card"><h2>🧾 Audit</h2><table><tr><th>Time</th><th>Action</th><th>Details</th></tr>
    {% for r in rows %}<tr><td>{{r.created_at}}</td><td>{{r.action}}</td><td>{{r.details}}</td></tr>{% endfor %}
    </table></div>""", rows=rows))


@app.route("/tools")
@login_required
def tools():
    return page("""
    <div class="grid">
    <div class="card col-6"><h2>📤 Export JSON</h2><p class="muted">Download all records as JSON.</p><a class="button" href="/export/json">Export JSON</a></div>
    <div class="card col-6"><h2>💾 Backup Database</h2><p class="muted">Create and download SQLite backup.</p><a class="button" href="/backup/db">Backup DB</a></div>
    <div class="card col-6"><h2>🔐 Change PIN</h2><form method="post" action="/change-pin"><label>Current PIN</label><input type="password" name="old_pin" required><label>New PIN</label><input type="password" name="new_pin" required><button>Change PIN</button></form></div>
    <div class="card col-6"><h2>⚠️ Reset Data</h2><p class="muted">Deletes database only. Backup first.</p><form method="post" action="/reset-db" onsubmit="return confirm('Delete all database records? Backup first.')"><label>Type RESET</label><input name="confirm" required><button class="danger">Reset Database</button></form></div>
    </div>
    """)


@app.route("/change-pin", methods=["POST"])
@login_required
def change_pin():
    if not check_pin(request.form.get("old_pin", "")):
        flash("Current PIN wrong.")
        return redirect(url_for("tools"))
    new_pin = request.form.get("new_pin", "").strip()
    if len(new_pin) < 4:
        flash("New PIN too short.")
        return redirect(url_for("tools"))
    save_pin(new_pin)
    audit("PIN_CHANGED", "PIN changed")
    memory("Security", "PIN changed", "Access key updated.", "Keep PIN protected.", "High")
    flash("PIN changed.")
    return redirect(url_for("tools"))


@app.route("/export/json")
@login_required
def export_json():
    data = {}
    tables = ["research_topics", "risk_register", "decision_log", "prediction_log", "permission_rules", "experiments", "audit_log", "sources", "review_queue", "hrm_memory_log"]
    for table in tables:
        data[table] = [dict(r) for r in query(f"SELECT * FROM {table} ORDER BY id")]
    path = EXPORT_DIR / f"oap_research_export_{now_stamp()}.json"
    path.write_text(json.dumps(data, indent=2))
    audit("EXPORT_JSON", str(path))
    return send_file(path, as_attachment=True)


@app.route("/backup/db")
@login_required
def backup_db():
    if not DB_PATH.exists():
        flash("No database yet.")
        return redirect(url_for("tools"))
    path = BACKUP_DIR / f"oap_research_kernel_backup_{now_stamp()}.db"
    shutil.copy2(DB_PATH, path)
    audit("DB_BACKUP", str(path))
    return send_file(path, as_attachment=True)


@app.route("/reset-db", methods=["POST"])
@login_required
def reset_db():
    if request.form.get("confirm") != "RESET":
        flash("Reset blocked. Type RESET exactly.")
        return redirect(url_for("tools"))
    backup_path = BACKUP_DIR / f"before_reset_{now_stamp()}.db"
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_path)
        DB_PATH.unlink()
    with app.app_context():
        init_db()
    audit("DATABASE_RESET", f"Previous database backed up to {backup_path}")
    flash("Database reset. Previous DB backed up.")
    return redirect(url_for("index"))


@app.route("/seed")
@login_required
def seed_data():
    if query("SELECT COUNT(*) AS c FROM research_topics", one=True)["c"] > 0:
        flash("Seed already exists.")
        return redirect(url_for("index"))

    seed_topics = [
        ("Foundation intelligence stack", "AI Reasoning", "LLMs, multimodal, coding, reasoning, memory, world models, small local models.", "OAP AI map", "Research", "Reviewed"),
        ("Agent intelligence with approval", "Agents", "Agents can plan and use tools, but OAP requires approval before action.", "OAP rule", "Research", "Reviewed"),
        ("World models for OAP operations", "World Models", "Study cause/effect, logistics, risk, navigation, weather, and planning.", "OAP map", "Research", "Needs review"),
        ("Local-first AI memory", "Privacy", "Private memory, SQLite, audit logs, source notes and permission rules before cloud.", "OAP doctrine", "Approved for planning", "Approved"),
        ("SIKA trust ledger readiness", "Finance / Ledger", "Future SIKA begins as contribution/trust records, not legal tender or bank claims.", "Compliance direction", "Delayed", "Needs review"),
    ]
    get_db().executemany("INSERT INTO research_topics (title,category,summary,source_note,status,review_status) VALUES (?,?,?,?,?,?)", seed_topics)

    seed_sources = [
        ("OAP Internal AI R&D Map", "Personal note", "OAP", "Internal strategy", "Primary source", "Research ceiling, deployment boundaries, HRM seed structure."),
        ("OAP Safety Laws", "Personal note", "OAP", "Internal doctrine", "Primary source", "7 active laws: proof, verification, compliance, community, ownership, audit, approval."),
    ]
    get_db().executemany("INSERT INTO sources (title,source_type,author,link_or_reference,reliability,summary) VALUES (?,?,?,?,?,?)", seed_sources)

    seed_risks = [
        (None, "Fake claim risk", "High", "Calling early tools full autonomy can mislead users.", "Use honest labels.", "Open"),
        (None, "Financial risk", "High", "Banking/payment/legal tender claims create legal risk.", "Delay public bank claims.", "Open"),
        (None, "Privacy risk", "High", "Research logs may store sensitive information.", "Keep minimal and local.", "Open"),
        (None, "Overbuilding risk", "Medium", "Building everything at once can block launch.", "Build small modules first.", "Mitigated"),
        (None, "Autonomy risk", "High", "Automation without approval can cause harm.", "Human approval before action.", "Open"),
    ]
    get_db().executemany("INSERT INTO risk_register (topic_id,risk_type,risk_level,description,mitigation,review_status) VALUES (?,?,?,?,?,?)", seed_risks)

    seed_decisions = [
        ("Research ceiling / deployment boundary", "Study broadly; deploy safely with law, privacy, approval and audit.", "Protects ambition and safety.", "Rejected unrestricted deployment.", "Approved"),
        ("Delay wallet/bank claims", "SIKA and bank-style UX stay roadmap-only until compliance readiness.", "Prevents legal risk.", "Rejected public bank claims.", "Approved"),
    ]
    get_db().executemany("INSERT INTO decision_log (title,decision,reason,rejected_options,approval_status) VALUES (?,?,?,?,?)", seed_decisions)

    seed_reviews = [
        ("Finance / Ledger", "SIKA trust ledger readiness", "Needs compliance review before public wording.", "High", "Needs review", ""),
        ("Governance", "Human-approved governor later", "Needs thresholds before any autonomy.", "High", "Needs review", ""),
    ]
    get_db().executemany("INSERT INTO review_queue (item_type,item_title,reason,priority,status,reviewer_note) VALUES (?,?,?,?,?,?)", seed_reviews)

    seed_memory = [
        ("Doctrine", "Research has no ceiling", "Research can be broad, deployment must be bounded.", "Keep permission levels clear.", "Critical"),
        ("Build", "HRM learns from records", "Memory comes from real records, not hype.", "Log research, decisions, risks, reviews.", "High"),
    ]
    get_db().executemany("INSERT INTO hrm_memory_log (event_type,title,lesson,next_action,importance) VALUES (?,?,?,?,?)", seed_memory)

    get_db().commit()
    audit("SEED_CREATED", "Starter v0.3 data inserted")
    flash("Seed data created.")
    return redirect(url_for("index"))


ALLOWED_DELETE_TABLES = {
    "research_topics", "risk_register", "decision_log", "prediction_log",
    "experiments", "sources", "review_queue", "hrm_memory_log"
}


@app.route("/delete/<table>/<int:item_id>", methods=["POST"])
@login_required
def delete_item(table, item_id):
    if table not in ALLOWED_DELETE_TABLES:
        flash("Delete blocked.")
        return redirect(url_for("index"))
    execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
    audit("ITEM_DELETED", f"{table} id={item_id}")
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        init_db()

    host = os.environ.get("OAP_HOST", "127.0.0.1")
    port = int(os.environ.get("OAP_PORT", "5001"))
    debug = os.environ.get("OAP_DEBUG", "false").lower() == "true"

    print(f"\n{APP_NAME}")
    print("Open: http://127.0.0.1:5001")
    print("Research has no ceiling. Deployment has boundaries.\n")

    app.run(host=host, port=port, debug=debug)
