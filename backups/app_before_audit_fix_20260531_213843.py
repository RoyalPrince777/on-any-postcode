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


def save_memory(memory_type, title, summary, lesson, next_action, visibility="private"):
    conn = db()
    conn.execute("""INSERT INTO hrm_memory_logs(memory_type,title,summary,lesson,next_action,visibility,created_at)
    VALUES(?,?,?,?,?,?,?)""", (memory_type, title, summary, lesson, next_action, visibility, now()))
    conn.commit()
    conn.close()


def current_member():
    return session.get("user", "guest")


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        username TEXT UNIQUE,
        oap_email TEXT,
        email TEXT,
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

    for col, typ in [
        ("nickname", "TEXT"),
        ("oap_email", "TEXT"),
        ("email", "TEXT"),
        ("postcode", "TEXT"),
        ("borough", "TEXT"),
        ("county_region", "TEXT"),
        ("country", "TEXT"),
        ("continent", "TEXT"),
        ("weather_location", "TEXT"),
        ("verification_level", "TEXT DEFAULT 'starter'"),
        ("role", "TEXT DEFAULT 'member'")
    ]:
        add_col(cur, "users", col, typ)

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

    user = cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,)).fetchone()
    if user:
        cur.execute("""UPDATE users SET nickname=?, oap_email=?, email=?, password=?, role=?, verification_level=?
        WHERE username=?""", (
            "N24-7", ADMIN_EMAIL, ADMIN_EMAIL,
            generate_password_hash(ADMIN_PASSWORD),
            "admin", "founder", ADMIN_USERNAME
        ))
    else:
        cur.execute("""INSERT INTO users(
            nickname, username, oap_email, email, password, postcode, borough, county_region,
            country, continent, weather_location, verification_level, role, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            "N24-7", ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_EMAIL,
            generate_password_hash(ADMIN_PASSWORD),
            "CR4", "Merton", "Greater London",
            "UK", "Europe", "London", "founder", "admin", now()
        ))

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
@{{session.get("user")}} <a href="/leave">Leave My World</a>
{% else %}
<a href="/join">Join OAP</a> <a href="/enter">Enter My World</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/privacy">Privacy</a>
<a href="/my_world">My World</a>
<a href="/community">Community</a>
<a href="/sports">Sports</a>
<a href="/culture">Culture</a>
<a href="/music">Music</a>
<a href="/artists">Artists</a>
<a href="/events">Events</a>
<a href="/news">News</a>
<a href="/search">Search</a>
<a href="/explorer">Explorer</a>
<a href="/weather">Weather</a>
<a href="/business">Business</a>
<a href="/messages">Messenger</a>
<a href="/awards">Awards</a>
<a href="/trust_badge">Trust Badge</a>
<a href="/opportunity_board">Opportunity Board</a>
<a href="/payouts">Payouts</a>
<a href="/approvals">Approvals</a>
<a href="/command_center">Command Center</a>
<a href="/routes">Routes</a>
<a href="/admin">Admin</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""


def render(content):
    return render_template_string(BASE, content=content)


@app.route("/favicon.ico")
def favicon():
    return ("", 204)


@app.route("/")
def home():
    conn = db()
    stats = {
        "members": conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        "culture": conn.execute("SELECT COUNT(*) c FROM culture_posts").fetchone()["c"],
        "artists": conn.execute("SELECT COUNT(*) c FROM artists").fetchone()["c"],
        "events": conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        "opportunities": conn.execute("SELECT COALESCE(SUM(amount),0) c FROM revenues").fetchone()["c"],
        "pending_payouts": conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='pending'").fetchone()["c"],
    }
    conn.close()

    return render(f"""
    <div class='card hero'>
      <h1>🌍 ON ANY POSTCODE 👑</h1>
      <p class='green'>Join OAP. Enter My World. Build trust through contribution.</p>
      <p>Every postcode has a story. Every culture has a song. Every community has a voice. Every member has a World.</p>
    </div>

    <div class='grid'>
      <div class='card'><h2>{stats['members']}</h2><p>Members</p></div>
      <div class='card'><h2>{stats['culture']}</h2><p>Culture Records</p></div>
      <div class='card'><h2>{stats['artists']}</h2><p>Artists</p></div>
      <div class='card'><h2>{stats['events']}</h2><p>Events</p></div>
      <div class='card'><h2>£{stats['opportunities']:.2f}</h2><p>Opportunity Board</p></div>
      <div class='card'><h2>£{stats['pending_payouts']:.2f}</h2><p>Pending Payouts</p></div>
    </div>

    <div class='card'>
      <a class='badge' href='/join'>Join OAP</a>
      <a class='badge' href='/enter'>Enter My World</a>
      <a class='badge' href='/privacy'>Privacy & Trust</a>
      <a class='badge' href='/search'>OAP Search</a>
      <a class='badge' href='/explorer'>Explorer</a>
      <a class='badge' href='/command_center'>Command Center</a>
    </div>
    """)


@app.route("/join", methods=["GET", "POST"])
@app.route("/signup", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        conn = db()
        try:
            conn.execute("""INSERT INTO users(
                nickname, username, oap_email, email, password, postcode, borough, county_region,
                country, continent, weather_location, verification_level, role, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                request.form["nickname"], request.form["username"],
                request.form.get("oap_email", ""), request.form.get("email", ""),
                generate_password_hash(request.form["password"]),
                request.form.get("postcode", ""), request.form.get("borough", ""),
                request.form.get("county_region", ""), request.form.get("country", ""),
                request.form.get("continent", ""), request.form.get("weather_location", ""),
                "starter", "member", now()
            ))
            conn.commit()
            log("Member joined OAP", request.form["username"])
            return redirect("/welcome")
        except sqlite3.IntegrityError:
            return render("<div class='card'><h1>Username already exists</h1><a href='/join'>Try again</a></div>")
        finally:
            conn.close()

    return render("""
    <div class='card hero'>
      <h1>Join OAP 🌍</h1>
      <p class='green'>Fast signup. Geography optional until Trust Badge or monetization.</p>
    </div>
    <div class='card'>
      <form method='POST'>
        <input name='nickname' placeholder='Nickname' required>
        <input name='username' placeholder='Username' required>
        <input name='oap_email' placeholder='OAP email optional later'>
        <input name='email' placeholder='Email optional'>
        <input name='password' type='password' placeholder='Password' required>
        <input name='postcode' placeholder='Postcode optional'>
        <input name='borough' placeholder='Borough optional'>
        <input name='county_region' placeholder='County / Region optional'>
        <input name='country' placeholder='Country optional'>
        <input name='continent' placeholder='Continent optional'>
        <input name='weather_location' placeholder='Weather location optional'>
        <button>Join OAP</button>
      </form>
    </div>
    """)


