from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
ADMIN_USERNAME = "N24-7"
ADMIN_EMAIL = "earthisourturf777@gmail.com"
ADMIN_PASSWORD = "2525"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def h(x):
    return escape(str(x or ""))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def add_col(cur, table, col, typ):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")

def log(action, username="system"):
    conn = db()
    conn.execute("INSERT INTO audit_logs(action,username,created_at) VALUES(?,?,?)", (action, username, now()))
    conn.commit()
    conn.close()

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'member',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        event_type TEXT,
        category TEXT,
        city TEXT,
        country TEXT,
        event_date TEXT,
        event_time TEXT,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS event_attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        event_title TEXT,
        recorder TEXT,
        invited_count INTEGER DEFAULT 0,
        attended_count INTEGER DEFAULT 0,
        products_sold INTEGER DEFAULT 0,
        revenue TEXT DEFAULT '0',
        notes TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        recipient TEXT,
        subject TEXT,
        body TEXT,
        status TEXT DEFAULT 'unread',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sika_ledger(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        record_type TEXT,
        title TEXT,
        description TEXT,
        currency TEXT DEFAULT 'SIKA',
        amount TEXT DEFAULT '0',
        sika_points INTEGER DEFAULT 0,
        source TEXT,
        status TEXT DEFAULT 'pending',
        guardian_note TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sika_accounts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        display_name TEXT,
        sika_balance INTEGER DEFAULT 0,
        gbp_notes TEXT DEFAULT '0',
        ghs_notes TEXT DEFAULT '0',
        trust_level TEXT DEFAULT 'starter',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )""")

    cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,))
    user = cur.fetchone()
    if user:
        cur.execute("UPDATE users SET email=?, password=?, role=? WHERE username=?",
            (ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", ADMIN_USERNAME))
    else:
        cur.execute("INSERT INTO users(username,email,password,role,created_at) VALUES(?,?,?,?,?)",
            (ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", now()))

    cur.execute("SELECT id FROM sika_accounts WHERE username=?", (ADMIN_USERNAME,))
    account = cur.fetchone()
    if not account:
        cur.execute("""INSERT INTO sika_accounts(username,display_name,sika_balance,gbp_notes,ghs_notes,trust_level,created_at)
        VALUES(?,?,?,?,?,?,?)""", (ADMIN_USERNAME, "N24-7", 0, "0", "0", "founder", now()))

    conn.commit()
    conn.close()

init_db()

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#080808;color:white;font-family:Arial}
.top{background:#111;padding:15px;border-bottom:1px solid #222}
.logo{font-size:22px;font-weight:900}
.wrap{padding:18px;max-width:1100px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:18px;margin:15px 0}
.hero{text-align:center;padding:35px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:12px;margin:8px 0;background:#0c0c0c;color:white;border:1px solid #333;border-radius:10px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:10px;padding:12px 18px;font-weight:800}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:5px 9px;border-radius:999px;font-size:12px;font-weight:bold}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/sika">SIKA Ledger</a>
<a href="/sika_accounts">SIKA Accounts</a>
<a href="/events">Events</a>
<a href="/attendance">Attendance</a>
<a href="/messages">Messages</a>
<a href="/admin">Admin</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def ensure_sika_account(username):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM sika_accounts WHERE username=?", (username,))
    account = cur.fetchone()
    if not account:
        cur.execute("""INSERT INTO sika_accounts(username,display_name,sika_balance,gbp_notes,ghs_notes,trust_level,created_at)
        VALUES(?,?,?,?,?,?,?)""", (username, username, 0, "0", "0", "starter", now()))
        conn.commit()
    conn.close()

@app.route("/")
def home():
    conn = db()
    total_sika = conn.execute("SELECT COALESCE(SUM(sika_points),0) c FROM sika_ledger WHERE status='approved'").fetchone()["c"]
    pending = conn.execute("SELECT COUNT(*) c FROM sika_ledger WHERE status='pending'").fetchone()["c"]
    events_count = conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    attendance_count = conn.execute("SELECT COUNT(*) c FROM event_attendance").fetchone()["c"]
    messages_count = conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"]
    recent = conn.execute("SELECT * FROM sika_ledger ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = f"""
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>OAP v3.2 — SIKA Contribution Ledger</p>
    <p>GBP = UK pricing. GHS = Ghana layer. SIKA = contribution/trust points only.</p>
    </div>

    <div class='card red'>
    <b>Compliance Note:</b> SIKA is not legal tender, not e-money, not a bank account, not an investment product, and not automatic currency conversion.
    It is an internal contribution/trust record until proper regulated routes exist.
    </div>

    <div class='grid'>
    <div class='card'><h2>{total_sika}</h2><p>Approved SIKA Points</p></div>
    <div class='card'><h2>{pending}</h2><p>Pending Ledger Records</p></div>
    <div class='card'><h2>{events_count}</h2><p>Events</p></div>
    <div class='card'><h2>{attendance_count}</h2><p>Attendance Records</p></div>
    <div class='card'><h2>{messages_count}</h2><p>Messages</p></div>
    </div>

    <div class='card'>
    <h2>Currency Strategy</h2>
    <p><b>Start with:</b> GBP + GHS + SIKA.</p>
    <p><b>Do not connect all currencies yet.</b> That adds compliance, FX, payment, fraud and accounting complexity too early.</p>
    </div>

    <div class='card'><h2>Recent SIKA Records</h2>
    """
    for r in recent:
        content += f"""
        <div class='card'>
        <b>{h(r['title'])}</b><br>
        {h(r['username'])} • {h(r['record_type'])} • {h(r['currency'])} • {h(r['amount'])}<br>
        SIKA: {h(r['sika_points'])} • Status: {h(r['status'])}
        <p>{h(r['description'])}</p>
        </div>
        """
    content += "</div>"
    return render(content)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], request.form["password"]):
            session["user"] = user["username"]
            ensure_sika_account(user["username"])
            log("User login", user["username"])
            return redirect("/")
        return "Invalid login"

    return render("""
    <div class='card'><h2>Login</h2>
    <form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Login</button>
    </form>
    <p class='small'>Default local admin: N24-7 / 2525</p>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/sika", methods=["GET","POST"])
