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

    for col, typ in [
        ("sender","TEXT"),("recipient","TEXT DEFAULT 'admin'"),
        ("subject","TEXT DEFAULT ''"),("body","TEXT DEFAULT ''"),
        ("status","TEXT DEFAULT 'unread'"),("created_at","TEXT DEFAULT ''")
    ]:
        add_col(cur, "messages", col, typ)

    cur.execute("""CREATE TABLE IF NOT EXISTS contacts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner TEXT,
        contact_name TEXT,
        contact_username TEXT,
        contact_note TEXT,
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
body{margin:0;background:#050505;color:white;font-family:Arial}
.top{background:#101010;padding:15px;border-bottom:1px solid #222;position:sticky;top:0;z-index:2}
.logo{font-size:22px;font-weight:900}
.wrap{padding:14px;max-width:1100px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:16px;margin:12px 0}
.hero{text-align:center;padding:30px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:13px;margin:8px 0;background:#0b0b0b;color:white;border:1px solid #333;border-radius:12px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:12px;padding:13px 18px;font-weight:900}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:bold}
.chatbox{display:flex;flex-direction:column;gap:8px}
.bubble{max-width:78%;padding:12px;border-radius:18px;margin:5px 0}
.me{align-self:flex-end;background:#00dd99;color:#001}
.them{align-self:flex-start;background:#242424;color:white}
.chatrow{display:flex;justify-content:space-between;gap:10px;align-items:center;border-bottom:1px solid #292929;padding:12px 0}
.avatar{width:42px;height:42px;border-radius:50%;background:#00dd99;color:#000;font-weight:900;display:inline-flex;align-items:center;justify-content:center;margin-right:10px}
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
<a href="/chats">Chats</a>
<a href="/contacts">Contacts</a>
<a href="/messages">Messages</a>
<a href="/events">Events</a>
<a href="/rsvps">RSVPs</a>
<a href="/attendance_dashboard">Attendance</a>
<a href="/signals">Signals</a>
<a href="/leads">Leads</a>
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
        "events": conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        "messages": conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"],
        "contacts": conn.execute("SELECT COUNT(*) c FROM contacts").fetchone()["c"],
        "rsvps": conn.execute("SELECT COUNT(*) c FROM event_rsvps").fetchone()["c"],
        "attendance": conn.execute("SELECT COUNT(*) c FROM event_attendance").fetchone()["c"],
    }
    conn.close()
    return render(f"""
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>Messenger Pro — WhatsApp-style local community chat</p>
    <p>Private-first, local-first, simple, auditable.</p>
    </div>
    <div class='grid'>
    <div class='card'><h2>{stats['messages']}</h2><p>Messages</p></div>
    <div class='card'><h2>{stats['contacts']}</h2><p>Contacts</p></div>
    <div class='card'><h2>{stats['events']}</h2><p>Events</p></div>
    <div class='card'><h2>{stats['rsvps']}</h2><p>RSVPs</p></div>
    <div class='card'><h2>{stats['attendance']}</h2><p>Attendance</p></div>
    </div>
    <div class='card'>
    <a class='badge' href='/chats'>Open Chats</a>
    <a class='badge' href='/contacts'>Add Contact</a>
    <a class='badge' href='/messages'>Send Message</a>
    </div>
    """)

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
    <p class='small'>Default admin: N24-7 / 2525</p>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/contacts", methods=["GET","POST"])
def contacts():
    owner = current_user()
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO contacts(owner,contact_name,contact_username,contact_note,created_at)
        VALUES(?,?,?,?,?)""", (
            owner, request.form["contact_name"], request.form["contact_username"], request.form["contact_note"], now()
        ))
        conn.commit()
        conn.close()
        log("Contact added", owner)
        return redirect("/contacts")

    conn = db()
    rows = conn.execute("SELECT * FROM contacts WHERE owner=? OR owner='guest' ORDER BY id DESC", (owner,)).fetchall()
    users = conn.execute("SELECT username FROM users ORDER BY username").fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>👥 Contacts</h1><p class='green'>Add people by username or nickname.</p></div>
    <div class='card'>
    <form method='POST'>
    <input name='contact_name' placeholder='Display name / nickname' required>
    <input name='contact_username' placeholder='Username e.g. N24-7 or admin' required>
    <textarea name='contact_note' placeholder='Note'></textarea>
    <button>Add Contact</button>
    </form></div>
    <div class='card'><h2>Known Users</h2>
    """
    for u in users:
        content += f"<p>@{h(u['username'])} <a href='/chat/{h(u['username'])}'>Chat</a></p>"
    content += "</div><div class='card'><h2>Your Contacts</h2>"
    for r in rows:
        first = h((r["contact_name"] or r["contact_username"] or "?")[:1]).upper()
        content += f"""
        <div class='chatrow'>
        <div><span class='avatar'>{first}</span><b>{h(r['contact_name'])}</b><br><span class='small'>@{h(r['contact_username'])} • {h(r['contact_note'])}</span></div>
        <a class='badge' href='/chat/{h(r['contact_username'])}'>Chat</a>
        </div>
        """
    content += "</div>"
    return render(content)

@app.route("/chats")
def chats():
    user = current_user()
    conn = db()
    rows = conn.execute("""
    SELECT * FROM messages
    WHERE sender=? OR recipient=? OR recipient='admin'
    ORDER BY id DESC
    LIMIT 200
    """, (user, user)).fetchall()
    conn.close()

    people = {}
    for m in rows:
        other = m["recipient"] if m["sender"] == user else m["sender"]
        if other not in people:
            people[other] = m

    content = """
    <div class='card hero'><h1>💬 Chats</h1><p class='green'>WhatsApp-style inbox.</p></div>
    <div class='card'>
    <a class='badge' href='/chat/admin'>Chat Admin</a>
    <a class='badge' href='/contacts'>Contacts</a>
    <a class='badge' href='/messages'>New Message</a>
    </div>
    <div class='card'>
    """
    if not people:
        content += "<p>No chats yet. Start with admin.</p>"
    for person, m in people.items():
        first = h((person or "?")[:1]).upper()
        unread = "🟢" if m["status"] == "unread" and m["recipient"] == user else ""
        content += f"""
        <a href='/chat/{h(person)}'>
        <div class='chatrow'>
        <div><span class='avatar'>{first}</span><b>@{h(person)}</b><br><span class='small'>{h(m['body'])[:60]}...</span></div>
        <div class='small'>{unread}<br>{h(m['created_at'])}</div>
        </div>
        </a>
        """
    content += "</div>"
    return render(content)

@app.route("/chat/<name>", methods=["GET","POST"])
def chat(name):
    user = current_user()
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO messages(sender,recipient,subject,body,status,created_at)
        VALUES(?,?,?,?,?,?)""", (user, name, request.form.get("subject",""), request.form["body"], "unread", now()))
        conn.commit()
        conn.close()
        log(f"Chat message sent to {name}", user)
        return redirect(f"/chat/{name}")

    conn = db()
    conn.execute("UPDATE messages SET status='read' WHERE recipient=? AND sender=?", (user, name))
    rows = conn.execute("""
    SELECT * FROM messages
    WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)
    ORDER BY id ASC
    """, (user, name, name, user)).fetchall()
    conn.commit()
    conn.close()

    content = f"""
    <div class='card hero'><h1>💬 Chat with @{h(name)}</h1><p class='green'>Local-first OAP messenger.</p></div>
    <div class='card chatbox'>
    """
    for m in rows:
        klass = "me" if m["sender"] == user else "them"
        label = "You" if m["sender"] == user else "@" + h(m["sender"])
        content += f"""
        <div class='bubble {klass}'>
        <b>{label}</b><br>
        {h(m['body'])}
        <br><span class='small'>{h(m['created_at'])}</span>
        </div>
        """
    content += f"""
    </div>
    <div class='card'>
    <form method='POST'>
    <input name='subject' placeholder='Subject optional'>
    <textarea name='body' placeholder='Type message...' required></textarea>
    <button>Send</button>
    </form>
    </div>
    """
    return render(content)

