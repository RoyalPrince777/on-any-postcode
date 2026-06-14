from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "oap-change-this-secret"
DB = "oap.db"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password TEXT NOT NULL,
        postcode TEXT,
        borough TEXT,
        county_region TEXT,
        country TEXT,
        continent TEXT,
        role TEXT DEFAULT 'member',
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        title TEXT,
        body TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        body TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        category TEXT,
        location TEXT,
        description TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        location TEXT,
        event_date TEXT,
        description TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        detail TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hrm_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal TEXT,
        lesson TEXT,
        created_at TEXT
    )
    """)

    con.commit()
    con.close()


def audit(action, detail):
    con = db()
    con.execute(
        "INSERT INTO audit_logs(action, detail, created_at) VALUES (?, ?, ?)",
        (action, detail, now())
    )
    con.commit()
    con.close()


def current_user():
    if "user_id" not in session:
        return None
    con = db()
    user = con.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    con.close()
    return user


BASE = """
<!doctype html>
<html>
<head>
<title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:#07120d;color:#f4fff8;margin:0}
header{background:#00a86b;padding:15px;color:#001b10}
header h2{margin:0}
nav{margin-top:10px}
nav a{display:inline-block;color:white;background:#0b3d28;margin:4px;padding:8px 10px;border-radius:9px;text-decoration:none;font-weight:bold}
.card{background:#10281b;margin:14px;padding:16px;border-radius:15px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px}
.tile{background:#143521;padding:16px;border-radius:14px;text-align:center}
input,textarea,select,button{width:100%;padding:12px;margin:7px 0;border-radius:10px;border:0;box-sizing:border-box}
button{background:#00a86b;color:white;font-weight:bold}
a{color:#58ffb0}
.small{color:#b7d9c5;font-size:13px}
.badge{background:#00a86b;color:#001b10;padding:4px 8px;border-radius:8px;font-weight:bold}
</style>
</head>
<body>
<header>
<h2>👑 ON ANY POSTCODE</h2>
<div>Born Local. Built Global. Earth Is Our Turf.</div>
<nav>
<a href="/">OAP World</a>
<a href="/community">Community</a>
<a href="/sports">Sports</a>
<a href="/culture">Culture</a>
<a href="/music">Music</a>
<a href="/artists">Artists</a>
<a href="/business">Business</a>
<a href="/events">Events</a>
<a href="/news">News</a>
<a href="/explorer">Explorer</a>
<a href="/weather">Weather</a>
<a href="/dashboard">Dashboard</a>
{% if user %}
<a href="/my_world">My World</a>
<a href="/leave">Leave My World</a>
{% else %}
<a href="/join">Join OAP</a>
<a href="/enter">Enter My World</a>
{% endif %}
</nav>
</header>
{{content|safe}}
</body>
</html>
"""


def page(content):
    return render_template_string(BASE, content=content, user=current_user())


@app.route("/")
def home():
    return page("""
    <div class="card">
    <h1>Welcome to OAP 🌍</h1>
    <p>OAP World is open. Join to create your World, post, message, build trust records and contribute.</p>
    </div>

    <div class="grid">
    <a class="tile" href="/community">🌍 Community</a>
    <a class="tile" href="/sports">⚽ Sports</a>
    <a class="tile" href="/culture">🎭 Culture</a>
    <a class="tile" href="/music">🎵 Music</a>
    <a class="tile" href="/artists">🎨 Artists</a>
    <a class="tile" href="/business">🏪 Business</a>
    <a class="tile" href="/events">🎪 Events</a>
    <a class="tile" href="/news">📰 News</a>
    <a class="tile" href="/explorer">🧭 Explorer</a>
    <a class="tile" href="/weather">🌦 Weather</a>
    <a class="tile" href="/my_world">👤 Enter My World</a>
    </div>
    """)


@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        postcode = request.form.get("postcode", "").strip()
        borough = request.form.get("borough", "").strip()
        county_region = request.form.get("county_region", "").strip()
        country = request.form.get("country", "").strip()
        continent = request.form.get("continent", "").strip()

        if not username or not password or not country or not continent:
            return page("<div class='card'>Username, password, country and continent are required.</div>")

        hashed = generate_password_hash(password)

        try:
            con = db()
            con.execute("""
                INSERT INTO users
                (nickname, username, email, password, postcode, borough, county_region, country, continent, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nickname, username, email, hashed, postcode, borough, county_region, country, continent, "member", now()))
            con.commit()
            con.close()
            audit("join_oap", f"{username} joined from {country}, {continent}")
            return redirect("/welcome")
        except sqlite3.IntegrityError:
            return page("<div class='card'>Username already exists. Choose another.</div>")

    return page("""
    <div class="card">
    <h2>Join OAP 🌍</h2>
    <form method="post">
    <input name="nickname" placeholder="Nickname">
    <input name="username" placeholder="Username *">
    <input name="email" placeholder="Email optional">
    <input name="password" type="password" placeholder="Password *">

    <h3>Location</h3>
    <input name="postcode" placeholder="Postcode optional">
    <input name="borough" placeholder="Borough optional">
    <input name="county_region" placeholder="County / Region optional">
    <input name="country" placeholder="Country *">
    <input name="continent" placeholder="Continent *">

    <button>Join OAP</button>
    </form>
    </div>
    """)


@app.route("/welcome")
def welcome():
    return page("""
    <div class="card">
    <h1>Welcome to OAP 🌍</h1>
    <p>Your World has been created.</p>
    <p>Choose where to go:</p>
    </div>
    <div class="grid">
    <a class="tile" href="/community">🌍 Community</a>
    <a class="tile" href="/sports">⚽ Sports</a>
    <a class="tile" href="/culture">🎭 Culture</a>
    <a class="tile" href="/music">🎵 Music</a>
    <a class="tile" href="/artists">🎨 Artists</a>
    <a class="tile" href="/business">🏪 Business</a>
    <a class="tile" href="/events">🎪 Events</a>
    <a class="tile" href="/news">📰 News</a>
    <a class="tile" href="/explorer">🧭 Explorer</a>
    <a class="tile" href="/weather">🌦 Weather</a>
    <a class="tile" href="/enter">👤 Enter My World</a>
    </div>
    """)


@app.route("/enter", methods=["GET", "POST"])
def enter():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        con = db()
        user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        con.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            audit("enter_my_world", f"{username} entered My World")
            return redirect("/my_world")

        return page("<div class='card'>Invalid details. Try again.</div>")

    return page("""
    <div class="card">
    <h2>Enter My World 👤</h2>
    <form method="post">
    <input name="username" placeholder="Username">
    <input name="password" type="password" placeholder="Password">
    <button>Enter My World</button>
    </form>
    </div>
    """)


@app.route("/leave")
def leave():
    if "username" in session:
        audit("leave_my_world", f"{session['username']} left My World")
    session.clear()
    return redirect("/")


@app.route("/my_world", methods=["GET", "POST"])
def my_world():
    user = current_user()
    if not user:
        return redirect("/enter")

    if request.method == "POST":
        category = request.form.get("category", "Community")
        title = request.form.get("title", "")
        body = request.form.get("body", "")
        con = db()
        con.execute(
            "INSERT INTO posts(user_id, category, title, body, created_at) VALUES (?, ?, ?, ?, ?)",
            (user["id"], category, title, body, now())
        )
        con.commit()
        con.close()
        audit("post_created", f"{user['username']} posted in {category}")
        return redirect("/my_world")

    con = db()
    posts = con.execute("""
        SELECT posts.*, users.username, users.country, users.continent
        FROM posts JOIN users ON posts.user_id = users.id
        ORDER BY posts.id DESC LIMIT 20
    """).fetchall()
    con.close()

    post_html = "".join([
        f"""
        <div class='card'>
        <span class='badge'>{p['category']}</span>
        <h3>{p['title']}</h3>
        <p>{p['body']}</p>
        <p class='small'>By {p['username']} — {p['country']} / {p['continent']} — {p['created_at']}</p>
        </div>
        """
        for p in posts
    ])

    return page(f"""
    <div class="card">
    <h2>👤 My World</h2>
    <p>Welcome {user['username']}.</p>
    <p class="small">{user['postcode']} {user['borough']} {user['county_region']} {user['country']} {user['continent']}</p>

    <form method="post">
    <select name="category">
    <option>Community</option>
    <option>Sports</option>
    <option>Culture</option>
    <option>Music</option>
    <option>Artists</option>
    <option>Business</option>
    <option>Events</option>
    <option>News</option>
    </select>
    <input name="title" placeholder="Title">
    <textarea name="body" placeholder="What are you contributing?"></textarea>
    <button>Post to OAP World</button>
    </form>
    </div>
    {post_html}
    """)


def board(category, emoji):
    con = db()
    posts = con.execute("""
        SELECT posts.*, users.username, users.country, users.continent
        FROM posts JOIN users ON posts.user_id = users.id
        WHERE posts.category=?
        ORDER BY posts.id DESC
    """, (category,)).fetchall()
    con.close()

    html = "".join([
        f"<div class='card'><h3>{p['title']}</h3><p>{p['body']}</p><p class='small'>By {p['username']} — {p['country']} / {p['continent']}</p></div>"
        for p in posts
    ]) or "<div class='card'>No posts yet. Be the first inside My World.</div>"

    return page(f"<div class='card'><h1>{emoji} {category}</h1></div>{html}")


@app.route("/community")
def community():
    return board("Community", "🌍")


@app.route("/sports")
def sports():
    return board("Sports", "⚽")


@app.route("/culture")
def culture():
    return board("Culture", "🎭")


@app.route("/music")
def music():
    return board("Music", "🎵")


@app.route("/artists")
def artists():
    return board("Artists", "🎨")


@app.route("/news")
def news():
    return board("News", "📰")


@app.route("/weather")
def weather():
    return page("""
    <div class="card">
    <h1>🌦 Weather</h1>
    <p>Weather layer prepared. First version will connect postcode, country and event planning.</p>
    </div>
    """)


@app.route("/business", methods=["GET", "POST"])
def business():
    user = current_user()

    if request.method == "POST":
        if not user:
            return redirect("/enter")
        name = request.form.get("name", "")
        category = request.form.get("category", "")
        location = request.form.get("location", "")
        description = request.form.get("description", "")
        con = db()
        con.execute(
            "INSERT INTO businesses(user_id, name, category, location, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], name, category, location, description, now())
        )
        con.commit()
        con.close()
        audit("business_created", f"{user['username']} added business {name}")
        return redirect("/business")

    con = db()
    rows = con.execute("SELECT * FROM businesses ORDER BY id DESC").fetchall()
    con.close()

    cards = "".join([
        f"<div class='card'><h3>{b['name']}</h3><p>{b['description']}</p><p class='small'>{b['category']} — {b['location']}</p></div>"
        for b in rows
    ]) or "<div class='card'>No businesses yet.</div>"

    form = """
    <div class="card">
    <h2>🏪 Add Business</h2>
    <form method="post">
    <input name="name" placeholder="Business name">
    <input name="category" placeholder="Category">
    <input name="location" placeholder="Location">
    <textarea name="description" placeholder="Description"></textarea>
    <button>Add Business</button>
    </form>
    </div>
    """ if user else "<div class='card'><a href='/enter'>Enter My World</a> to add a business.</div>"

    return page(f"<div class='card'><h1>🏪 Business</h1></div>{form}{cards}")


@app.route("/events", methods=["GET", "POST"])
def events():
    user = current_user()

    if request.method == "POST":
        if not user:
            return redirect("/enter")
        name = request.form.get("name", "")
        location = request.form.get("location", "")
        event_date = request.form.get("event_date", "")
        description = request.form.get("description", "")
        con = db()
        con.execute(
            "INSERT INTO events(user_id, name, location, event_date, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], name, location, event_date, description, now())
        )
        con.commit()
        con.close()
        audit("event_created", f"{user['username']} added event {name}")
        return redirect("/events")

    con = db()
    rows = con.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
    con.close()

    cards = "".join([
        f"<div class='card'><h3>{e['name']}</h3><p>{e['description']}</p><p class='small'>{e['event_date']} — {e['location']}</p></div>"
        for e in rows
    ]) or "<div class='card'>No events yet.</div>"

    form = """
    <div class="card">
    <h2>🎪 Add Event</h2>
    <form method="post">
    <input name="name" placeholder="Event name">
    <input name="location" placeholder="Location">
    <input name="event_date" placeholder="Date">
    <textarea name="description" placeholder="Description"></textarea>
    <button>Add Event</button>
    </form>
    </div>
    """ if user else "<div class='card'><a href='/enter'>Enter My World</a> to add an event.</div>"

    return page(f"<div class='card'><h1>🎪 Events</h1></div>{form}{cards}")


@app.route("/explorer")
def explorer():
    q = request.args.get("q", "").strip()
    results = ""

    if q:
        like = f"%{q}%"
        con = db()
        posts = con.execute("SELECT title, body, category FROM posts WHERE title LIKE ? OR body LIKE ?", (like, like)).fetchall()
        users = con.execute("SELECT username, country, continent FROM users WHERE username LIKE ? OR country LIKE ? OR continent LIKE ?", (like, like, like)).fetchall()
        businesses = con.execute("SELECT name, description, location FROM businesses WHERE name LIKE ? OR description LIKE ? OR location LIKE ?", (like, like, like)).fetchall()
        events_rows = con.execute("SELECT name, description, location FROM events WHERE name LIKE ? OR description LIKE ? OR location LIKE ?", (like, like, like)).fetchall()
        con.close()

        results += "".join([f"<div class='card'><b>Post:</b> {p['title']} <p>{p['body']}</p><p class='small'>{p['category']}</p></div>" for p in posts])
        results += "".join([f"<div class='card'><b>Member:</b> {u['username']} <p>{u['country']} / {u['continent']}</p></div>" for u in users])
        results += "".join([f"<div class='card'><b>Business:</b> {b['name']} <p>{b['description']}</p><p class='small'>{b['location']}</p></div>" for b in businesses])
        results += "".join([f"<div class='card'><b>Event:</b> {e['name']} <p>{e['description']}</p><p class='small'>{e['location']}</p></div>" for e in events_rows])

    return page(f"""
    <div class="card">
    <h1>🧭 Explorer</h1>
    <form method="get">
    <input name="q" placeholder="Search OAP World" value="{q}">
    <button>Search</button>
    </form>
    </div>
    {results}
    """)


@app.route("/messages", methods=["GET", "POST"])
def messages():
    user = current_user()
    if not user:
        return redirect("/enter")

    if request.method == "POST":
        body = request.form.get("body", "")
        con = db()
        con.execute("INSERT INTO messages(sender_id, body, created_at) VALUES (?, ?, ?)", (user["id"], body, now()))
        con.commit()
        con.close()
        audit("message_sent", f"{user['username']} sent a message")
        return redirect("/messages")

    con = db()
    rows = con.execute("""
        SELECT messages.*, users.username
        FROM messages JOIN users ON messages.sender_id = users.id
        ORDER BY messages.id DESC
    """).fetchall()
    con.close()

    html = "".join([
        f"<div class='card'><b>{m['username']}</b><p>{m['body']}</p><p class='small'>{m['created_at']}</p></div>"
        for m in rows
    ])

    return page(f"""
    <div class="card">
    <h2>💬 Messages</h2>
    <form method="post">
    <textarea name="body" placeholder="Send message"></textarea>
    <button>Send</button>
    </form>
    </div>
    {html}
    """)


@app.route("/hrm_memory", methods=["GET", "POST"])
def hrm_memory():
    if request.method == "POST":
        signal = request.form.get("signal", "")
        lesson = request.form.get("lesson", "")
        con = db()
        con.execute("INSERT INTO hrm_memory(signal, lesson, created_at) VALUES (?, ?, ?)", (signal, lesson, now()))
        con.commit()
        con.close()
        audit("hrm_memory", signal)
        return redirect("/hrm_memory")

    con = db()
    rows = con.execute("SELECT * FROM hrm_memory ORDER BY id DESC").fetchall()
    con.close()

    html = "".join([
        f"<div class='card'><h3>{r['signal']}</h3><p>{r['lesson']}</p><p class='small'>{r['created_at']}</p></div>"
        for r in rows
    ])

    return page(f"""
    <div class="card">
    <h2>🧠 HRM Memory</h2>
    <form method="post">
    <input name="signal" placeholder="Signal">
    <textarea name="lesson" placeholder="Lesson learned"></textarea>
    <button>Record Lesson</button>
    </form>
    </div>
    {html}
    """)


@app.route("/dashboard")
def dashboard():
    con = db()
    users = con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    posts = con.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
    businesses = con.execute("SELECT COUNT(*) c FROM businesses").fetchone()["c"]
    events_count = con.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    logs = con.execute("SELECT COUNT(*) c FROM audit_logs").fetchone()["c"]
    con.close()

    return page(f"""
    <div class="card">
    <h1>📊 OAP Dashboard</h1>
    <p>Members: {users}</p>
    <p>Posts: {posts}</p>
    <p>Businesses: {businesses}</p>
    <p>Events: {events_count}</p>
    <p>Audit Logs: {logs}</p>
    </div>
    <div class="card">
    <h2>🚦 Launch Test Goal</h2>
    <p>10 members, 10 posts, 3 businesses, 3 events, 0 crashes.</p>
    </div>
    """)


@app.route("/admin")
def admin():
    con = db()
    logs = con.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50").fetchall()
    con.close()

    html = "".join([
        f"<div class='card'><b>{l['action']}</b><p>{l['detail']}</p><p class='small'>{l['created_at']}</p></div>"
        for l in logs
    ])

    return page(f"""
    <div class="card">
    <h1>🛡️ Admin / Audit</h1>
    <p>Guardian reviews. Chancellor records. Sentinel protects.</p>
    <p><a href="/hrm_memory">Open HRM Memory</a></p>
    </div>
    {html}
    """)


@app.route("/verification")
def verification():
    return page("""
    <div class="card">
    <h1>✅ Verification</h1>
    <p>Trust badges come through proof, contribution, consistency, HRM review, audit records and human approval.</p>
    </div>
    """)


@app.route("/revenue")
def revenue():
    return page("""
    <div class="card">
    <h1>💷 Revenue Board</h1>
    <p>Fastest path: members → posts → businesses → events → products → OAP Market later.</p>
    <p>No bank claims. No debt-first model. Real value first.</p>
    </div>
    """)


@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    init_db()
    print("OAP CORE v1.1 running")
    print("Open: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
