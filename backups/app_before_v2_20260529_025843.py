from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import shutil
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
UPLOAD_FOLDER = "static/uploads"
BACKUP_FOLDER = "backups"
SCHEMA_VERSION = "1.9_messenger_stability"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_file(file):
    if not file or file.filename == "":
        return ""
    name = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, f"{stamp()}_{name}")
    file.save(path)
    return path

def add_column_if_missing(cur, table, column, coltype):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

def log(action, username="system"):
    conn = db()
    conn.execute("INSERT INTO audit_logs(action, username, created_at) VALUES(?,?,?)", (action, username, now()))
    conn.commit()
    conn.close()

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS schema_meta(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT,
        note TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'user',
        verified INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    add_column_if_missing(cur, "users", "role", "TEXT DEFAULT 'user'")
    add_column_if_missing(cur, "users", "verified", "INTEGER DEFAULT 0")

    cur.execute("""CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT,
        image TEXT,
        created_at TEXT
    )""")
    add_column_if_missing(cur, "posts", "image", "TEXT")

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

    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        body TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS risk_register(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        severity TEXT,
        status TEXT DEFAULT 'open',
        mitigation TEXT,
        owner TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS decision_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        decision TEXT,
        reason TEXT,
        approved_by TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS backup_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        note TEXT,
        created_by TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )""")

    cur.execute("INSERT INTO schema_meta(version,note,created_at) VALUES(?,?,?)",
                (SCHEMA_VERSION, "Messenger + Stability Core loaded", now()))

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
.wrap{padding:18px;max-width:1000px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:18px;margin:15px 0}
.hero{text-align:center;padding:35px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:12px;margin:8px 0;background:#0c0c0c;color:white;border:1px solid #333;border-radius:10px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:10px;padding:12px 18px;font-weight:800}
img,audio,video{max-width:100%;width:100%;border-radius:14px;margin-top:10px}
.nav{line-height:2;margin-top:10px}.small{color:#aaa;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.me{background:#0f2b22}.them{background:#202020}
.open{color:#ffd166}.closed{color:#00dd99}.high{color:#ff6b6b}.medium{color:#ffd166}.low{color:#00dd99}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a><a href="/register">Join</a>
{% endif %}
</div>
</div>
<div class="wrap">
<div class="nav">
<a href="/">Home</a>
<a href="/creators">Creators</a>
<a href="/media">Media</a>
<a href="/market">Market</a>
<a href="/messages">Messages</a>
<a href="/stability">Stability</a>
<a href="/admin">HRM</a>
</div>
{{content|safe}}
</div>
</body>
</html>
"""

@app.route("/")
def home():
    conn = db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 10").fetchall()
    creators = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC LIMIT 6").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC LIMIT 6").fetchall()
    products = conn.execute("SELECT * FROM market_products WHERE status='approved' ORDER BY id DESC LIMIT 6").fetchall()
    risks = conn.execute("SELECT * FROM risk_register WHERE status='open' ORDER BY id DESC LIMIT 3").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>✨👑Born Local🔥💨🚀✨Built Global💎💦</p>
    <p>Earth Is Our Turf</p>
    <p>Community → Commerce → Distribution → Infrastructure → Financial Layers</p>
    </div>
    """

    if session.get("user"):
        content += """
        <div class='card'>
        <h2>✍️ Create Post</h2>
        <form method='POST' action='/post' enctype='multipart/form-data'>
        <textarea name='content' placeholder="What's happening?" required></textarea>
        <input type='file' name='image'>
        <button>Post</button>
        </form>
        </div>
        """

    content += "<div class='card'><h2>🛡️ Stability Signals</h2>"
    for r in risks:
        content += f"<div class='card'><b>{r['title']}</b> <span class='{r['severity'].lower()}'>{r['severity']}</span><p>{r['mitigation']}</p></div>"
    if not risks:
        content += "<p class='green'>No open risks logged.</p>"
    content += "</div>"

    content += "<div class='card'><h2>🛍️ OAP Market</h2><div class='grid'>"
    for p in products:
        content += f"<div class='card'><b>{p['title']}</b><br><span class='gold'>{p['category']}</span><br><b>{p['price']}</b>"
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<p>{p['description']}</p><a href='/product/{p['id']}'>Open Product</a></div>"
    content += "</div></div>"

    content += "<div class='card'><h2>🎤 Creator Highlights</h2><div class='grid'>"
    for c in creators:
        content += f"<div class='card'><b>{c['display_name']}</b><p class='green'>{c['category']}</p>"
        if c["image"]:
            content += f"<img src='/{c['image']}'>"
        content += f"<p>{c['bio'] or ''}</p><a href='/creator/{c['username']}'>Open Profile</a></div>"
    content += "</div></div>"

    content += "<div class='card'><h2>🎵 Media Releases</h2>"
    for r in releases:
        content += f"<div class='card'><b>{r['title']}</b> <span class='gold'>{r['status']}</span><br>{r['category']}<p>{r['description']}</p><a href='/release/{r['id']}'>Open Release</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>📰 Feed</h2>"
    for p in posts:
        content += f"<div class='card'><b>@{p['username']}</b><p>{p['content']}</p>"
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<div class='small'>{p['created_at']}</div></div>"
    content += "</div>"

    return render_template_string(BASE, content=content)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = generate_password_hash(request.form["password"])
        conn = db()
        try:
            conn.execute("INSERT INTO users(username,email,password,created_at) VALUES(?,?,?,?)",
                         (username, email, password, now()))
            conn.commit()
            log("User registered", username)
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
        username = request.form["username"].strip()
        password = request.form["password"]
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user"] = username
            log("User login", username)
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

@app.route("/post", methods=["POST"])
def post():
    if not session.get("user"):
        return redirect("/login")
    image = save_file(request.files.get("image"))
    conn = db()
    conn.execute("INSERT INTO posts(username,content,image,created_at) VALUES(?,?,?,?)",
                 (session["user"], request.form["content"], image, now()))
    conn.commit()
    conn.close()
    log("Post created", session["user"])
    return redirect("/")

@app.route("/creators", methods=["GET","POST"])
def creators():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT OR REPLACE INTO creator_profiles
        (username,display_name,category,bio,image,link,created_at)
        VALUES(?,?,?,?,?,?,?)""",
        (session["user"], request.form["display_name"], request.form["category"],
         request.form["bio"], image, request.form["link"], now()))
        conn.commit()
        conn.close()
        log("Creator profile saved", session["user"])
        return redirect("/creators")

    conn = db()
    rows = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC").fetchall()
    conn.close()

    content = "<div class='card'><h2>🎤 Creator Profiles</h2>"
    if session.get("user"):
        content += """
        <form method='POST' enctype='multipart/form-data'>
        <input name='display_name' placeholder='Display name' required>
        <input name='category' placeholder='Music, fashion, sport, comedy, education...' required>
        <textarea name='bio' placeholder='Bio'></textarea>
        <input name='link' placeholder='Main link'>
        <input type='file' name='image'>
        <button>Save Creator Profile</button>
        </form>
        """
    content += "</div><div class='grid'>"
    for c in rows:
        content += f"<div class='card'><h2>{c['display_name']}</h2><p class='green'>{c['category']}</p>"
        if c["image"]:
            content += f"<img src='/{c['image']}'>"
        content += f"<p>{c['bio'] or ''}</p><a href='/creator/{c['username']}'>Open Profile</a> <a href='/message/{c['username']}'>Message</a></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/creator/<username>")