@app.route("/welcome")
def welcome():
    return render("""
    <div class='card hero'>
      <h1>Welcome to OAP 🌍</h1>
      <p class='green'>Your World has been created.</p>
    </div>
    <div class='grid'>
      <div class='card'><h2>🌍 Community</h2><a href='/community'>Open</a></div>
      <div class='card'><h2>⚽ Sports</h2><a href='/sports'>Open</a></div>
      <div class='card'><h2>🎵 Culture</h2><a href='/culture'>Open</a></div>
      <div class='card'><h2>🎤 Artists</h2><a href='/artists'>Open</a></div>
      <div class='card'><h2>📅 Events</h2><a href='/events'>Open</a></div>
      <div class='card'><h2>🌍 My World</h2><a href='/enter'>Enter My World</a></div>
    </div>
    """)


@app.route("/enter", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def enter():
    if request.method == "POST":
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], request.form["password"]):
            session["user"] = user["username"]
            log("Member entered My World", user["username"])
            return redirect("/my_world")
        return render("<div class='card'><h1>Invalid login</h1><a href='/enter'>Try again</a></div>")

    return render("""
    <div class='card hero'><h1>Enter My World 🌍</h1></div>
    <div class='card'>
      <form method='POST'>
        <input name='username' placeholder='Username' required>
        <input name='password' type='password' placeholder='Password' required>
        <button>Enter My World</button>
      </form>
      <p class='small'>Default admin: N24-7 / 2525</p>
    </div>
    """)


@app.route("/leave")
@app.route("/logout")
def leave():
    session.clear()
    return redirect("/")


