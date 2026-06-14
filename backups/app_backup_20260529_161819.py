from flask import Flask, request, redirect, url_for, render_template_string, g, flash
import sqlite3
from pathlib import Path
from datetime import datetime
import os
import secrets
import html

APP_NAME = "OAP AI Research Kernel v0.1"
DB_PATH = Path("oap_research_kernel.db")
SECRET_PATH = Path(".oap_secret")

app = Flask(__name__)

if not SECRET_PATH.exists():
    SECRET_PATH.write_text(secrets.token_hex(32))

app.secret_key = SECRET_PATH.read_text().strip()


# ============================================================
# DATABASE
# ============================================================

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def execute(sql, params=()):
    db = get_db()
    db.execute(sql, params)
    db.commit()


def query(sql, params=(), one=False):
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def init_db():
    db = get_db()

    db.executescript(
        """
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
        """
    )

    existing_rules = query("SELECT COUNT(*) AS c FROM permission_rules", one=True)
    if existing_rules["c"] == 0:
        default_rules = [
            ("Level 0", "Research only", "AI can research, summarize, compare, and map ideas. No real-world action.", 1),
            ("Level 1", "Suggestion only", "AI can recommend safe next steps, checklists, and options.", 1),
            ("Level 2", "Draft only", "AI can draft plans, posts, policies, code, messages, and reports for human review.", 1),
            ("Level 3", "Human-approved action", "AI can only act after explicit human approval and audit logging.", 0),
            ("Level 4", "Restricted automation later", "Limited automation only after testing, rollback, safety rules, and audit history.", 0),
            ("Level 5", "No-go zone for now", "No control over money, banking, legal claims, health decisions, private data movement, surveillance, deployment, or irreversible action.", 0),
        ]

        db.executemany(
            """
            INSERT INTO permission_rules (level, name, description, allowed)
            VALUES (?, ?, ?, ?)
            """,
            default_rules
        )

        db.execute(
            """
            INSERT INTO audit_log (action, details)
            VALUES (?, ?)
            """,
            ("SYSTEM_INIT", "Default permission rules created")
        )

    db.commit()


def audit(action, details=""):
    execute(
        "INSERT INTO audit_log (action, details) VALUES (?, ?)",
        (clean(action), clean(details))
    )


# ============================================================
# HELPERS
# ============================================================

def clean(value):
    if value is None:
        return ""
    return html.escape(str(value).strip())


def short(value, length=140):
    value = str(value or "")
    return value[:length] + "..." if len(value) > length else value


def stats():
    return {
        "topics": query("SELECT COUNT(*) AS c FROM research_topics", one=True)["c"],
        "risks": query("SELECT COUNT(*) AS c FROM risk_register", one=True)["c"],
        "decisions": query("SELECT COUNT(*) AS c FROM decision_log", one=True)["c"],
        "predictions": query("SELECT COUNT(*) AS c FROM prediction_log", one=True)["c"],
        "experiments": query("SELECT COUNT(*) AS c FROM experiments", one=True)["c"],
        "audits": query("SELECT COUNT(*) AS c FROM audit_log", one=True)["c"],
    }


# ============================================================
# BASE TEMPLATE
# ============================================================

