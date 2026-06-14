from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_experiences_v1"
DB = "oap_world.db"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def qcount(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

def total_value(conn):
    return round(conn.execute("SELECT COALESCE(SUM(amount),0) FROM value_created").fetchone()[0], 2)

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS oap_experiences(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        experience_type TEXT,
        host_name TEXT,
        location TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        experience_date TEXT,
        status TEXT,
        ticket_value REAL,
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

BASE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Experiences</title>
<style>
body{margin:0;font-family:Arial;background:#07110b;color:#f5fff7}
header{padding:22px;background:#0d1f14;border-bottom:1px solid #1f4d2e}
nav a{color:#b8ffc8;margin-right:10px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:1120px;margin:auto}
.card{background:#102417;border:1px solid #275b36;border-radius:18px;padding:18px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
input,textarea,select,button{width:100%;padding:13px;margin:7px 0;border-radius:12px;border:0}
button{background:#21c45a;color:#031006;font-weight:bold}
.badge{display:inline-block;background:#183b25;color:#b8ffc8;padding:7px 10px;border-radius:20px;margin:4px}
.big{font-size:34px;font-weight:bold;color:#ffd76b}
.gold{color:#ffd76b}.green{color:#9dffb3}.red{color:#ff8d8d}.small{opacity:.75;font-size:13px}
.exp{background:#1b1425;border-color:#8b5cf6}
</style>
</head>
<body>
<header>
<h1>🎪 OAP Experiences</h1>
<nav>
<a href="/">Home</a>
<a href="/experiences">Experiences</a>
<a href="/add-experience">Add Experience</a>
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

@app.route("/")
def home():
    return page("""
    <div class="card exp">
    <h2>🎪 OAP Experiences</h2>
    <p>Experiences create real activity. Activity creates members, businesses, creators, proof, and Value Created.</p>
    </div>

    <div class="grid">
      <div class="card"><h3>⚽ Watch Party</h3><p>Sports, World Cup, AFCON, boxing.</p></div>
      <div class="card"><h3>🎵 Music Night</h3><p>OAP Media, artists, culture.</p></div>
      <div class="card"><h3>🏪 Business Showcase</h3><p>Local businesses and market stalls.</p></div>
      <div class="card"><h3>🎨 Creator Meetup</h3><p>Creators, artists, comedy, fashion.</p></div>
      <div class="card"><h3>🎓 Learning Session</h3><p>Skills, youth-safe education, workshops.</p></div>
      <div class="card"><h3>🌳 Community Day</h3><p>Roots, family, people, local unity.</p></div>
    </div>
    """)

@app.route("/experiences")
def experiences():
    conn = db()
    rows = conn.execute("SELECT * FROM oap_experiences ORDER BY id DESC").fetchall()
    conn.close()

    html = "<div class='card exp'><h2>🎪 OAP Experiences</h2>"
    html += "<p><a class='badge' href='/add-experience'>Add OAP Experience</a></p>"
    if not rows:
        html += "<p>No OAP Experiences recorded yet.</p>"
    for r in rows:
        html += f"""
        <div class="card">
        <h3>{r['title']}</h3>
        <p><span class="badge">{r['experience_type']}</span> <span class="badge">{r['status']}</span> <span class="badge">£{r['ticket_value']}</span></p>
        <p><b>Host:</b> {r['host_name']}</p>
        <p><b>Where:</b> {r['location']} — {r['postcode']} → {r['borough']} → {r['country']}</p>
        <p><b>Date:</b> {r['experience_date']}</p>
        <p>{r['description']}</p>
        <p class="small">{r['created_at']}</p>
        </div>
        """
    html += "</div>"
    return page(html)

@app.route("/add-experience", methods=["GET","POST"])
def add_experience():
    if request.method == "POST":
        ticket_value = float(request.form["ticket_value"] or 0)

        conn = db()
        conn.execute("""INSERT INTO oap_experiences
        (title, experience_type, host_name, location, postcode, borough, country, experience_date, status, ticket_value, description, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            request.form["title"],
            request.form["experience_type"],
            request.form["host_name"],
            request.form["location"],
            request.form["postcode"],
            request.form["borough"],
            request.form["country"],
            request.form["experience_date"],
            request.form["status"],
            ticket_value,
            request.form["description"],
            now()
        ))

        conn.execute("""INSERT INTO proof_of_contribution
        (member_name, contribution_type, proof_note, status, created_at)
        VALUES (?,?,?,?,?)""", (
            request.form["host_name"],
            "OAP Experience",
            f"Hosted/created experience: {request.form['title']}",
            "Contribution Recorded",
            now()
        ))

        if ticket_value > 0:
            conn.execute("""INSERT INTO value_created(source, amount, note, created_at)
            VALUES (?,?,?,?)""", (
                "OAP Experience",
                ticket_value,
                f"{request.form['title']} recorded ticket/value signal",
                now()
            ))

        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return page("""
    <div class="card exp">
    <h2>🎪 Add OAP Experience</h2>
    <form method="post">
    <input name="title" placeholder="Experience title" required>
    <select name="experience_type">
      <option>Watch Party</option>
      <option>Music Night</option>
      <option>Comedy Night</option>
      <option>Business Showcase</option>
      <option>Creator Meetup</option>
      <option>Learning Session</option>
      <option>Community Day</option>
      <option>OAP Awards</option>
    </select>
    <input name="host_name" placeholder="Host / organiser / creator / business">
    <input name="location" placeholder="Location">
    <input name="postcode" placeholder="Postcode">
    <input name="borough" placeholder="Borough">
    <input name="country" placeholder="Country">
    <input name="experience_date" placeholder="Date / time">
    <select name="status">
      <option>Planned</option>
      <option>Open</option>
      <option>Completed</option>
      <option>Paused</option>
    </select>
    <input name="ticket_value" placeholder="Value created / ticket value e.g. 5.00">
    <textarea name="description" placeholder="Experience description / proof note"></textarea>
    <button>Record OAP Experience</button>
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
        html += "<p>No proof records yet.</p>"
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
    for r in rows:
        html += f"<div class='card'><p><span class='badge'>{r['source']}</span> £{r['amount']} — {r['note']}</p><p class='small'>{r['created_at']}</p></div>"
    return page(html)

@app.route("/dashboard")
def dashboard():
    conn = db()
    experiences_count = qcount(conn, "oap_experiences")
    proof_count = qcount(conn, "proof_of_contribution")
    value = total_value(conn)

    type_rows = conn.execute("""
        SELECT experience_type, COUNT(*) as count, COALESCE(SUM(ticket_value),0) as total
        FROM oap_experiences
        GROUP BY experience_type
    """).fetchall()
    conn.close()

    html = """
    <div class="card">
    <h2>👑 Sovereign Dashboard — OAP Experiences</h2>
    <div class="grid">
    """
    html += f"<div class='card'><div class='big'>{experiences_count}</div><p>OAP Experiences</p></div>"
    html += f"<div class='card'><div class='big'>{proof_count}</div><p>Proof of Contribution</p></div>"
    html += f"<div class='card'><div class='big'>£{value}</div><p>Value Created</p></div>"
    html += "</div></div>"

    html += "<div class='card'><h2>🚦 Signal Lights</h2>"
    html += f"<p class='{'green' if experiences_count else 'red'}'>{'✅' if experiences_count else '🔴'} First OAP Experience</p>"
    html += f"<p class='{'green' if value else 'red'}'>{'✅' if value else '🔴'} First Value Created</p>"
    html += "<p class='gold'>Next: operate this with one real experience, one business, one creator, one member.</p>"
    html += "</div>"

    html += "<div class='card'><h2>🎪 Experience Breakdown</h2>"
    if not type_rows:
        html += "<p>No breakdown yet.</p>"
    for t in type_rows:
        html += f"<p><span class='badge'>{t['experience_type']}</span> {t['count']} experience(s) — £{t['total']} value</p>"
    html += "</div>"

    return page(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