@app.route("/privacy")
@app.route("/trust")
def privacy():
    return render("""
    <div class='card hero'>
      <h1>🛡️ OAP Privacy & Trust Promise</h1>
      <p class='green'>Human-first. Private-first. Community-first.</p>
    </div>
    <div class='card'>
      <h2>Your OAP Rights</h2>
      <p>✅ Your data belongs to you.</p>
      <p>✅ Your profile belongs to you.</p>
      <p>✅ Your content belongs to you.</p>
      <p>✅ Your messages belong to you.</p>
      <p>✅ Your culture belongs to you.</p>
      <p>✅ Your business belongs to you.</p>
    </div>
    <div class='card'>
      <h2>OAP Promise</h2>
      <p>We collect only what is needed to run the platform.</p>
      <p>We do not sell member data.</p>
      <p>We do not build hidden advertising profiles.</p>
      <p>We do not force unnecessary personal information.</p>
      <p>Members control what they share publicly.</p>
      <p>Privacy, dignity, youth safety, culture, and community come first.</p>
    </div>
    <div class='card warn'>
      <b>Collaboration rule:</b> OAP owns the core. We collaborate only where it fits the mission and never give away trust.
    </div>
    """)


@app.route("/my_world")
def my_world():
    username = current_member()
    conn = db()
    member = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    culture_count = conn.execute("SELECT COUNT(*) c FROM culture_posts WHERE username=?", (username,)).fetchone()["c"]
    artist_count = conn.execute("SELECT COUNT(*) c FROM artists WHERE username=?", (username,)).fetchone()["c"]
    event_count = conn.execute("SELECT COUNT(*) c FROM events WHERE username=?", (username,)).fetchone()["c"]
    award_count = conn.execute("SELECT COUNT(*) c FROM awards WHERE username=?", (username,)).fetchone()["c"]
    opportunity = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM revenues WHERE username=?", (username,)).fetchone()["c"]
    paid = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE username=? AND status='paid'", (username,)).fetchone()["c"]
    conn.close()

    nickname = member["nickname"] if member else username
    trust_badge = member["verification_level"] if member else "guest"

    return render(f"""
    <div class='card hero'>
      <h1>🌍 {h(nickname)}'s World</h1>
      <p class='green'>Every member has a World.</p>
      <p>Trust Badge: {h(trust_badge)}</p>
    </div>
    <div class='grid'>
      <div class='card'><h2>💬</h2><p>Messenger</p><a href='/messages'>Open</a></div>
      <div class='card'><h2>{culture_count}</h2><p>My Culture</p><a href='/culture'>Open</a></div>
      <div class='card'><h2>{artist_count}</h2><p>My Artists</p><a href='/artists'>Open</a></div>
      <div class='card'><h2>{event_count}</h2><p>My Events</p><a href='/events'>Open</a></div>
      <div class='card'><h2>{award_count}</h2><p>My Awards</p><a href='/awards'>Open</a></div>
      <div class='card'><h2>⭐</h2><p>My Trust Badge</p><a href='/trust_badge'>Open</a></div>
      <div class='card'><h2>£{opportunity:.2f}</h2><p>Opportunity Board</p><a href='/opportunity_board'>Open</a></div>
      <div class='card'><h2>£{paid:.2f}</h2><p>Paid Payouts</p><a href='/payouts'>Open</a></div>
    </div>
    <div class='card warn'>Coming later inside My World: Media, Music, Business, Family Tree, Affiliate Tree, SIKA.</div>
    """)


@app.route("/community")
def community():
    return render("""
    <div class='card hero'><h1>🌍 Community</h1>
    <p class='green'>Postcode → Borough → County/Region → Country → Continent → Global → Planet → Universe</p></div>
    <div class='grid'>
      <div class='card'><h2>📍 Postcode</h2><p>Trust starts local.</p></div>
      <div class='card'><h2>🏙 Borough</h2><p>Neighbouring postcodes connect.</p></div>
      <div class='card'><h2>🗺 Region</h2><p>Regional culture and opportunity.</p></div>
      <div class='card'><h2>🇬🇭 Country</h2><p>Country spaces and heritage.</p></div>
      <div class='card'><h2>🌍 Continent</h2><p>Continents and diaspora spaces.</p></div>
      <div class='card'><h2>⭐ United States of Africa</h2><p>Community, culture, creators, education, business and diaspora collaboration.</p></div>
      <div class='card'><h2>🌱 Planet</h2><p>Dignity, humanity and environment.</p></div>
      <div class='card'><h2>✨ Universe</h2><p>Learning, wisdom and future generations.</p></div>
    </div>
    """)


@app.route("/sports")
def sports():
    return render("""
    <div class='card hero'><h1>⚽ Sports</h1><p class='green'>World Cup, football, boxing, Olympics, chess, culture tournaments.</p></div>
    <div class='grid'>
      <div class='card'><h2>🏆 World Cup</h2><p>Watch parties, countries, creators, reports.</p></div>
      <div class='card'><h2>⚽ Football</h2><p>Local-to-global football energy.</p></div>
      <div class='card'><h2>🥊 Boxing</h2><p>Events and community sports culture.</p></div>
      <div class='card'><h2>♟ Chess</h2><p>Strategy tournaments later.</p></div>
    </div>
    """)