@app.route("/messages", methods=["GET","POST"])
def messages():
    if request.method == "POST":
        sender = current_user()
        conn = db()
        conn.execute("""INSERT INTO messages(sender,recipient,subject,body,status,created_at)
        VALUES(?,?,?,?,?,?)""", (
            sender, request.form["recipient"], request.form["subject"], request.form["body"], "unread", now()
        ))
        conn.commit()
        conn.close()
        log("Message sent", sender)
        return redirect(f"/chat/{request.form['recipient']}")

    user = current_user()
    conn = db()
    rows = conn.execute("""
    SELECT * FROM messages
    WHERE recipient=? OR sender=? OR recipient='admin'
    ORDER BY id DESC LIMIT 100
    """, (user, user)).fetchall()
    conn.close()

    content = """
    <div class='card'><h1>New Message</h1>
    <form method='POST'>
    <input name='recipient' placeholder='Recipient username' value='admin'>
    <input name='subject' placeholder='Subject'>
    <textarea name='body' placeholder='Message'></textarea>
    <button>Send</button>
    </form></div>
    <div class='card'><h2>Recent Messages</h2>
    """
    for m in rows:
        content += f"""
        <div class='card'>
        <b>{h(m['subject'])}</b><br>
        {h(m['sender'])} → {h(m['recipient'])}<br>
        <p>{h(m['body'])}</p>
        <a href='/chat/{h(m['sender'] if m['sender'] != user else m['recipient'])}'>Open Chat</a>
        </div>
        """
    content += "</div>"
    return render(content)

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method == "POST":
        username = current_user()
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
        return redirect("/events")

    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>Events</h1>
    <form method='POST'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'><option>Watch Party</option><option>Creator Meetup</option><option>Business Popup</option><option>Community Event</option></select>
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
        content += f"<div class='card'><b>{h(e['title'])}</b><br>ID: {e['id']} • {h(e['event_type'])} • {h(e['city'])}<br><a href='/event/{e['id']}'>Open</a></div>"
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
    <p>{h(e['event_date'])} {h(e['event_time'])} • {h(e['venue'])}</p>
    <p>{h(e['description'])}</p>
    <a class='badge' href='/rsvps?event_id={e['id']}&event_title={h(e['title'])}'>RSVP</a>
    </div>
    """)

@app.route("/rsvps", methods=["GET","POST"])
def rsvps():
    if request.method == "POST":
        username = current_user()
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
        return redirect("/rsvps")

    event_id = request.args.get("event_id","")
    event_title = request.args.get("event_title","")
    conn = db()
    rows = conn.execute("SELECT * FROM event_rsvps ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = f"""
    <div class='card'><h1>RSVPs</h1>
    <form method='POST'>
    <input name='event_id' value='{h(event_id)}' placeholder='Event ID'>
    <input name='event_title' value='{h(event_title)}' placeholder='Event title' required>
    <input name='attendee_name' placeholder='Name / nickname'>
    <input name='attendee_contact' placeholder='Contact'>
    <input name='quantity' value='1'>
    <textarea name='note' placeholder='Note'></textarea>
    <button>RSVP</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['event_title'])}</b><br>{h(r['attendee_name'])} • Qty {r['quantity']} • {h(r['status'])}</div>"
    return render(content)

