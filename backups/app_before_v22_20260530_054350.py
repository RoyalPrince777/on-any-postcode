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
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

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

def add_col(cur, table, col, coltype):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")

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
    add_col(cur, "posts", "image", "TEXT")

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

    cur.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        category TEXT,
        price TEXT,
        supplier TEXT,
        sku TEXT,
        description TEXT,
        image TEXT,
        product_link TEXT,
        status TEXT DEFAULT 'pending',
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sales_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        product_title TEXT,
        username TEXT,
        buyer_note TEXT,
        amount TEXT,
        supplier TEXT,
        status TEXT DEFAULT 'recorded',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS retail_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        product_id INTEGER,
        product_title TEXT,
        username TEXT,
        note TEXT,
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

def retail_event(event_type, product_id, product_title, username, note=""):
    conn = db()
    conn.execute("""INSERT INTO retail_events(event_type,product_id,product_title,username,note,created_at)
                   VALUES(?,?,?,?,?,?)""", (event_type, product_id, product_title, username, note, now()))
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
img,audio,video{max-width:100%;width:100%;border-radius:14px;margin-top:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.nav{line-height:2;margin-top:10px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:4px 8px;border-radius:999px;font-size:12px;font-weight:bold}
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
<a href="/retail">Retail</a>
<a href="/retail_hrm">Retail HRM</a>
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
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 8").fetchall()
    products = conn.execute("SELECT * FROM products WHERE status='approved' ORDER BY id DESC LIMIT 8").fetchall()
    creators = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC LIMIT 6").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC LIMIT 6").fetchall()
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

    content += "<div class='card'><h2>🛍️ Featured OAP Retail</h2><div class='grid'>"
    for p in products:
        content += f"""
        <div class='card'>
        <b>{p['title']}</b><br>
        <span class='gold'>{p['price']}</span><br>
        <span class='small'>{p['category']} • {p['supplier']}</span>
        """
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<p>{p['description'] or ''}</p><a href='/product/{p['id']}'>Open Product</a></div>"
    content += "</div></div>"

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

    content += "<div class='card'><h2>📰 Feed</h2>"
    for p in posts:
        content += f"<div class='card'><b>@{p['username']}</b><p>{p['content']}</p>"
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<div class='small'>{p['created_at']}</div></div>"
    content += "</div>"

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
    <input name='category' placeholder='Music, fashion, sport, comedy, education...' required>
    <textarea name='bio' placeholder='Bio'></textarea>
    <input name='link' placeholder='Link'>
    <input type='file' name='image'>
    <button>Save Creator</button>
    </form></div>
    """
    for c in rows:
        content += f"<div class='card'><b>{c['display_name']}</b><p>{c['category']}</p><p>{c['bio'] or ''}</p></div>"
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

@app.route("/retail", methods=["GET","POST"])
def retail():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO products
        (username,title,category,price,supplier,sku,description,image,product_link,status,views,clicks,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            session["user"],
            request.form["title"],
            request.form["category"],
            request.form["price"],
            request.form["supplier"],
            request.form["sku"],
            request.form["description"],
            image,
            request.form["product_link"],
            "pending",
            0,
            0,
            now()
        ))
        conn.commit()
        conn.close()
        log("Retail product submitted", session["user"])
        return redirect("/retail")

    conn = db()
    rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    <div class='card'><h2>🛍️ OAP Retail</h2>
    <p>OAP is the destination. Printful, Printify, Tapstitch and other POD suppliers are fulfilment routes.</p>
    <form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Product title' required>
    <input name='category' placeholder='T-shirt, hoodie, bandana, tracksuit, cap...' required>
    <input name='price' placeholder='Price e.g. £25'>
    <input name='supplier' placeholder='Printful, Printify, Tapstitch, Gelato, Local Printer...' required>
    <input name='sku' placeholder='SKU / supplier product ID'>
    <textarea name='description' placeholder='Product description'></textarea>
    <input name='product_link' placeholder='External fulfilment/payment link'>
    <input type='file' name='image'>
    <button>Submit Product For HRM Review</button>
    </form></div>
    <div class='grid'>
    """
    for p in rows:
        content += f"""
        <div class='card'>
        <b>{p['title']}</b> <span class='gold'>{p['status']}</span><br>
        <span>{p['category']}</span><br>
        <b>{p['price']}</b><br>
        <span class='small'>Supplier: {p['supplier']} | SKU: {p['sku'] or 'N/A'}</span>
        """
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += f"<p>{p['description'] or ''}</p><a href='/product/{p['id']}'>Open Product</a></div>"
    content += "</div>"
    return render(content)

