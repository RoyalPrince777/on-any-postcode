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

    cur.execute("""CREATE TABLE IF NOT EXISTS news_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        category TEXT,
        summary TEXT,
        body TEXT,
        source_note TEXT,
        verification_status TEXT DEFAULT 'needs review',
        country TEXT DEFAULT 'Global',
        city TEXT DEFAULT '',
        postcode TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")
    for col, typ in [
        ("source_note","TEXT"),("verification_status","TEXT DEFAULT 'needs review'"),
        ("country","TEXT DEFAULT 'Global'"),("city","TEXT DEFAULT ''"),
        ("postcode","TEXT DEFAULT ''"),("views","INTEGER DEFAULT 0"),
        ("status","TEXT DEFAULT 'pending'")
    ]:
        add_col(cur, "news_posts", col, typ)

    cur.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        event_type TEXT,
        category TEXT,
        country_focus TEXT,
        postcode TEXT,
        city TEXT,
        country TEXT,
        venue TEXT,
        event_date TEXT,
        event_time TEXT,
        description TEXT,
        ticket_price TEXT,
        capacity TEXT,
        contact TEXT,
        status TEXT DEFAULT 'pending',
        views INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS event_rsvps(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        event_title TEXT,
        username TEXT,
        attendee_name TEXT,
        attendee_contact TEXT,
        quantity INTEGER DEFAULT 1,
        note TEXT,
        status TEXT DEFAULT 'new',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS event_attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        event_title TEXT,
        recorder TEXT,
        invited_count INTEGER DEFAULT 0,
        attended_count INTEGER DEFAULT 0,
        new_people_count INTEGER DEFAULT 0,
        returning_people_count INTEGER DEFAULT 0,
        products_sold INTEGER DEFAULT 0,
        revenue TEXT DEFAULT '0',
        notes TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS event_reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        event_title TEXT,
        reviewer TEXT,
        what_worked TEXT,
        what_failed TEXT,
        lesson TEXT,
        next_action TEXT,
        rating TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS community_signals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_type TEXT,
        title TEXT,
        location TEXT,
        description TEXT,
        opportunity TEXT,
        risk_note TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS business_leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT,
        category TEXT,
        contact TEXT,
        location TEXT,
        opportunity TEXT,
        status TEXT DEFAULT 'new',
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

    cur.execute("""CREATE TABLE IF NOT EXISTS hrm_memory_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_type TEXT,
        title TEXT,
        summary TEXT,
        lesson TEXT,
        next_action TEXT,
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
pre{white-space:pre-wrap;font-family:Arial}
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
<a href="/events">Events</a>
<a href="/rsvps">RSVPs</a>
<a href="/attendance_dashboard">Attendance Dashboard</a>
<a href="/attendance">Attendance</a>
<a href="/reviews">Reviews</a>
<a href="/messages">Messages</a>
<a href="/signals">Signals</a>
<a href="/leads">Business Leads</a>
<a href="/news">News</a>
<a href="/admin">Admin</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def memory(memory_type, title, summary, lesson, next_action):
    conn = db()
    conn.execute("""INSERT INTO hrm_memory_logs(memory_type,title,summary,lesson,next_action,created_at)
    VALUES(?,?,?,?,?,?)""", (memory_type, title, summary, lesson, next_action, now()))
    conn.commit()
    conn.close()

@app.route("/")
def home():
    conn = db()
    stats = {
        "events": conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        "rsvps": conn.execute("SELECT COUNT(*) c FROM event_rsvps").fetchone()["c"],
        "attendance": conn.execute("SELECT COUNT(*) c FROM event_attendance").fetchone()["c"],
        "reviews": conn.execute("SELECT COUNT(*) c FROM event_reviews").fetchone()["c"],
        "messages": conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"],
        "signals": conn.execute("SELECT COUNT(*) c FROM community_signals").fetchone()["c"],
        "leads": conn.execute("SELECT COUNT(*) c FROM business_leads").fetchone()["c"],
    }
    news_rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = f"""
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>OAP v3.1 — Messenger + RSVP + Attendance Dashboard</p>
    <p>Views are observation. Value is attendance, orders, revenue, trust, and community.</p>
    </div>
    <div class='grid'>
    <div class='card'><h2>{stats['events']}</h2><p>Events</p></div>
    <div class='card'><h2>{stats['rsvps']}</h2><p>RSVPs</p></div>
    <div class='card'><h2>{stats['attendance']}</h2><p>Attendance</p></div>
    <div class='card'><h2>{stats['reviews']}</h2><p>Reviews</p></div>
    <div class='card'><h2>{stats['messages']}</h2><p>Messages</p></div>
    <div class='card'><h2>{stats['signals']}</h2><p>Signals</p></div>
    <div class='card'><h2>{stats['leads']}</h2><p>Business Leads</p></div>
    </div>
    <div class='card'>
    <h2>Quick Actions</h2>
    <a class='badge' href='/events'>Create Event</a>
    <a class='badge' href='/rsvps'>RSVP</a>
    <a class='badge' href='/attendance_dashboard'>Dashboard</a>
    <a class='badge' href='/messages'>Message</a>
    <a class='badge' href='/signals'>Signal</a>
    <a class='badge' href='/leads'>Lead</a>
    </div>
    <div class='card'><h2>Latest News</h2>
    """
    for n in news_rows:
        content += f"<div class='card'><b>{h(n['title'])}</b><p>{h(n['summary'])}</p><a href='/news/{n['id']}'>Read</a></div>"
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

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO events(username,title,event_type,category,country_focus,postcode,city,country,venue,event_date,event_time,description,ticket_price,capacity,contact,status,views,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["title"], request.form["event_type"], request.form["category"],
            request.form["country_focus"], request.form["postcode"], request.form["city"],
            request.form["country"], request.form["venue"], request.form["event_date"],
            request.form["event_time"], request.form["description"], request.form["ticket_price"],
            request.form["capacity"], request.form["contact"], "pending", 0, now()
        ))
        conn.commit()
        conn.close()
        log("Event submitted", username)
        memory("event", request.form["title"], "Event created", "Events need attendance and review records after completion.", "Collect RSVP and attendance.")
        return redirect("/events")

    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Events / Watch Parties</h1>
    <form method='POST'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'><option>Watch Party</option><option>Creator Meetup</option><option>Business Popup</option><option>Community Event</option><option>Awareness Event</option></select>
    <input name='category' value='Community'>
    <input name='country_focus' value='Global'>
    <input name='postcode' placeholder='Postcode'>
    <input name='city' placeholder='City'>
    <input name='country' value='UK'>
    <input name='venue' placeholder='Venue'>
    <input name='event_date' placeholder='Date'>
    <input name='event_time' placeholder='Time'>
    <textarea name='description' placeholder='Description'></textarea>
    <input name='ticket_price' placeholder='Ticket price'>
    <input name='capacity' placeholder='Capacity'>
    <input name='contact' placeholder='Contact'>
    <button>Submit Event</button>
    </form></div>
    """
    for e in rows:
        content += f"""
        <div class='card'>
        <b>{h(e['title'])}</b><br>
        ID: {e['id']} • {h(e['event_type'])} • {h(e['category'])}<br>
        {h(e['event_date'])} {h(e['event_time'])} • {h(e['city'])}<br>
        <span class='small'>Status: {h(e['status'])}</span><br>
        <a href='/event/{e['id']}'>Open</a>
        </div>
        """
    return render(content)

@app.route("/event/<int:id>")
def event_detail(id):
    conn = db()
    e = conn.execute("SELECT * FROM events WHERE id=?", (id,)).fetchone()
    if not e:
        conn.close()
        return "Event not found"
    conn.execute("UPDATE events SET views=views+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return render(f"""
    <div class='card'>
    <h1>{h(e['title'])}</h1>
    <p class='gold'>{h(e['event_type'])} • {h(e['category'])}</p>
    <p>{h(e['event_date'])} {h(e['event_time'])} • {h(e['venue'])} • {h(e['city'])}</p>
    <p>{h(e['description'])}</p>
    <a class='badge' href='/rsvps?event_id={e['id']}&event_title={h(e['title'])}'>RSVP</a>
    </div>
    """)

@app.route("/rsvps", methods=["GET","POST"])
def rsvps():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO event_rsvps(event_id,event_title,username,attendee_name,attendee_contact,quantity,note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (
            request.form["event_id"], request.form["event_title"], username,
            request.form["attendee_name"], request.form["attendee_contact"],
            int(request.form.get("quantity") or 1), request.form["note"], "new", now()
        ))
        conn.commit()
        conn.close()
        log("RSVP recorded", username)
        memory("rsvp", request.form["event_title"], "RSVP recorded", "RSVP shows intent, not full value yet.", "Confirm attendance after event.")
        return redirect("/rsvps")

    event_id = request.args.get("event_id", "")
    event_title = request.args.get("event_title", "")
    conn = db()
    rows = conn.execute("SELECT * FROM event_rsvps ORDER BY id DESC LIMIT 100").fetchall()
    events_rows = conn.execute("SELECT id,title FROM events ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = f"""
    <div class='card'><h1>Event RSVPs</h1>
    <form method='POST'>
    <input name='event_id' placeholder='Event ID' value='{h(event_id)}'>
    <input name='event_title' placeholder='Event title' value='{h(event_title)}' required>
    <input name='attendee_name' placeholder='Attendee name / nickname'>
    <input name='attendee_contact' placeholder='Contact / handle'>
    <input name='quantity' placeholder='Quantity' value='1'>
    <textarea name='note' placeholder='Note'></textarea>
    <button>Record RSVP</button>
    </form></div>
    <div class='card'><h2>Event IDs</h2>
    """
    for e in events_rows:
        content += f"<p>{e['id']} — {h(e['title'])}</p>"
    content += "</div>"
    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['event_title'])}</b> — {h(r['status'])}<br>
        {h(r['attendee_name'])} | {h(r['attendee_contact'])} | Qty: {r['quantity']}<br>
        <a href='/rsvp/{r['id']}/contacted'>Contacted</a>
        <a href='/rsvp/{r['id']}/confirmed'>Confirmed</a>
        <a href='/rsvp/{r['id']}/cancelled'>Cancel</a>
        </div>
        """
    return render(content)