BASE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{{ app_name }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        :root {
            --bg: #050505;
            --panel: #111111;
            --panel2: #191919;
            --text: #f3f3f3;
            --muted: #a3a3a3;
            --green: #22c55e;
            --gold: #facc15;
            --red: #ef4444;
            --blue: #38bdf8;
            --border: #2a2a2a;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background:
                radial-gradient(circle at top, rgba(34,197,94,0.15), transparent 30%),
                radial-gradient(circle at bottom right, rgba(250,204,21,0.10), transparent 25%),
                var(--bg);
            color: var(--text);
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.5;
        }

        a {
            color: var(--green);
            text-decoration: none;
            font-weight: 700;
        }

        .wrap {
            max-width: 1150px;
            margin: 0 auto;
            padding: 18px;
        }

        .hero {
            background: linear-gradient(135deg, rgba(34,197,94,0.16), rgba(250,204,21,0.10));
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 22px;
            margin-bottom: 16px;
            box-shadow: 0 0 30px rgba(34,197,94,0.08);
        }

        .hero h1 {
            margin: 0;
            font-size: 28px;
            letter-spacing: -0.5px;
        }

        .hero p {
            margin: 8px 0 0;
            color: var(--muted);
        }

        .law {
            margin-top: 14px;
            background: rgba(0,0,0,0.35);
            border-left: 4px solid var(--gold);
            padding: 12px;
            border-radius: 12px;
            font-weight: 700;
        }

        nav {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 16px;
        }

        nav a {
            background: var(--panel);
            border: 1px solid var(--border);
            padding: 10px 12px;
            border-radius: 999px;
            color: var(--text);
        }

        nav a:hover {
            border-color: var(--green);
            color: var(--green);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 14px;
        }

        .col-12 { grid-column: span 12; }
        .col-8 { grid-column: span 8; }
        .col-6 { grid-column: span 6; }
        .col-4 { grid-column: span 4; }
        .col-3 { grid-column: span 3; }

        @media (max-width: 800px) {
            .col-8, .col-6, .col-4, .col-3 {
                grid-column: span 12;
            }

            .hero h1 {
                font-size: 23px;
            }
        }

        .card {
            background: rgba(17,17,17,0.92);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 16px;
            margin-bottom: 14px;
        }

        .card h2, .card h3 {
            margin-top: 0;
        }

        .muted {
            color: var(--muted);
            font-size: 14px;
        }

        .stat {
            font-size: 28px;
            font-weight: 900;
            color: var(--green);
        }

        input, textarea, select {
            width: 100%;
            background: #070707;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 12px;
            border-radius: 12px;
            margin: 6px 0 12px;
            font-size: 15px;
        }

        textarea {
            min-height: 100px;
        }

        label {
            display: block;
            color: var(--gold);
            font-weight: 800;
            margin-top: 4px;
        }

        button, .button {
            background: var(--green);
            color: #001b08;
            border: none;
            padding: 11px 14px;
            border-radius: 999px;
            font-weight: 900;
            cursor: pointer;
            display: inline-block;
        }

        button:hover, .button:hover {
            filter: brightness(1.08);
        }

        .danger {
            background: var(--red);
            color: white;
        }

        .tag {
            display: inline-block;
            padding: 5px 9px;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--muted);
            font-size: 13px;
            margin: 2px;
        }

        .tag-green {
            border-color: var(--green);
            color: var(--green);
        }

        .tag-gold {
            border-color: var(--gold);
            color: var(--gold);
        }

        .tag-red {
            border-color: var(--red);
            color: var(--red);
        }

        .tag-blue {
            border-color: var(--blue);
            color: var(--blue);
        }

        .flash {
            background: rgba(34,197,94,0.14);
            border: 1px solid rgba(34,197,94,0.45);
            padding: 12px;
            border-radius: 14px;
            margin-bottom: 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            overflow: hidden;
            border-radius: 12px;
        }

        th, td {
            border-bottom: 1px solid var(--border);
            padding: 10px;
            text-align: left;
            vertical-align: top;
        }

        th {
            color: var(--gold);
            background: rgba(250,204,21,0.05);
        }

        .small-actions {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }

        .footer {
            color: var(--muted);
            font-size: 13px;
            padding: 25px 0;
        }
    </style>
</head>
<body>
<div class="wrap">

    <section class="hero">
        <h1>👑 {{ app_name }}</h1>
        <p>ON ANY POSTCODE — AI research has no ceiling. Deployment has boundaries.</p>
        <div class="law">
            OAP AI may research infinitely, reason deeply, and recommend powerfully — but it may not control money, identity, deployment, private data, legal decisions, health decisions, or real-world actions without human approval and audit.
        </div>
    </section>

    <nav>
        <a href="{{ url_for('index') }}">Dashboard</a>
        <a href="{{ url_for('topics') }}">Research</a>
        <a href="{{ url_for('risks') }}">Risks</a>
        <a href="{{ url_for('decisions') }}">Decisions</a>
        <a href="{{ url_for('predictions') }}">Predictions</a>
        <a href="{{ url_for('permissions') }}">Permissions</a>
        <a href="{{ url_for('experiments') }}">Experiments</a>
        <a href="{{ url_for('audit_page') }}">Audit</a>
        <a href="{{ url_for('seed_data') }}">Seed</a>
    </nav>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
            <div class="flash">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {{ content|safe }}

    <div class="footer">
        Human-first. Private-first. Reliable-first. Local-first. Audit before automation. 🌍💚
    </div>

