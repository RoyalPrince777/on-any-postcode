from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(action, username="system"):
    conn = db()
    conn.execute("INSERT INTO audit_logs(action, username, created_at) VALUES(?,?,?)", (action, username, now()))
    conn.commit()
    conn.close()

def save_file(file):
    if not file or file.filename == "":
        return ""
    name = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{name}")
    file.save(path)
    return path

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'user',
        verified INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    for col in ["verified INTEGER DEFAULT 0"]:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col}")
        except:
            pass

    cur.execute("""CREATE TABLE IF NOT EXISTS creator_profiles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        display_name TEXT,
        category TEXT,
        bio TEXT,
        image TEXT,
        link TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT,
        image TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        location TEXT,
        event_date TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS businesses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        description TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        body TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS verification_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        reason TEXT,
        proof TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS promo_slots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        category TEXT,
        description TEXT,
        link TEXT,
        image TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS founder_memberships(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        tier TEXT,
        note TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS market_products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        category TEXT,
        price TEXT,
        description TEXT,
        image TEXT,
        link TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS media_releases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        category TEXT,
        description TEXT,
        media_file TEXT,
        cover_art TEXT,
        rights_note TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS rights_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        release_id INTEGER,
        proof_note TEXT,
        action TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )""")

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
.top{background:#111;padding:15px;display:flex;justify-content:space-between;border-bottom:1px solid #222}
.logo{font-weight:900;font-size:20px}
.wrap{padding:18px;max-width:1000px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:18px;margin:15px 0}
.hero{text-align:center;padding:35px 10px}
.hero h1{font-size:34px;margin:5px}
.green{color:#00dd99}
.gold{color:#ffd166}
.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin:0 6px}
input,textarea,select{width:100%;padding:12px;margin:8px 0;background:#0c0c0c;color:white;border:1px solid #333;border-radius:10px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:10px;padding:12px 18px;font-weight:800}
img{max-width:100%;border-radius:14px;margin-top:10px}
audio,video{width:100%;margin-top:10px;border-radius:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.nav{margin-top:10px;line-height:2}
.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:#00dd99;color:#000;font-weight:800;font-size:12px}
.pending{color:#ffd166}
.approved{color:#00dd99}
.rejected{color:#ff6b6b}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get('user') %}
@{{session.get('user')}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a><a href="/register">Join</a>
{% endif %}
</div>
</div>
<div class="wrap">
<div class="nav">
<a href="/">Home</a>
<a href="/creators">Creators</a>
<a href="/events">Events</a>
<a href="/businesses">Businesses</a>
<a href="/messages">Messages</a>
<a href="/verify">Verify</a>
<a href="/promos">Promos</a>
<a href="/founder">Founder</a>
<a href="/market">Market</a>
<a href="/media">Media</a>
<a href="/admin">HRM</a>
</div>
{{content|safe}}
</div>
</body>
</html>
"""

def is_verified(username):
    conn = db()
    row = conn.execute("SELECT verified FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row and row["verified"] == 1

def badge(username):
    return " <span class='badge'>VERIFIED</span>" if is_verified(username) else ""

@app.route("/")
def home():
    conn = db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 8").fetchall()
    creators = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC LIMIT 6").fetchall()
    promos = conn.execute("SELECT * FROM promo_slots WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    releases = conn.execute("SELECT * FROM media_releases WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    conn.close()

    content = """
    <div class='hero card'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <div class='green'>✨👑Born Local🔥💨🚀✨Built Global💎💦</div>
    <p>Earth Is Our Turf</p>
    <p>Community → Commerce → Distribution → Infrastructure → Financial Layers</p>
    </div>
    """

    content += "<div class='card'><h2>🎵 OAP Media Releases</h2><div class='grid'>"
    for r in releases:
        content += f"<div class='card'><b>{r['title']}</b><br><span class='gold'>{r['category']}</span>"
        if r["cover_art"]:
            content += f"<img src='/{r['cover_art']}'>"
        content += f"<p>{r['description']}</p><a href='/release/{r['id']}'>Open Release</a></div>"
    content += "</div></div>"

    content += "<div class='card'><h2>💰 Featured Promos</h2><div class='grid'>"
    for p in promos:
        content += f"<div class='card'><b>{p['title']}</b><p>{p['description']}</p></div>"
    content += "</div></div>"

    if session.get("user"):
        content += """
        <div class='card'><h2>✍️ Create Post</h2>
        <form method='POST' action='/create_post' enctype='multipart/form-data'>
        <textarea name='content' placeholder="What's happening on your postcode?" required></textarea>
        <input type='file' name='image'>
        <button>Post</button>
        </form></div>
        """

    content += "<div class='card'><h2>📰 Feed + News</h2>"
    for p in posts:
        content += f"<div class='card'><b>@{p['username']}</b>{badge(p['username'])}<p>{p['content']}</p>"
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<div class='small'>{p['created_at']}</div></div>"
    content += "</div>"

    content += "<div class='card'><h2>🎤 Creator Highlights</h2><div class='grid'>"
    for c in creators:
        content += f"<div class='card'><b>{c['display_name']}</b>{badge(c['username'])}<br><span class='green'>{c['category']}</span>"
        if c["image"]:
            content += f"<img src='/{c['image']}'>"
        content += f"<p>{c['bio'] or ''}</p><a href='/creator/{c['username']}'>View</a></div>"
    content += "</div></div>"

    return render_template_string(BASE, content=content)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = db()
        try:
            conn.execute("INSERT INTO users(username,email,password,created_at) VALUES(?,?,?,?)",
                (request.form["username"].strip(), request.form["email"].strip(),
                 generate_password_hash(request.form["password"]), now()))
            conn.commit()
            log("User registered", request.form["username"].strip())
            return redirect("/login")
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()
    return render_template_string(BASE, content="""
    <div class='card'><h2>Create Account</h2>
    <form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='email' placeholder='Email' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Register</button>
    </form></div>
    """)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"].strip(),)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], request.form["password"]):
            session["user"] = user["username"]
            log("User login", user["username"])
            return redirect("/")
        return "Invalid login"
    return render_template_string(BASE, content="""
    <div class='card'><h2>Login</h2>
    <form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Login</button>
    </form></div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/create_post", methods=["POST"])
def create_post():
    if not session.get("user"):
        return redirect("/login")
    image = save_file(request.files.get("image"))
    conn = db()
    conn.execute("INSERT INTO posts(username,content,image,created_at) VALUES(?,?,?,?)",
                 (session["user"], request.form["content"], image, now()))
    conn.commit()
    conn.close()
    log("Created post", session["user"])
    return redirect("/")

@app.route("/creators", methods=["GET","POST"])
def creators():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT OR REPLACE INTO creator_profiles(username,display_name,category,bio,image,link,created_at)
        VALUES(?,?,?,?,?,?,?)""",
        (session["user"], request.form["display_name"], request.form["category"],
         request.form["bio"], image, request.form["link"], now()))
        conn.commit()
        conn.close()
        log("Creator profile updated", session["user"])
        return redirect("/creators")

    conn = db()
    rows = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC").fetchall()
    conn.close()

    content = "<div class='card'><h2>🎤 Creator Profiles</h2>"
    if session.get("user"):
        content += """
        <form method='POST' enctype='multipart/form-data'>
        <input name='display_name' placeholder='Display name' required>
        <input name='category' placeholder='Music, comedy, fashion, sport, education...' required>
        <textarea name='bio' placeholder='Bio'></textarea>
        <input name='link' placeholder='Main link'>
        <input type='file' name='image'>
        <button>Save Creator Profile</button>
        </form>
        """
    content += "</div><div class='grid'>"
    for c in rows:
        content += f"<div class='card'><b>{c['display_name']}</b>{badge(c['username'])}<br><span class='green'>{c['category']}</span>"
        if c["image"]:
            content += f"<img src='/{c['image']}'>"
        content += f"<p>{c['bio'] or ''}</p><a href='/creator/{c['username']}'>Open</a> <a href='/message/{c['username']}'>Message</a></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/creator/<username>")
def creator(username):
    conn = db()
    c = conn.execute("SELECT * FROM creator_profiles WHERE username=?", (username,)).fetchone()
    posts = conn.execute("SELECT * FROM posts WHERE username=? ORDER BY id DESC", (username,)).fetchall()
    releases = conn.execute("SELECT * FROM media_releases WHERE username=? ORDER BY id DESC", (username,)).fetchall()
    conn.close()
    if not c:
        return "Creator not found"

    content = f"<div class='card'><h1>{c['display_name']} {badge(username)}</h1><div class='green'>{c['category']}</div>"
    if c["image"]:
        content += f"<img src='/{c['image']}'>"
    content += f"<p>{c['bio'] or ''}</p><a href='{c['link'] or '#'}'>Main Link</a></div>"

    content += "<div class='card'><h2>🎵 Releases</h2>"
    for r in releases:
        content += f"<div class='card'><b>{r['title']}</b> <span class='{r['status']}'>{r['status']}</span><br><a href='/release/{r['id']}'>Open Release</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>Posts</h2>"
    for p in posts:
        content += f"<div class='card'><p>{p['content']}</p><span class='small'>{p['created_at']}</span></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/media", methods=["GET","POST"])
def media():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        media_file = save_file(request.files.get("media_file"))
        cover_art = save_file(request.files.get("cover_art"))
        conn = db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO media_releases(username,title,category,description,media_file,cover_art,rights_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (session["user"], request.form["title"], request.form["category"],
         request.form["description"], media_file, cover_art, request.form["rights_note"], "pending", now()))
        release_id = cur.lastrowid
        cur.execute("INSERT INTO rights_logs(username,release_id,proof_note,action,created_at) VALUES(?,?,?,?,?)",
                    (session["user"], release_id, request.form["rights_note"], "Release uploaded for review", now()))
        conn.commit()
        conn.close()
        log("Media release uploaded", session["user"])
        return redirect("/media")

    conn = db()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    <div class='card'><h2>🎵 OAP Media Uploads</h2>
    <p>OAP is the destination. Upload only owned, licensed, or cleared media.</p>
    """

    if session.get("user"):
        content += """
        <form method='POST' enctype='multipart/form-data'>
        <input name='title' placeholder='Release title' required>
        <input name='category' placeholder='Music, video, podcast, trailer, interview...' required>
        <textarea name='description' placeholder='Release description'></textarea>
        <textarea name='rights_note' placeholder='Rights/proof note: who owns this, who approved it, source proof...' required></textarea>
        <label>Media file</label>
        <input type='file' name='media_file' required>
        <label>Cover art</label>
        <input type='file' name='cover_art'>
        <button>Submit Release For HRM Review</button>
        </form>
        """
    content += "</div><div class='grid'>"

    for r in releases:
        content += f"<div class='card'><b>{r['title']}</b> <span class='{r['status']}'>{r['status']}</span><br><span class='gold'>{r['category']}</span>"
        if r["cover_art"]:
            content += f"<img src='/{r['cover_art']}'>"
        content += f"<p>{r['description']}</p><a href='/release/{r['id']}'>Open Release</a><div class='small'>By @{r['username']}</div></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/release/<int:release_id>")
def release_page(release_id):
    conn = db()
    r = conn.execute("SELECT * FROM media_releases WHERE id=?", (release_id,)).fetchone()
    rights = conn.execute("SELECT * FROM rights_logs WHERE release_id=? ORDER BY id DESC", (release_id,)).fetchall()
    conn.close()
    if not r:
        return "Release not found"

    content = f"<div class='card'><h1>{r['title']}</h1><div class='gold'>{r['category']}</div><p>By @{r['username']} {badge(r['username'])}</p>"
    if r["cover_art"]:
        content += f"<img src='/{r['cover_art']}'>"
    content += f"<p>{r['description']}</p>"

    if r["media_file"]:
        lower = r["media_file"].lower()
        if lower.endswith((".mp3", ".wav", ".ogg", ".m4a")):
            content += f"<audio controls src='/{r['media_file']}'></audio>"
        elif lower.endswith((".mp4", ".webm", ".mov")):
            content += f"<video controls src='/{r['media_file']}'></video>"
        else:
            content += f"<a href='/{r['media_file']}'>Open Media File</a>"

    content += f"<p>Status: <span class='{r['status']}'>{r['status']}</span></p></div>"
    content += "<div class='card'><h2>🛡️ Rights + Proof Log</h2>"
    for x in rights:
        content += f"<div class='card'><b>{x['action']}</b><p>{x['proof_note']}</p><span class='small'>{x['created_at']}</span></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/messages")
def messages():
    if not session.get("user"):
        return redirect("/login")
    me = session["user"]
    conn = db()
    users = conn.execute("SELECT username FROM users WHERE username != ? ORDER BY username", (me,)).fetchall()
    inbox = conn.execute("SELECT * FROM messages WHERE receiver=? OR sender=? ORDER BY id DESC LIMIT 50", (me, me)).fetchall()
    conn.close()
    content = "<div class='card'><h2>💬 Messenger</h2></div><div class='card'><h3>Users</h3>"
    for u in users:
        content += f"<a href='/message/{u['username']}'>@{u['username']}</a> "
    content += "</div>"
    for m in inbox:
        other = m["sender"] if m["sender"] != me else m["receiver"]
        content += f"<div class='card'><b>@{other}</b><p>{m['body']}</p><a href='/message/{other}'>Open</a></div>"
    return render_template_string(BASE, content=content)

@app.route("/message/<username>", methods=["GET","POST"])
def message_user(username):
    if not session.get("user"):
        return redirect("/login")
    me = session["user"]
    if username == me:
        return redirect("/messages")
    conn = db()
    target = conn.execute("SELECT username FROM users WHERE username=?", (username,)).fetchone()
    if not target:
        conn.close()
        return "User not found"
    if request.method == "POST":
        conn.execute("INSERT INTO messages(sender,receiver,body,is_read,created_at) VALUES(?,?,?,?,?)",
                     (me, username, request.form["body"], 0, now()))
        conn.commit()
        conn.close()
        log(f"Message sent to {username}", me)
        return redirect(f"/message/{username}")
    thread = conn.execute("SELECT * FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY id ASC",
                          (me, username, username, me)).fetchall()
    conn.close()
    content = f"<div class='card'><h2>Thread with @{username}</h2></div>"
    for m in thread:
        content += f"<div class='card'><b>@{m['sender']}</b><p>{m['body']}</p><span class='small'>{m['created_at']}</span></div>"
    content += "<div class='card'><form method='POST'><textarea name='body' required></textarea><button>Send</button></form></div>"
    return render_template_string(BASE, content=content)

@app.route("/verify", methods=["GET","POST"])
def verify():
    if not session.get("user"):
        return redirect("/login")
    if request.method == "POST":
        proof = save_file(request.files.get("proof"))
        conn = db()
        conn.execute("INSERT INTO verification_requests(username,reason,proof,status,created_at) VALUES(?,?,?,?,?)",
                     (session["user"], request.form["reason"], proof, "pending", now()))
        conn.commit()
        conn.close()
        log("Verification requested", session["user"])
        return redirect("/verify")
    return render_template_string(BASE, content="""
    <div class='card'><h2>🛡️ Request Verification</h2>
    <form method='POST' enctype='multipart/form-data'>
    <textarea name='reason' placeholder='Reason/proof' required></textarea>
    <input type='file' name='proof'>
    <button>Submit</button>
    </form></div>
    """)

@app.route("/promos", methods=["GET","POST"])
def promos():
    if not session.get("user"):
        return redirect("/login")
    if request.method == "POST":
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("INSERT INTO promo_slots(username,title,category,description,link,image,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (session["user"], request.form["title"], request.form["category"], request.form["description"], request.form["link"], image, "pending", now()))
        conn.commit()
        conn.close()
        log("Promo submitted", session["user"])
        return redirect("/promos")
    conn = db()
    rows = conn.execute("SELECT * FROM promo_slots ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h2>💰 Promo Slots</h2><form method='POST' enctype='multipart/form-data'><input name='title' placeholder='Title'><input name='category' placeholder='Category'><textarea name='description'></textarea><input name='link' placeholder='Link'><input type='file' name='image'><button>Submit</button></form></div>"
    for p in rows:
        content += f"<div class='card'><b>{p['title']}</b> <span class='{p['status']}'>{p['status']}</span><p>{p['description']}</p></div>"
    return render_template_string(BASE, content=content)

@app.route("/founder", methods=["GET","POST"])
def founder():
    if not session.get("user"):
        return redirect("/login")
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO founder_memberships(username,tier,note,status,created_at) VALUES(?,?,?,?,?)",
                     (session["user"], request.form["tier"], request.form["note"], "pending", now()))
        conn.commit()
        conn.close()
        log("Founder membership requested", session["user"])
        return redirect("/founder")
    return render_template_string(BASE, content="""
    <div class='card'><h2>👑 Founder Membership</h2>
    <p>Membership only. Not shares, not investment, not banking.</p>
    <form method='POST'>
    <select name='tier'><option>Supporter</option><option>Creator Founder</option><option>Business Founder</option><option>Royal Founder</option></select>
    <textarea name='note'></textarea>
    <button>Request</button>
    </form></div>
    """)

@app.route("/market", methods=["GET","POST"])
def market():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("INSERT INTO market_products(username,title,category,price,description,image,link,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (session["user"], request.form["title"], request.form["category"], request.form["price"], request.form["description"], image, request.form["link"], "pending", now()))
        conn.commit()
        conn.close()
        log("Market product submitted", session["user"])
        return redirect("/market")
    conn = db()
    products = conn.execute("SELECT * FROM market_products ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h2>🛍️ OAP Market</h2><form method='POST' enctype='multipart/form-data'><input name='title' placeholder='Product title'><input name='category' placeholder='Category'><input name='price' placeholder='Price'><textarea name='description'></textarea><input name='link' placeholder='Optional link'><input type='file' name='image'><button>Submit Product</button></form></div><div class='grid'>"
    for p in products:
        content += f"<div class='card'><b>{p['title']}</b> <span class='{p['status']}'>{p['status']}</span><br><b>{p['price']}</b><p>{p['description']}</p></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO events(title,location,event_date,created_at) VALUES(?,?,?,?)",
                     (request.form["title"], request.form["location"], request.form["event_date"], now()))
        conn.commit()
        conn.close()
        log("Event created", session.get("user","guest"))
        return redirect("/events")
    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h2>⚽ Events</h2><form method='POST'><input name='title'><input name='location'><input type='date' name='event_date'><button>Create</button></form></div>"
    for e in rows:
        content += f"<div class='card'><b>{e['title']}</b><br>{e['location']}<br>{e['event_date']}</div>"
    return render_template_string(BASE, content=content)

@app.route("/businesses", methods=["GET","POST"])
def businesses():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO businesses(name,category,description,created_at) VALUES(?,?,?,?)",
                     (request.form["name"], request.form["category"], request.form["description"], now()))
        conn.commit()
        conn.close()
        log("Business added", session.get("user","guest"))
        return redirect("/businesses")
    conn = db()
    rows = conn.execute("SELECT * FROM businesses ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h2>🏪 Business Board</h2><form method='POST'><input name='name'><input name='category'><textarea name='description'></textarea><button>Add</button></form></div>"
    for b in rows:
        content += f"<div class='card'><b>{b['name']}</b><br>{b['category']}<p>{b['description']}</p></div>"
    return render_template_string(BASE, content=content)

@app.route("/admin")
def admin():
    conn = db()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    verifs = conn.execute("SELECT * FROM verification_requests ORDER BY id DESC LIMIT 20").fetchall()
    promos = conn.execute("SELECT * FROM promo_slots ORDER BY id DESC LIMIT 20").fetchall()
    founders = conn.execute("SELECT * FROM founder_memberships ORDER BY id DESC LIMIT 20").fetchall()
    products = conn.execute("SELECT * FROM market_products ORDER BY id DESC LIMIT 20").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()

    content = "<div class='card'><h2>🧠 HRM Admin Review Core</h2><p>Guardian • Chancellor • Sentinel</p></div>"

    sections = [
        ("🛡️ Verification", verifs, "verify"),
        ("💰 Promos", promos, "promo"),
        ("👑 Founders", founders, "founder"),
        ("🛍️ Products", products, "product"),
        ("🎵 Media Releases", releases, "release"),
    ]

    for title, rows, kind in sections:
        content += f"<div class='card'><h2>{title}</h2>"
        for x in rows:
            label = x["username"] if "username" in x.keys() else "item"
            name = x["title"] if "title" in x.keys() else label
            content += f"<div class='card'><b>{name}</b> by @{label} <span class='{x['status']}'>{x['status']}</span><br>"
            content += f"<a href='/admin/{kind}/{x['id']}/approved'>Approve</a> <a href='/admin/{kind}/{x['id']}/rejected'>Reject</a></div>"
        content += "</div>"

    content += "<div class='card'><h2>📜 Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{l['action']}</b><br>{l['username']}<br><span class='small'>{l['created_at']}</span></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/admin/<kind>/<int:item_id>/<status>")
def admin_action(kind, item_id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")

    tables = {
        "verify": "verification_requests",
        "promo": "promo_slots",
        "founder": "founder_memberships",
        "product": "market_products",
        "release": "media_releases"
    }

    if kind not in tables:
        return redirect("/admin")

    conn = db()
    item = conn.execute(f"SELECT * FROM {tables[kind]} WHERE id=?", (item_id,)).fetchone()
    if item:
        conn.execute(f"UPDATE {tables[kind]} SET status=? WHERE id=?", (status, item_id))

        if kind == "verify" and status == "approved":
            conn.execute("UPDATE users SET verified=1 WHERE username=?", (item["username"],))

        if kind == "release":
            conn.execute("INSERT INTO rights_logs(username,release_id,proof_note,action,created_at) VALUES(?,?,?,?,?)",
                         (item["username"], item_id, item["rights_note"], f"Release {status} by HRM review", now()))

        conn.commit()
        log(f"{kind} {status}", "admin")
    conn.close()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
