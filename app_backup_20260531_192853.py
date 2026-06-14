from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
ADMIN_USERNAME = "N24-7"
ADMIN_EMAIL = "oap@onanypostcode.local"
ADMIN_PASSWORD = "2525"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def h(x):
    return escape(str(x or ""))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def log(action, username="system"):
    conn = db()
    conn.execute(
        "INSERT INTO audit_logs(action,username,created_at) VALUES(?,?,?)",
        (action, username, now())
    )
    conn.commit()
    conn.close()

def save_memory(memory_type, title, summary, lesson, next_action, visibility="private"):
    conn = db()
    conn.execute("""INSERT INTO hrm_memory_logs(memory_type,title,summary,lesson,next_action,visibility,created_at)
    VALUES(?,?,?,?,?,?,?)""", (memory_type, title, summary, lesson, next_action, visibility, now()))
    conn.commit()
    conn.close()

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        username TEXT UNIQUE,
        oap_email TEXT,
        password TEXT,
        postcode TEXT,
        borough TEXT,
        county_region TEXT,
        country TEXT,
        continent TEXT,
        weather_location TEXT,
        verification_level TEXT DEFAULT 'starter',
        role TEXT DEFAULT 'member',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS culture_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        culture_type TEXT,
        title TEXT,
        heritage_group TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        continent TEXT,
        body TEXT,
        source_note TEXT,
        status TEXT DEFAULT 'approved',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS artists(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        artist_name TEXT,
        genre TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        continent TEXT,
        bio TEXT,
        link TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        event_type TEXT,
        category TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        continent TEXT,
        venue TEXT,
        event_date TEXT,
        event_time TEXT,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS awards(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        award_name TEXT,
        award_type TEXT,
        nominee_name TEXT,
        reason TEXT,
        geography_level TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS verification_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        requested_level TEXT,
        proof TEXT,
        contribution_note TEXT,
        status TEXT DEFAULT 'pending',
        reviewer_note TEXT,
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

    cur.execute("""CREATE TABLE IF NOT EXISTS revenues(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        customer_name TEXT,
        source TEXT,
        description TEXT,
        amount REAL DEFAULT 0,
        currency TEXT DEFAULT 'GBP',
        status TEXT DEFAULT 'recorded',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS payouts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        recipient_name TEXT,
        reason TEXT,
        amount REAL DEFAULT 0,
        currency TEXT DEFAULT 'GBP',
        status TEXT DEFAULT 'pending',
        approved_by TEXT,
        paid_date TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS approvals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        approval_type TEXT,
        record_id INTEGER,
        status TEXT DEFAULT 'pending',
        reviewer TEXT,
        notes TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS hrm_memory_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_type TEXT,
        title TEXT,
        summary TEXT,
        lesson TEXT,
        next_action TEXT,
        visibility TEXT DEFAULT 'private',
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
        cur.execute("""UPDATE users SET nickname=?, oap_email=?, password=?, role=?, verification_level=?
        WHERE username=?""", ("N24-7", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", "founder", ADMIN_USERNAME))
    else:
        cur.execute("""INSERT INTO users(nickname,username,oap_email,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("N24-7", ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD),
         "CR4", "Merton", "Greater London", "UK", "Europe", "London", "founder", "admin", now()))

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
body{margin:0;background:#050505;color:white;font-family:Arial}
.top{background:#101010;padding:15px;border-bottom:1px solid #222;position:sticky;top:0;z-index:2}
.logo{font-size:22px;font-weight:900}
.wrap{padding:14px;max-width:1150px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:16px;margin:12px 0}
.hero{text-align:center;padding:30px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:13px;margin:8px 0;background:#0b0b0b;color:white;border:1px solid #333;border-radius:12px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:12px;padding:13px 18px;font-weight:900}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:bold;margin:3px}
.warn{background:#2b1600;border-color:#6b3b00}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a> <a href="/signup">Join</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/my_world">My World</a>
<a href="/dashboard">Dashboard</a>
<a href="/culture">Culture</a>
<a href="/artists">Artists</a>
<a href="/events">Events</a>
<a href="/awards">Awards</a>
<a href="/verification">Verification</a>
<a href="/messages">Messenger</a>
<a href="/revenue">Revenue</a>
<a href="/payouts">Payouts</a>
<a href="/approvals">Approvals</a>
<a href="/hrm_memory">HRM</a>
<a href="/admin">Admin</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def current_user():
    return session.get("user", "guest")

@app.route("/")
def home():
    conn = db()
    stats = {
        "users": conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        "culture": conn.execute("SELECT COUNT(*) c FROM culture_posts").fetchone()["c"],
        "artists": conn.execute("SELECT COUNT(*) c FROM artists").fetchone()["c"],
        "events": conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        "revenue": conn.execute("SELECT COALESCE(SUM(amount),0) c FROM revenues").fetchone()["c"],
        "payouts": conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='paid'").fetchone()["c"],
    }
    conn.close()

    return render(f"""
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>v3.7 — My World + Revenue + Payouts + Approvals</p>
    <p>Every member has a World. Track value before financial infrastructure.</p>
    </div>

    <div class='grid'>
    <div class='card'><h2>{stats['users']}</h2><p>Users</p></div>
    <div class='card'><h2>{stats['culture']}</h2><p>Culture</p></div>
    <div class='card'><h2>{stats['artists']}</h2><p>Artists</p></div>
    <div class='card'><h2>{stats['events']}</h2><p>Events</p></div>
    <div class='card'><h2>£{stats['revenue']:.2f}</h2><p>Total Revenue</p></div>
    <div class='card'><h2>£{stats['payouts']:.2f}</h2><p>Paid Payouts</p></div>
    </div>

    <div class='card'>
    <a class='badge' href='/my_world'>Open My World</a>
    <a class='badge' href='/dashboard'>Founder Dashboard</a>
    <a class='badge' href='/revenue'>Record Revenue</a>
    <a class='badge' href='/payouts'>Request Payout</a>
    <a class='badge' href='/approvals'>Approvals</a>
    </div>

    <div class='card warn'>
    <b>Financial boundary:</b> This is a manual revenue and payout ledger. Not a bank. Not e-money. No automatic money movement.
    </div>
    """)

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        conn = db()
        try:
            conn.execute("""INSERT INTO users(nickname,username,oap_email,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                request.form["nickname"], request.form["username"], request.form.get("oap_email",""),
                generate_password_hash(request.form["password"]),
                request.form.get("postcode",""), request.form.get("borough",""), request.form.get("county_region",""),
                request.form.get("country",""), request.form.get("continent",""), request.form.get("weather_location",""),
                "starter", "member", now()
            ))
            conn.commit()
            log("User signup", request.form["username"])
            return redirect("/login")
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()

    return render("""
    <div class='card hero'><h1>Join OAP</h1><p class='green'>Fast signup. Location optional until verification or monetization.</p></div>
    <div class='card'><form method='POST'>
    <input name='nickname' placeholder='Nickname' required>
    <input name='username' placeholder='Username' required>
    <input name='oap_email' placeholder='OAP email optional later'>
    <input name='password' type='password' placeholder='Password' required>
    <input name='postcode' placeholder='Postcode optional'>
    <input name='borough' placeholder='Borough optional'>
    <input name='county_region' placeholder='County / Region optional'>
    <input name='country' placeholder='Country optional'>
    <input name='continent' placeholder='Continent optional'>
    <input name='weather_location' placeholder='Weather location optional'>
    <button>Join</button>
    </form></div>
    """)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"]):
            session["user"] = user["username"]
            log("User login", user["username"])
            return redirect("/")
        return "Invalid login"
    return render("""
    <div class='card'><h2>Login</h2><form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Login</button>
    </form><p class='small'>Default admin: N24-7 / 2525</p></div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/my_world")
def my_world():
    username = current_user()
    conn = db()
    u = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    culture_count = conn.execute("SELECT COUNT(*) c FROM culture_posts WHERE username=?", (username,)).fetchone()["c"]
    artist_count = conn.execute("SELECT COUNT(*) c FROM artists WHERE username=?", (username,)).fetchone()["c"]
    event_count = conn.execute("SELECT COUNT(*) c FROM events WHERE username=?", (username,)).fetchone()["c"]
    award_count = conn.execute("SELECT COUNT(*) c FROM awards WHERE username=?", (username,)).fetchone()["c"]
    rev = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM revenues WHERE username=?", (username,)).fetchone()["c"]
    pay = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE username=? AND status='paid'", (username,)).fetchone()["c"]
    conn.close()

    nickname = u["nickname"] if u else username
    verification = u["verification_level"] if u else "guest"

    return render(f"""
    <div class='card hero'>
    <h1>🌍 {h(nickname)}'s World</h1>
    <p class='green'>Every member has a World.</p>
    <p>Verification: {h(verification)}</p>
    </div>

    <div class='grid'>
    <div class='card'><h2>💬</h2><p>Messenger</p><a href='/messages'>Open</a></div>
    <div class='card'><h2>{culture_count}</h2><p>My Culture</p><a href='/culture'>Open</a></div>
    <div class='card'><h2>{artist_count}</h2><p>My Artists</p><a href='/artists'>Open</a></div>
    <div class='card'><h2>{event_count}</h2><p>My Events</p><a href='/events'>Open</a></div>
    <div class='card'><h2>{award_count}</h2><p>My Awards</p><a href='/awards'>Open</a></div>
    <div class='card'><h2>⭐</h2><p>My Verification</p><a href='/verification'>Open</a></div>
    <div class='card'><h2>£{rev:.2f}</h2><p>My Revenue</p><a href='/revenue'>Open</a></div>
    <div class='card'><h2>£{pay:.2f}</h2><p>My Paid Payouts</p><a href='/payouts'>Open</a></div>
    </div>

    <div class='card warn'>
    <b>Coming later inside My World:</b> Media, Music, Business, Family Tree, Affiliate Tree, SIKA.
    </div>
    """)

@app.route("/dashboard")
def dashboard():
    conn = db()
    total_revenue = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM revenues").fetchone()["c"]
    pending_payouts = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='pending'").fetchone()["c"]
    approved_payouts = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='approved'").fetchone()["c"]
    paid_payouts = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='paid'").fetchone()["c"]
    pending_approvals = conn.execute("SELECT COUNT(*) c FROM approvals WHERE status='pending'").fetchone()["c"]
    users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    events = conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    artists_count = conn.execute("SELECT COUNT(*) c FROM artists").fetchone()["c"]
    conn.close()

    return render(f"""
    <div class='card hero'><h1>📊 Founder Dashboard</h1><p class='green'>Monitor before payouts. Records before finance.</p></div>
    <div class='grid'>
    <div class='card'><h2>£{total_revenue:.2f}</h2><p>Total Revenue</p></div>
    <div class='card'><h2>£{pending_payouts:.2f}</h2><p>Pending Payouts</p></div>
    <div class='card'><h2>£{approved_payouts:.2f}</h2><p>Approved Payouts</p></div>
    <div class='card'><h2>£{paid_payouts:.2f}</h2><p>Paid Payouts</p></div>
    <div class='card'><h2>{pending_approvals}</h2><p>Pending Approvals</p></div>
    <div class='card'><h2>{users}</h2><p>Users</p></div>
    <div class='card'><h2>{events}</h2><p>Events</p></div>
    <div class='card'><h2>{artists_count}</h2><p>Artists</p></div>
    </div>
    """)

@app.route("/revenue", methods=["GET","POST"])
def revenue():
    if request.method == "POST":
        username = request.form.get("username") or current_user()
        conn = db()
        conn.execute("""INSERT INTO revenues(username,customer_name,source,description,amount,currency,status,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (
            username, request.form["customer_name"], request.form["source"], request.form["description"],
            float(request.form.get("amount") or 0), request.form["currency"], "recorded", now()
        ))
        conn.commit()
        conn.close()
        save_memory("revenue", request.form["source"], "Revenue recorded.", "Revenue must be tracked before payouts.", "Review whether payout is required.")
        log("Revenue recorded", username)
        return redirect("/revenue")

    conn = db()
    rows = conn.execute("SELECT * FROM revenues ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>💰 Revenue Ledger</h1><p class='green'>Record income before payouts.</p></div>
    <div class='card'><form method='POST'>
    <input name='username' placeholder='Linked username optional'>
    <input name='customer_name' placeholder='Customer / business / artist name'>
    <select name='source'>
    <option>Business Listing</option><option>Featured Promotion</option><option>Artist Promotion</option><option>Event Promotion</option><option>Vendor Slot</option><option>Founder Membership</option><option>Other</option>
    </select>
    <input name='amount' placeholder='Amount e.g. 20'>
    <select name='currency'><option>GBP</option><option>GHS</option><option>EUR</option><option>SIKA</option></select>
    <textarea name='description' placeholder='What was paid for?'></textarea>
    <button>Record Revenue</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['source'])}</b><br>{h(r['currency'])} {h(r['amount'])} • {h(r['customer_name'])}<p>{h(r['description'])}</p><span class='small'>{h(r['created_at'])}</span></div>"
    return render(content)

@app.route("/payouts", methods=["GET","POST"])
def payouts():
    if request.method == "POST":
        username = request.form.get("username") or current_user()
        conn = db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO payouts(username,recipient_name,reason,amount,currency,status,approved_by,paid_date,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (
            username, request.form["recipient_name"], request.form["reason"],
            float(request.form.get("amount") or 0), request.form["currency"],
            "pending", "", "", now()
        ))
        payout_id = cur.lastrowid
        cur.execute("""INSERT INTO approvals(approval_type,record_id,status,reviewer,notes,created_at)
        VALUES(?,?,?,?,?,?)""", ("payout", payout_id, "pending", "", "Payout requires human approval.", now()))
        conn.commit()
        conn.close()
        save_memory("payout", request.form["recipient_name"], "Payout request created.", "No automatic payouts. Human approval required.", "Review payout in approvals.")
        log("Payout requested", username)
        return redirect("/payouts")

    conn = db()
    rows = conn.execute("SELECT * FROM payouts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>💸 Payout Ledger</h1><p class='green'>Manual payouts only. Human approval before money moves.</p></div>
    <div class='card warn'>This does not send money. It records payout status for manual payment and audit.</div>
    <div class='card'><form method='POST'>
    <input name='username' placeholder='Linked username optional'>
    <input name='recipient_name' placeholder='Recipient name'>
    <input name='amount' placeholder='Amount e.g. 10'>
    <select name='currency'><option>GBP</option><option>GHS</option><option>EUR</option><option>SIKA</option></select>
    <textarea name='reason' placeholder='Reason for payout'></textarea>
    <button>Create Payout Request</button>
    </form></div>
    """
    for p in rows:
        content += f"<div class='card'><b>{h(p['recipient_name'])}</b><br>{h(p['currency'])} {h(p['amount'])} • Status: {h(p['status'])}<p>{h(p['reason'])}</p><span class='small'>Approved by: {h(p['approved_by'])} • Paid date: {h(p['paid_date'])}</span></div>"
    return render(content)

@app.route("/approvals")
def approvals():
    conn = db()
    rows = conn.execute("SELECT * FROM approvals ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>✅ Approvals</h1><p class='green'>Review before action.</p></div>"
    for a in rows:
        content += f"""
        <div class='card'>
        <b>{h(a['approval_type'])}</b> #{h(a['record_id'])}<br>
        Status: {h(a['status'])}<p>{h(a['notes'])}</p>
        <a href='/approval/{a['id']}/approved'>Approve</a>
        <a href='/approval/{a['id']}/rejected'>Reject</a>
        <a href='/approval/{a['id']}/paid'>Mark Paid</a>
        </div>
        """
    return render(content)

@app.route("/approval/<int:id>/<status>")
def approval_action(id, status):
    if status not in ["approved", "rejected", "paid"]:
        return redirect("/approvals")
    reviewer = current_user()
    conn = db()
    approval = conn.execute("SELECT * FROM approvals WHERE id=?", (id,)).fetchone()
    if approval:
        conn.execute("UPDATE approvals SET status=?, reviewer=?, notes=? WHERE id=?",
                     (status, reviewer, f"Reviewed as {status} by {reviewer}", id))
        if approval["approval_type"] == "payout":
            if status == "approved":
                conn.execute("UPDATE payouts SET status=?, approved_by=? WHERE id=?",
                             ("approved", reviewer, approval["record_id"]))
            elif status == "rejected":
                conn.execute("UPDATE payouts SET status=?, approved_by=? WHERE id=?",
                             ("rejected", reviewer, approval["record_id"]))
            elif status == "paid":
                conn.execute("UPDATE payouts SET status=?, approved_by=?, paid_date=? WHERE id=?",
                             ("paid", reviewer, now(), approval["record_id"]))
        conn.commit()
    conn.close()
    save_memory("approval", f"Approval {id}", f"Approval marked {status}", "Approval workflow protects OAP.", "Keep payout logs accurate.")
    log(f"Approval {status}", reviewer)
    return redirect("/approvals")

@app.route("/culture", methods=["GET","POST"])
def culture():
    if request.method == "POST":
        username = current_user()
        conn = db()
        conn.execute("""INSERT INTO culture_posts(username,culture_type,title,heritage_group,postcode,borough,country,continent,body,source_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["culture_type"], request.form["title"], request.form["heritage_group"],
            request.form["postcode"], request.form["borough"], request.form["country"], request.form["continent"],
            request.form["body"], request.form["source_note"], "approved", now()
        ))
        conn.commit()
        conn.close()
        save_memory("culture", request.form["title"], "Culture record saved.", "Culture connects community.", "Connect to artists/events/awards.", "public")
        return redirect("/culture")
    conn = db()
    rows = conn.execute("SELECT * FROM culture_posts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>🎵 Culture</h1></div>
    <div class='card'><form method='POST'>
    <select name='culture_type'><option>Song / Music</option><option>Story</option><option>Language</option><option>Proverb</option><option>Food</option><option>Dance</option><option>Festival</option></select>
    <input name='title' placeholder='Title' required>
    <input name='heritage_group' placeholder='Heritage group'>
    <input name='postcode' placeholder='Postcode'>
    <input name='borough' placeholder='Borough'>
    <input name='country' placeholder='Country'>
    <input name='continent' placeholder='Continent'>
    <textarea name='body' placeholder='Culture record'></textarea>
    <textarea name='source_note' placeholder='Rights/proof note'></textarea>
    <button>Save</button></form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['culture_type'])} • {h(r['heritage_group'])}<p>{h(r['body'])}</p></div>"
    return render(content)

@app.route("/artists", methods=["GET","POST"])
def artists():
    if request.method == "POST":
        username = current_user()
        conn = db()
        conn.execute("""INSERT INTO artists(username,artist_name,genre,postcode,borough,country,continent,bio,link,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["artist_name"], request.form["genre"], request.form["postcode"],
            request.form["borough"], request.form["country"], request.form["continent"],
            request.form["bio"], request.form["link"], "pending", now()
        ))
        conn.commit()
        conn.close()
        save_memory("artist", request.form["artist_name"], "Artist submitted.", "Artists connect culture and revenue.", "Review artist.")
        return redirect("/artists")
    conn = db()
    rows = conn.execute("SELECT * FROM artists ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>🎤 Artists</h1></div>
    <div class='card'><form method='POST'>
    <input name='artist_name' placeholder='Artist name' required>
    <input name='genre' placeholder='Genre'>
    <input name='postcode' placeholder='Postcode'>
    <input name='borough' placeholder='Borough'>
    <input name='country' placeholder='Country'>
    <input name='continent' placeholder='Continent'>
    <textarea name='bio' placeholder='Bio'></textarea>
    <input name='link' placeholder='Link'>
    <button>Submit Artist</button></form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['artist_name'])}</b><br>{h(r['genre'])} • {h(r['country'])} • {h(r['status'])}<p>{h(r['bio'])}</p></div>"
    return render(content)

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method == "POST":
        username = current_user()
        conn = db()
        conn.execute("""INSERT INTO events(username,title,event_type,category,postcode,borough,country,continent,venue,event_date,event_time,description,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["title"], request.form["event_type"], request.form["category"],
            request.form["postcode"], request.form["borough"], request.form["country"], request.form["continent"],
            request.form["venue"], request.form["event_date"], request.form["event_time"], request.form["description"],
            "pending", now()
        ))
        conn.commit()
        conn.close()
        return redirect("/events")
    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Events</h1><form method='POST'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'><option>Culture Event</option><option>Watch Party</option><option>Community Event</option><option>Artist Event</option><option>Business Popup</option></select>
    <input name='category' value='Community'>
    <input name='postcode' placeholder='Postcode'>
    <input name='borough' placeholder='Borough'>
    <input name='country' placeholder='Country'>
    <input name='continent' placeholder='Continent'>
    <input name='venue' placeholder='Venue'>
    <input name='event_date' placeholder='Date'>
    <input name='event_time' placeholder='Time'>
    <textarea name='description' placeholder='Description'></textarea>
    <button>Submit Event</button></form></div>
    """
    for e in rows:
        content += f"<div class='card'><b>{h(e['title'])}</b><br>{h(e['event_type'])} • {h(e['postcode'])} → {h(e['country'])}</div>"
    return render(content)

@app.route("/awards", methods=["GET","POST"])
def awards():
    if request.method == "POST":
        username = current_user()
        conn = db()
        conn.execute("""INSERT INTO awards(username,award_name,award_type,nominee_name,reason,geography_level,status,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (
            username, request.form["award_name"], request.form["award_type"], request.form["nominee_name"],
            request.form["reason"], request.form["geography_level"], "pending", now()
        ))
        conn.commit()
        conn.close()
        return redirect("/awards")
    conn = db()
    rows = conn.execute("SELECT * FROM awards ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>🏅 Awards</h1></div>
    <div class='card'><form method='POST'>
    <input name='award_name' placeholder='Award name' required>
    <select name='award_type'><option>Artist of the Year</option><option>Community Song</option><option>Culture Ambassador</option><option>Youth Creator</option><option>Community Champion</option><option>Business Champion</option></select>
    <input name='nominee_name' placeholder='Nominee'>
    <select name='geography_level'><option>Postcode</option><option>Borough</option><option>Country</option><option>Continent</option><option>Global</option><option>Planet</option><option>Universe</option></select>
    <textarea name='reason' placeholder='Reason'></textarea>
    <button>Submit Award</button></form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['award_name'])}</b><br>{h(r['award_type'])} • {h(r['status'])}<p>{h(r['reason'])}</p></div>"
    return render(content)

@app.route("/verification", methods=["GET","POST"])
def verification():
    if request.method == "POST":
        username = current_user()
        conn = db()
        conn.execute("""INSERT INTO verification_requests(username,requested_level,proof,contribution_note,status,reviewer_note,created_at)
        VALUES(?,?,?,?,?,?,?)""", (
            username, request.form["requested_level"], request.form["proof"], request.form["contribution_note"],
            "pending", "", now()
        ))
        conn.commit()
        conn.close()
        return redirect("/verification")
    conn = db()
    rows = conn.execute("SELECT * FROM verification_requests ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>⭐ Verification</h1><p class='green'>Proof + Trust + Contribution + Consistency.</p></div>
    <div class='card'><form method='POST'>
    <select name='requested_level'>
    <option>Postcode Verified</option><option>Borough Verified</option><option>County / Region Verified</option><option>Country Verified</option><option>Continent Verified</option><option>Global Verified</option><option>Planet Verified</option><option>Universe Verified</option>
    </select>
    <textarea name='proof' placeholder='Proof'></textarea>
    <textarea name='contribution_note' placeholder='Contribution note'></textarea>
    <button>Request Verification</button></form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['requested_level'])}</b><br>@{h(r['username'])} • {h(r['status'])}<p>{h(r['proof'])}</p></div>"
    return render(content)

@app.route("/messages", methods=["GET","POST"])
def messages():
    if request.method == "POST":
        sender = current_user()
        conn = db()
        conn.execute("INSERT INTO messages(sender,recipient,subject,body,status,created_at) VALUES(?,?,?,?,?,?)",
                     (sender, request.form["recipient"], request.form["subject"], request.form["body"], "unread", now()))
        conn.commit()
        conn.close()
        return redirect("/messages")
    user = current_user()
    conn = db()
    rows = conn.execute("SELECT * FROM messages WHERE recipient=? OR sender=? OR recipient='admin' ORDER BY id DESC LIMIT 100", (user,user)).fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Messenger</h1><form method='POST'>
    <input name='recipient' value='admin'>
    <input name='subject' placeholder='Subject'>
    <textarea name='body' placeholder='Message'></textarea>
    <button>Send</button></form></div>
    """
    for m in rows:
        content += f"<div class='card'><b>{h(m['subject'])}</b><br>{h(m['sender'])} → {h(m['recipient'])}<p>{h(m['body'])}</p></div>"
    return render(content)

@app.route("/hrm_memory")
def hrm_memory():
    conn = db()
    rows = conn.execute("SELECT * FROM hrm_memory_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>🧠 HRM Memory</h1></div>"
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['memory_type'])}<p>{h(r['summary'])}</p><p>{h(r['lesson'])}</p></div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>Admin</h1></div><div class='card'><h2>Users</h2>"
    for u in users:
        content += f"<div class='card'>@{h(u['username'])} — {h(u['verification_level'])}<br>{h(u['postcode'])} → {h(u['country'])}</div>"
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    content += "</div>"
    return render(content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