@app.route("/rsvp/<int:id>/<status>")
def rsvp_status(id, status):
    if status not in ["new","contacted","confirmed","cancelled"]:
        return redirect("/rsvps")
    conn = db()
    conn.execute("UPDATE event_rsvps SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"RSVP {status}", session.get("user","admin"))
    return redirect("/rsvps")

@app.route("/attendance", methods=["GET","POST"])
def attendance():
    if request.method == "POST":
        recorder = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO event_attendance(event_id,event_title,recorder,invited_count,attended_count,new_people_count,returning_people_count,products_sold,revenue,notes,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (
            request.form["event_id"], request.form["event_title"], recorder,
            int(request.form.get("invited_count") or 0),
            int(request.form.get("attended_count") or 0),
            int(request.form.get("new_people_count") or 0),
            int(request.form.get("returning_people_count") or 0),
            int(request.form.get("products_sold") or 0),
            request.form["revenue"], request.form["notes"], now()
        ))
        conn.commit()
        conn.close()
        log("Attendance recorded", recorder)
        memory("attendance", request.form["event_title"], "Attendance recorded", "Attendance is stronger than views.", "Review what worked and record business leads.")
        return redirect("/attendance_dashboard")

    conn = db()
    rows = conn.execute("SELECT * FROM event_attendance ORDER BY id DESC LIMIT 100").fetchall()
    events_rows = conn.execute("SELECT id,title FROM events ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Attendance Records</h1>
    <form method='POST'>
    <input name='event_id' placeholder='Event ID'>
    <input name='event_title' placeholder='Event title' required>
    <input name='invited_count' placeholder='Invited count' value='0'>
    <input name='attended_count' placeholder='Attended count' value='0'>
    <input name='new_people_count' placeholder='New people' value='0'>
    <input name='returning_people_count' placeholder='Returning people' value='0'>
    <input name='products_sold' placeholder='Products sold' value='0'>
    <input name='revenue' placeholder='Revenue e.g. £0'>
    <textarea name='notes' placeholder='Notes'></textarea>
    <button>Record Attendance</button>
    </form></div>
    <div class='card'><h2>Event IDs</h2>
    """
    for e in events_rows:
        content += f"<p>{e['id']} — {h(e['title'])}</p>"
    content += "</div>"
    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['event_title'])}</b><br>
        Invited: {r['invited_count']} | Attended: {r['attended_count']} | New: {r['new_people_count']} | Returning: {r['returning_people_count']}<br>
        Products Sold: {r['products_sold']} | Revenue: {h(r['revenue'])}
        <p>{h(r['notes'])}</p>
        </div>
        """
    return render(content)

@app.route("/attendance_dashboard")
def attendance_dashboard():
    conn = db()
    total_invited = conn.execute("SELECT COALESCE(SUM(invited_count),0) c FROM event_attendance").fetchone()["c"]
    total_attended = conn.execute("SELECT COALESCE(SUM(attended_count),0) c FROM event_attendance").fetchone()["c"]
    total_new = conn.execute("SELECT COALESCE(SUM(new_people_count),0) c FROM event_attendance").fetchone()["c"]
    total_returning = conn.execute("SELECT COALESCE(SUM(returning_people_count),0) c FROM event_attendance").fetchone()["c"]
    total_products = conn.execute("SELECT COALESCE(SUM(products_sold),0) c FROM event_attendance").fetchone()["c"]
    rows = conn.execute("SELECT * FROM event_attendance ORDER BY id DESC LIMIT 50").fetchall()
    rsvps_count = conn.execute("SELECT COUNT(*) c FROM event_rsvps").fetchone()["c"]
    reviews_count = conn.execute("SELECT COUNT(*) c FROM event_reviews").fetchone()["c"]
    leads_count = conn.execute("SELECT COUNT(*) c FROM business_leads").fetchone()["c"]
    conn.close()
    content = f"""
    <div class='card hero'><h1>📊 Attendance Dashboard</h1><p class='green'>Real-world value, not vanity views.</p></div>
    <div class='grid'>
    <div class='card'><h2>{total_invited}</h2><p>Invited</p></div>
    <div class='card'><h2>{total_attended}</h2><p>Attended</p></div>
    <div class='card'><h2>{total_new}</h2><p>New People</p></div>
    <div class='card'><h2>{total_returning}</h2><p>Returning</p></div>
    <div class='card'><h2>{total_products}</h2><p>Products Sold</p></div>
    <div class='card'><h2>{rsvps_count}</h2><p>RSVPs</p></div>
    <div class='card'><h2>{reviews_count}</h2><p>Reviews</p></div>
    <div class='card'><h2>{leads_count}</h2><p>Business Leads</p></div>
    </div>
    <div class='card'><h2>Attendance Records</h2>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['event_title'])}</b><br>Attended: {r['attended_count']} | Revenue: {h(r['revenue'])}<p>{h(r['notes'])}</p></div>"
    content += "</div>"
    return render(content)

@app.route("/reviews", methods=["GET","POST"])
def reviews():
    if request.method == "POST":
        reviewer = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO event_reviews(event_id,event_title,reviewer,what_worked,what_failed,lesson,next_action,rating,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (
            request.form["event_id"], request.form["event_title"], reviewer,
            request.form["what_worked"], request.form["what_failed"],
            request.form["lesson"], request.form["next_action"], request.form["rating"], now()
        ))
        conn.commit()
        conn.close()
        log("Event review recorded", reviewer)
        memory("review", request.form["event_title"], "Post-event review recorded", request.form["lesson"], request.form["next_action"])
        return redirect("/reviews")

    conn = db()
    rows = conn.execute("SELECT * FROM event_reviews ORDER BY id DESC LIMIT 100").fetchall()
    events_rows = conn.execute("SELECT id,title FROM events ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Post-Event Reviews</h1>
    <form method='POST'>
    <input name='event_id' placeholder='Event ID'>
    <input name='event_title' placeholder='Event title' required>
    <textarea name='what_worked' placeholder='What worked?'></textarea>
    <textarea name='what_failed' placeholder='What failed / weakness?'></textarea>
    <textarea name='lesson' placeholder='Lesson learned'></textarea>
    <textarea name='next_action' placeholder='Next action'></textarea>
    <input name='rating' placeholder='Rating 1-10'>
    <button>Save Review</button>
    </form></div><div class='card'><h2>Event IDs</h2>
    """
    for e in events_rows:
        content += f"<p>{e['id']} — {h(e['title'])}</p>"
    content += "</div>"
    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['event_title'])}</b> — Rating {h(r['rating'])}<br>
        <p><b>Worked:</b> {h(r['what_worked'])}</p>
        <p><b>Failed:</b> {h(r['what_failed'])}</p>
        <p><b>Lesson:</b> {h(r['lesson'])}</p>
        <p><b>Next:</b> {h(r['next_action'])}</p>
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
    <input name='recipient' placeholder='Recipient e.g. admin or N24-7' value='admin'>
    <input name='subject' placeholder='Subject'>
    <textarea name='body' placeholder='Message'></textarea>
    <button>Send Message</button>
    </form></div>
    """
    for m in rows:
        content += f"""
        <div class='card'>
        <b>{h(m['subject'])}</b><br>
        From: {h(m['sender'])} → To: {h(m['recipient'])}<br>
        <p>{h(m['body'])}</p>
        <span class='small'>{h(m['created_at'])} • {h(m['status'])}</span>
        </div>
        """
    return render(content)

@app.route("/signals", methods=["GET","POST"])
def signals():
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO community_signals(signal_type,title,location,description,opportunity,risk_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (
            request.form["signal_type"], request.form["title"], request.form["location"],
            request.form["description"], request.form["opportunity"], request.form["risk_note"], "open", now()
        ))
        conn.commit()
        conn.close()
        log("Community signal recorded", session.get("user","guest"))
        memory("signal", request.form["title"], request.form["description"], "Signals reveal opportunity or risk.", request.form["opportunity"])
        return redirect("/signals")

    conn = db()
    rows = conn.execute("SELECT * FROM community_signals ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Community Signals</h1>
    <form method='POST'>
    <select name='signal_type'><option>Opportunity</option><option>Need</option><option>Risk</option><option>Idea</option><option>Feedback</option></select>
    <input name='title' placeholder='Signal title' required>
    <input name='location' placeholder='Location / postcode'>
    <textarea name='description' placeholder='What happened?'></textarea>
    <textarea name='opportunity' placeholder='Opportunity'></textarea>
    <textarea name='risk_note' placeholder='Risk / protection note'></textarea>
    <button>Save Signal</button>
    </form></div>
    """
    for s in rows:
        content += f"<div class='card'><b>{h(s['title'])}</b> — {h(s['signal_type'])}<br><span class='small'>{h(s['location'])}</span><p>{h(s['description'])}</p><p class='green'>{h(s['opportunity'])}</p><p class='red'>{h(s['risk_note'])}</p></div>"
    return render(content)