def creator_profile(username):
    conn = db()
    c = conn.execute("SELECT * FROM creator_profiles WHERE username=?", (username,)).fetchone()
    releases = conn.execute("SELECT * FROM media_releases WHERE username=? ORDER BY id DESC", (username,)).fetchall()
    posts = conn.execute("SELECT * FROM posts WHERE username=? ORDER BY id DESC", (username,)).fetchall()
    products = conn.execute("SELECT * FROM market_products WHERE username=? ORDER BY id DESC", (username,)).fetchall()
    conn.close()
    if not c:
        return "Creator not found"

    content = f"<div class='card'><h1>{c['display_name']}</h1><p class='green'>{c['category']}</p>"
    if c["image"]:
        content += f"<img src='/{c['image']}'>"
    content += f"<p>{c['bio'] or ''}</p><a href='{c['link'] or '#'}'>Main Link</a> <a href='/message/{username}'>Message</a></div>"

    content += "<div class='card'><h2>🛍️ Products</h2>"
    for p in products:
        content += f"<div class='card'><b>{p['title']}</b> — {p['status']}<br><a href='/product/{p['id']}'>Open Product</a></div>"
    content += "</div><div class='card'><h2>🎵 Releases</h2>"
    for r in releases:
        content += f"<div class='card'><b>{r['title']}</b> — {r['status']}<br><a href='/release/{r['id']}'>Open Release</a></div>"
    content += "</div><div class='card'><h2>📰 Posts</h2>"
    for p in posts:
        content += f"<div class='card'><p>{p['content']}</p><span class='small'>{p['created_at']}</span></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/messages")