</div>
</body>
</html>
"""


def page(content):
    return render_template_string(BASE, app_name=APP_NAME, content=content)


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    s = stats()

    recent_topics = query("SELECT * FROM research_topics ORDER BY id DESC LIMIT 5")
    recent_risks = query("SELECT * FROM risk_register ORDER BY id DESC LIMIT 5")
    recent_decisions = query("SELECT * FROM decision_log ORDER BY id DESC LIMIT 5")
    recent_predictions = query("SELECT * FROM prediction_log ORDER BY id DESC LIMIT 5")

    content = render_template_string(
        """
        <div class="grid">
            <div class="card col-3"><div class="stat">{{ s.topics }}</div><div class="muted">Research Topics</div></div>
            <div class="card col-3"><div class="stat">{{ s.risks }}</div><div class="muted">Risk Records</div></div>
            <div class="card col-3"><div class="stat">{{ s.decisions }}</div><div class="muted">Decisions</div></div>
            <div class="card col-3"><div class="stat">{{ s.predictions }}</div><div class="muted">Predictions</div></div>
        </div>

        <div class="grid">
            <div class="card col-6">
                <h2>🧠 Current Kernel Status</h2>
                <p><strong>Public name:</strong> OAP AI Research Kernel v0.1</p>
                <p><strong>Private architecture:</strong> HRM Kernel Seed v0.1</p>
                <p><strong>Current AI level:</strong> Research, planning, risk review, decision support, prediction logging.</p>
                <p><strong>Not active yet:</strong> autonomy, money control, deployment control, surveillance, private data movement, health/legal decisions.</p>
            </div>

            <div class="card col-6">
                <h2>⚖️ Active 7 Laws</h2>
                <span class="tag tag-green">Proof before execution</span>
                <span class="tag tag-green">Verification before sharing</span>
                <span class="tag tag-green">Compliance before claims</span>
                <span class="tag tag-green">Community before middlemen</span>
                <span class="tag tag-green">Ownership before dependency</span>
                <span class="tag tag-green">Audit before automation</span>
                <span class="tag tag-green">Human approval before action</span>
            </div>
        </div>

        <div class="grid">
            <div class="card col-6">
                <h2>Latest Research</h2>
                {% for row in recent_topics %}
                    <p><strong>{{ row.title }}</strong><br>
                    <span class="muted">{{ row.category }} — {{ row.status }}</span></p>
                {% else %}
                    <p class="muted">No research yet. Add or seed data.</p>
                {% endfor %}
            </div>

            <div class="card col-6">
                <h2>Latest Risks</h2>
                {% for row in recent_risks %}
                    <p><strong>{{ row.risk_type }}</strong>
                    <span class="tag {% if row.risk_level == 'High' %}tag-red{% elif row.risk_level == 'Medium' %}tag-gold{% else %}tag-green{% endif %}">{{ row.risk_level }}</span><br>
                    <span class="muted">{{ row.description[:120] }}</span></p>
                {% else %}
                    <p class="muted">No risks recorded yet.</p>
                {% endfor %}
            </div>
        </div>

        <div class="grid">
            <div class="card col-6">
                <h2>Latest Decisions</h2>
                {% for row in recent_decisions %}
                    <p><strong>{{ row.title }}</strong><br>
                    <span class="muted">{{ row.approval_status }} — {{ row.created_at }}</span></p>
                {% else %}
                    <p class="muted">No decisions recorded yet.</p>
                {% endfor %}
            </div>

            <div class="card col-6">
                <h2>Latest Predictions</h2>
                {% for row in recent_predictions %}
                    <p><strong>{{ row.prediction[:120] }}</strong><br>
                    <span class="muted">Confidence: {{ row.confidence }} — Result: {{ row.result }}</span></p>
                {% else %}
                    <p class="muted">No predictions recorded yet.</p>
                {% endfor %}
            </div>
        </div>
        """,
        s=s,
        recent_topics=recent_topics,
        recent_risks=recent_risks,
        recent_decisions=recent_decisions,
        recent_predictions=recent_predictions
    )

    return page(content)


# ============================================================
# RESEARCH TOPICS
# ============================================================

@app.route("/topics", methods=["GET", "POST"])
def topics():
    if request.method == "POST":
        title = clean(request.form.get("title"))
        category = clean(request.form.get("category"))
        summary = clean(request.form.get("summary"))
        source_note = clean(request.form.get("source_note"))
        status = clean(request.form.get("status"))

        if title:
            execute(
                """
                INSERT INTO research_topics (title, category, summary, source_note, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, category or "General", summary, source_note, status or "Research")
            )
            audit("TOPIC_CREATED", title)
            flash("Research topic added.")
        return redirect(url_for("topics"))

    rows = query("SELECT * FROM research_topics ORDER BY id DESC")

    content = render_template_string(
        """
        <div class="grid">
            <div class="card col-4">
                <h2>➕ Add Research Topic</h2>
                <form method="post">
                    <label>Title</label>
                    <input name="title" placeholder="Example: World models for OAP logistics" required>

                    <label>Category</label>
                    <select name="category">
                        <option>AI Reasoning</option>
                        <option>Agents</option>
                        <option>World Models</option>
                        <option>Robotics</option>
                        <option>Cybersecurity</option>
                        <option>Privacy</option>
                        <option>Governance</option>
                        <option>Finance / Ledger</option>
                        <option>Community Operations</option>
                        <option>Media / News</option>
                        <option>Health / Wellbeing</option>
                        <option>Humanitarian</option>
                        <option>Hardware / Wearables</option>
                        <option>General</option>
                    </select>

                    <label>Summary</label>
                    <textarea name="summary" placeholder="What did we learn?"></textarea>

                    <label>Source Note</label>
                    <textarea name="source_note" placeholder="Book, paper, link name, video, observation, or human source note"></textarea>

                    <label>Status</label>
                    <select name="status">
                        <option>Research</option>
                        <option>Review</option>
                        <option>Approved for planning</option>
                        <option>Delayed</option>
                        <option>Rejected</option>
                    </select>

                    <button>Add Topic</button>
                </form>
            </div>

            <div class="card col-8">
                <h2>📚 Research Library</h2>
                <table>
                    <tr>
                        <th>Topic</th>
                        <th>Category</th>
                        <th>Status</th>
                        <th>Summary</th>
                        <th>Action</th>
                    </tr>
                    {% for row in rows %}
                    <tr>
                        <td><strong>{{ row.title }}</strong><br><span class="muted">{{ row.created_at }}</span></td>
                        <td><span class="tag tag-blue">{{ row.category }}</span></td>
                        <td><span class="tag tag-green">{{ row.status }}</span></td>
                        <td>{{ row.summary[:180] }}</td>
                        <td>
                            <form method="post" action="{{ url_for('delete_item', table='research_topics', item_id=row.id) }}">
                                <button class="danger" onclick="return confirm('Delete this topic?')">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" class="muted">No research topics yet.</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        """,
        rows=rows
    )

    return page(content)