@app.route("/culture", methods=["GET", "POST"])
def culture():
    if request.method == "POST":
        username = current_member()
        conn = db()
        conn.execute("""INSERT INTO culture_posts(username,culture_type,title,heritage_group,postcode,borough,country,continent,body,source_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["culture_type"], request.form["title"], request.form["heritage_group"],
            request.form["postcode"], request.form["borough"], request.form["country"], request.form["continent"],
            request.form["body"], request.form["source_note"], "approved", now()
        ))
        conn.commit()
        conn.close()
        save_memory("culture", request.form["title"], "Culture record saved.", "Culture belongs to the community.", "Connect culture to artists, events, awards.", "public")
        log("Culture record saved", username)
        return redirect("/culture")

    conn = db()
    rows = conn.execute("SELECT * FROM culture_posts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>🎵 Culture</h1><p class='green'>Songs, stories, language, proverbs, food, clothing, dance and festivals.</p></div>
    <div class='card'>
      <form method='POST'>
        <select name='culture_type'><option>Song / Music</option><option>Story</option><option>Language</option><option>Proverb</option><option>Food</option><option>Dance</option><option>Festival</option><option>Heritage</option></select>
        <input name='title' placeholder='Title' required>
        <input name='heritage_group' placeholder='Heritage group'>
        <input name='postcode' placeholder='Postcode'>
        <input name='borough' placeholder='Borough'>
        <input name='country' placeholder='Country'>
        <input name='continent' placeholder='Continent'>
        <textarea name='body' placeholder='Culture record'></textarea>
        <textarea name='source_note' placeholder='Rights / source / proof note'></textarea>
        <button>Save Culture</button>
      </form>
    </div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['culture_type'])} • {h(r['heritage_group'])}<p>{h(r['body'])}</p></div>"
    return render(content)


@app.route("/music")
def music():
    return render("""
    <div class='card hero'><h1>🎵 OAP Music</h1><p class='green'>Own Spotify-style destination later. Structure first, media later.</p></div>
    <div class='card warn'>Only owned, licensed, or cleared media should be hosted. No autoplay.</div>
    <div class='grid'>
      <div class='card'><h2>Artist Profiles</h2><p>Connected to My World.</p></div>
      <div class='card'><h2>Releases</h2><p>Singles, albums, playlists later.</p></div>
      <div class='card'><h2>Country Songs</h2><p>Manual play/pause later.</p></div>
    </div>
    """)


@app.route("/artists", methods=["GET", "POST"])
def artists():
    if request.method == "POST":
        username = current_member()
        conn = db()
        conn.execute("""INSERT INTO artists(username,artist_name,genre,postcode,borough,country,continent,bio,link,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (
            username, request.form["artist_name"], request.form["genre"],
            request.form["postcode"], request.form["borough"], request.form["country"], request.form["continent"],
            request.form["bio"], request.form["link"], "pending", now()
        ))
        conn.commit()
        conn.close()
        save_memory("artist", request.form["artist_name"], "Artist submitted.", "Artists connect culture and monetization.", "Review artist profile.")
        log("Artist submitted", username)
        return redirect("/artists")

    conn = db()
    rows = conn.execute("SELECT * FROM artists ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>🎤 Artists</h1></div>
    <div class='card'>
      <form method='POST'>
        <input name='artist_name' placeholder='Artist name' required>
        <input name='genre' placeholder='Genre'>
        <input name='postcode' placeholder='Postcode'>
        <input name='borough' placeholder='Borough'>
        <input name='country' placeholder='Country'>
        <input name='continent' placeholder='Continent'>
        <textarea name='bio' placeholder='Bio'></textarea>
        <input name='link' placeholder='Link'>
        <button>Submit Artist</button>
      </form>
    </div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['artist_name'])}</b><br>{h(r['genre'])} • {h(r['country'])} • {h(r['status'])}<p>{h(r['bio'])}</p></div>"
    return render(content)