@app.route("/product/<int:id>")
def product(id):
    conn = db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    if not p:
        conn.close()
        return "Product not found"

    conn.execute("UPDATE products SET views = views + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    retail_event("view", id, p["title"], session.get("user", "guest"), "Product page viewed")

    content = f"""
    <div class='card'>
    <h1>{p['title']}</h1>
    <p class='green'>{p['category']}</p>
    <p class='gold'>{p['price']}</p>
    <p>Supplier: {p['supplier']}</p>
    <p>SKU: {p['sku'] or 'N/A'}</p>
    """
    if p["image"]:
        content += f"<img src='/{p['image']}'>"
    content += f"<p>{p['description'] or ''}</p><p>Status: {p['status']}</p>"

    if p["product_link"]:
        content += f"<a class='badge' href='/product/{id}/click'>Open Buy/Fulfilment Link</a>"

    content += """
    </div>
    <div class='card'>
    <h2>Record Manual Sale</h2>
    <form method='POST' action='/sale_record'>
    <input type='hidden' name='product_id' value='""" + str(p["id"]) + """'>
    <input type='hidden' name='product_title' value='""" + p["title"] + """'>
    <input type='hidden' name='supplier' value='""" + (p["supplier"] or "") + """'>
    <input name='amount' placeholder='Amount e.g. £25'>
    <textarea name='buyer_note' placeholder='Buyer/order note'></textarea>
    <button>Record Sale</button>
    </form>
    </div>
    """
    return render(content)

@app.route("/product/<int:id>/click")
def product_click(id):
    conn = db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    if not p:
        conn.close()
        return "Product not found"
    conn.execute("UPDATE products SET clicks = clicks + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    retail_event("click", id, p["title"], session.get("user", "guest"), "External product link clicked")
    if p["product_link"]:
        return redirect(p["product_link"])
    return redirect(f"/product/{id}")

@app.route("/sale_record", methods=["POST"])
def sale_record():
    if not session.get("user"):
        return redirect("/login")
    conn = db()
    conn.execute("""INSERT INTO sales_records(product_id,product_title,username,buyer_note,amount,supplier,status,created_at)
    VALUES(?,?,?,?,?,?,?,?)""",
    (
        request.form["product_id"],
        request.form["product_title"],
        session["user"],
        request.form["buyer_note"],
        request.form["amount"],
        request.form["supplier"],
        "recorded",
        now()
    ))
    conn.commit()
    conn.close()
    retail_event("sale_recorded", request.form["product_id"], request.form["product_title"], session["user"], request.form["amount"])
    log("Retail sale recorded", session["user"])
    return redirect("/retail_hrm")

@app.route("/retail_hrm")
def retail_hrm():
    conn = db()
    total_products = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
    approved_products = conn.execute("SELECT COUNT(*) c FROM products WHERE status='approved'").fetchone()["c"]
    total_views = conn.execute("SELECT COALESCE(SUM(views),0) c FROM products").fetchone()["c"]
    total_clicks = conn.execute("SELECT COALESCE(SUM(clicks),0) c FROM products").fetchone()["c"]
    total_sales = conn.execute("SELECT COUNT(*) c FROM sales_records").fetchone()["c"]
    products = conn.execute("SELECT * FROM products ORDER BY views DESC, clicks DESC LIMIT 20").fetchall()
    sales = conn.execute("SELECT * FROM sales_records ORDER BY id DESC LIMIT 20").fetchall()
    events = conn.execute("SELECT * FROM retail_events ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()

    content = f"""
    <div class='card'>
    <h1>🧠 OAP Retail HRM</h1>
    <p>Tracks products, suppliers, views, clicks, sales records and learning signals.</p>
    </div>

    <div class='grid'>
    <div class='card'><h2>{total_products}</h2><p>Total Products</p></div>
    <div class='card'><h2>{approved_products}</h2><p>Approved Products</p></div>
    <div class='card'><h2>{total_views}</h2><p>Product Views</p></div>
    <div class='card'><h2>{total_clicks}</h2><p>External Clicks</p></div>
    <div class='card'><h2>{total_sales}</h2><p>Recorded Sales</p></div>
    </div>
    """

    content += "<div class='card'><h2>Top Retail Products</h2>"
    for p in products:
        content += f"<div class='card'><b>{p['title']}</b><br>{p['supplier']} • {p['price']}<br>Views: {p['views']} | Clicks: {p['clicks']} | Status: {p['status']}</div>"
    content += "</div>"

    content += "<div class='card'><h2>Sales Records</h2>"
    for s in sales:
        content += f"<div class='card'><b>{s['product_title']}</b><br>{s['amount']} • {s['supplier']}<br>{s['buyer_note']}<br><span class='small'>{s['created_at']}</span></div>"
    content += "</div>"

    content += "<div class='card'><h2>Retail Events</h2>"
    for e in events:
        content += f"<div class='card'><b>{e['event_type']}</b> — {e['product_title']}<br>{e['username']} • {e['note']}<br><span class='small'>{e['created_at']}</span></div>"
    content += "</div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall()
    conn.close()

    content = "<div class='card'><h2>🧠 HRM Admin</h2><p>Guardian • Chancellor • Sentinel</p></div>"

    content += "<div class='card'><h2>Retail Products Review</h2>"
    for p in products:
        content += f"<div class='card'>{p['title']} — {p['status']} <a href='/admin/product/{p['id']}/approved'>Approve</a> <a href='/admin/product/{p['id']}/rejected'>Reject</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>Media Releases Review</h2>"
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
    p = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    conn.execute("UPDATE products SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    if p:
        retail_event(f"product_{status}", id, p["title"], session.get("user", "admin"), "HRM review action")
    log(f"Retail product {status}", session.get("user", "admin"))
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