# ============================================================
# RISKS
# ============================================================

@app.route("/risks", methods=["GET", "POST"])
def risks():
    if request.method == "POST":
        topic_id = request.form.get("topic_id") or None
        risk_type = clean(request.form.get("risk_type"))
        risk_level = clean(request.form.get("risk_level"))
        description = clean(request.form.get("description"))
        mitigation = clean(request.form.get("mitigation"))

        if risk_type and description:
            execute(
                """
                INSERT INTO risk_register (topic_id, risk_type, risk_level, description, mitigation)
                VALUES (?, ?, ?, ?, ?)
                """,
                (topic_id, risk_type, risk_level or "Medium", description, mitigation)
            )
            audit("RISK_CREATED", f"{risk_type} / {risk_level}")
            flash("Risk record added.")
        return redirect(url_for("risks"))

    rows = query(
        """
        SELECT r.*, t.title AS topic_title
        FROM risk_register r
        LEFT JOIN research_topics t ON r.topic_id = t.id
        ORDER BY r.id DESC
        """
    )

    topics_rows = query("SELECT id, title FROM research_topics ORDER BY title")

    content = render_template_string(
        """
        <div class="grid">
            <div class="card col-4">
                <h2>🛡️ Add Risk</h2>
                <form method="post">
                    <label>Linked Topic</label>
                    <select name="topic_id">
                        <option value="">No linked topic</option>
                        {% for t in topics_rows %}
                            <option value="{{ t.id }}">{{ t.title }}</option>
                        {% endfor %}
                    </select>

                    <label>Risk Type</label>
                    <select name="risk_type">
                        <option>Legal risk</option>
                        <option>Privacy risk</option>
                        <option>Security risk</option>
                        <option>Community harm risk</option>
                        <option>Financial risk</option>
                        <option>Reputation risk</option>
                        <option>Overbuilding risk</option>
                        <option>Fake claim risk</option>
                        <option>Youth safety risk</option>
                        <option>Humanitarian risk</option>
                    </select>

                    <label>Risk Level</label>
                    <select name="risk_level">
                        <option>Low</option>
                        <option selected>Medium</option>
                        <option>High</option>
                    </select>

                    <label>Description</label>
                    <textarea name="description" required></textarea>

                    <label>Mitigation</label>
                    <textarea name="mitigation" placeholder="How do we reduce or block the risk?"></textarea>

                    <button>Add Risk</button>
                </form>
            </div>

            <div class="card col-8">
                <h2>⚠️ Risk Register</h2>
                <table>
                    <tr>
                        <th>Risk</th>
                        <th>Level</th>
                        <th>Description</th>
                        <th>Mitigation</th>
                        <th>Action</th>
                    </tr>
                    {% for row in rows %}
                    <tr>
                        <td>
                            <strong>{{ row.risk_type }}</strong><br>
                            <span class="muted">{{ row.topic_title or 'No topic linked' }}</span>
                        </td>
                        <td>
                            <span class="tag {% if row.risk_level == 'High' %}tag-red{% elif row.risk_level == 'Medium' %}tag-gold{% else %}tag-green{% endif %}">
                                {{ row.risk_level }}
                            </span>
                        </td>
                        <td>{{ row.description }}</td>
                        <td>{{ row.mitigation }}</td>
                        <td>
                            <form method="post" action="{{ url_for('delete_item', table='risk_register', item_id=row.id) }}">
                                <button class="danger" onclick="return confirm('Delete this risk?')">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" class="muted">No risks recorded.</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        """,
        rows=rows,
        topics_rows=topics_rows
    )

    return page(content)


