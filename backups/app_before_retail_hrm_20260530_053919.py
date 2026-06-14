from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)

ALLOWED = {"jpg","jpeg","png","webp","gif","mp3","wav","ogg","m4a","mp4","webm","mov","pdf"}

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def save_file(f):
    if not f or f.filename == "":
        return ""
    name = secure_filename(f.filename)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED:
        return ""
    path = os.path.join(UPLOAD, datetime.now().strftime("%Y%m%d%H%M%S_") + name)
    f.save(path)
    return path

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

    cur.execute("""CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT,
        image TEXT,
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

    cur.execute("""CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )""")

    conn.commit()
    conn.close()

def log(action, username="system"):
    conn = db()
    conn.execute("INSERT INTO audit_logs(action, username, created_at) VALUES(?,?,?)", (action, username, now()))
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
.green{color:#00dd99}.gold{color:#ffd166}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea{width:100%;padding:12px;margin:8px 0;background:#0c0c0c;color:white;border:1px solid #333;border-radius:10px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:10px;padding:12px 18px;font-weight:800}
img,audio,video{max-width:100%;width:100%;border-radius:14px;margin-top:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.nav{line-height:2;margin-top:10px}
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
<a href="/admin">HRM</a>
</div>
{{content|safe}}
</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

@app.route("/")
def home():
    conn = db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 10").fetchall()
    creators = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC LIMIT 6").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC LIMIT 6").fetchall()
    products = conn.execute("SELECT * FROM market_products ORDER BY id DESC LIMIT 6").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>✨👑Born Local🔥💨🚀✨Built Global💎💦</p>
    <p>Earth Is Our Turf</p>
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

    content += "<div class='card'><h2>📰 Feed</h2>"
    for p in posts:
        content += f"<div class='card'><b>@{p['username']}</b><p>{p['content']}</p>"
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<div class='small'>{p['created_at']}</div></div>"
    content += "</div>"

    content += "<div class='card'><h2>🎤 Creators</h2><div class='grid'>"
    for c in creators:
        content += f"<div class='card'><b>{c['display_name']}</b><p class='green'>{c['category']}</p>"
        if c["image"]:
            content += f"<img src='/{c['image']}'>"
        content += f"<p>{c['bio'] or ''}</p></div>"
    content += "</div></div>"

    content += "<div class='card'><h2>🎵 Media</h2>"
    for r in releases:
        content += f"<div class='card'><b>{r['title']}</b> <span class='gold'>{r['status']}</span><p>{r['description']}</p><a href='/release/{r['id']}'>Open</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>🛍️ Market</h2><div class='grid'>"
    for p in products:
        content += f"<div class='card'><b>{p['title']}</b><p class='gold'>{p['price']}</p><p>{p['description']}</p><a href='/product/{p['id']}'>Open</a></div>"
    content += "</div></div>"

    return render(content)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        role = "admin" if username.lower() == "admin" else "member"
        conn = db()
        try:
            conn.execute("INSERT INTO users(username,email,password,role,created_at) VALUES(?,?,?,?,?)",
                (username, request.form["email"], generate_password_hash(request.form["password"]), role, now()))
            conn.commit()
            log("User registered", username)
            return redirect("/login")
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()

    return render("""
    <div class='card'><h2>Register</h2>
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
        (session["user"], request.form["content"][:1000], image, now()))
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
        (session["user"], request.form["display_name"], request.form["category"], request.form["bio"], image, request.form["link"], now()))
        conn.commit()
        conn.close()
        log("Creator profile saved", session["user"])
        return redirect("/creators")

    conn = db()
    rows = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    <div class='card'><h2>🎤 Creator Profiles</h2>
    <form method='POST' enctype='multipart/form-data'>
    <input name='display_name' placeholder='Display name' required>
    <input name='category' placeholder='Category' required>
    <textarea name='bio' placeholder='Bio'></textarea>
    <input name='link' placeholder='Link'>
    <input type='file' name='image'>
    <button>Save Creator</button>
    </form></div>
    """
    for c in rows:
        content += f"<div class='card'><b>{c['display_name']}</b><p>{c['bio'] or ''}</p></div>"
    return render(content)

@app.route("/media", methods=["GET","POST"])
def media():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        media_file = save_file(request.files.get("media_file"))
        cover_art = save_file(request.files.get("cover_art"))
        if not media_file:
            return "Blocked or invalid media file."
        conn = db()
        conn.execute("""INSERT INTO media_releases
        (username,title,category,description,media_file,cover_art,rights_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (session["user"], request.form["title"], request.form["category"], request.form["description"], media_file, cover_art, request.form["rights_note"], "pending", now()))
        conn.commit()
        conn.close()
        log("Media submitted", session["user"])
        return redirect("/media")

    conn = db()
    rows = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    <div class='card'><h2>🎵 Media Upload</h2>
    <form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Title' required>
    <input name='category' placeholder='Category' required>
    <textarea name='description' placeholder='Description'></textarea>
    <textarea name='rights_note' placeholder='Rights proof' required></textarea>
    <input type='file' name='media_file' required>
    <input type='file' name='cover_art'>
    <button>Submit</button>
    </form></div>
    """
    for r in rows:
        content += f"<div class='card'><b>{r['title']}</b> — {r['status']}<br><a href='/release/{r['id']}'>Open</a></div>"
    return render(content)

@app.route("/release/<int:id>")
def release(id):
    conn = db()
    r = conn.execute("SELECT * FROM media_releases WHERE id=?", (id,)).fetchone()
    conn.close()
    if not r:
        return "Release not found"
    content = f"<div class='card'><h1>{r['title']}</h1><p>{r['description']}</p>"
    if r["cover_art"]:
        content += f"<img src='/{r['cover_art']}'>"
    if r["media_file"]:
        f = r["media_file"].lower()
        if f.endswith((".mp3",".wav",".ogg",".m4a")):
            content += f"<audio controls src='/{r['media_file']}'></audio>"
        elif f.endswith((".mp4",".webm",".mov")):
            content += f"<video controls src='/{r['media_file']}'></video>"
        else:
            content += f"<a href='/{r['media_file']}'>Open file</a>"
    content += f"<div class='card'><h2>Rights</h2><p>{r['rights_note']}</p></div></div>"
    return render(content)

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
        (session["user"], request.form["title"], request.form["category"], request.form["price"], request.form["description"], image, request.form["link"], "pending", now()))
        conn.commit()
        conn.close()
        log("Product submitted", session["user"])
        return redirect("/market")

    conn = db()
    rows = conn.execute("SELECT * FROM market_products ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    <div class='card'><h2>🛍️ Market</h2>
    <form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Product title' required>
    <input name='category' placeholder='Category' required>
    <input name='price' placeholder='Price'>
    <textarea name='description' placeholder='Description'></textarea>
    <input name='link' placeholder='Optional link'>
    <input type='file' name='image'>
    <button>Submit Product</button>
    </form></div>
    """
    for p in rows:
        content += f"<div class='card'><b>{p['title']}</b> — {p['status']}<p>{p['description']}</p><a href='/product/{p['id']}'>Open</a></div>"
    return render(content)