def sika():
    if request.method == "POST":
        username = request.form["username"].strip() or session.get("user", "guest")
        ensure_sika_account(username)

        conn = db()
        conn.execute("""INSERT INTO sika_ledger(username,record_type,title,description,currency,amount,sika_points,source,status,guardian_note,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (
            username,
            request.form["record_type"],
            request.form["title"],
            request.form["description"],
            request.form["currency"],
            request.form["amount"],
            int(request.form.get("sika_points") or 0),
            request.form["source"],
            "pending",
            request.form["guardian_note"],
            now()
        ))
        conn.commit()
        conn.close()
        log("SIKA record submitted", username)
        return redirect("/sika")

    conn = db()
    rows = conn.execute("SELECT * FROM sika_ledger ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>💚 SIKA Contribution Ledger</h1>
    <p class='green'>Records before wallet. Trust before finance.</p>
    </div>

    <div class='card red'>
    SIKA is internal contribution/trust points only. GBP and GHS are notes for pricing/reference records, not held money.
    </div>

    <div class='card'>
    <form method='POST'>
    <input name='username' placeholder='Username / contributor' value=''>
    <select name='record_type'>
    <option>Attendance</option>
    <option>Event Help</option>
    <option>Creator Work</option>
    <option>Business Lead</option>
    <option>Community Signal</option>
    <option>Product Sale Note</option>
    <option>Learning / Review</option>
    </select>
    <input name='title' placeholder='Record title' required>
    <textarea name='description' placeholder='What value was created?'></textarea>
    <select name='currency'>
    <option>SIKA</option>
    <option>GBP</option>
    <option>GHS</option>
    </select>
    <input name='amount' placeholder='Amount / note e.g. 0, £10, GH₵50'>
    <input name='sika_points' placeholder='SIKA points e.g. 10' value='0'>
    <input name='source' placeholder='Source e.g. event, review, attendance'>
    <textarea name='guardian_note' placeholder='Guardian / compliance note'></textarea>
    <button>Submit SIKA Record For Review</button>
    </form>
    </div>
    """

    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['title'])}</b><br>
        User: {h(r['username'])}<br>
        Type: {h(r['record_type'])}<br>
        Currency: {h(r['currency'])} • Amount: {h(r['amount'])} • SIKA: {h(r['sika_points'])}<br>
        Status: {h(r['status'])}
        <p>{h(r['description'])}</p>
        <p class='small'>{h(r['guardian_note'])}</p>
        </div>
        """

    return render(content)

@app.route("/sika_accounts")
def sika_accounts():
    conn = db()
    accounts = conn.execute("SELECT * FROM sika_accounts ORDER BY sika_balance DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>👑 SIKA Accounts</h1>
    <p class='green'>Contribution balances, not bank balances.</p>
    </div>
    """

    for a in accounts:
        content += f"""
        <div class='card'>
        <b>{h(a['display_name'])}</b> (@{h(a['username'])})<br>
        SIKA Balance: {h(a['sika_balance'])}<br>
        GBP Notes: {h(a['gbp_notes'])}<br>
        GHS Notes: {h(a['ghs_notes'])}<br>
        Trust Level: {h(a['trust_level'])}
        </div>
        """

    return render(content)

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO events(username,title,event_type,category,city,country,event_date,event_time,description,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (
            username,
            request.form["title"],
            request.form["event_type"],
            request.form["category"],
            request.form["city"],
            request.form["country"],
            request.form["event_date"],
            request.form["event_time"],
            request.form["description"],
            "pending",
            now()
        ))
        conn.commit()
        conn.close()
        log("Event submitted", username)
        return redirect("/events")

    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card'><h1>Events</h1>
    <form method='POST'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'><option>Watch Party</option><option>Community Event</option><option>Business Popup</option><option>Creator Meetup</option></select>
    <input name='category' value='Community'>
    <input name='city' placeholder='City'>
    <input name='country' value='UK'>
    <input name='event_date' placeholder='Date'>
    <input name='event_time' placeholder='Time'>
    <textarea name='description' placeholder='Description'></textarea>
    <button>Submit Event</button>
    </form></div>
    """

    for e in rows:
        content += f"""
        <div class='card'>
        <b>{h(e['title'])}</b><br>
        {h(e['event_type'])} • {h(e['category'])}<br>
        {h(e['city'])}, {h(e['country'])} • {h(e['event_date'])} {h(e['event_time'])}<br>
        Status: {h(e['status'])}
        </div>
        """
    return render(content)

@app.route("/attendance", methods=["GET","POST"])
def attendance():
    if request.method == "POST":
        recorder = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO event_attendance(event_id,event_title,recorder,invited_count,attended_count,products_sold,revenue,notes,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (
            request.form["event_id"],
            request.form["event_title"],
            recorder,
            int(request.form.get("invited_count") or 0),
            int(request.form.get("attended_count") or 0),
            int(request.form.get("products_sold") or 0),
            request.form["revenue"],
            request.form["notes"],
            now()
        ))
        conn.commit()
        conn.close()
        log("Attendance recorded", recorder)
        return redirect("/attendance")

    conn = db()
    rows = conn.execute("SELECT * FROM event_attendance ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card'><h1>Attendance</h1>
    <form method='POST'>
    <input name='event_id' placeholder='Event ID'>
    <input name='event_title' placeholder='Event title' required>
    <input name='invited_count' value='0'>
    <input name='attended_count' value='0'>
    <input name='products_sold' value='0'>
    <input name='revenue' placeholder='Revenue e.g. £0 / GH₵0'>
    <textarea name='notes' placeholder='Notes'></textarea>
    <button>Record Attendance</button>
    </form></div>
    """
    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['event_title'])}</b><br>
        Invited: {r['invited_count']} | Attended: {r['attended_count']} | Products: {r['products_sold']} | Revenue: {h(r['revenue'])}
        <p>{h(r['notes'])}</p>
        </div>
        """
    return render(content)

@app.route("/messages", methods=["GET","POST"])
def messages():
    if request.method == "POST":
        sender = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO messages(sender,recipient,subject,body,status,created_at)
        VALUES(?,?,?,?,?,?)""", (sender, request.form["recipient"], request.form["subject"], request.form["body"], "unread", now()))
        conn.commit()
        conn.close()
        log("Message sent", sender)
        return redirect("/messages")

    user = session.get("user", "guest")
    conn = db()
    rows = conn.execute("SELECT * FROM messages WHERE recipient=? OR sender=? OR recipient='admin' ORDER BY id DESC LIMIT 100", (user, user)).fetchall()
    conn.close()

    content = """
    <div class='card'><h1>Messages</h1>
    <form method='POST'>
    <input name='recipient' value='admin'>
    <input name='subject' placeholder='Subject'>
    <textarea name='body' placeholder='Message'></textarea>
    <button>Send</button>
    </form></div>
    """
    for m in rows:
        content += f"""
        <div class='card'>
        <b>{h(m['subject'])}</b><br>
        {h(m['sender'])} → {h(m['recipient'])}<br>
        <p>{h(m['body'])}</p>
        <span class='small'>{h(m['status'])} • {h(m['created_at'])}</span>
        </div>
        """
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    sika_rows = conn.execute("SELECT * FROM sika_ledger ORDER BY id DESC LIMIT 80").fetchall()
    event_rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 80").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card'><h1>HRM Admin</h1></div><div class='card'><h2>SIKA Review</h2>"
    for s in sika_rows:
        content += f"""
        <div class='card'>
        <b>{h(s['title'])}</b><br>
        User: {h(s['username'])} • SIKA: {h(s['sika_points'])} • Status: {h(s['status'])}<br>
        <a href='/admin/sika/{s['id']}/approved'>Approve</a>
        <a href='/admin/sika/{s['id']}/rejected'>Reject</a>
        </div>
        """
    content += "</div><div class='card'><h2>Event Review</h2>"
    for e in event_rows:
        content += f"""
        <div class='card'>
        <b>{h(e['title'])}</b><br>
        Status: {h(e['status'])}<br>
        <a href='/admin/event/{e['id']}/approved'>Approve</a>
        <a href='/admin/event/{e['id']}/rejected'>Reject</a>
        </div>
        """
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    content += "</div>"
    return render(content)

@app.route("/admin/sika/<int:id>/<status>")
def admin_sika(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")

    conn = db()
    row = conn.execute("SELECT * FROM sika_ledger WHERE id=?", (id,)).fetchone()

    if row:
        conn.execute("UPDATE sika_ledger SET status=? WHERE id=?", (status, id))
        if status == "approved":
            ensure_sika_account(row["username"])
            conn.execute(
                "UPDATE sika_accounts SET sika_balance=sika_balance+? WHERE username=?",
                (int(row["sika_points"] or 0), row["username"])
            )
        conn.commit()

    conn.close()
    log(f"SIKA {status}", session.get("user","admin"))
    return redirect("/admin")

@app.route("/admin/event/<int:id>/<status>")
def admin_event(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE events SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"Event {status}", session.get("user","admin"))
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
