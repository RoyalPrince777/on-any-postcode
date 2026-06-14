from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_5014_secret"
DB = "oap_5014_ai_council.db"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS council_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mission TEXT,
        selected_role TEXT,
        decision TEXT,
        risk_level TEXT,
        human_approval TEXT,
        notes TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

COUNCIL = {
    "GPT Architect": "Architecture, orchestration, system design",
    "Claude Chancellor": "Privacy, governance, safety, policy",
    "Gemini Archivist": "Memory, long context, ecosystem review",
    "Kimi Expansion": "Deep decomposition, scaling, roadmap",
    "Grok Challenger": "Stress-test, objections, rapid challenge",
    "HRM Record Keeper": "Logs, lessons, audit, memory review",
    "Sovereign Veto": "Final human approval before real-world action"
}

ANIMAL_TEAM = {
    "Bee": "Coordination",
    "Gorilla": "Protection",
    "Lion": "Leadership",
    "Tiger": "Focus",
    "Panther": "Adaptation",
    "Eagle": "Vision",
    "Falcon": "Speed",
    "Elephant": "Memory",
    "Owl": "Wisdom",
    "Dolphin": "Communication",
    "Horse": "Movement",
    "Stag": "Balance"
}

def route_mission(text):
    t = (text or "").lower()
    if any(x in t for x in ["privacy", "risk", "law", "policy", "governance", "safety"]):
        return "Claude Chancellor"
    if any(x in t for x in ["memory", "history", "record", "archive", "learn", "logs", "audit"]):
        return "HRM Record Keeper"
    if any(x in t for x in ["scale", "expand", "roadmap", "growth", "future"]):
        return "Kimi Expansion"
    if any(x in t for x in ["stress", "test", "weakness", "threat", "challenge"]):
        return "Grok Challenger"
    if any(x in t for x in ["long context", "ecosystem", "research"]):
        return "Gemini Archivist"
    return "GPT Architect"

def animal_signal(text):
    t = (text or "").lower()
    if any(x in t for x in ["coordinate", "event", "people", "task", "community"]):
        return "Bee"
    if any(x in t for x in ["protect", "security", "safe", "guard"]):
        return "Gorilla"
    if any(x in t for x in ["lead", "command", "decision"]):
        return "Lion"
    if any(x in t for x in ["focus", "priority", "single"]):
        return "Tiger"
    if any(x in t for x in ["adapt", "change", "pivot"]):
        return "Panther"
    if any(x in t for x in ["vision", "future", "overview"]):
        return "Eagle"
    if any(x in t for x in ["fast", "urgent", "speed"]):
        return "Falcon"
    if any(x in t for x in ["memory", "record", "history"]):
        return "Elephant"
    if any(x in t for x in ["wisdom", "judge", "truth"]):
        return "Owl"
    if any(x in t for x in ["message", "chat", "communication"]):
        return "Dolphin"
    if any(x in t for x in ["move", "route", "field", "runner"]):
        return "Horse"
    return "Stag"

