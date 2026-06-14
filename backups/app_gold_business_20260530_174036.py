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

def add_col(cur, table, col, coltype):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")

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
        printful_id TEXT,
        printful_variant_id TEXT,
        description TEXT,
        image TEXT,
        product_link TEXT,
        status TEXT DEFAULT 'pending',
        stock_status TEXT DEFAULT 'available',
        collection TEXT DEFAULT 'General',
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    add_col(cur, "products", "printful_id", "TEXT")
    add_col(cur, "products", "printful_variant_id", "TEXT")
    add_col(cur, "products", "stock_status", "TEXT DEFAULT 'available'")
    add_col(cur, "products", "collection", "TEXT DEFAULT 'General'")

    cur.execute("""CREATE TABLE IF NOT EXISTS business_profiles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        business_name TEXT,
        category TEXT,
        postcode TEXT,
        city TEXT,
        country TEXT,
        description TEXT,
        offer TEXT,
        contact TEXT,
        website TEXT,
        image TEXT,
        status TEXT DEFAULT 'pending',
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS business_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER,
        business_name TEXT,
        event_type TEXT,
        username TEXT,
        note TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS order_intents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        product_title TEXT,
        username TEXT,
        customer_name TEXT,
        customer_contact TEXT,
        size TEXT,
        colour TEXT,
        quantity TEXT,
        amount TEXT,
        supplier TEXT,
        fulfilment_link TEXT,
        note TEXT,
        status TEXT DEFAULT 'new',
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
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
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
        verification_status TEXT DEFAULT 'draft',
        image TEXT,
        related_product_id INTEGER,
        related_link TEXT,
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

    conn.commit()
    conn.close()

def business_event(event_type, business_id, business_name, username, note=""):
    conn = db()
    conn.execute("""INSERT INTO business_events(business_id,business_name,event_type,username,note,created_at)
                   VALUES(?,?,?,?,?,?)""", (business_id, business_name, event_type, username, note, now()))
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
.wrap{padding:18px;max-width:1120px;margin:auto}
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
<a href="/news">News</a>
<a href="/business">Business</a>
<a href="/search">Search</a>
<a href="/creators">Creators</a>
<a href="/media">Media</a>
<a href="/retail">Retail</a>
<a href="/promos">Promos</a>
<a href="/orders">Orders</a>
<a href="/business_hrm">Business HRM</a>
<a href="/admin">HRM</a>
</div>
{{content|safe}}
</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def product_card(p):
    html = f"<div class='card'><b>{p['title']}</b><br><span class='gold'>{p['price']}</span><br><span class='small'>{p['category']} • {p['supplier']}</span>"
    if p["image"]:
        html += f"<img src='/{p['image']}'>"
    html += f"<p>{p['description'] or ''}</p><a href='/product/{p['id']}'>Open Product</a></div>"
    return html

def business_card(b):
    html = f"<div class='card'><b>{b['business_name']}</b><br><span class='gold'>{b['category']}</span><br><span class='small'>{b['postcode']} • {b['city']} • {b['country']}</span>"
    if b["image"]:
        html += f"<img src='/{b['image']}'>"
    html += f"<p>{b['description'] or ''}</p><p class='green'>{b['offer'] or ''}</p><a href='/business/{b['id']}'>Open Business</a></div>"
    return html

def news_card(n):
    html = f"<div class='card'><b>{n['title']}</b><br><span class='gold'>{n['category']}</span><p>{n['summary'] or ''}</p>"
    if n["image"]:
        html += f"<img src='/{n['image']}'>"
    html += f"<a href='/news/{n['id']}'>Read Story</a></div>"
    return html

@app.route("/")
def home():
    conn = db()
    news = conn.execute("SELECT * FROM news_posts WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    businesses = conn.execute("SELECT * FROM business_profiles WHERE status='approved' ORDER BY id DESC LIMIT 6").fetchall()
    products = conn.execute("SELECT * FROM products WHERE status='approved' ORDER BY id DESC LIMIT 6").fetchall()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 6").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>✨👑Born Local🔥💨🚀✨Built Global💎💦</p>
    <p>News + Business + Retail + Creators + HRM</p>
    </div>
    """

    if session.get("user"):
        content += """
        <div class='card'><h2>Create Post</h2>
        <form method='POST' action='/post' enctype='multipart/form-data'>
        <textarea name='content' placeholder="What's happening?" required></textarea>
        <input type='file' name='image'>
        <button>Post</button>
        </form></div>
        """

    content += "<div class='card'><h2>📰 News</h2><div class='grid'>"
    for n in news:
        content += news_card(n)
    content += "</div></div>"

    content += "<div class='card'><h2>🏪 Local Business Board</h2><div class='grid'>"
    for b in businesses:
        content += business_card(b)
    content += "</div></div>"

    content += "<div class='card'><h2>🛍️ Retail</h2><div class='grid'>"
    for p in products:
        content += product_card(p)
    content += "</div></div>"

    content += "<div class='card'><h2>Feed</h2>"
    for p in posts:
        content += f"<div class='card'><b>@{p['username']}</b><p>{p['content']}</p>"
        if p["image"]:
            content += f"<img src='/{p['image']}'>"
        content += "</div>"
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
    return render("""<div class='card'><h2>Register</h2><form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='email' placeholder='Email' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Register</button></form></div>""")

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
    return render("""<div class='card'><h2>Login</h2><form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Login</button></form></div>""")

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

@app.route("/business", methods=["GET","POST"])
def business():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO business_profiles(username,business_name,category,postcode,city,country,description,offer,contact,website,image,status,views,clicks,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            session["user"], request.form["business_name"], request.form["category"],
            request.form["postcode"], request.form["city"], request.form["country"],
            request.form["description"], request.form["offer"], request.form["contact"],
            request.form["website"], image, "pending", 0, 0, now()
        ))
        conn.commit()
        conn.close()
        log("Business submitted", session["user"])
        return redirect("/business")

    conn = db()
    rows = conn.execute("SELECT * FROM business_profiles ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    <div class='card'><h1>🏪 OAP Business Board</h1>
    <p>Local businesses, postcode offers, services, community commerce.</p>
    <form method='POST' enctype='multipart/form-data'>
    <input name='business_name' placeholder='Business name' required>
    <input name='category' placeholder='Food, fashion, music, service, shop, barber...' required>
    <input name='postcode' placeholder='Postcode e.g. CR4, SW16, N24-7'>
    <input name='city' placeholder='City / area'>
    <input name='country' placeholder='Country' value='UK'>
    <textarea name='description' placeholder='Business description'></textarea>
    <textarea name='offer' placeholder='Offer / promo / deal'></textarea>
    <input name='contact' placeholder='Contact / email / phone / handle'>
    <input name='website' placeholder='Website / link'>
    <input type='file' name='image'>
    <button>Submit Business For HRM Review</button>
    </form></div><div class='grid'>
    """
    for b in rows:
        content += business_card(b)
    content += "</div>"
    return render(content)

@app.route("/business/<int:id>")
def business_detail(id):
    conn = db()
    b = conn.execute("SELECT * FROM business_profiles WHERE id=?", (id,)).fetchone()
    if not b:
        conn.close()
        return "Business not found"
    conn.execute("UPDATE business_profiles SET views=views+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    business_event("view", id, b["business_name"], session.get("user","guest"), "Business page viewed")

    content = f"""
    <div class='card'>
    <h1>{b['business_name']}</h1>
    <p class='gold'>{b['category']}</p>
    <p>{b['postcode']} • {b['city']} • {b['country']}</p>
    """
    if b["image"]:
        content += f"<img src='/{b['image']}'>"
    content += f"""
    <p>{b['description']}</p>
    <div class='card'><h2>Offer</h2><p class='green'>{b['offer']}</p></div>
    <p>Contact: {b['contact']}</p>
    <p>Status: {b['status']}</p>
    """
    if b["website"]:
        content += f"<a class='badge' href='/business/{id}/click'>Open Business Link</a>"
    content += "</div>"
    return render(content)

@app.route("/business/<int:id>/click")
def business_click(id):
    conn = db()
    b = conn.execute("SELECT * FROM business_profiles WHERE id=?", (id,)).fetchone()
    if not b:
        conn.close()
        return "Business not found"
    conn.execute("UPDATE business_profiles SET clicks=clicks+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    business_event("click", id, b["business_name"], session.get("user","guest"), "Business link clicked")
    if b["website"]:
        return redirect(b["website"])
    return redirect(f"/business/{id}")

@app.route("/business_hrm")
def business_hrm():
    conn = db()
    total = conn.execute("SELECT COUNT(*) c FROM business_profiles").fetchone()["c"]
    approved = conn.execute("SELECT COUNT(*) c FROM business_profiles WHERE status='approved'").fetchone()["c"]
    views = conn.execute("SELECT COALESCE(SUM(views),0) c FROM business_profiles").fetchone()["c"]
    clicks = conn.execute("SELECT COALESCE(SUM(clicks),0) c FROM business_profiles").fetchone()["c"]
    top = conn.execute("SELECT * FROM business_profiles ORDER BY views DESC, clicks DESC LIMIT 20").fetchall()
    events = conn.execute("SELECT * FROM business_events ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()

    content = f"""
    <div class='card'><h1>🧠 Business HRM</h1></div>
    <div class='grid'>
    <div class='card'><h2>{total}</h2><p>Total Businesses</p></div>
    <div class='card'><h2>{approved}</h2><p>Approved</p></div>
    <div class='card'><h2>{views}</h2><p>Views</p></div>
    <div class='card'><h2>{clicks}</h2><p>Clicks</p></div>
    </div>
    <div class='card'><h2>Top Businesses</h2>
    """
    for b in top:
        content += f"<div class='card'><b>{b['business_name']}</b><br>{b['category']} • {b['postcode']}<br>Views: {b['views']} | Clicks: {b['clicks']} | Status: {b['status']}</div>"
    content += "</div><div class='card'><h2>Business Events</h2>"
    for e in events:
        content += f"<div class='card'><b>{e['event_type']}</b> — {e['business_name']}<br>{e['username']} • {e['note']}<br><span class='small'>{e['created_at']}</span></div>"
    content += "</div>"
    return render(content)

@app.route("/creators", methods=["GET","POST"])
def creators():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT OR REPLACE INTO creator_profiles(username,display_name,category,bio,image,link,created_at)
        VALUES(?,?,?,?,?,?,?)""",
        (session["user"], request.form["display_name"], request.form["category"], request.form["bio"], image, request.form["link"], now()))
        conn.commit()
        conn.close()
        log("Creator profile saved", session["user"])
        return redirect("/creators")
    conn = db()
    rows = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC").fetchall()
    conn.close()
    content = """<div class='card'><h2>Creators</h2><form method='POST' enctype='multipart/form-data'>
    <input name='display_name' placeholder='Display name' required>
    <input name='category' placeholder='Category' required>
    <textarea name='bio' placeholder='Bio'></textarea>
    <input name='link' placeholder='Link'>
    <input type='file' name='image'>
    <button>Save Creator</button></form></div>"""
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
        conn.execute("""INSERT INTO media_releases(username,title,category,description,media_file,cover_art,rights_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (session["user"], request.form["title"], request.form["category"], request.form["description"], media_file, cover_art, request.form["rights_note"], "pending", now()))
        conn.commit()
        conn.close()
        log("Media submitted", session["user"])
        return redirect("/media")
    conn = db()
    rows = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall()
    conn.close()
    content = """<div class='card'><h2>Media Upload</h2><form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Title' required>
    <input name='category' placeholder='Category' required>
    <textarea name='description' placeholder='Description'></textarea>
    <textarea name='rights_note' placeholder='Rights proof' required></textarea>
    <input type='file' name='media_file' required>
    <input type='file' name='cover_art'>
    <button>Submit</button></form></div>"""
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
        conn.execute("""INSERT INTO products(username,title,category,price,supplier,sku,printful_id,printful_variant_id,description,image,product_link,status,stock_status,collection,views,clicks,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (session["user"], request.form["title"], request.form["category"], request.form["price"], request.form["supplier"], request.form["sku"], request.form["printful_id"], request.form["printful_variant_id"], request.form["description"], image, request.form["product_link"], "pending", request.form["stock_status"], request.form["collection"], 0, 0, now()))
        conn.commit()
        conn.close()
        log("Retail product submitted", session["user"])
        return redirect("/retail")
    conn = db()
    rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    content = """<div class='card'><h2>Retail + Printful Connector</h2><form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Product title' required>
    <input name='category' placeholder='Category' required>
    <input name='price' placeholder='Price'>
    <input name='supplier' placeholder='Printful / Printify / Tapstitch' required>
    <input name='sku' placeholder='SKU'>
    <input name='printful_id' placeholder='Printful product ID'>
    <input name='printful_variant_id' placeholder='Printful variant ID'>
    <input name='collection' placeholder='Collection' value='General'>
    <select name='stock_status'><option>available</option><option>limited</option><option>preorder</option><option>sold out</option></select>
    <textarea name='description' placeholder='Description'></textarea>
    <input name='product_link' placeholder='Fulfilment/payment link'>
    <input type='file' name='image'>
    <button>Submit Product</button></form></div><div class='grid'>"""
    for p in rows:
        content += product_card(p)
    content += "</div>"
    return render(content)

@app.route("/product/<int:id>")
def product(id):
    conn = db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    if not p:
        conn.close()
        return "Product not found"
    conn.execute("UPDATE products SET views=views+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    content = f"<div class='card'><h1>{p['title']}</h1><p class='gold'>{p['price']}</p><p>{p['description']}</p>"
    if p["image"]:
        content += f"<img src='/{p['image']}'>"
    if p["product_link"]:
        content += f"<a class='badge' href='/product/{id}/click'>Open Buy Link</a>"
    content += "</div>"
    return render(content)

@app.route("/product/<int:id>/click")
def product_click(id):
    conn = db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    if not p:
        conn.close()
        return "Product not found"
    conn.execute("UPDATE products SET clicks=clicks+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    if p["product_link"]:
        return redirect(p["product_link"])
    return redirect(f"/product/{id}")

@app.route("/news", methods=["GET","POST"])
def news():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO news_posts(username,title,category,summary,body,source_note,verification_status,image,related_product_id,related_link,views,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (session["user"], request.form["title"], request.form["category"], request.form["summary"], request.form["body"], request.form["source_note"], request.form["verification_status"], image, request.form.get("related_product_id") or 0, request.form["related_link"], 0, "pending", now()))
        conn.commit()
        conn.close()
        log("News submitted", session["user"])
        return redirect("/news")
    conn = db()
    rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC").fetchall()
    conn.close()
    content = """<div class='card'><h1>News</h1><form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Title' required>
    <input name='category' placeholder='Community / Retail / Business / World Cup' required>
    <textarea name='summary' placeholder='Summary'></textarea>
    <textarea name='body' placeholder='Story'></textarea>
    <textarea name='source_note' placeholder='Source/proof note'></textarea>
    <select name='verification_status'><option>draft</option><option>verified</option><option>needs review</option></select>
    <input name='related_product_id' placeholder='Related product ID'>
    <input name='related_link' placeholder='Related link'>
    <input type='file' name='image'>
    <button>Submit News</button></form></div><div class='grid'>"""
    for n in rows:
        content += news_card(n)
    content += "</div>"
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
    content = f"<div class='card'><h1>{n['title']}</h1><p class='gold'>{n['category']}</p>"
    if n["image"]:
        content += f"<img src='/{n['image']}'>"
    content += f"<h3>{n['summary']}</h3><p>{n['body']}</p><div class='card'><h2>Verification</h2><p>{n['source_note']}</p></div></div>"
    return render(content)

@app.route("/promos")
def promos():
    conn = db()
    rows = conn.execute("SELECT * FROM promo_slots ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h1>Promos</h1></div>"
    for p in rows:
        content += f"<div class='card'><b>{p['title']}</b> — {p['status']}</div>"
    return render(content)

@app.route("/orders")
def orders():
    conn = db()
    rows = conn.execute("SELECT * FROM order_intents ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()
    content = "<div class='card'><h1>Orders</h1></div>"
    for o in rows:
        content += f"<div class='card'><b>{o['product_title']}</b> — {o['status']} — {o['amount']}</div>"
    return render(content)

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    content = f"""<div class='card'><h1>Search</h1><form method='GET'>
    <input name='q' placeholder='Search OAP...' value='{q}'><button>Search</button></form></div>"""
    if not q:
        return render(content)
    like = f"%{q}%"
    conn = db()
    businesses = conn.execute("SELECT * FROM business_profiles WHERE business_name LIKE ? OR category LIKE ? OR postcode LIKE ? OR city LIKE ?", (like,like,like,like)).fetchall()
    products = conn.execute("SELECT * FROM products WHERE title LIKE ? OR category LIKE ? OR supplier LIKE ?", (like,like,like)).fetchall()
    news_rows = conn.execute("SELECT * FROM news_posts WHERE title LIKE ? OR category LIKE ? OR summary LIKE ?", (like,like,like)).fetchall()
    conn.close()
    content += "<div class='card'><h2>Businesses</h2>"
    for b in businesses:
        content += f"<p><a href='/business/{b['id']}'>{b['business_name']}</a> — {b['postcode']}</p>"
    content += "</div><div class='card'><h2>Products</h2>"
    for p in products:
        content += f"<p><a href='/product/{p['id']}'>{p['title']}</a> — {p['price']}</p>"
    content += "</div><div class='card'><h2>News</h2>"
    for n in news_rows:
        content += f"<p><a href='/news/{n['id']}'>{n['title']}</a> — {n['category']}</p>"
    content += "</div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    businesses = conn.execute("SELECT * FROM business_profiles ORDER BY id DESC").fetchall()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    news_rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h1>HRM Admin</h1></div>"
    content += "<div class='card'><h2>Business Review</h2>"
    for b in businesses:
        content += f"<div class='card'>{b['business_name']} — {b['status']} <a href='/admin/business/{b['id']}/approved'>Approve</a> <a href='/admin/business/{b['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Retail Review</h2>"
    for p in products:
        content += f"<div class='card'>{p['title']} — {p['status']} <a href='/admin/product/{p['id']}/approved'>Approve</a> <a href='/admin/product/{p['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>News Review</h2>"
    for n in news_rows:
        content += f"<div class='card'>{n['title']} — {n['status']} <a href='/admin/news/{n['id']}/approved'>Approve</a> <a href='/admin/news/{n['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Media Review</h2>"
    for r in releases:
        content += f"<div class='card'>{r['title']} — {r['status']} <a href='/admin/release/{r['id']}/approved'>Approve</a> <a href='/admin/release/{r['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{l['action']}</b><br>{l['username']}<br>{l['created_at']}</div>"
    content += "</div>"
    return render(content)

@app.route("/admin/business/<int:id>/<status>")
def admin_business(id, status):
    if status not in ["approved","rejected"]:
        return redirect("/admin")
    conn = db()
    b = conn.execute("SELECT * FROM business_profiles WHERE id=?", (id,)).fetchone()
    conn.execute("UPDATE business_profiles SET status=? WHERE id=?", (status,id))
    conn.commit()
    conn.close()
    if b:
        business_event(f"business_{status}", id, b["business_name"], session.get("user","admin"), "HRM review")
    log(f"Business {status}", session.get("user","admin"))
    return redirect("/admin")

@app.route("/admin/product/<int:id>/<status>")
def admin_product(id, status):
    if status not in ["approved","rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE products SET status=? WHERE id=?", (status,id))
    conn.commit()
    conn.close()
    log(f"Product {status}", session.get("user","admin"))
    return redirect("/admin")

@app.route("/admin/news/<int:id>/<status>")
def admin_news(id, status):
    if status not in ["approved","rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE news_posts SET status=? WHERE id=?", (status,id))
    conn.commit()
    conn.close()
    log(f"News {status}", session.get("user","admin"))
    return redirect("/admin")

@app.route("/admin/release/<int:id>/<status>")
def admin_release(id, status):
    if status not in ["approved","rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE media_releases SET status=? WHERE id=?", (status,id))
    conn.commit()
    conn.close()
    log(f"Release {status}", session.get("user","admin"))
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