@app.route("/events", methods=["GET", "POST"])
def events():
    if request.method == "POST":
        username = current_member()
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
        log("Event submitted", username)
        return redirect("/events")

    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>📅 Events</h1></div>
    <div class='card'>
      <form method='POST'>
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
        <button>Submit Event</button>
      </form>
    </div>
    """
    for e in rows:
        content += f"<div class='card'><b>{h(e['title'])}</b><br>{h(e['event_type'])} • {h(e['postcode'])} → {h(e['country'])}<p>{h(e['description'])}</p></div>"
    return render(content)


@app.route("/news")
def news():
    return render("""
    <div class='card hero'><h1>📰 OAP News</h1><p class='green'>Human-centered news: culture, sports, events, business, opportunities.</p></div>
    <div class='card'>News engine coming after Search and Explorer. No doom-scrolling, no panic, no unverified claims.</div>
    """)


@app.route("/weather")
def weather():
    return render("""
    <div class='card hero'><h1>🌦 OAP Weather</h1><p class='green'>Weather for events, watch parties, field operations and planning.</p></div>
    <div class='card'>Weather integration comes later. For now, store preferred weather location at Join OAP.</div>
    """)


@app.route("/business")
def business():
    return render("""
    <div class='card hero'><h1>🏪 OAP Business</h1><p class='green'>Business directory, promotions, vendor slots and local discovery coming next.</p></div>
    <div class='card'>Business is the next monetization layer after stable core, search, payouts and approvals.</div>
    """)


@app.route("/explorer")
def explorer():
    return render("""
    <div class='card hero'><h1>🧭 OAP Explorer</h1><p class='green'>Discover OAP from postcode to universe.</p></div>
    <div class='grid'>
      <div class='card'><h2>📍 Postcode</h2><p>Local events, artists, businesses.</p></div>
      <div class='card'><h2>🏙 Borough</h2><p>Neighbouring community activity.</p></div>
      <div class='card'><h2>🗺 Region</h2><p>Regional opportunities.</p></div>
      <div class='card'><h2>🇬🇭 Country</h2><p>Country culture and spaces.</p></div>
      <div class='card'><h2>🌍 Continent</h2><p>Continental collaboration.</p></div>
      <div class='card'><h2>🌎 Global</h2><p>Born local, built global.</p></div>
      <div class='card'><h2>🌱 Planet</h2><p>Human dignity and nature.</p></div>
      <div class='card'><h2>✨ Universe</h2><p>Future learning and wisdom.</p></div>
    </div>
    """)


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    content = f"""
    <div class='card hero'>
      <h1>🔎 OAP Search</h1>
      <p class='green'>OAP-first search. Not Google. Search your community records.</p>
    </div>
    <div class='card'>
      <form method='GET'>
        <input name='q' value='{h(q)}' placeholder='Search culture, artists, events, awards, members...'>
        <button>Search</button>
      </form>
    </div>
    """
    if not q:
        return render(content)

    like = f"%{q}%"
    conn = db()
    results = []

    for query, label in [
        ("SELECT title, culture_type AS type, body AS text FROM culture_posts WHERE title LIKE ? OR body LIKE ? OR heritage_group LIKE ? LIMIT 20", "Culture"),
        ("SELECT artist_name AS title, genre AS type, bio AS text FROM artists WHERE artist_name LIKE ? OR genre LIKE ? OR bio LIKE ? LIMIT 20", "Artist"),
        ("SELECT title, event_type AS type, description AS text FROM events WHERE title LIKE ? OR event_type LIKE ? OR description LIKE ? LIMIT 20", "Event"),
        ("SELECT username AS title, verification_level AS type, nickname AS text FROM users WHERE username LIKE ? OR nickname LIKE ? OR country LIKE ? LIMIT 20", "Member")
    ]:
        try:
            for r in conn.execute(query, (like, like, like)):
                results.append((label, r["title"], r["type"], r["text"]))
        except Exception:
            pass

    try:
        for r in conn.execute("SELECT award_name AS title, award_type AS type, reason AS text FROM awards WHERE award_name LIKE ? OR award_type LIKE ? OR nominee_name LIKE ? OR reason LIKE ? LIMIT 20", (like, like, like, like)):
            results.append(("Award", r["title"], r["type"], r["text"]))
    except Exception:
        pass

    conn.close()

    content += "<div class='card'><h2>Results</h2>"
    if not results:
        content += "<p>No results yet. Add culture, artists, events or awards first.</p>"
    for section, title, typ, text in results:
        content += f"<div class='card'><b>{h(section)}: {h(title)}</b><br><span class='green'>{h(typ)}</span><p>{h(text)}</p></div>"
    content += "</div>"
    return render(content)


@app.route("/messages", methods=["GET", "POST"])
def messages():
    if request.method == "POST":
        sender = current_member()
        conn = db()
        conn.execute("INSERT INTO messages(sender,recipient,subject,body,status,created_at) VALUES(?,?,?,?,?,?)",
                     (sender, request.form["recipient"], request.form["subject"], request.form["body"], "unread", now()))
        conn.commit()
        conn.close()
        log("Message sent", sender)
        return redirect("/messages")

    member = current_member()
    conn = db()
    rows = conn.execute("SELECT * FROM messages WHERE recipient=? OR sender=? OR recipient='admin' ORDER BY id DESC LIMIT 100", (member, member)).fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>💬 Messenger</h1></div>
    <div class='card'>
      <form method='POST'>
        <input name='recipient' value='admin'>
        <input name='subject' placeholder='Subject'>
        <textarea name='body' placeholder='Message'></textarea>
        <button>Send</button>
      </form>
    </div>
    """
    for m in rows:
        content += f"<div class='card'><b>{h(m['subject'])}</b><br>{h(m['sender'])} → {h(m['recipient'])}<p>{h(m['body'])}</p></div>"
    return render(content)


