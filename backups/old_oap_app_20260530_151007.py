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
        stock_status TEXT DEFAULT 'available',
        collection TEXT DEFAULT 'General',
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    add_col(cur, "products", "stock_status", "TEXT DEFAULT 'available'")
    add_col(cur, "products", "collection", "TEXT DEFAULT 'General'")

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

    cur.execute("""CREATE TABLE IF NOT EXISTS retail_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        product_id INTEGER,
        product_title TEXT,
        username TEXT,
        note TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS customer_feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        product_title TEXT,
        username TEXT,
        rating TEXT,
        feedback TEXT,
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
.warn{background:#2b2110;border-color:#6b4b00}
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
<a href="/search">Search</a>
<a href="/creators">Creators</a>
<a href="/media">Media</a>
<a href="/retail">Retail</a>
<a href="/collections">Collections</a>
<a href="/promos">Promos</a>
<a href="/orders">Orders</a>
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

def product_card(p):
    html = f"""
    <div class='card'>
    <b>{p['title']}</b><br>
    <span class='gold'>{p['price']}</span><br>
    <span class='small'>{p['category']} • {p['collection']} • {p['supplier']}</span><br>
    <span class='badge'>{p['stock_status']}</span>
    """
    if p["image"]:
        html += f"<img src='/{p['image']}'>"
    html += f"<p>{p['description'] or ''}</p><a href='/product/{p['id']}'>Open Product</a></div>"
    return html

def promo_card(p):
    html = f"""
    <div class='card'>
    <b>{p['title']}</b><br>
    <span class='gold'>{p['category']}</span>
    """
    if p["image"]:
        html += f"<img src='/{p['image']}'>"
    html += f"<p>{p['description'] or ''}</p><a href='/promo/{p['id']}'>Open Promo</a></div>"
    return html

@app.route("/")
def home():
    conn = db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 8").fetchall()
    products = conn.execute("SELECT * FROM products WHERE status='approved' ORDER BY id DESC LIMIT 8").fetchall()
    promos = conn.execute("SELECT * FROM promo_slots WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    creators = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC LIMIT 6").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC LIMIT 6").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>✨👑Born Local🔥💨🚀✨Built Global💎💦</p>
    <p>Earth Is Our Turf</p>
    <p>OAP = Community + Media + Retail + HRM</p>
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

    content += "<div class='card'><h2>📢 Featured Promos</h2><div class='grid'>"
    for p in promos:
        content += promo_card(p)
    content += "</div></div>"

    content += "<div class='card'><h2>🛍️ Featured OAP Retail</h2><div class='grid'>"
    for p in products:
        content += product_card(p)
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
        (username,title,category,price,supplier,sku,description,image,product_link,status,stock_status,collection,views,clicks,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
            request.form["stock_status"],
            request.form["collection"],
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
    <p>OAP is the destination. POD suppliers are fulfilment routes.</p>
    <form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Product title' required>
    <input name='category' placeholder='T-shirt, hoodie, bandana, tracksuit, cap...' required>
    <input name='price' placeholder='Price e.g. £25'>
    <input name='supplier' placeholder='Printful, Printify, Tapstitch, Gelato, Local Printer...' required>
    <input name='sku' placeholder='SKU / supplier product ID'>
    <input name='collection' placeholder='Founder Collection, World Cup, Bandanas...' value='General'>
    <select name='stock_status'>
        <option>available</option>
        <option>limited</option>
        <option>preorder</option>
        <option>sold out</option>
    </select>
    <textarea name='description' placeholder='Product description'></textarea>
    <input name='product_link' placeholder='External fulfilment/payment link'>
    <input type='file' name='image'>
    <button>Submit Product For HRM Review</button>
    </form></div>
    <div class='grid'>
    """
    for p in rows:
        content += product_card(p)
    content += "</div>"
    return render(content)

@app.route("/collections")
def collections():
    conn = db()
    rows = conn.execute("SELECT collection, COUNT(*) count FROM products GROUP BY collection ORDER BY count DESC").fetchall()
    conn.close()

    content = "<div class='card'><h1>🧢 OAP Collections</h1></div><div class='grid'>"
    for r in rows:
        content += f"<div class='card'><h2>{r['collection']}</h2><p>{r['count']} products</p><a href='/collection/{r['collection']}'>Open Collection</a></div>"
    content += "</div>"
    return render(content)

@app.route("/collection/<name>")
def collection(name):
    conn = db()
    rows = conn.execute("SELECT * FROM products WHERE collection=? ORDER BY id DESC", (name,)).fetchall()
    conn.close()
    content = f"<div class='card'><h1>🧢 {name}</h1></div><div class='grid'>"
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

    conn.execute("UPDATE products SET views = views + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    retail_event("view", id, p["title"], session.get("user", "guest"), "Product page viewed")

    content = f"""
    <div class='card'>
    <h1>{p['title']}</h1>
    <p class='green'>{p['category']} • {p['collection']}</p>
    <p class='gold'>{p['price']}</p>
    <p>Supplier: {p['supplier']}</p>
    <p>SKU: {p['sku'] or 'N/A'}</p>
    <p>Status: {p['status']} • Stock: {p['stock_status']}</p>
    """
    if p["image"]:
        content += f"<img src='/{p['image']}'>"
    content += f"<p>{p['description'] or ''}</p>"

    if p["product_link"]:
        content += f"<a class='badge' href='/product/{id}/click'>Open Buy/Fulfilment Link</a>"

    content += """
    </div>
    <div class='card'>
    <h2>Checkout / Order Interest</h2>
    <form method='POST' action='/order_intent'>
    <input type='hidden' name='product_id' value='""" + str(p["id"]) + """'>
    <input type='hidden' name='product_title' value='""" + p["title"] + """'>
    <input type='hidden' name='supplier' value='""" + (p["supplier"] or "") + """'>
    <input type='hidden' name='fulfilment_link' value='""" + (p["product_link"] or "") + """'>
    <input name='customer_name' placeholder='Customer name'>
    <input name='customer_contact' placeholder='Email / phone / handle'>
    <input name='size' placeholder='Size e.g. M, L, XL'>
    <input name='colour' placeholder='Colour'>
    <input name='quantity' placeholder='Quantity' value='1'>
    <input name='amount' placeholder='Amount e.g. £25'>
    <textarea name='note' placeholder='Order note'></textarea>
    <button>Record Order Interest</button>
    </form>
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

    <div class='card'>
    <h2>Customer Feedback</h2>
    <form method='POST' action='/feedback'>
    <input type='hidden' name='product_id' value='""" + str(p["id"]) + """'>
    <input type='hidden' name='product_title' value='""" + p["title"] + """'>
    <select name='rating'>
        <option>5</option><option>4</option><option>3</option><option>2</option><option>1</option>
    </select>
    <textarea name='feedback' placeholder='Feedback'></textarea>
    <button>Submit Feedback</button>
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

@app.route("/order_intent", methods=["POST"])
def order_intent():
    username = session.get("user", "guest")
    conn = db()
    conn.execute("""INSERT INTO order_intents(product_id,product_title,username,customer_name,customer_contact,size,colour,quantity,amount,supplier,fulfilment_link,note,status,created_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (
        request.form["product_id"],
        request.form["product_title"],
        username,
        request.form["customer_name"],
        request.form["customer_contact"],
        request.form["size"],
        request.form["colour"],
        request.form["quantity"],
        request.form["amount"],
        request.form["supplier"],
        request.form["fulfilment_link"],
        request.form["note"],
        "new",
        now()
    ))
    conn.commit()
    conn.close()
    retail_event("order_intent", request.form["product_id"], request.form["product_title"], username, request.form["amount"])
    log("Order intent recorded", username)
    return redirect("/orders")

@app.route("/orders")
def orders():
    conn = db()
    rows = conn.execute("SELECT * FROM order_intents ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card'><h1>🧾 OAP Order Intents</h1><p>Manual checkout/order-interest records before full payment integration.</p></div>"
    for o in rows:
        content += f"""
        <div class='card'>
        <b>{o['product_title']}</b> — {o['status']}<br>
        Customer: {o['customer_name']} | {o['customer_contact']}<br>
        Size: {o['size']} | Colour: {o['colour']} | Qty: {o['quantity']}<br>
        Amount: {o['amount']} | Supplier: {o['supplier']}<br>
        <p>{o['note']}</p>
        <a href='/order/{o['id']}/contacted'>Mark Contacted</a>
        <a href='/order/{o['id']}/fulfilled'>Mark Fulfilled</a>
        <a href='/order/{o['id']}/cancelled'>Cancel</a>
        <span class='small'>{o['created_at']}</span>
        </div>
        """
    return render(content)

@app.route("/order/<int:id>/<status>")
def order_status(id, status):
    if status not in ["new", "contacted", "fulfilled", "cancelled"]:
        return redirect("/orders")
    conn = db()
    order = conn.execute("SELECT * FROM order_intents WHERE id=?", (id,)).fetchone()
    conn.execute("UPDATE order_intents SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    if order:
        retail_event(f"order_{status}", order["product_id"], order["product_title"], session.get("user", "admin"), "Order status updated")
    log(f"Order marked {status}", session.get("user", "admin"))
    return redirect("/orders")

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

@app.route("/feedback", methods=["POST"])
def feedback():
    username = session.get("user", "guest")
    conn = db()
    conn.execute("""INSERT INTO customer_feedback(product_id,product_title,username,rating,feedback,created_at)
    VALUES(?,?,?,?,?,?)""",
    (
        request.form["product_id"],
        request.form["product_title"],
        username,
        request.form["rating"],
        request.form["feedback"],
        now()
    ))
    conn.commit()
    conn.close()
    retail_event("feedback", request.form["product_id"], request.form["product_title"], username, request.form["rating"])
    log("Customer feedback recorded", username)
    return redirect(f"/product/{request.form['product_id']}")

@app.route("/promos", methods=["GET","POST"])
def promos():
    if request.method == "POST":
        if not session.get("user"):
            return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO promo_slots(username,title,category,description,link,image,status,views,clicks,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (
            session["user"],
            request.form["title"],
            request.form["category"],
            request.form["description"],
            request.form["link"],
            image,
            "pending",
            0,
            0,
            now()
        ))
        conn.commit()
        conn.close()
        log("Promo submitted", session["user"])
        return redirect("/promos")

    conn = db()
    rows = conn.execute("SELECT * FROM promo_slots ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    <div class='card'><h1>📢 OAP Promo Slots</h1>
    <form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Promo title' required>
    <input name='category' placeholder='Clothing, creator, event, music, business...' required>
    <textarea name='description' placeholder='Promo description'></textarea>
    <input name='link' placeholder='Promo link'>
    <input type='file' name='image'>
    <button>Submit Promo For Review</button>
    </form></div><div class='grid'>
    """
    for p in rows:
        content += promo_card(p)
    content += "</div>"
    return render(content)

@app.route("/promo/<int:id>")
def promo(id):
    conn = db()
    p = conn.execute("SELECT * FROM promo_slots WHERE id=?", (id,)).fetchone()
    if not p:
        conn.close()
        return "Promo not found"
    conn.execute("UPDATE promo_slots SET views = views + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    content = f"<div class='card'><h1>{p['title']}</h1><p class='gold'>{p['category']}</p><p>{p['description']}</p><p>Status: {p['status']}</p>"
    if p["image"]:
        content += f"<img src='/{p['image']}'>"
    if p["link"]:
        content += f"<a class='badge' href='/promo/{id}/click'>Open Promo Link</a>"
    content += "</div>"
    return render(content)

@app.route("/promo/<int:id>/click")
def promo_click(id):
    conn = db()
    p = conn.execute("SELECT * FROM promo_slots WHERE id=?", (id,)).fetchone()
    if not p:
        conn.close()
        return "Promo not found"
    conn.execute("UPDATE promo_slots SET clicks = clicks + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    log("Promo clicked", session.get("user", "guest"))
    if p["link"]:
        return redirect(p["link"])
    return redirect(f"/promo/{id}")

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    content = """
    <div class='card'><h1>🔎 OAP Search</h1>
    <form method='GET'>
    <input name='q' placeholder='Search products, creators, media, posts, promos...' value='""" + q + """'>
    <button>Search</button>
    </form></div>
    """
    if not q:
        return render(content)

    like = f"%{q}%"
    conn = db()
    products = conn.execute("""SELECT * FROM products WHERE title LIKE ? OR category LIKE ? OR supplier LIKE ? OR collection LIKE ? OR description LIKE ?""", (like, like, like, like, like)).fetchall()
    promos = conn.execute("""SELECT * FROM promo_slots WHERE title LIKE ? OR category LIKE ? OR description LIKE ?""", (like, like, like)).fetchall()
    creators = conn.execute("""SELECT * FROM creator_profiles WHERE display_name LIKE ? OR category LIKE ? OR bio LIKE ?""", (like, like, like)).fetchall()
    releases = conn.execute("""SELECT * FROM media_releases WHERE title LIKE ? OR category LIKE ? OR description LIKE ?""", (like, like, like)).fetchall()
    posts = conn.execute("""SELECT * FROM posts WHERE content LIKE ?""", (like,)).fetchall()
    conn.close()

    content += "<div class='card'><h2>🛍️ Products</h2>"
    for p in products:
        content += f"<p><a href='/product/{p['id']}'>{p['title']}</a> — {p['supplier']} — {p['price']}</p>"
    content += "</div><div class='card'><h2>📢 Promos</h2>"
    for p in promos:
        content += f"<p><a href='/promo/{p['id']}'>{p['title']}</a> — {p['category']}</p>"
    content += "</div><div class='card'><h2>🎤 Creators</h2>"
    for c in creators:
        content += f"<p>{c['display_name']} — {c['category']}</p>"
    content += "</div><div class='card'><h2>🎵 Media</h2>"
    for r in releases:
        content += f"<p><a href='/release/{r['id']}'>{r['title']}</a> — {r['category']}</p>"
    content += "</div><div class='card'><h2>📰 Posts</h2>"
    for p in posts:
        content += f"<p>@{p['username']}: {p['content']}</p>"
    content += "</div>"
    return render(content)

@app.route("/retail_hrm")
def retail_hrm():
    conn = db()
    total_products = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
    approved_products = conn.execute("SELECT COUNT(*) c FROM products WHERE status='approved'").fetchone()["c"]
    total_views = conn.execute("SELECT COALESCE(SUM(views),0) c FROM products").fetchone()["c"]
    total_clicks = conn.execute("SELECT COALESCE(SUM(clicks),0) c FROM products").fetchone()["c"]
    total_sales = conn.execute("SELECT COUNT(*) c FROM sales_records").fetchone()["c"]
    total_orders = conn.execute("SELECT COUNT(*) c FROM order_intents").fetchone()["c"]
    total_feedback = conn.execute("SELECT COUNT(*) c FROM customer_feedback").fetchone()["c"]
    total_promos = conn.execute("SELECT COUNT(*) c FROM promo_slots").fetchone()["c"]
    products = conn.execute("SELECT * FROM products ORDER BY views DESC, clicks DESC LIMIT 20").fetchall()
    sales = conn.execute("SELECT * FROM sales_records ORDER BY id DESC LIMIT 20").fetchall()
    orders = conn.execute("SELECT * FROM order_intents ORDER BY id DESC LIMIT 20").fetchall()
    events = conn.execute("SELECT * FROM retail_events ORDER BY id DESC LIMIT 30").fetchall()
    feedback_rows = conn.execute("SELECT * FROM customer_feedback ORDER BY id DESC LIMIT 20").fetchall()
    suppliers = conn.execute("SELECT supplier, COUNT(*) c, COALESCE(SUM(views),0) views, COALESCE(SUM(clicks),0) clicks FROM products GROUP BY supplier ORDER BY c DESC").fetchall()
    promos = conn.execute("SELECT * FROM promo_slots ORDER BY views DESC, clicks DESC LIMIT 20").fetchall()
    conn.close()

    content = f"""
    <div class='card'>
    <h1>🧠 OAP Retail HRM</h1>
    <p>Tracks products, suppliers, views, clicks, order intents, sales, promos, feedback and learning signals.</p>
    </div>

    <div class='grid'>
    <div class='card'><h2>{total_products}</h2><p>Total Products</p></div>
    <div class='card'><h2>{approved_products}</h2><p>Approved Products</p></div>
    <div class='card'><h2>{total_views}</h2><p>Product Views</p></div>
    <div class='card'><h2>{total_clicks}</h2><p>External Clicks</p></div>
    <div class='card'><h2>{total_orders}</h2><p>Order Intents</p></div>
    <div class='card'><h2>{total_sales}</h2><p>Recorded Sales</p></div>
    <div class='card'><h2>{total_feedback}</h2><p>Feedback Records</p></div>
    <div class='card'><h2>{total_promos}</h2><p>Promo Slots</p></div>
    </div>
    """

    content += "<div class='card'><h2>Supplier Performance</h2>"
    for s in suppliers:
        content += f"<div class='card'><b>{s['supplier']}</b><br>Products: {s['c']} | Views: {s['views']} | Clicks: {s['clicks']}</div>"
    content += "</div>"

    content += "<div class='card'><h2>Promo Performance</h2>"
    for p in promos:
        content += f"<div class='card'><b>{p['title']}</b> — {p['status']}<br>Views: {p['views']} | Clicks: {p['clicks']}</div>"
    content += "</div>"

    content += "<div class='card'><h2>Top Retail Products</h2>"
    for p in products:
        content += f"<div class='card'><b>{p['title']}</b><br>{p['supplier']} • {p['price']}<br>Views: {p['views']} | Clicks: {p['clicks']} | Stock: {p['stock_status']} | Status: {p['status']}</div>"
    content += "</div>"

    content += "<div class='card'><h2>Order Intents</h2>"
    for o in orders:
        content += f"<div class='card'><b>{o['product_title']}</b> — {o['status']}<br>{o['customer_name']} | {o['customer_contact']}<br>{o['amount']} • {o['supplier']}<br><span class='small'>{o['created_at']}</span></div>"
    content += "</div>"

    content += "<div class='card'><h2>Sales Records</h2>"
    for s in sales:
        content += f"<div class='card'><b>{s['product_title']}</b><br>{s['amount']} • {s['supplier']}<br>{s['buyer_note']}<br><span class='small'>{s['created_at']}</span></div>"
    content += "</div>"

    content += "<div class='card'><h2>Customer Feedback</h2>"
    for f in feedback_rows:
        content += f"<div class='card'><b>{f['product_title']}</b> — Rating {f['rating']}<p>{f['feedback']}</p><span class='small'>{f['username']} — {f['created_at']}</span></div>"
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
    promos = conn.execute("SELECT * FROM promo_slots ORDER BY id DESC").fetchall()
    orders = conn.execute("SELECT * FROM order_intents ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()

    content = "<div class='card'><h2>🧠 HRM Admin</h2><p>Guardian • Chancellor • Sentinel</p></div>"

    content += "<div class='card'><h2>Order Intents</h2>"
    for o in orders:
        content += f"<div class='card'>{o['product_title']} — {o['status']} — {o['amount']}<br>{o['customer_contact']}</div>"
    content += "</div>"

    content += "<div class='card'><h2>Retail Products Review</h2>"
    for p in products:
        content += f"<div class='card'>{p['title']} — {p['status']} • {p['stock_status']} <a href='/admin/product/{p['id']}/approved'>Approve</a> <a href='/admin/product/{p['id']}/rejected'>Reject</a></div>"
    content += "</div>"

    content += "<div class='card'><h2>Promo Review</h2>"
    for p in promos:
        content += f"<div class='card'>{p['title']} — {p['status']} <a href='/admin/promo/{p['id']}/approved'>Approve</a> <a href='/admin/promo/{p['id']}/rejected'>Reject</a></div>"
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

@app.route("/admin/promo/<int:id>/<status>")
def admin_promo(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")
    conn = db()
    promo = conn.execute("SELECT * FROM promo_slots WHERE id=?", (id,)).fetchone()
    conn.execute("UPDATE promo_slots SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    if promo:
        log(f"Promo {status}: {promo['title']}", session.get("user", "admin"))
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