@app.route("/leads", methods=["GET","POST"])
def leads():
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO business_leads(business_name,category,contact,location,opportunity,status,created_at)
        VALUES(?,?,?,?,?,?,?)""", (
            request.form["business_name"], request.form["category"], request.form["contact"],
            request.form["location"], request.form["opportunity"], "new", now()
        ))
        conn.commit()
        conn.close()
        log("Business lead recorded", session.get("user","guest"))
        memory("lead", request.form["business_name"], request.form["opportunity"], "Business leads are monetization signals.", "Follow up and convert to listing/promo.")
        return redirect("/leads")

    conn = db()
    rows = conn.execute("SELECT * FROM business_leads ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Business Leads</h1>
    <form method='POST'>
    <input name='business_name' placeholder='Business name' required>
    <input name='category' placeholder='Category'>
    <input name='contact' placeholder='Contact'>
    <input name='location' placeholder='Location / postcode'>
    <textarea name='opportunity' placeholder='Opportunity / pitch'></textarea>
    <button>Save Lead</button>
    </form></div>
    """
    for l in rows:
        content += f"<div class='card'><b>{h(l['business_name'])}</b> — {h(l['category'])}<br><span class='small'>{h(l['location'])}</span><p>{h(l['opportunity'])}</p><p>{h(l['contact'])}</p></div>"
    return render(content)