@app.route("/awards", methods=["GET", "POST"])
def awards():
    if request.method == "POST":
        username = current_member()
        conn = db()
        conn.execute("""INSERT INTO awards(username,award_name,award_type,nominee_name,reason,geography_level,status,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (
            username, request.form["award_name"], request.form["award_type"], request.form["nominee_name"],
            request.form["reason"], request.form["geography_level"], "pending", now()
        ))
        conn.commit()
        conn.close()
        save_memory("award", request.form["award_name"], "Award nomination submitted.", "Recognition follows contribution.", "Review award proof.", "public")
        log("Award submitted", username)
        return redirect("/awards")

    conn = db()
    rows = conn.execute("SELECT * FROM awards ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>🏅 Awards</h1></div>
    <div class='card'>
      <form method='POST'>
        <input name='award_name' placeholder='Award name' required>
        <select name='award_type'><option>Artist of the Year</option><option>Community Song</option><option>Culture Ambassador</option><option>Youth Creator</option><option>Community Champion</option><option>Business Champion</option></select>
        <input name='nominee_name' placeholder='Nominee'>
        <select name='geography_level'><option>Postcode</option><option>Borough</option><option>Country</option><option>Continent</option><option>Global</option><option>Planet</option><option>Universe</option></select>
        <textarea name='reason' placeholder='Reason'></textarea>
        <button>Submit Award</button>
      </form>
    </div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['award_name'])}</b><br>{h(r['award_type'])} • {h(r['status'])}<p>{h(r['reason'])}</p></div>"
    return render(content)


@app.route("/trust_badge", methods=["GET", "POST"])
@app.route("/verification", methods=["GET", "POST"])
def trust_badge():
    if request.method == "POST":
        username = current_member()
        conn = db()
        conn.execute("""INSERT INTO verification_requests(username,requested_level,proof,contribution_note,status,reviewer_note,created_at)
        VALUES(?,?,?,?,?,?,?)""", (
            username, request.form["requested_level"], request.form["proof"], request.form["contribution_note"],
            "pending", "", now()
        ))
        conn.commit()
        conn.close()
        save_memory("trust_badge", request.form["requested_level"], "Trust Badge request submitted.", "Trust Badge must be proof-based.", "Review before approval.")
        log("Trust Badge requested", username)
        return redirect("/trust_badge")

    conn = db()
    rows = conn.execute("SELECT * FROM verification_requests ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>⭐ Trust Badge</h1><p class='green'>Proof + Trust + Contribution + Consistency.</p></div>
    <div class='card'>
      <form method='POST'>
        <select name='requested_level'>
          <option>Postcode Badge</option><option>Borough Badge</option><option>County / Region Badge</option><option>Country Badge</option><option>Continent Badge</option><option>Global Badge</option><option>Planet Badge</option><option>Universe Badge</option>
        </select>
        <textarea name='proof' placeholder='Proof'></textarea>
        <textarea name='contribution_note' placeholder='Contribution note'></textarea>
        <button>Request Trust Badge</button>
      </form>
    </div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['requested_level'])}</b><br>@{h(r['username'])} • {h(r['status'])}<p>{h(r['proof'])}</p></div>"
    return render(content)


@app.route("/opportunity_board", methods=["GET", "POST"])
@app.route("/revenue", methods=["GET", "POST"])
def opportunity_board():
    if request.method == "POST":
        username = request.form.get("username") or current_member()
        conn = db()
        conn.execute("""INSERT INTO revenues(username,customer_name,source,description,amount,currency,status,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (
            username, request.form["customer_name"], request.form["source"], request.form["description"],
            float(request.form.get("amount") or 0), request.form["currency"], "recorded", now()
        ))
        conn.commit()
        conn.close()
        save_memory("opportunity", request.form["source"], "Opportunity recorded.", "Track value before payouts.", "Review whether payout is required.")
        log("Opportunity recorded", username)
        return redirect("/opportunity_board")

    conn = db()
    rows = conn.execute("SELECT * FROM revenues ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card hero'><h1>💰 Opportunity Board</h1><p class='green'>Business listings, promotions, event opportunities and creator opportunities.</p></div>
    <div class='card'>
      <form method='POST'>
        <input name='username' placeholder='Linked username optional'>
        <input name='customer_name' placeholder='Customer / business / artist name'>
        <select name='source'><option>Business Listing</option><option>Featured Promotion</option><option>Artist Promotion</option><option>Event Promotion</option><option>Vendor Slot</option><option>Founder Membership</option><option>Other</option></select>
        <input name='amount' placeholder='Amount e.g. 20'>
        <select name='currency'><option>GBP</option><option>GHS</option><option>EUR</option><option>SIKA</option></select>
        <textarea name='description' placeholder='What was paid for?'></textarea>
        <button>Record Opportunity</button>
      </form>
    </div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['source'])}</b><br>{h(r['currency'])} {h(r['amount'])} • {h(r['customer_name'])}<p>{h(r['description'])}</p></div>"
    return render(content)


