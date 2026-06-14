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

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'user',
        created_at TEXT
    )""")

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
.wrap{padding:18px;max-width:900px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:18px;margin:15px 0}
.hero{text-align:center;padding:35px 10px}
.hero h1{font-size:34px;margin:5px}
.green{color:#00dd99}
a{color:#00dd99;text-decoration:none;margin:0 6px}
input,textarea{width:100%;padding:12px;margin:8px 0;background:#0c0c0c;color:white;border:1px solid #333;border-radius:10px}
button{background:#00dd99;color:#000;border:0;border-radius:10px;padding:12px 18px;font-weight:800}
img{max-width:100%;border-radius:14px;margin-top:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.nav{margin-top:10px;line-height:2}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get('user') %}
@{{session.get('user')}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a>
<a href="/register">Join</a>
{% endif %}
</div>
</div>
<div class="wrap">
<div class="nav">
<a href="/">Home</a>
<a href="/creators">Creators</a>
<a href="/events">Events</a>
<a href="/businesses">Businesses</a>
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
    events = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 5").fetchall()
    businesses = conn.execute("SELECT * FROM businesses ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = """
    <div class='hero card'>
        <h1>🌍 ON ANY POSTCODE 👑</h1>
        <div class='green'>✨👑Born Local🔥💨🚀✨Built Global💎💦</div>
        <p>Earth Is Our Turf</p>
        <p>Community → Commerce → Distribution → Infrastructure → Financial Layers</p>
    </div>
    """

    if session.get("user"):
        content += """
        <div class='card'>
        <h2>✍️ Create Post</h2>
        <form method='POST' action='/create_post' enctype='multipart/form-data'>
        <textarea name='content' placeholder="What's happening on your postcode?" required></textarea>
        <input type='file' name='image'>
        <button>Post</button>
        </form>
        </div>
        """

    content += "<div class='card'><h2>📰 Feed + News</h2>"
    for p in posts:
        content += f"<div class='card'><b>@{p['username']}</b><p>{p['content']}</p>"
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<div class='small'>{p['created_at']}</div></div>"
    content += "</div>"

    content += "<div class='card'><h2>🎤 Creator Highlights</h2><div class='grid'>"
    for c in creators:
        content += f"<div class='card'><b>{c['display_name']}</b><br><span class='green'>{c['category']}</span>"
        if c["image"]:
            content += f"<img src='/{c['image']}'>"
        content += f"<p>{c['bio'] or ''}</p><a href='/creator/{c['username']}'>View Profile</a></div>"
    content += "</div></div>"

    content += "<div class='card'><h2>⚽ Events</h2>"
    for e in events:
        content += f"<div class='card'><b>{e['title']}</b><br>📍 {e['location']}<br>📅 {e['event_date']}</div>"
    content += "</div>"

    content += "<div class='card'><h2>🏪 Business Board</h2>"
    for b in businesses:
        content += f"<div class='card'><b>{b['name']}</b><br>🏷️ {b['category']}<p>{b['description']}</p></div>"
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
                         (username,email,password,now()))
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

def save_file(file):
    if not file or file.filename == "":
        return ""
    name = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{name}")
    file.save(path)
    return path

@app.route("/create_post", methods=["POST"])
def create_post():
    if not session.get("user"):
        return redirect("/login")

    image = save_file(request.files.get("image"))
    content = request.form["content"]

    conn = db()
    conn.execute("INSERT INTO posts(username,content,image,created_at) VALUES(?,?,?,?)",
                 (session["user"], content, image, now()))
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
        conn.execute("""INSERT OR REPLACE INTO creator_profiles
        (username,display_name,category,bio,image,link,created_at)
        VALUES(?,?,?,?,?,?,?)""",
        (
            session["user"],
            request.form["display_name"],
            request.form["category"],
            request.form["bio"],
            image,
            request.form["link"],
            now()
        ))
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
        content += f"<div class='card'><b>{c['display_name']}</b><br><span class='green'>{c['category']}</span>"
        if c["image"]:
            content += f"<img src='/{c['image']}'>"
        content += f"<p>{c['bio'] or ''}</p><a href='/creator/{c['username']}'>Open</a></div>"
    content += "</div>"
    return render_template_string(BASE, content=content)

@app.route("/creator/<username>")
def creator(username):
    conn = db()
    c = conn.execute("SELECT * FROM creator_profiles WHERE username=?", (username,)).fetchone()
    posts = conn.execute("SELECT * FROM posts WHERE username=? ORDER BY id DESC", (username,)).fetchall()
    conn.close()

    if not c:
        return "Creator not found"

    content = f"<div class='card'><h1>{c['display_name']}</h1><div class='green'>{c['category']}</div>"
    if c["image"]:
        content += f"<img src='/{c['image']}'>"
    content += f"<p>{c['bio'] or ''}</p><a href='{c['link'] or '#'}'>Main Link</a></div>"
    content += "<div class='card'><h2>Creator Posts</h2>"
    for p in posts:
        content += f"<div class='card'><p>{p['content']}</p><span class='small'>{p['created_at']}</span></div>"
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

    content = """
    <div class='card'><h2>⚽ Events</h2>
    <form method='POST'>
    <input name='title' placeholder='Event title' required>
    <input name='location' placeholder='Location' required>
    <input type='date' name='event_date' required>
    <button>Create Event</button>
    </form></div>
    """
    for e in rows:
        content += f"<div class='card'><b>{e['title']}</b><br>📍 {e['location']}<br>📅 {e['event_date']}</div>"
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

    content = """
    <div class='card'><h2>🏪 Business Board</h2>
    <form method='POST'>
    <input name='name' placeholder='Business name' required>
    <input name='category' placeholder='Category' required>
    <textarea name='description' placeholder='Description'></textarea>
    <button>Add Business</button>
    </form></div>
    """
    for b in rows:
        content += f"<div class='card'><b>{b['name']}</b><br>🏷️ {b['category']}<p>{b['description']}</p></div>"
    return render_template_string(BASE, content=content)

@app.route("/admin")
def admin():
    conn = db()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card'><h2>🧠 HRM Memory + Audit Logs</h2>"
    content += "<p>Proof before execution. Audit before automation. Human approval before action.</p></div>"
    for l in logs:
        content += f"<div class='card'><b>{l['action']}</b><br>👤 {l['username']}<br><span class='small'>{l['created_at']}</span></div>"
    return render_template_string(BASE, content=content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