@app.route("/news")
def news():
    conn = db()
    rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = "<div class='card'><h1>News</h1></div>"
    for n in rows:
        content += f"<div class='card'><b>{h(n['title'])}</b><p>{h(n['summary'])}</p><a href='/news/{n['id']}'>Read</a></div>"
    return render(content)

@app.route("/news/<int:id>")
def news_detail(id):
    conn = db()
    n = conn.execute("SELECT * FROM news_posts WHERE id=?", (id,)).fetchone()
    if not n:
        conn.close()
        return "News not found"
    conn.execute("UPDATE news_posts SET views=views+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return render(f"""
    <div class='card'>
    <h1>{h(n['title'])}</h1>
    <p class='gold'>{h(n['category'])}</p>
    <p class='small'>Public: {h(n['status'])} | Review: {h(n['verification_status'])}</p>
    <h2>{h(n['summary'])}</h2>
    <pre>{h(n['body'])}</pre>
    <div class='card'><h2>Verification</h2><p>{h(n['source_note'])}</p></div>
    </div>
    """)

@app.route("/admin")
def admin():
    conn = db()
    news_rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 80").fetchall()
    event_rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 80").fetchall()
    rsvps_rows = conn.execute("SELECT * FROM event_rsvps ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()
    content = "<div class='card'><h1>HRM Admin</h1></div><div class='card'><h2>News Review</h2>"
    for n in news_rows:
        content += f"<div class='card'><b>{h(n['title'])}</b><br>Public: {h(n['status'])} | Review: {h(n['verification_status'])}<br><a href='/admin/news/{n['id']}/approved'>Approve</a><a href='/admin/news/{n['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Event Review</h2>"
    for e in event_rows:
        content += f"<div class='card'><b>{h(e['title'])}</b><br>Status: {h(e['status'])}<br><a href='/admin/event/{e['id']}/approved'>Approve</a><a href='/admin/event/{e['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>RSVP Review</h2>"
    for r in rsvps_rows:
        content += f"<div class='card'><b>{h(r['event_title'])}</b><br>{h(r['attendee_name'])} • {h(r['status'])}</div>"
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    content += "</div>"
    return render(content)

@app.route("/admin/news/<int:id>/<status>")
def admin_news(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    verification = "verified" if status == "approved" else "rejected"
    conn = db()
    conn.execute("UPDATE news_posts SET status=?, verification_status=? WHERE id=?", (status, verification, id))
    conn.commit()
    conn.close()
    log(f"News {status}", session.get("user","admin"))
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