@app.route("/rsvp/<int:id>/<status>")
def rsvp_status(id, status):
    if status not in ["new","contacted","confirmed","cancelled"]:
        return redirect("/rsvps")
    conn = db()
    conn.execute("UPDATE event_rsvps SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    return redirect("/rsvps")

@app.route("/attendance", methods=["GET","POST"])
def attendance():
    if request.method == "POST":
        recorder = current_user()
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
        return redirect("/attendance_dashboard")
    return render("<div class='card'><h1>Attendance</h1><form method='POST'><input name='event_id' placeholder='Event ID'><input name='event_title' placeholder='Event title'><input name='invited_count' value='0'><input name='attended_count' value='0'><input name='new_people_count' value='0'><input name='returning_people_count' value='0'><input name='products_sold' value='0'><input name='revenue' placeholder='Revenue'><textarea name='notes'></textarea><button>Save</button></form></div>")

@app.route("/attendance_dashboard")
def attendance_dashboard():
    conn = db()
    total_attended = conn.execute("SELECT COALESCE(SUM(attended_count),0) c FROM event_attendance").fetchone()["c"]
    total_invited = conn.execute("SELECT COALESCE(SUM(invited_count),0) c FROM event_attendance").fetchone()["c"]
    rows = conn.execute("SELECT * FROM event_attendance ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = f"<div class='card hero'><h1>Attendance Dashboard</h1></div><div class='grid'><div class='card'><h2>{total_invited}</h2><p>Invited</p></div><div class='card'><h2>{total_attended}</h2><p>Attended</p></div></div>"
    for r in rows:
        content += f"<div class='card'><b>{h(r['event_title'])}</b><br>Attended: {r['attended_count']}<p>{h(r['notes'])}</p></div>"
    return render(content)

@app.route("/reviews", methods=["GET","POST"])
def reviews():
    if request.method == "POST":
        conn = db()
        conn.execute("""INSERT INTO event_reviews(event_id,event_title,reviewer,what_worked,what_failed,lesson,next_action,rating,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (
            request.form["event_id"], request.form["event_title"], current_user(),
            request.form["what_worked"], request.form["what_failed"], request.form["lesson"],
            request.form["next_action"], request.form["rating"], now()
        ))
        conn.commit()
        conn.close()
        return redirect("/reviews")
    return render("<div class='card'><h1>Reviews</h1><form method='POST'><input name='event_id'><input name='event_title' placeholder='Event title'><textarea name='what_worked'></textarea><textarea name='what_failed'></textarea><textarea name='lesson'></textarea><textarea name='next_action'></textarea><input name='rating'><button>Save</button></form></div>")

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
        return redirect("/signals")
    return render("<div class='card'><h1>Signals</h1><form method='POST'><select name='signal_type'><option>Opportunity</option><option>Need</option><option>Risk</option><option>Idea</option></select><input name='title'><input name='location'><textarea name='description'></textarea><textarea name='opportunity'></textarea><textarea name='risk_note'></textarea><button>Save</button></form></div>")

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
        return redirect("/leads")
    return render("<div class='card'><h1>Business Leads</h1><form method='POST'><input name='business_name'><input name='category'><input name='contact'><input name='location'><textarea name='opportunity'></textarea><button>Save</button></form></div>")

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
    return render(f"<div class='card'><h1>{h(n['title'])}</h1><p>{h(n['summary'])}</p><pre>{h(n['body'])}</pre></div>")

@app.route("/admin")
def admin():
    conn = db()
    events_rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 80").fetchall()
    msgs = conn.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()
    content = "<div class='card'><h1>Admin</h1></div><div class='card'><h2>Events</h2>"
    for e in events_rows:
        content += f"<div class='card'><b>{h(e['title'])}</b> • {h(e['status'])}<br><a href='/admin/event/{e['id']}/approved'>Approve</a><a href='/admin/event/{e['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Messages</h2>"
    for m in msgs:
        content += f"<div class='card'>{h(m['sender'])} → {h(m['recipient'])}<p>{h(m['body'])}</p></div>"
    content += "</div><div class='card'><h2>Logs</h2>"
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
    return redirect("/admin")

@app.route("/admin/event/<int:id>/<status>")
def admin_event(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE events SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