def messages():
    if not session.get("user"):
        return redirect("/login")

    me = session["user"]
    conn = db()
    users = conn.execute("SELECT username FROM users WHERE username != ? ORDER BY username", (me,)).fetchall()
    inbox = conn.execute("SELECT * FROM messages WHERE sender=? OR receiver=? ORDER BY id DESC LIMIT 50", (me, me)).fetchall()
    conn.close()

    content = "<div class='card'><h2>💬 OAP Messenger</h2><p>Private user-to-user messaging. Human-first, audit-aware.</p></div>"
    content += "<div class='card'><h3>Users</h3>"
    for u in users:
        content += f"<a href='/message/{u['username']}'>@{u['username']}</a> "
    content += "</div>"

    content += "<div class='card'><h3>Recent Messages</h3>"
    for m in inbox:
        other = m["sender"] if m["sender"] != me else m["receiver"]
        direction = "From" if m["receiver"] == me else "To"
        unread = " 🟢 unread" if m["receiver"] == me and m["is_read"] == 0 else ""
        content += f"<div class='card'><b>{direction}: @{other}</b>{unread}<p>{m['body']}</p><span class='small'>{m['created_at']}</span><br><a href='/message/{other}'>Open Thread</a></div>"
    content += "</div>"
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
        body = request.form["body"].strip()
        if body:
            conn.execute("INSERT INTO messages(sender,receiver,body,is_read,created_at) VALUES(?,?,?,?,?)",
                         (me, username, body, 0, now()))
            conn.commit()
            conn.close()
            log(f"Message sent to {username}", me)
            return redirect(f"/message/{username}")

    conn.execute("UPDATE messages SET is_read=1 WHERE receiver=? AND sender=?", (me, username))
    conn.commit()
    thread = conn.execute("""SELECT * FROM messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY id ASC""", (me, username, username, me)).fetchall()
    conn.close()

    content = f"<div class='card'><h2>💬 Thread with @{username}</h2></div>"
    for m in thread:
        cls = "me" if m["sender"] == me else "them"
        content += f"<div class='card {cls}'><b>@{m['sender']}</b><p>{m['body']}</p><span class='small'>{m['created_at']}</span></div>"
    content += """
    <div class='card'>
    <form method='POST'>
    <textarea name='body' placeholder='Write message...' required></textarea>
    <button>Send</button>
    </form>
    </div>
    """
    return render_template_string(BASE, content=content)

