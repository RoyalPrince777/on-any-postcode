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
    conn.execute("INSERT INTO audit_logs(action,username,created_at) VALUES(?,?,?)", (action, username, now()))
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

    cur.execute("""CREATE TABLE IF NOT EXISTS royalty_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        heritage_line TEXT,
        record_type TEXT,
        body TEXT,
        stewardship_note TEXT,
        status TEXT DEFAULT 'approved',
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
        cur.execute("UPDATE users SET nickname=?, oap_email=?, password=?, role=?, verification_level=? WHERE username=?",
            ("N24-7", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", "founder", ADMIN_USERNAME))
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
<a href="/login">Login</a> <a href="/signup">Join</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/community">Community</a>
<a href="/culture">Culture</a>
<a href="/artists">Artists</a>
<a href="/royalty">Royalty</a>
<a href="/awards">Awards</a>
<a href="/verification">Verification</a>
<a href="/events">Events</a>
<a href="/messages">Messenger</a>
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

def save_memory(memory_type, title, summary, lesson, next_action, visibility="private"):
    conn = db()
    conn.execute("""INSERT INTO hrm_memory_logs(memory_type,title,summary,lesson,next_action,visibility,created_at)
    VALUES(?,?,?,?,?,?,?)""", (memory_type, title, summary, lesson, next_action, visibility, now()))
    conn.commit()
    conn.close()

@app.route("/")
def home():
    conn = db()
    stats = {
        "culture": conn.execute("SELECT COUNT(*) c FROM culture_posts").fetchone()["c"],
        "artists": conn.execute("SELECT COUNT(*) c FROM artists").fetchone()["c"],
        "royalty": conn.execute("SELECT COUNT(*) c FROM royalty_records").fetchone()["c"],
        "awards": conn.execute("SELECT COUNT(*) c FROM awards").fetchone()["c"],
        "verification": conn.execute("SELECT COUNT(*) c FROM verification_requests").fetchone()["c"],
        "events": conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
    }
    culture = conn.execute("SELECT * FROM culture_posts ORDER BY id DESC LIMIT 3").fetchall()
    artists = conn.execute("SELECT * FROM artists ORDER BY id DESC LIMIT 3").fetchall()
    conn.close()

    content = f"""
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>v3.6 — Culture + Artists + Royalty + Awards + Verification</p>
    <p>Every postcode has a story. Every culture has a song. Every community has a voice.</p>
    </div>

    <div class='grid'>
    <div class='card'><h2>{stats['culture']}</h2><p>Culture Posts</p></div>
    <div class='card'><h2>{stats['artists']}</h2><p>Artists</p></div>
    <div class='card'><h2>{stats['royalty']}</h2><p>Royalty Records</p></div>
    <div class='card'><h2>{stats['awards']}</h2><p>Awards</p></div>
    <div class='card'><h2>{stats['verification']}</h2><p>Verification Requests</p></div>
    <div class='card'><h2>{stats['events']}</h2><p>Events</p></div>
    </div>

    <div class='card'>
    <a class='badge' href='/culture'>Culture</a>
    <a class='badge' href='/artists'>Artists</a>
    <a class='badge' href='/royalty'>Royalty</a>
    <a class='badge' href='/awards'>Awards</a>
    <a class='badge' href='/verification'>Verification</a>
    </div>

    <div class='card'><h2>Latest Culture</h2>
    """
    for c in culture:
        content += f"<div class='card'><b>{h(c['title'])}</b><br>{h(c['culture_type'])} • {h(c['heritage_group'])}<p>{h(c['body'])}</p></div>"
    content += "</div><div class='card'><h2>Latest Artists</h2>"
    for a in artists:
        content += f"<div class='card'><b>{h(a['artist_name'])}</b><br>{h(a['genre'])} • {h(a['country'])}<p>{h(a['bio'])}</p></div>"
    content += "</div>"
    return render(content)

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
    <div class='card hero'><h1>Join OAP</h1><p class='green'>Fast signup. Geography optional until verification or monetization.</p></div>
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
        if user and check_password_hash(user["password"], request.form["password"]):
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

@app.route("/community")
def community():
    return render("""
    <div class='card hero'><h1>🌍 Community Navigation</h1>
    <p class='green'>Postcode → Borough → County/Region → Country → Continent → Global → Planet → Universe</p></div>
    <div class='grid'>
    <div class='card'><h2>📍 Postcode</h2><p>Trust starts local.</p></div>
    <div class='card'><h2>🏙 Borough</h2><p>Neighbouring postcodes connect.</p></div>
    <div class='card'><h2>🗺 County / Region</h2><p>Regional opportunity and culture.</p></div>
    <div class='card'><h2>🇬🇭 Country</h2><p>Country spaces and heritage.</p></div>
    <div class='card'><h2>🌍 Continent</h2><p>Africa, Europe, Asia, Caribbean, Americas and more.</p></div>
    <div class='card'><h2>⭐ United States of Africa</h2><p>Community, culture, creators, education, business and diaspora collaboration space.</p></div>
    <div class='card'><h2>🌱 Planet</h2><p>Dignity, humanity, environment and future generations.</p></div>
    <div class='card'><h2>✨ Universe</h2><p>Learning, ideas, wisdom and future possibility.</p></div>
    </div>
    """)

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
        save_memory("culture", request.form["title"], "Culture record saved.", "Culture preserves identity and connects community.", "Connect to artists, events and awards.", "public")
        log("Culture post saved", username)
        return redirect("/culture")

    conn = db()
    rows = conn.execute("SELECT * FROM culture_posts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>🎵 Culture Board</h1><p class='green'>Songs, stories, language, proverbs, food, clothing, dance and festivals.</p></div>
    <div class='card'><form method='POST'>
    <select name='culture_type'>
    <option>Song / Music</option><option>Story</option><option>Language</option><option>Proverb</option><option>Food</option><option>Clothing</option><option>Dance</option><option>Festival</option><option>Heritage</option>
    </select>
    <input name='title' placeholder='Title' required>
    <input name='heritage_group' placeholder='Heritage group e.g. Akan, Akyem, Jamaican, Brazilian'>
    <input name='postcode' placeholder='Postcode'>
    <input name='borough' placeholder='Borough'>
    <input name='country' placeholder='Country'>
    <input name='continent' placeholder='Continent'>
    <textarea name='body' placeholder='Culture record'></textarea>
    <textarea name='source_note' placeholder='Source / rights / proof note'></textarea>
    <button>Save Culture Record</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['culture_type'])} • {h(r['heritage_group'])}<br>{h(r['postcode'])} → {h(r['country'])}<p>{h(r['body'])}</p><p class='small'>{h(r['source_note'])}</p></div>"
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
        save_memory("artist", request.form["artist_name"], "Artist profile submitted.", "Artists connect culture, events and monetization.", "Review and approve artist profile.", "public")
        log("Artist submitted", username)
        return redirect("/artists")

    conn = db()
    rows = conn.execute("SELECT * FROM artists ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>🎤 Artists</h1><p class='green'>Music, culture, creators, releases, events and awards.</p></div>
    <div class='card'><form method='POST'>
    <input name='artist_name' placeholder='Artist name' required>
    <input name='genre' placeholder='Genre e.g. Highlife, Afrobeats, Reggae, Grime'>
    <input name='postcode' placeholder='Postcode'>
    <input name='borough' placeholder='Borough'>
    <input name='country' placeholder='Country'>
    <input name='continent' placeholder='Continent'>
    <textarea name='bio' placeholder='Artist biography'></textarea>
    <input name='link' placeholder='Link'>
    <button>Submit Artist</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['artist_name'])}</b><br>{h(r['genre'])} • {h(r['country'])}<br>Status: {h(r['status'])}<p>{h(r['bio'])}</p><p>{h(r['link'])}</p></div>"
    return render(content)

@app.route("/royalty", methods=["GET","POST"])
def royalty():
    if request.method == "POST":
        username = current_user()
        conn = db()
        conn.execute("""INSERT INTO royalty_records(username,title,heritage_line,record_type,body,stewardship_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (
            username, request.form["title"], request.form["heritage_line"], request.form["record_type"],
            request.form["body"], request.form["stewardship_note"], "approved", now()
        ))
        conn.commit()
        conn.close()
        save_memory("royalty", request.form["title"], "Royalty/stewardship record saved.", "Royalty means service, stewardship and legacy.", "Connect record to culture, awards and family tree later.")
        log("Royalty record saved", username)
        return redirect("/royalty")

    conn = db()
    rows = conn.execute("SELECT * FROM royalty_records ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>👑 Royalty Layer</h1>
    <p class='green'>Akan → Akyem → Begoro → KORADASO → Prince of KORADASO</p>
    <p>Royalty means service, stewardship, culture, dignity, protection and future generations.</p></div>
    <div class='card'><form method='POST'>
    <input name='title' placeholder='Record title' required>
    <select name='heritage_line'>
    <option>Akan</option><option>Akyem</option><option>Begoro</option><option>KORADASO</option><option>Prince of KORADASO</option><option>Royalty Layer</option>
    </select>
    <select name='record_type'>
    <option>Heritage Record</option><option>Stewardship Record</option><option>Culture Record</option><option>Leadership Record</option><option>Legacy Record</option><option>Royal Archive</option>
    </select>
    <textarea name='body' placeholder='Record body'></textarea>
    <textarea name='stewardship_note' placeholder='Service / responsibility / dignity note'></textarea>
    <button>Save Royalty Record</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['heritage_line'])} • {h(r['record_type'])}<p>{h(r['body'])}</p><p class='gold'>{h(r['stewardship_note'])}</p></div>"
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
        save_memory("award", request.form["award_name"], "Award nomination submitted.", "Awards create recognition for contribution.", "Review nomination and approve if proof is strong.", "public")
        log("Award submitted", username)
        return redirect("/awards")

    conn = db()
    rows = conn.execute("SELECT * FROM awards ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>🏅 OAP Awards</h1><p class='green'>Recognition follows contribution.</p></div>
    <div class='card'><form method='POST'>
    <input name='award_name' placeholder='Award name' required>
    <select name='award_type'>
    <option>Artist of the Year</option><option>Community Song</option><option>Culture Ambassador</option><option>Youth Creator</option><option>Community Champion</option><option>Business Champion</option><option>Watch Party Champion</option><option>Heritage Preservation</option>
    </select>
    <input name='nominee_name' placeholder='Nominee'>
    <select name='geography_level'>
    <option>Postcode</option><option>Borough</option><option>County / Region</option><option>Country</option><option>Continent</option><option>Global</option><option>Planet</option><option>Universe</option>
    </select>
    <textarea name='reason' placeholder='Why should they receive this award?'></textarea>
    <button>Submit Award Nomination</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['award_name'])}</b><br>{h(r['award_type'])} • {h(r['geography_level'])}<br>Nominee: {h(r['nominee_name'])}<p>{h(r['reason'])}</p>Status: {h(r['status'])}</div>"
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
        save_memory("verification", request.form["requested_level"], "Verification request submitted.", "Verification must be earned through proof and contribution.", "Review proof before approval.")
        log("Verification requested", username)
        return redirect("/verification")

    conn = db()
    rows = conn.execute("SELECT * FROM verification_requests ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = """
    <div class='card hero'><h1>⭐ Verification</h1><p class='green'>Proof + Trust + Contribution + Consistency.</p></div>
    <div class='grid'>
    <div class='card'><h2>📍 Postcode</h2><p>Local contribution.</p></div>
    <div class='card'><h2>🏙 Borough</h2><p>Multiple local records.</p></div>
    <div class='card'><h2>🗺 County / Region</h2><p>Regional activity.</p></div>
    <div class='card'><h2>🇬🇭 Country</h2><p>National contribution.</p></div>
    <div class='card'><h2>🌍 Continent</h2><p>Cross-country connection.</p></div>
    <div class='card'><h2>🌎 Global</h2><p>Global community value.</p></div>
    <div class='card'><h2>🌱 Planet</h2><p>Human dignity and service.</p></div>
    <div class='card'><h2>✨ Universe</h2><p>Wisdom, legacy and long-term contribution.</p></div>
    </div>
    <div class='card'><form method='POST'>
    <select name='requested_level'>
    <option>Postcode Verified</option><option>Borough Verified</option><option>County / Region Verified</option><option>Country Verified</option><option>Continent Verified</option><option>Global Verified</option><option>Planet Verified</option><option>Universe Verified</option>
    </select>
    <textarea name='proof' placeholder='Proof: events, culture posts, artist work, awards, business, community service'></textarea>
    <textarea name='contribution_note' placeholder='Contribution note'></textarea>
    <button>Request Verification</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{h(r['requested_level'])}</b><br>@{h(r['username'])} • {h(r['status'])}<p>{h(r['proof'])}</p><p>{h(r['contribution_note'])}</p></div>"
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
        log("Event submitted", username)
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
        content += f"<div class='card'><b>{h(e['title'])}</b><br>{h(e['event_type'])} • {h(e['postcode'])} → {h(e['country'])}<p>{h(e['description'])}</p>Status: {h(e['status'])}</div>"
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
        log("Message sent", sender)
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
    content = "<div class='card hero'><h1>🧠 HRM Memory</h1><p class='green'>Memory before intelligence.</p></div>"
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['memory_type'])} • {h(r['visibility'])}<p>{h(r['summary'])}</p><p><b>Lesson:</b> {h(r['lesson'])}</p><p><b>Next:</b> {h(r['next_action'])}</p></div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 50").fetchall()
    artists_rows = conn.execute("SELECT * FROM artists ORDER BY id DESC LIMIT 50").fetchall()
    awards_rows = conn.execute("SELECT * FROM awards ORDER BY id DESC LIMIT 50").fetchall()
    ver_rows = conn.execute("SELECT * FROM verification_requests ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card hero'><h1>Admin</h1></div><div class='card'><h2>Users</h2>"
    for u in users:
        content += f"<div class='card'>@{h(u['username'])} — {h(u['verification_level'])}<br>{h(u['postcode'])} → {h(u['borough'])} → {h(u['country'])}</div>"

    content += "</div><div class='card'><h2>Artist Review</h2>"
    for a in artists_rows:
        content += f"<div class='card'><b>{h(a['artist_name'])}</b> — {h(a['status'])}<br><a href='/admin/artist/{a['id']}/approved'>Approve</a><a href='/admin/artist/{a['id']}/rejected'>Reject</a></div>"

    content += "</div><div class='card'><h2>Award Review</h2>"
    for aw in awards_rows:
        content += f"<div class='card'><b>{h(aw['award_name'])}</b> — {h(aw['status'])}<br><a href='/admin/award/{aw['id']}/approved'>Approve</a><a href='/admin/award/{aw['id']}/rejected'>Reject</a></div>"

    content += "</div><div class='card'><h2>Verification Review</h2>"
    for v in ver_rows:
        content += f"<div class='card'><b>{h(v['requested_level'])}</b> @{h(v['username'])} — {h(v['status'])}<br><a href='/admin/verification/{v['id']}/approved'>Approve</a><a href='/admin/verification/{v['id']}/rejected'>Reject</a></div>"

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
    log(f"Artist {status}", current_user())
    return redirect("/admin")

@app.route("/admin/award/<int:id>/<status>")
def admin_award(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE awards SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"Award {status}", current_user())
    return redirect("/admin")

@app.route("/admin/verification/<int:id>/<status>")
def admin_verification(id, status):
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
    log(f"Verification {status}", current_user())
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