@app.route("/product/<int:id>")
def product(id):
    conn = db()
    p = conn.execute("SELECT * FROM market_products WHERE id=?", (id,)).fetchone()
    conn.close()
    if not p:
        return "Product not found"
    content = f"<div class='card'><h1>{p['title']}</h1><p class='gold'>{p['price']}</p><p>{p['description']}</p>"
    if p["image"]:
        content += f"<img src='/{p['image']}'>"
    if p["link"]:
        content += f"<a href='{p['link']}'>Open Link</a>"
    content += "</div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    products = conn.execute("SELECT * FROM market_products ORDER BY id DESC").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall()
    conn.close()

    content = "<div class='card'><h2>🧠 HRM Admin</h2></div>"

    content += "<div class='card'><h2>Products</h2>"
    for p in products:
        content += f"<div class='card'>{p['title']} — {p['status']} <a href='/admin/product/{p['id']}/approved'>Approve</a> <a href='/admin/product/{p['id']}/rejected'>Reject</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>Releases</h2>"
    for r in releases:
        content += f"<div class='card'>{r['title']} — {r['status']} <a href='/admin/release/{r['id']}/approved'>Approve</a> <a href='/admin/release/{r['id']}/rejected'>Reject</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{l['action']}</b><br>{l['username']}<br>{l['created_at']}</div>"
    content += "</div>"
    return render(content)

@app.route("/admin/product/<int:id>/<status>")
def admin_product(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE market_products SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"Product {status}", session.get("user", "admin"))
    return redirect("/admin")

@app.route("/admin/release/<int:id>/<status>")
def admin_release(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE media_releases SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    log(f"Release {status}", session.get("user", "admin"))
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