BASE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP AI Router / Council Service</title>
<style>
body{margin:0;font-family:Arial;background:#080d14;color:#f5f9ff}
header{padding:22px;background:#101a28;border-bottom:1px solid #283d5c}
nav a{color:#b8d8ff;margin-right:12px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:960px;margin:auto}
.card{background:#111b2a;border:1px solid #2d4568;border-radius:18px;padding:18px;margin:14px 0}
input,textarea,select,button{width:100%;padding:13px;margin:7px 0;border-radius:12px;border:0}
button{background:#4aa3ff;color:#04101d;font-weight:bold}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.badge{display:inline-block;background:#19365a;padding:7px 10px;border-radius:20px;margin:4px}
.small{opacity:.75;font-size:13px}
.warn{background:#2a1c11;border-color:#65451f}
.green{background:#102417;border-color:#275b36}
</style>
</head>
<body>
<header>
<h1>🤖 5014 AI Router / Council Service</h1>
<nav>
<a href="/">Gateway</a>
<a href="/council">Council</a>
<a href="/animals">Animal Team</a>
<a href="/new">New Mission</a>
<a href="/logs">Logs</a>
<a href="/rules">Rules</a>
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
    <h2>👑 OAP AI Council Router</h2>
    <p>Mission → Route → Animal Signal → Review → Record → Human Approval.</p>
    <p>Bee belongs officially to Animal Team. In this service, Bee appears only as the coordination bridge.</p>
    </div>
    """)

@app.route("/council")
def council():
    html = "<div class='card'><h2>🏛️ AI Council Roles</h2>"
    for name, role in COUNCIL.items():
        html += f"<p><span class='badge'>{name}</span> {role}</p>"
    html += "</div>"
    return page(html)

@app.route("/animals")
def animals():
    html = "<div class='card green'><h2>🐝 Animal Team</h2>"
    html += "<p>Official symbolic operating roles for OAP movement, coordination, protection, memory, communication, and balance.</p>"
    for name, role in ANIMAL_TEAM.items():
        html += f"<p><span class='badge'>{name}</span> {role}</p>"
    html += "<p><b>Bee Law:</b> Connect people, coordinate fairly, share knowledge, strengthen community, create value, protect the hive, leave things better than you found them.</p>"
    html += "</div>"
    return page(html)

@app.route("/new", methods=["GET","POST"])
def new():
    if request.method == "POST":
        mission = request.form.get("mission","")
        selected = route_mission(mission)
        animal = animal_signal(mission)
        decision = f"Council route: {selected}. Animal signal: {animal} = {ANIMAL_TEAM[animal]}. Record first. Verify before build. Human approval required before real-world action."
        conn = db()
        conn.execute("""INSERT INTO council_logs
        (mission, selected_role, decision, risk_level, human_approval, notes, created_at)
        VALUES (?,?,?,?,?,?,?)""", (
            mission,
            selected,
            decision,
            request.form.get("risk_level","Medium"),
            request.form.get("human_approval","Pending"),
            request.form.get("notes",""),
            now()
        ))
        conn.commit()
        conn.close()
        return redirect("/logs")

    return page("""
    <div class="card">
    <h2>📝 New Council Mission</h2>
    <form method="post">
      <textarea name="mission" placeholder="Mission / problem / build task" required></textarea>
      <select name="risk_level">
        <option>Low</option>
        <option selected>Medium</option>
        <option>High</option>
        <option>Restricted</option>
      </select>
      <select name="human_approval">
        <option selected>Pending</option>
        <option>Approved</option>
        <option>Rejected</option>
      </select>
      <textarea name="notes" placeholder="Notes, proof, limits, next step"></textarea>
      <button>Route Mission</button>
    </form>
    </div>
    """)

@app.route("/logs")
def logs():
    conn = db()
    rows = conn.execute("SELECT * FROM council_logs ORDER BY id DESC").fetchall()
    conn.close()
    html = "<div class='card'><h2>📚 Council Logs</h2>"
    if not rows:
        html += "<p>No logs yet.</p>"
    for r in rows:
        html += f"""
        <div class='card'>
        <h3>#{r['id']} {r['selected_role']}</h3>
        <p><b>Mission:</b> {r['mission']}</p>
        <p><b>Decision:</b> {r['decision']}</p>
        <p><b>Risk:</b> {r['risk_level']} | <b>Human Approval:</b> {r['human_approval']}</p>
        <p><b>Notes:</b> {r['notes']}</p>
        <p class='small'>{r['created_at']}</p>
        </div>
        """
    html += "</div>"
    return page(html)

@app.route("/rules")
def rules():
    return page("""
    <div class="card warn">
    <h2>🛡️ Council Laws</h2>
    <p>Record → Verify → Build.</p>
    <p>No memory = no intelligence.</p>
    <p>No verification = no trust.</p>
    <p>No audit = no automation.</p>
    <p>No human approval = no real-world action.</p>
    <p>AI suggests. HRM records. Council reviews. Animal Team signals. User approves.</p>
    </div>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5014, debug=False)