@app.route("/media", methods=["GET","POST"])
def media():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        media_file = save_file(request.files.get("media_file"))
        cover_art = save_file(request.files.get("cover_art"))
        conn = db()
        conn.execute("""INSERT INTO media_releases
        (username,title,category,description,media_file,cover_art,rights_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (session["user"], request.form["title"], request.form["category"], request.form["description"],
         media_file, cover_art, request.form["rights_note"], "pending", now()))
        conn.commit()
        conn.close()
        log("Media release submitted", session["user"])
        return redirect("/media")

    conn = db()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h2>🎵 OAP Media Uploads</h2><p>Upload only owned, licensed, or cleared media.</p>"
    if session.get("user"):
        content += """
        <form method='POST' enctype='multipart/form-data'>
        <input name='title' placeholder='Release title' required>
        <input name='category' placeholder='Music, video, podcast, trailer...' required>
        <textarea name='description' placeholder='Description'></textarea>
        <textarea name='rights_note' placeholder='Rights/proof note' required></textarea>
        <label>Media file</label><input type='file' name='media_file' required>
        <label>Cover art</label><input type='file' name='cover_art'>
        <button>Submit Release</button>
        </form>
        """
    content += "</div>"
    for r in releases:
        content += f"<div class='card'><b>{r['title']}</b> <span class='gold'>{r['status']}</span><br>{r['category']}<p>{r['description']}</p><a href='/release/{r['id']}'>Open Release</a></div>"
    return render_template_string(BASE, content=content)

@app.route("/release/<int:release_id>")
def release(release_id):
    conn = db()
    r = conn.execute("SELECT * FROM media_releases WHERE id=?", (release_id,)).fetchone()
    conn.close()
    if not r:
        return "Release not found"

    content = f"<div class='card'><h1>{r['title']}</h1><p class='gold'>{r['category']}</p><p>By @{r['username']}</p>"
    if r["cover_art"]:
        content += f"<img src='/{r['cover_art']}'>"
    content += f"<p>{r['description']}</p>"
    if r["media_file"]:
        f = r["media_file"].lower()
        if f.endswith((".mp3", ".wav", ".ogg", ".m4a")):
            content += f"<audio controls src='/{r['media_file']}'></audio>"
        elif f.endswith((".mp4", ".webm", ".mov")):
            content += f"<video controls src='/{r['media_file']}'></video>"
        else:
            content += f"<a href='/{r['media_file']}'>Open file</a>"
    content += f"<div class='card'><h2>🛡️ Rights + Proof</h2><p>{r['rights_note']}</p><p>Status: {r['status']}</p></div></div>"
    return render_template_string(BASE, content=content)

@app.route("/market", methods=["GET","POST"])
def market():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO market_products
        (username,title,category,price,description,image,link,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (session["user"], request.form["title"], request.form["category"], request.form["price"],
         request.form["description"], image, request.form["link"], "pending", now()))
        conn.commit()
        conn.close()
        log("Market product submitted", session["user"])
        return redirect("/market")

    conn = db()
    products = conn.execute("SELECT * FROM market_products ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h2>🛍️ OAP Market</h2><p>OAP is the destination. External links are optional routes only.</p>"
    if session.get("user"):
        content += """
        <form method='POST' enctype='multipart/form-data'>
        <input name='title' placeholder='Product title' required>
        <input name='category' placeholder='Clothing, digital, event, music bundle, service...' required>
        <input name='price' placeholder='Price e.g. £25'>
        <textarea name='description' placeholder='Product description'></textarea>
        <input name='link' placeholder='Optional product/payment/fulfilment link'>
        <input type='file' name='image'>
        <button>Submit Product For HRM Review</button>
        </form>
        """
    content += "</div><div class='grid'>"
    for p in products:
        content += f"<div class='card'><h2>{p['title']}</h2><p class='green'>{p['category']}</p><p class='gold'>{p['price']}</p>"
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<p>{p['description']}</p><p>Status: {p['status']}</p><a href='/product/{p['id']}'>Open Product</a></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/product/<int:product_id>")
def product(product_id):
    conn = db()
    p = conn.execute("SELECT * FROM market_products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    if not p:
        return "Product not found"

    content = f"<div class='card'><h1>{p['title']}</h1><p class='green'>{p['category']}</p><p class='gold'>{p['price']}</p><p>By @{p['username']}</p>"
    if p["image"]:
        content += f"<img src='/{p['image']}'>"
    content += f"<p>{p['description']}</p><p>Status: {p['status']}</p>"
    if p["link"]:
        content += f"<a href='{p['link']}'>Open Product Link</a>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/stability", methods=["GET","POST"])
def stability():
    if not session.get("user"):
        return redirect("/login")

    if request.method == "POST":
        form_type = request.form.get("form_type")
        conn = db()
        if form_type == "risk":
            conn.execute("""INSERT INTO risk_register(title,category,severity,status,mitigation,owner,created_at)
            VALUES(?,?,?,?,?,?,?)""",
            (request.form["title"], request.form["category"], request.form["severity"], "open",
             request.form["mitigation"], session["user"], now()))
            conn.commit()
            conn.close()
            log("Risk registered", session["user"])
            return redirect("/stability")
        if form_type == "decision":
            conn.execute("""INSERT INTO decision_logs(title,decision,reason,approved_by,created_at)
            VALUES(?,?,?,?,?)""",
            (request.form["title"], request.form["decision"], request.form["reason"], session["user"], now()))
            conn.commit()
            conn.close()
            log("Decision logged", session["user"])
            return redirect("/stability")
        conn.close()

    conn = db()
    risks = conn.execute("SELECT * FROM risk_register ORDER BY id DESC").fetchall()
    decisions = conn.execute("SELECT * FROM decision_logs ORDER BY id DESC").fetchall()
    backups = conn.execute("SELECT * FROM backup_logs ORDER BY id DESC").fetchall()
    schema = conn.execute("SELECT * FROM schema_meta ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = """
    <div class='card'><h2>🛡️ OAP Stability Core</h2>
    <form method='POST' action='/backup_now'><button>Create Database Backup</button></form></div>

    <div class='card'><h2>⚠️ Add Risk</h2>
    <form method='POST'>
    <input type='hidden' name='form_type' value='risk'>
    <input name='title' placeholder='Risk title' required>
    <input name='category' placeholder='Database, security, media, market, overbuild...' required>
    <select name='severity'><option>High</option><option>Medium</option><option>Low</option></select>
    <textarea name='mitigation' placeholder='Mitigation' required></textarea>
    <button>Log Risk</button>
    </form></div>

    <div class='card'><h2>🧠 Add Decision</h2>
    <form method='POST'>
    <input type='hidden' name='form_type' value='decision'>
    <input name='title' placeholder='Decision title' required>
    <textarea name='decision' placeholder='Decision' required></textarea>
    <textarea name='reason' placeholder='Reason' required></textarea>
    <button>Log Decision</button>
    </form></div>
    """

    content += "<div class='card'><h2>⚠️ Risk Register</h2>"
    for r in risks:
        content += f"<div class='card'><b>{r['title']}</b> <span class='{r['severity'].lower()}'>{r['severity']}</span><br>{r['category']}<p>{r['mitigation']}</p><p>Status: {r['status']}</p><a href='/risk/{r['id']}/closed'>Close Risk</a></div>"
    content += "</div><div class='card'><h2>🧠 Decision Log</h2>"
    for d in decisions:
        content += f"<div class='card'><b>{d['title']}</b><p>{d['decision']}</p><p>{d['reason']}</p><span class='small'>{d['approved_by']} — {d['created_at']}</span></div>"
    content += "</div><div class='card'><h2>💾 Backup Log</h2>"
    for b in backups:
        content += f"<div class='card'><b>{b['filename']}</b><p>{b['note']}</p><span class='small'>{b['created_by']} — {b['created_at']}</span></div>"
    content += "</div><div class='card'><h2>🧱 Schema Memory</h2>"
    for s in schema:
        content += f"<div class='card'><b>{s['version']}</b><p>{s['note']}</p><span class='small'>{s['created_at']}</span></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/backup_now", methods=["POST"])
def backup_now():
    if not session.get("user"):
        return redirect("/login")
    filename = f"oap_backup_{stamp()}.db"
    filepath = os.path.join(BACKUP_FOLDER, filename)
    if os.path.exists(DB):
        shutil.copy(DB, filepath)
        conn = db()
        conn.execute("INSERT INTO backup_logs(filename,note,created_by,created_at) VALUES(?,?,?,?)",
                     (filename, "Manual database backup created", session["user"], now()))
        conn.commit()
        conn.close()
        log("Database backup created", session["user"])
    return redirect("/stability")

@app.route("/risk/<int:risk_id>/<status>")
def update_risk(risk_id, status):
    if not session.get("user"):
        return redirect("/login")
    if status not in ["open", "closed"]:
        return redirect("/stability")
    conn = db()
    conn.execute("UPDATE risk_register SET status=? WHERE id=?", (status, risk_id))
    conn.commit()
    conn.close()
    log(f"Risk marked {status}", session["user"])
    return redirect("/stability")

@app.route("/admin")
def admin():
    conn = db()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC LIMIT 50").fetchall()
    creators = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC LIMIT 50").fetchall()
    products = conn.execute("SELECT * FROM market_products ORDER BY id DESC LIMIT 50").fetchall()
    risks = conn.execute("SELECT * FROM risk_register WHERE status='open' ORDER BY id DESC LIMIT 20").fetchall()
    messages_count = conn.execute("SELECT COUNT(*) AS c FROM messages").fetchone()["c"]
    conn.close()

    content = f"""
    <div class='card'><h2>🧠 HRM Admin Core</h2>
    <p>Guardian • Chancellor • Sentinel</p>
    <p>Total messages: {messages_count}</p>
    </div>
    """

    content += "<div class='card'><h2>⚠️ Open Risks</h2>"
    for r in risks:
        content += f"<div class='card'><b>{r['title']}</b> <span class='{r['severity'].lower()}'>{r['severity']}</span><p>{r['mitigation']}</p></div>"
    content += "</div>"

    content += "<div class='card'><h2>🛍️ Market Review</h2>"
    for p in products:
        content += f"<div class='card'><b>{p['title']}</b> by @{p['username']} — {p['status']}<br><a href='/admin/product/{p['id']}/approved'>Approve</a><a href='/admin/product/{p['id']}/rejected'>Reject</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>🎵 Release Review</h2>"
    for r in releases:
        content += f"<div class='card'><b>{r['title']}</b> by @{r['username']} — {r['status']}<br><a href='/admin/release/{r['id']}/approved'>Approve</a><a href='/admin/release/{r['id']}/rejected'>Reject</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>🎤 Creator Records</h2>"
    for c in creators:
        content += f"<div class='card'><b>{c['display_name']}</b> — @{c['username']}<br>{c['category']}</div>"
    content += "</div><div class='card'><h2>📜 Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{l['action']}</b><br>{l['username']}<br>{l['created_at']}</div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/admin/release/<int:release_id>/<status>")
def admin_release(release_id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    r = conn.execute("SELECT * FROM media_releases WHERE id=?", (release_id,)).fetchone()
    if r:
        conn.execute("UPDATE media_releases SET status=? WHERE id=?", (status, release_id))
        conn.commit()
        log(f"Release {status}: {r['title']}", "admin")
    conn.close()
    return redirect("/admin")

@app.route("/admin/product/<int:product_id>/<status>")
def admin_product(product_id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    p = conn.execute("SELECT * FROM market_products WHERE id=?", (product_id,)).fetchone()
    if p:
        conn.execute("UPDATE market_products SET status=? WHERE id=?", (status, product_id))
        conn.commit()
        log(f"Product {status}: {p['title']}", "admin")
    conn.close()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