# ============================================================
# DECISIONS
# ============================================================

@app.route("/decisions", methods=["GET", "POST"])
def decisions():
    if request.method == "POST":
        title = clean(request.form.get("title"))
        decision = clean(request.form.get("decision"))
        reason = clean(request.form.get("reason"))
        rejected_options = clean(request.form.get("rejected_options"))
        approval_status = clean(request.form.get("approval_status"))

        if title and decision:
            execute(
                """
                INSERT INTO decision_log (title, decision, reason, rejected_options, approval_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, decision, reason, rejected_options, approval_status or "Pending")
            )
            audit("DECISION_CREATED", title)
            flash("Decision logged.")
        return redirect(url_for("decisions"))

    rows = query("SELECT * FROM decision_log ORDER BY id DESC")

    content = render_template_string(
        """
        <div class="grid">
            <div class="card col-4">
                <h2>⚖️ Add Decision</h2>
                <form method="post">
                    <label>Title</label>
                    <input name="title" required placeholder="Example: Delay wallet until real trust records exist">

                    <label>Decision</label>
                    <textarea name="decision" required></textarea>

                    <label>Reason</label>
                    <textarea name="reason"></textarea>

                    <label>Rejected Options</label>
                    <textarea name="rejected_options" placeholder="What did we reject and why?"></textarea>

                    <label>Approval Status</label>
                    <select name="approval_status">
                        <option>Pending</option>
                        <option>Approved</option>
                        <option>Rejected</option>
                        <option>Needs review</option>
                    </select>

                    <button>Log Decision</button>
                </form>
            </div>

            <div class="card col-8">
                <h2>📜 Decision Log</h2>
                <table>
                    <tr>
                        <th>Decision</th>
                        <th>Reason</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                    {% for row in rows %}
                    <tr>
                        <td>
                            <strong>{{ row.title }}</strong><br>
                            {{ row.decision }}<br>
                            <span class="muted">{{ row.created_at }}</span>
                        </td>
                        <td>
                            {{ row.reason }}
                            {% if row.rejected_options %}
                                <br><br><span class="muted">Rejected: {{ row.rejected_options }}</span>
                            {% endif %}
                        </td>
                        <td><span class="tag tag-gold">{{ row.approval_status }}</span></td>
                        <td>
                            <form method="post" action="{{ url_for('delete_item', table='decision_log', item_id=row.id) }}">
                                <button class="danger" onclick="return confirm('Delete this decision?')">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="4" class="muted">No decisions logged.</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        """,
        rows=rows
    )

    return page(content)


# ============================================================
# PREDICTIONS
# ============================================================

@app.route("/predictions", methods=["GET", "POST"])
def predictions():
    if request.method == "POST":
        prediction = clean(request.form.get("prediction"))
        reason = clean(request.form.get("reason"))
        expected_date = clean(request.form.get("expected_date"))
        result = clean(request.form.get("result"))
        confidence = clean(request.form.get("confidence"))

        if prediction:
            execute(
                """
                INSERT INTO prediction_log (prediction, reason, expected_date, result, confidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                (prediction, reason, expected_date, result or "Not reviewed yet", confidence or "Low")
            )
            audit("PREDICTION_CREATED", prediction[:120])
            flash("Prediction logged.")
        return redirect(url_for("predictions"))

    rows = query("SELECT * FROM prediction_log ORDER BY id DESC")

    content = render_template_string(
        """
        <div class="grid">
            <div class="card col-4">
                <h2>🔮 Add Prediction</h2>
                <form method="post">
                    <label>Prediction</label>
                    <textarea name="prediction" required placeholder="Example: World Cup Energy will increase local creator/business engagement."></textarea>

                    <label>Reason</label>
                    <textarea name="reason"></textarea>

                    <label>Expected Review Date</label>
                    <input name="expected_date" placeholder="Example: 2026-07-15">

                    <label>Result</label>
                    <select name="result">
                        <option>Not reviewed yet</option>
                        <option>Correct</option>
                        <option>Partly correct</option>
                        <option>Wrong</option>
                        <option>Needs more data</option>
                    </select>

                    <label>Confidence</label>
                    <select name="confidence">
                        <option>Low</option>
                        <option>Medium</option>
                        <option>High</option>
                    </select>

                    <button>Log Prediction</button>
                </form>
            </div>

            <div class="card col-8">
                <h2>📈 Prediction Log</h2>
                <table>
                    <tr>
                        <th>Prediction</th>
                        <th>Reason</th>
                        <th>Review</th>
                        <th>Action</th>
                    </tr>
                    {% for row in rows %}
                    <tr>
                        <td>
                            <strong>{{ row.prediction }}</strong><br>
                            <span class="tag tag-blue">{{ row.confidence }}</span>
                            <span class="tag tag-gold">{{ row.result }}</span>
                        </td>
                        <td>{{ row.reason }}</td>
                        <td>
                            <span class="muted">Expected: {{ row.expected_date or 'Not set' }}</span><br>
                            <span class="muted">Created: {{ row.created_at }}</span>
                        </td>
                        <td>
                            <form method="post" action="{{ url_for('delete_item', table='prediction_log', item_id=row.id) }}">
                                <button class="danger" onclick="return confirm('Delete this prediction?')">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="4" class="muted">No predictions logged.</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        """,
        rows=rows
    )

    return page(content)


# ============================================================
# PERMISSIONS
# ============================================================

@app.route("/permissions", methods=["GET", "POST"])
def permissions():
    if request.method == "POST":
        rule_id = request.form.get("rule_id")
        allowed = 1 if request.form.get("allowed") == "1" else 0
        execute("UPDATE permission_rules SET allowed = ? WHERE id = ?", (allowed, rule_id))
        audit("PERMISSION_UPDATED", f"rule_id={rule_id}, allowed={allowed}")
        flash("Permission rule updated.")
        return redirect(url_for("permissions"))

    rows = query("SELECT * FROM permission_rules ORDER BY id ASC")

    content = render_template_string(
        """
        <div class="card">
            <h2>🔐 AI Permission System</h2>
            <p class="muted">
                This page defines what the OAP AI Research Kernel is allowed to do.
                Current build allows research, suggestions, and drafts only.
                Real-world action remains blocked unless human approval and audit exist.
            </p>

            <table>
                <tr>
                    <th>Level</th>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Allowed?</th>
                    <th>Update</th>
                </tr>
                {% for row in rows %}
                <tr>
                    <td><span class="tag tag-blue">{{ row.level }}</span></td>
                    <td><strong>{{ row.name }}</strong></td>
                    <td>{{ row.description }}</td>
                    <td>
                        {% if row.allowed %}
                            <span class="tag tag-green">Allowed</span>
                        {% else %}
                            <span class="tag tag-red">Blocked</span>
                        {% endif %}
                    </td>
                    <td>
                        <form method="post" class="small-actions">
                            <input type="hidden" name="rule_id" value="{{ row.id }}">
                            <button name="allowed" value="1">Allow</button>
                            <button class="danger" name="allowed" value="0">Block</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        """,
        rows=rows
    )

    return page(content)


# ============================================================
# EXPERIMENTS
# ============================================================

@app.route("/experiments", methods=["GET", "POST"])
def experiments():
    if request.method == "POST":
        title = clean(request.form.get("title"))
        purpose = clean(request.form.get("purpose"))
        safety_limit = clean(request.form.get("safety_limit"))
        result = clean(request.form.get("result"))
        status = clean(request.form.get("status"))

        if title:
            execute(
                """
                INSERT INTO experiments (title, purpose, safety_limit, result, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, purpose, safety_limit, result, status or "Planned")
            )
            audit("EXPERIMENT_CREATED", title)
            flash("Experiment logged.")
        return redirect(url_for("experiments"))

    rows = query("SELECT * FROM experiments ORDER BY id DESC")

    content = render_template_string(
        """
        <div class="grid">
            <div class="card col-4">
                <h2>🧪 Add Experiment</h2>
                <form method="post">
                    <label>Title</label>
                    <input name="title" required placeholder="Example: Test checklist planner with World Cup event">

                    <label>Purpose</label>
                    <textarea name="purpose"></textarea>

                    <label>Safety Limit</label>
                    <textarea name="safety_limit" placeholder="What must this experiment NOT do?"></textarea>

                    <label>Result</label>
                    <textarea name="result"></textarea>

                    <label>Status</label>
                    <select name="status">
                        <option>Planned</option>
                        <option>Running</option>
                        <option>Completed</option>
                        <option>Paused</option>
                        <option>Rejected</option>
                    </select>

                    <button>Add Experiment</button>
                </form>
            </div>

            <div class="card col-8">
                <h2>🧬 Experiments</h2>
                <table>
                    <tr>
                        <th>Experiment</th>
                        <th>Purpose</th>
                        <th>Safety Limit</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                    {% for row in rows %}
                    <tr>
                        <td><strong>{{ row.title }}</strong><br><span class="muted">{{ row.created_at }}</span></td>
                        <td>{{ row.purpose }}</td>
                        <td>{{ row.safety_limit }}</td>
                        <td><span class="tag tag-gold">{{ row.status }}</span></td>
                        <td>
                            <form method="post" action="{{ url_for('delete_item', table='experiments', item_id=row.id) }}">
                                <button class="danger" onclick="return confirm('Delete this experiment?')">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" class="muted">No experiments logged.</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        """,
        rows=rows
    )

    return page(content)


# ============================================================
# AUDIT
# ============================================================

@app.route("/audit")
def audit_page():
    rows = query("SELECT * FROM audit_log ORDER BY id DESC LIMIT 250")

    content = render_template_string(
        """
        <div class="card">
            <h2>🧾 Audit History</h2>
            <p class="muted">Every important system action gets recorded here. Audit before automation.</p>

            <table>
                <tr>
                    <th>Time</th>
                    <th>Action</th>
                    <th>Details</th>
                </tr>
                {% for row in rows %}
                <tr>
                    <td>{{ row.created_at }}</td>
                    <td><span class="tag tag-green">{{ row.action }}</span></td>
                    <td>{{ row.details }}</td>
                </tr>
                {% else %}
                <tr><td colspan="3" class="muted">No audit records.</td></tr>
                {% endfor %}
            </table>
        </div>
        """,
        rows=rows
    )

    return page(content)


# ============================================================
# SEED DATA
# ============================================================

@app.route("/seed")
def seed_data():
    topic_count = query("SELECT COUNT(*) AS c FROM research_topics", one=True)["c"]

    if topic_count == 0:
        seed_topics = [
            (
                "Foundation intelligence stack",
                "AI Reasoning",
                "LLMs, multimodal models, coding models, reasoning systems, memory, world models, and small local models form the base AI stack.",
                "Internal OAP AI R&D map",
                "Research"
            ),
            (
                "Agent intelligence with approval",
                "Agents",
                "AI can plan, use tools, operate workflows, and remember context, but OAP requires human approval before real-world action.",
                "OAP safety rule",
                "Research"
            ),
            (
                "World models for OAP operations",
                "World Models",
                "Study cause/effect, logistics, risk, navigation, weather, field operations, and future planning before action.",
                "OAP AI R&D map",
                "Research"
            ),
            (
                "Local-first AI memory",
                "Privacy",
                "Private memory, local SQLite records, audit logs, source notes, and permission rules should come before cloud dependence.",
                "OAP local-first doctrine",
                "Approved for planning"
            ),
            (
                "Human-approved autonomous governor",
                "Governance",
                "Long-term direction only. AI watches, learns, predicts, recommends, audits, and waits for human approval.",
                "Deployment boundary rule",
                "Delayed"
            ),
            (
                "OAP News and Media intelligence",
                "Media / News",
                "Human-centered operational news covering community, events, sports, culture, creators, businesses, weather, transport, and safe awareness.",
                "OAP owned-media direction",
                "Research"
            ),
            (
                "SIKA trust ledger readiness",
                "Finance / Ledger",
                "Future SIKA should start as contribution/trust records and loyalty-style points, not legal tender, e-money, or bank claims.",
                "OAP compliance direction",
                "Delayed"
            ),
        ]

        db = get_db()
        db.executemany(
            """
            INSERT INTO research_topics (title, category, summary, source_note, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            seed_topics
        )

        seed_risks = [
            (None, "Fake claim risk", "High", "Calling early checklist or research tools full AI autonomy could mislead users.", "Use honest labels: Research Kernel, Checklist Planner, HRM Seed."),
            (None, "Financial risk", "High", "Banking, wallet, payment, legal tender, or investment claims could trigger serious legal duties.", "Delay public bank claims; record trust/contribution only until compliant route exists."),
            (None, "Privacy risk", "High", "Research logs may accidentally store private or sensitive information.", "Keep local-first, minimal data, no unnecessary private data, export/delete controls later."),
            (None, "Overbuilding risk", "Medium", "Trying to build agents, wallets, robotics, and media all at once can stop launch.", "Build small: Research Kernel, Command Core, creator/business/event layer first."),
            (None, "Autonomy risk", "High", "Automation without approval can cause harm, mistakes, or legal exposure.", "Human approval before action. Audit before automation."),
        ]

        db.executemany(
            """
            INSERT INTO risk_register (topic_id, risk_type, risk_level, description, mitigation)
            VALUES (?, ?, ?, ?, ?)
            """,
            seed_risks
        )

        seed_decisions = [
            (
                "Adopt research has no ceiling, deployment has boundaries",
                "OAP can study all areas deeply, but real actions require safety, legality, privacy, audit, and human approval.",
                "This protects ambition while preventing unsafe deployment.",
                "Rejected: unrestricted deployment, fake autonomy, uncontrolled AI actions.",
                "Approved"
            ),
            (
                "Delay wallet/banking claims",
                "SIKA and bank-style systems stay roadmap-only until trust records, compliance readiness, and proper authorization exist.",
                "Prevents legal and reputation risk.",
                "Rejected: public licensed bank claims before authorization.",
                "Approved"
            ),
        ]

        db.executemany(
            """
            INSERT INTO decision_log (title, decision, reason, rejected_options, approval_status)
            VALUES (?, ?, ?, ?, ?)
            """,
            seed_decisions
        )

        seed_predictions = [
            (
                "World Cup and major event energy can drive OAP creator, business, media, and community engagement.",
                "Sports/events create natural attention, local gatherings, content, business promotion, and creator activity.",
                "2026-07-31",
                "Not reviewed yet",
                "Medium"
            ),
            (
                "Local-first audit logs will become the base for future HRM learning.",
                "Real records create proof, feedback, mistakes, fixes, and safer AI memory.",
                "2026-08-31",
                "Not reviewed yet",
                "Medium"
            ),
        ]

        db.executemany(
            """
            INSERT INTO prediction_log (prediction, reason, expected_date, result, confidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            seed_predictions
        )

        seed_experiments = [
            (
                "Research Kernel test",
                "Use this app to record 10 AI research topics, 5 risks, 3 decisions, and 3 predictions.",
                "No real-world action. No private data. No deployment automation.",
                "",
                "Planned"
            )
        ]

        db.executemany(
            """
            INSERT INTO experiments (title, purpose, safety_limit, result, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            seed_experiments
        )

        db.execute(
            "INSERT INTO audit_log (action, details) VALUES (?, ?)",
            ("SEED_DATA_CREATED", "Starter OAP AI Research Kernel data inserted")
        )

        db.commit()
        flash("Seed data created.")
    else:
        flash("Seed data already exists. No duplicate seed added.")

    return redirect(url_for("index"))


# ============================================================
# DELETE
# ============================================================

ALLOWED_DELETE_TABLES = {
    "research_topics",
    "risk_register",
    "decision_log",
    "prediction_log",
    "experiments",
}


@app.route("/delete/<table>/<int:item_id>", methods=["POST"])
def delete_item(table, item_id):
    if table not in ALLOWED_DELETE_TABLES:
        flash("Delete blocked: table not allowed.")
        return redirect(url_for("index"))

    execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
    audit("ITEM_DELETED", f"{table} id={item_id}")
    flash("Item deleted.")
    return redirect(request.referrer or url_for("index"))


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    with app.app_context():
        init_db()

    host = os.environ.get("OAP_HOST", "127.0.0.1")
    port = int(os.environ.get("OAP_PORT", "5001"))
    debug = os.environ.get("OAP_DEBUG", "false").lower() == "true"

    print("")
    print("==============================================")
    print(f"{APP_NAME}")
    print("Research has no ceiling. Deployment has boundaries.")
    print(f"Open: http://{host}:{port}")
    print("==============================================")
    print("")

    app.run(host=host, port=port, debug=debug)