@app.route("/payouts", methods=["GET", "POST"])
def payouts():
    if request.method == "POST":
        username = request.form.get("username") or current_member()
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
    <div class='card'>
      <form method='POST'>
        <input name='username' placeholder='Linked username optional'>
        <input name='recipient_name' placeholder='Recipient name'>
        <input name='amount' placeholder='Amount e.g. 10'>
        <select name='currency'><option>GBP</option><option>GHS</option><option>EUR</option><option>SIKA</option></select>
        <textarea name='reason' placeholder='Reason for payout'></textarea>
        <button>Create Payout Request</button>
      </form>
    </div>
    """
    for p in rows:
        content += f"<div class='card'><b>{h(p['recipient_name'])}</b><br>{h(p['currency'])} {h(p['amount'])} • Status: {h(p['status'])}<p>{h(p['reason'])}</p></div>"
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
    reviewer = current_member()
    conn = db()
    approval = conn.execute("SELECT * FROM approvals WHERE id=?", (id,)).fetchone()
    if approval:
        conn.execute("UPDATE approvals SET status=?, reviewer=?, notes=? WHERE id=?",
                     (status, reviewer, f"Reviewed as {status} by {reviewer}", id))
        if approval["approval_type"] == "payout":
            if status == "approved":
                conn.execute("UPDATE payouts SET status=?, approved_by=? WHERE id=?", ("approved", reviewer, approval["record_id"]))
            elif status == "rejected":
                conn.execute("UPDATE payouts SET status=?, approved_by=? WHERE id=?", ("rejected", reviewer, approval["record_id"]))
            elif status == "paid":
                conn.execute("UPDATE payouts SET status=?, approved_by=?, paid_date=? WHERE id=?", ("paid", reviewer, now(), approval["record_id"]))
        conn.commit()
    conn.close()
    save_memory("approval", f"Approval {id}", f"Approval marked {status}", "Approval workflow protects OAP.", "Keep payout logs accurate.")
    log(f"Approval {status}", reviewer)
    return redirect("/approvals")


@app.route("/command_center")
@app.route("/dashboard")
def command_center():
    conn = db()
    total_opportunity = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM revenues").fetchone()["c"]
    pending_payouts = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='pending'").fetchone()["c"]
    approved_payouts = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='approved'").fetchone()["c"]
    paid_payouts = conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='paid'").fetchone()["c"]
    pending_approvals = conn.execute("SELECT COUNT(*) c FROM approvals WHERE status='pending'").fetchone()["c"]
    members = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    events_count = conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    artists_count = conn.execute("SELECT COUNT(*) c FROM artists").fetchone()["c"]
    conn.close()

    return render(f"""
    <div class='card hero'><h1>🎯 Command Center</h1><p class='green'>Monitor before payouts. Records before finance.</p></div>
    <div class='grid'>
      <div class='card'><h2>£{total_opportunity:.2f}</h2><p>Opportunity Board</p></div>
      <div class='card'><h2>£{pending_payouts:.2f}</h2><p>Pending Payouts</p></div>
      <div class='card'><h2>£{approved_payouts:.2f}</h2><p>Approved Payouts</p></div>
      <div class='card'><h2>£{paid_payouts:.2f}</h2><p>Paid Payouts</p></div>
      <div class='card'><h2>{pending_approvals}</h2><p>Pending Approvals</p></div>
      <div class='card'><h2>{members}</h2><p>Members</p></div>
      <div class='card'><h2>{events_count}</h2><p>Events</p></div>
      <div class='card'><h2>{artists_count}</h2><p>Artists</p></div>
    </div>
    """)


@app.route("/hrm_memory")
def hrm_memory():
    conn = db()
    rows = conn.execute("SELECT * FROM hrm_memory_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>🧠 HRM Memory</h1><p class='green'>Memory before intelligence.</p></div>"
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['memory_type'])} • {h(r['visibility'])}<p>{h(r['summary'])}</p><p><b>Lesson:</b> {h(r['lesson'])}</p><p><b>Next:</b> {h(r['next_action'])}</p></div>"
    return render(content)


@app.route("/routes")
def routes():
    links = []
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods:
            links.append(str(rule.rule))
    links = sorted(set(links))
    content = "<div class='card hero'><h1>🧪 Route Checker</h1></div><div class='card'>"
    for link in links:
        content += f"<p><a href='{h(link)}'>{h(link)}</a></p>"
    content += "</div>"
    return render(content)


@app.route("/admin")
def admin():
    conn = db()
    members = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 50").fetchall()
    artists_rows = conn.execute("SELECT * FROM artists ORDER BY id DESC LIMIT 50").fetchall()
    awards_rows = conn.execute("SELECT * FROM awards ORDER BY id DESC LIMIT 50").fetchall()
    badge_rows = conn.execute("SELECT * FROM verification_requests ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card hero'><h1>⚙ Admin</h1></div><div class='card'><h2>Members</h2>"
    for member in members:
        content += f"<div class='card'>@{h(member['username'])} — {h(member['verification_level'])}<br>{h(member['postcode'])} → {h(member['country'])}</div>"

    content += "</div><div class='card'><h2>Artists</h2>"
    for a in artists_rows:
        content += f"<div class='card'><b>{h(a['artist_name'])}</b> — {h(a['status'])}<br><a href='/admin/artist/{a['id']}/approved'>Approve</a><a href='/admin/artist/{a['id']}/rejected'>Reject</a></div>"

    content += "</div><div class='card'><h2>Awards</h2>"
    for aw in awards_rows:
        content += f"<div class='card'><b>{h(aw['award_name'])}</b> — {h(aw['status'])}<br><a href='/admin/award/{aw['id']}/approved'>Approve</a><a href='/admin/award/{aw['id']}/rejected'>Reject</a></div>"

    content += "</div><div class='card'><h2>Trust Badges</h2>"
    for badge in badge_rows:
        content += f"<div class='card'><b>{h(badge['requested_level'])}</b> @{h(badge['username'])} — {h(badge['status'])}<br><a href='/admin/trust_badge/{badge['id']}/approved'>Approve</a><a href='/admin/trust_badge/{badge['id']}/rejected'>Reject</a></div>"

    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    content += "</div>"
    return render(content)


@app.route("/admin/artist/<int:id>/<status>")
def admin_artist(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE artists SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"Artist {status}", current_member())
    return redirect("/admin")


@app.route("/admin/award/<int:id>/<status>")
def admin_award(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE awards SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"Award {status}", current_member())
    return redirect("/admin")


@app.route("/admin/trust_badge/<int:id>/<status>")
@app.route("/admin/verification/<int:id>/<status>")
def admin_trust_badge(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    req = conn.execute("SELECT * FROM verification_requests WHERE id=?", (id,)).fetchone()
    if req:
        conn.execute("UPDATE verification_requests SET status=?, reviewer_note=? WHERE id=?", (status, "Reviewed by admin", id))
        if status == "approved":
            conn.execute("UPDATE users SET verification_level=? WHERE username=?", (req["requested_level"], req["username"]))
        conn.commit()
    conn.close()
    log(f"Trust Badge {status}", current_member())
    return redirect("/admin")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
