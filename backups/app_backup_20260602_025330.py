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
    CREATE TABLE IF NOT EXISTS real_people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT,
        contact TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        status TEXT DEFAULT 'Invited',
        note TEXT,
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
body{margin:0;font-family:Arial;background:#07130d;color:#f4fff7}
header{padding:18px;background:#0d2417;border-bottom:1px solid #1f5c38}
.wrap{padding:18px;max-width:1000px;margin:auto}
a{color:#6fffa8;text-decoration:none;font-weight:bold}
.nav a{display:inline-block;margin:6px 8px 6px 0;padding:10px 12px;background:#163923;border-radius:12px}
.card{background:#10261a;border:1px solid #245c3b;border-radius:18px;padding:16px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.metric{background:#061009;border:1px solid #347a4d;border-radius:18px;padding:16px;text-align:center}
.metric h2{margin:0;color:#8dffb0;font-size:34px}
input,select,textarea{width:100%;padding:13px;margin:8px 0;border-radius:12px;border:1px solid #347a4d;background:#061009;color:white;box-sizing:border-box}
button{width:100%;padding:14px;border:0;border-radius:12px;background:#31d36b;color:#041007;font-weight:bold;font-size:16px}
.tag{display:inline-block;padding:5px 9px;border-radius:999px;background:#244b32;color:#b8ffd0;font-size:13px}
</style>
</head>
<body>
<header>
<h2>🌍 ON ANY POSTCODE</h2>
<div class="nav">
<a href="/">Home</a>
<a href="/real-people">🤝 Real People</a>
<a href="/invite-person">➕ Invite</a>
<a href="/value">💚 Value</a>
</div>
</header>
<div class="wrap">{{ body|safe }}</div>
</body>
</html>
""", title=title, body=body)

def count_role(role):
    conn = db()
    n = conn.execute("SELECT COUNT(*) FROM real_people WHERE role=?", (role,)).fetchone()[0]
    conn.close()
    return n

@app.route("/")
def home():
    conn = db()
    values = conn.execute("SELECT COUNT(*) FROM value_records").fetchone()[0]
    conn.close()

    body = f"""
<div class="card">
<h1>🚀 OAP Real People Launch</h1>
<p>Goal: 1 Community Member, 1 Founder, 1 Business, 1 Creator, 1 Experience, 1 Value Record.</p>
</div>

<div class="grid">
<div class="metric"><h2>{count_role('Community Member')}</h2><p>Community Members</p></div>
<div class="metric"><h2>{count_role('Founder')}</h2><p>Founders</p></div>
<div class="metric"><h2>{count_role('Business')}</h2><p>Businesses</p></div>
<div class="metric"><h2>{count_role('Creator')}</h2><p>Creators</p></div>
<div class="metric"><h2>{count_role('Experience Lead')}</h2><p>Experience Leads</p></div>
<div class="metric"><h2>{values}</h2><p>Value Records</p></div>
</div>

<div class="card">
<p><a href="/invite-person">➕ Invite Real Person Now</a></p>
<p><a href="/real-people">🤝 View Real People Board</a></p>
<p><a href="/value">💚 Record Value Created</a></p>
</div>
"""
    return layout("OAP Launch", body)

@app.route("/invite-person", methods=["GET", "POST"])
def invite_person():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        contact = request.form.get("contact", "").strip()
        postcode = request.form.get("postcode", "").strip()
        borough = request.form.get("borough", "").strip()
        country = request.form.get("country", "").strip()
        note = request.form.get("note", "").strip()

        if name:
            conn = db()
            conn.execute("""
            INSERT INTO real_people
            (name, role, contact, postcode, borough, country, status, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, role, contact, postcode, borough, country, "Invited", note, now()))
            conn.commit()
            conn.close()

        return redirect(url_for("real_people"))

    body = """
<div class="card">
<h1>➕ Invite Real Person</h1>
<form method="POST">
<label>Name / Nickname</label>
<input name="name" placeholder="Name">

<label>Role</label>
<select name="role">
<option>Community Member</option>
<option>Founder</option>
<option>Business</option>
<option>Creator</option>
<option>Experience Lead</option>
</select>

<label>Contact</label>
<input name="contact" placeholder="Phone / Instagram / email">

<label>Postcode</label>
<input name="postcode" placeholder="Postcode">

<label>Borough</label>
<input name="borough" placeholder="Borough">

<label>Country</label>
<input name="country" placeholder="Country">

<label>Note</label>
<textarea name="note" placeholder="Why invite them?"></textarea>

<button type="submit">Invite Person</button>
</form>
</div>
"""
    return layout("Invite", body)

@app.route("/real-people")
def real_people():
    conn = db()
    rows = conn.execute("SELECT * FROM real_people ORDER BY id DESC").fetchall()
    conn.close()

    cards = ""
    for r in rows:
        cards += f"""
<div class="card">
<span class="tag">{r['role']}</span>
<span class="tag">{r['status']}</span>
<h3>{r['name']}</h3>
<p><b>Contact:</b> {r['contact'] or ''}</p>
<p><b>Area:</b> {r['postcode'] or ''} {r['borough'] or ''} {r['country'] or ''}</p>
<p>{r['note'] or ''}</p>
<p>
<a href="/set-status/{r['id']}/Joined">Mark Joined</a> |
<a href="/set-status/{r['id']}/Value Created">Value Created</a> |
<a href="/set-status/{r['id']}/Follow Up">Follow Up</a>
</p>
</div>
"""

    if cards == "":
        cards = "<div class='card'><p>No real people yet. Invite the first person now.</p></div>"

    body = f"""
<div class="card">
<h1>🤝 Real People Board</h1>
<p>Stop building forever. Start inviting real people.</p>
<p><a href="/invite-person">➕ Invite Person</a></p>
</div>
{cards}
"""
    return layout("Real People", body)

@app.route("/set-status/<int:person_id>/<status>")
def set_status(person_id, status):
    conn = db()
    person = conn.execute("SELECT * FROM real_people WHERE id=?", (person_id,)).fetchone()

    if person:
        conn.execute("UPDATE real_people SET status=? WHERE id=?", (status, person_id))

        if status == "Value Created":
            conn.execute("""
            INSERT INTO value_records
            (title, value_type, amount, proof_note, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (
                "Value Created: " + person["name"],
                person["role"],
                "Manual / Proof",
                person["note"] or "Real person value created.",
                now()
            ))

    conn.commit()
    conn.close()
    return redirect(url_for("real_people"))

@app.route("/value", methods=["GET", "POST"])
def value():
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
            conn.commit()
            conn.close()

        return redirect(url_for("home"))

    conn = db()
    rows = conn.execute("SELECT * FROM value_records ORDER BY id DESC").fetchall()
    conn.close()

    cards = ""
    for r in rows:
        cards += f"""
<div class="card">
<span class="tag">{r['value_type']}</span>
<h3>{r['title']}</h3>
<p><b>Amount:</b> {r['amount'] or ''}</p>
<p>{r['proof_note'] or ''}</p>
</div>
"""

    body = f"""
<div class="card">
<h1>💚 Record Value Created</h1>
<form method="POST">
<input name="title" placeholder="Example: First Founder joined">
<select name="value_type">
<option>Community Member</option>
<option>Founder</option>
<option>Business</option>
<option>Creator</option>
<option>Experience</option>
<option>Sale</option>
</select>
<input name="amount" placeholder="£0 / £5 / £10 / £25">
<textarea name="proof_note" placeholder="Proof note"></textarea>
<button type="submit">Record Value</button>
</form>
</div>
{cards}
"""
    return layout("Value", body)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
