from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "oap_world.db"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def clean_username(username):
    return username.lower().strip().replace(" ", "").replace("@", "")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        personal_email TEXT,
        oap_email TEXT UNIQUE,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        continent TEXT,
        tier TEXT DEFAULT 'Community Member',
        status TEXT DEFAULT 'Active',
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
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.metric{background:#061009;border:1px solid #347a4d;border-radius:18px;padding:16px;text-align:center}
.metric h2{margin:0;color:#8dffb0;font-size:34px}
input,select,textarea{width:100%;padding:13px;margin:8px 0;border-radius:12px;border:1px solid #347a4d;background:#061009;color:white;box-sizing:border-box}
button{width:100%;padding:14px;border:0;border-radius:12px;background:#31d36b;color:#041007;font-weight:bold;font-size:16px}
.tag{display:inline-block;padding:5px 9px;border-radius:999px;background:#244b32;color:#b8ffd0;font-size:13px}
.email{font-size:20px;color:#8dffb0;font-weight:bold}
</style>
</head>
<body>
<header>
<h2>🌍 ON ANY POSTCODE</h2>
<div class="nav">
<a href="/">Home</a>
<a href="/join-oap">🌍 Join OAP</a>
<a href="/members">👤 Members</a>
<a href="/mail-list">📧 OAP Mail</a>
<a href="/value">💚 Value</a>
</div>
</header>
<div class="wrap">{{ body|safe }}</div>
</body>
</html>
""", title=title, body=body)

@app.route("/")
def home():
    conn = db()
    members = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    free = conn.execute("SELECT COUNT(*) FROM members WHERE tier='Community Member'").fetchone()[0]
    founders = conn.execute("SELECT COUNT(*) FROM members WHERE tier!='Community Member'").fetchone()[0]
    values = conn.execute("SELECT COUNT(*) FROM value_records").fetchone()[0]
    conn.close()

    body = f"""
<div class="card">
<h1>🚀 OAP Member Launch</h1>
<p>Join OAP. Enter My World. Get your OAP identity.</p>
</div>

<div class="grid">
<div class="metric"><h2>{members}</h2><p>Total Members</p></div>
<div class="metric"><h2>{free}</h2><p>Community Members</p></div>
<div class="metric"><h2>{founders}</h2><p>Founders / Paid Tiers</p></div>
<div class="metric"><h2>{values}</h2><p>Value Records</p></div>
</div>

<div class="card">
<p><a href="/join-oap">🌍 Join OAP Now</a></p>
<p><a href="/members">👤 View Members</a></p>
<p><a href="/mail-list">📧 View OAP Email Identities</a></p>
</div>
"""
    return layout("OAP Member Launch", body)

@app.route("/join-oap", methods=["GET", "POST"])
def join_oap():
    error = ""

    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()
        username = clean_username(request.form.get("username", ""))
        password = request.form.get("password", "").strip()
        personal_email = request.form.get("personal_email", "").strip()
        postcode = request.form.get("postcode", "").strip()
        borough = request.form.get("borough", "").strip()
        country = request.form.get("country", "").strip()
        continent = request.form.get("continent", "").strip()
        tier = request.form.get("tier", "Community Member").strip()

        if nickname and username and password:
            oap_email = username + "@oap.world"

            try:
                conn = db()
                conn.execute("""
                INSERT INTO members
                (nickname, username, password, personal_email, oap_email, postcode, borough, country, continent, tier, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nickname, username, password, personal_email, oap_email,
                    postcode, borough, country, continent, tier, "Active", now()
                ))

                amount = "£0"
                if tier == "Postcode Founder":
                    amount = "£5"
                elif tier == "Borough Builder":
                    amount = "£10"
                elif tier == "Country Champion":
                    amount = "£25"

                conn.execute("""
                INSERT INTO value_records
                (title, value_type, amount, proof_note, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    "New OAP Member: " + nickname,
                    tier,
                    amount,
                    "OAP email identity created: " + oap_email,
                    now()
                ))

                conn.commit()
                conn.close()

                return redirect(url_for("my_world", username=username))

            except sqlite3.IntegrityError:
                error = "Username already taken. Choose another username."

    body = f"""
<div class="card">
<h1>🌍 Join OAP</h1>
<p>Create your OAP identity. Email is optional for now. Your OAP address is reserved automatically.</p>
<p style="color:#ffb3b3;">{error}</p>

<form method="POST">
<label>Nickname</label>
<input name="nickname" placeholder="Example: Prince Lloyd">

<label>Username</label>
<input name="username" placeholder="example: earthisourturf777">

<label>Password</label>
<input name="password" type="password" placeholder="Create password">

<label>Personal Email Optional</label>
<input name="personal_email" placeholder="example@gmail.com">

<label>Postcode</label>
<input name="postcode" placeholder="Example: SW16">

<label>Borough</label>
<input name="borough" placeholder="Example: Mitcham / Lambeth / Croydon">

<label>Country</label>
<input name="country" placeholder="Example: UK / Ghana">

<label>Continent</label>
<input name="continent" placeholder="Example: Europe / Africa">

<label>OAP Circle Tier</label>
<select name="tier">
<option>Community Member</option>
<option>Postcode Founder</option>
<option>Borough Builder</option>
<option>Country Champion</option>
</select>

<button type="submit">Join OAP</button>
</form>
</div>
"""
    return layout("Join OAP", body)

@app.route("/my-world/<username>")
def my_world(username):
    conn = db()
    member = conn.execute("SELECT * FROM members WHERE username=?", (username,)).fetchone()
    conn.close()

    if not member:
        return redirect(url_for("join_oap"))

    body = f"""
<div class="card">
<h1>👤 My World</h1>
<span class="tag">{member['tier']}</span>
<span class="tag">{member['status']}</span>
<h2>{member['nickname']}</h2>
<p>@{member['username']}</p>
<p class="email">📧 {member['oap_email']}</p>
<p><b>Personal Email:</b> {member['personal_email'] or 'Not added'}</p>
<p><b>Area:</b> {member['postcode'] or ''} {member['borough'] or ''} {member['country'] or ''} {member['continent'] or ''}</p>
</div>

<div class="card">
<h2>🚦 Launch Actions</h2>
<p><a href="/join-oap">Invite another member</a></p>
<p><a href="/members">View all members</a></p>
<p><a href="/value">Record value created</a></p>
</div>
"""
    return layout("My World", body)

@app.route("/members")
def members():
    conn = db()
    rows = conn.execute("SELECT * FROM members ORDER BY id DESC").fetchall()
    conn.close()

    cards = ""
    for m in rows:
        cards += f"""
<div class="card">
<span class="tag">{m['tier']}</span>
<span class="tag">{m['status']}</span>
<h3>{m['nickname']}</h3>
<p>@{m['username']}</p>
<p class="email">📧 {m['oap_email']}</p>
<p>{m['postcode'] or ''} {m['borough'] or ''} {m['country'] or ''} {m['continent'] or ''}</p>
<p><a href="/my-world/{m['username']}">Enter My World</a></p>
</div>
"""

    if cards == "":
        cards = "<div class='card'><p>No members yet. Add first member now.</p></div>"

    body = f"""
<div class="card">
<h1>👤 OAP Members</h1>
<p>Every member has a World.</p>
<p><a href="/join-oap">🌍 Join OAP</a></p>
</div>
{cards}
"""
    return layout("Members", body)

@app.route("/mail-list")
def mail_list():
    conn = db()
    rows = conn.execute("SELECT nickname, username, oap_email, personal_email, tier FROM members ORDER BY id DESC").fetchall()
    conn.close()

    cards = ""
    for r in rows:
        cards += f"""
<div class="card">
<span class="tag">{r['tier']}</span>
<h3>{r['nickname']}</h3>
<p class="email">📧 {r['oap_email']}</p>
<p><b>Forward later to:</b> {r['personal_email'] or 'No forwarding email yet'}</p>
</div>
"""

    if cards == "":
        cards = "<div class='card'><p>No OAP email identities yet.</p></div>"

    body = f"""
<div class="card">
<h1>📧 OAP Mail Identity List</h1>
<p>This reserves future member addresses like username@oap.world. This is identity first, not full mail server yet.</p>
</div>
{cards}
"""
    return layout("OAP Mail", body)

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
<h1>💚 Value Created</h1>
<form method="POST">
<input name="title" placeholder="Example: First Founder joined">
<select name="value_type">
<option>Community Member</option>
<option>Founder</option>
<option>Business</option>
<option>Creator</option>
<option>Experience</option>
<option>Sale</option>
<option>OAP Mail</option>
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
