from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_5013_secret"
DB = "oap_5013_field.db"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS field_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        postcode TEXT,
        area TEXT,
        weather_note TEXT,
        map_note TEXT,
        navigation_note TEXT,
        risk_level TEXT,
        action_status TEXT,
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
<title>OAP Field Infrastructure Core</title>
<style>
body{margin:0;font-family:Arial;background:#07110b;color:#f5fff7}
header{padding:22px;background:#0d1f14;border-bottom:1px solid #1f4d2e}
nav a{color:#b8ffc8;margin-right:12px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:950px;margin:auto}
.card{background:#102417;border:1px solid #275b36;border-radius:18px;padding:18px;margin:14px 0}
input,textarea,select,button{width:100%;padding:13px;margin:7px 0;border-radius:12px;border:0}
button{background:#21c45a;color:#031006;font-weight:bold}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}
.badge{display:inline-block;padding:7px 10px;border-radius:20px;background:#183b25;margin:4px}
.small{opacity:.78;font-size:13px}
</style>
</head>
<body>
<header>
<h1>🌦️ 5013 Field Infrastructure Core</h1>
<nav>
<a href="/">Gateway</a>
<a href="/weather">Weather</a>
<a href="/maps">Maps</a>
<a href="/navigation">Navigation</a>
<a href="/field-log">Field Log</a>
<a href="/records">Records</a>
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
    <h2>🛰️ OAP Weather / Maps / Navigation</h2>
    <p>Field Infrastructure Core for postcode operations, events, riders, local safety, and route planning.</p>
    <div class="grid">
      <div class="card"><h3>🌦️ Weather</h3><p>Manual weather notes now. API later.</p></div>
      <div class="card"><h3>🗺️ Maps</h3><p>Area records, postcode notes, local zones.</p></div>
      <div class="card"><h3>🧭 Navigation</h3><p>Route instructions, risk notes, field movement.</p></div>
      <div class="card"><h3>🧠 HRM Ready</h3><p>Every record teaches the system later.</p></div>
    </div>
    </div>
    """)

@app.route("/weather")
def weather():
    return page("""
    <div class="card">
    <h2>🌦️ Weather Core</h2>
    <p>Use this for local field readiness before events, deliveries, markets, and community operations.</p>
    <span class="badge">Rain risk</span>
    <span class="badge">Wind risk</span>
    <span class="badge">Heat/cold</span>
    <span class="badge">Travel delay</span>
    <p class="small">Live weather API comes later. For now, record verified human notes.</p>
    </div>
    """)

@app.route("/maps")
def maps():
    return page("""
    <div class="card">
    <h2>🗺️ Maps Core</h2>
    <p>Postcode → Borough → County/Region → Country → Continent → Global.</p>
    <p>Use this to record useful local knowledge: safe meeting points, business areas, event zones, pickup zones, and no-go risk areas.</p>
    </div>
    """)

@app.route("/navigation")
def navigation():
    return page("""
    <div class="card">
    <h2>🧭 Navigation Core</h2>
    <p>Navigation is for lawful movement, event support, rider planning, and field coordination.</p>
    <p>No surveillance. No stalking. No unsafe routing. Human approval before real-world action.</p>
    </div>
    """)

@app.route("/field-log", methods=["GET","POST"])
def field_log():
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO field_logs
        (title, postcode, area, weather_note, map_note, navigation_note, risk_level, action_status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)""", (
            request.form.get("title",""),
            request.form.get("postcode",""),
            request.form.get("area",""),
            request.form.get("weather_note",""),
            request.form.get("map_note",""),
            request.form.get("navigation_note",""),
            request.form.get("risk_level","Low"),
            request.form.get("action_status","Recorded"),
            now()
        ))
        conn.commit()
        conn.close()
        return redirect("/records")

    return page("""
    <div class="card">
    <h2>📝 New Field Log</h2>
    <form method="post">
      <input name="title" placeholder="Title e.g. Mitcham event route check" required>
      <input name="postcode" placeholder="Postcode">
      <input name="area" placeholder="Area / Borough / Country">
      <textarea name="weather_note" placeholder="Weather note"></textarea>
      <textarea name="map_note" placeholder="Map / local zone note"></textarea>
      <textarea name="navigation_note" placeholder="Navigation / route note"></textarea>
      <select name="risk_level">
        <option>Low</option>
        <option>Medium</option>
        <option>High</option>
      </select>
      <select name="action_status">
        <option>Recorded</option>
        <option>Needs Review</option>
        <option>Approved</option>
        <option>Rejected</option>
      </select>
      <button>Save Field Record</button>
    </form>
    </div>
    """)

@app.route("/records")
def records():
    conn = db()
    rows = conn.execute("SELECT * FROM field_logs ORDER BY id DESC").fetchall()
    conn.close()

    html = "<div class='card'><h2>📚 Field Records</h2>"
    if not rows:
        html += "<p>No records yet.</p>"
    for r in rows:
        html += f"""
        <div class='card'>
        <h3>#{r['id']} {r['title']}</h3>
        <p><b>Postcode:</b> {r['postcode']} | <b>Area:</b> {r['area']}</p>
        <p><b>Weather:</b> {r['weather_note']}</p>
        <p><b>Map:</b> {r['map_note']}</p>
        <p><b>Navigation:</b> {r['navigation_note']}</p>
        <p><b>Risk:</b> {r['risk_level']} | <b>Status:</b> {r['action_status']}</p>
        <p class='small'>{r['created_at']}</p>
        </div>
        """
    html += "</div>"
    return page(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=False)
