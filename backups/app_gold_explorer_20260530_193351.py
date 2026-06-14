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
        country TEXT DEFAULT 'UK',
        city TEXT DEFAULT '',
        postcode TEXT DEFAULT '',
        status TEXT DEFAULT 'approved',
        views INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    add_col(cur, "creator_profiles", "country", "TEXT DEFAULT 'UK'")
    add_col(cur, "creator_profiles", "city", "TEXT DEFAULT ''")
    add_col(cur, "creator_profiles", "postcode", "TEXT DEFAULT ''")
    add_col(cur, "creator_profiles", "status", "TEXT DEFAULT 'approved'")
    add_col(cur, "creator_profiles", "views", "INTEGER DEFAULT 0")

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
        country TEXT DEFAULT 'UK',
        city TEXT DEFAULT '',
        postcode TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    add_col(cur, "products", "printful_id", "TEXT")
    add_col(cur, "products", "printful_variant_id", "TEXT")
    add_col(cur, "products", "stock_status", "TEXT DEFAULT 'available'")
    add_col(cur, "products", "collection", "TEXT DEFAULT 'General'")
    add_col(cur, "products", "country", "TEXT DEFAULT 'UK'")
    add_col(cur, "products", "city", "TEXT DEFAULT ''")
    add_col(cur, "products", "postcode", "TEXT DEFAULT ''")

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

    cur.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        event_type TEXT,
        category TEXT,
        country_focus TEXT,
        postcode TEXT,
        city TEXT,
        country TEXT,
        venue TEXT,
        event_date TEXT,
        event_time TEXT,
        description TEXT,
        ticket_price TEXT,
        capacity TEXT,
        contact TEXT,
        related_product_id INTEGER,
        related_business_id INTEGER,
        image TEXT,
        status TEXT DEFAULT 'pending',
        views INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS event_rsvps(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        event_title TEXT,
        username TEXT,
        attendee_name TEXT,
        attendee_contact TEXT,
        quantity TEXT,
        note TEXT,
        status TEXT DEFAULT 'new',
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
        country TEXT DEFAULT 'UK',
        city TEXT DEFAULT '',
        postcode TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")
    add_col(cur, "news_posts", "country", "TEXT DEFAULT 'UK'")
    add_col(cur, "news_posts", "city", "TEXT DEFAULT ''")
    add_col(cur, "news_posts", "postcode", "TEXT DEFAULT ''")

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

    cur.execute("""CREATE TABLE IF NOT EXISTS explorer_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_type TEXT,
        area_value TEXT,
        username TEXT,
        action TEXT,
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

def explorer_log(area_type, area_value, action, note=""):
    conn = db()
    conn.execute("""INSERT INTO explorer_logs(area_type,area_value,username,action,note,created_at)
                   VALUES(?,?,?,?,?,?)""", (area_type, area_value, session.get("user","guest"), action, note, now()))
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
<a href="/explorer">Explorer</a>
<a href="/globe_hrm">Globe HRM</a>
<a href="/events">Events</a>
<a href="/worldcup">World Cup</a>
<a href="/news">News</a>
<a href="/business">Business</a>
<a href="/creators">Creators</a>
<a href="/media">Media</a>
<a href="/retail">Retail</a>
<a href="/search">Search</a>
<a href="/admin">HRM</a>
</div>
{{content|safe}}
</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def news_card(n):
    html = f"<div class='card'><b>{n['title']}</b><br><span class='gold'>{n['category']}</span><br><span class='small'>{n['city']} • {n['country']} • {n['postcode']}</span><p>{n['summary'] or ''}</p>"
    if n["image"]:
        html += f"<img src='/{n['image']}'>"
    html += f"<a href='/news/{n['id']}'>Read</a></div>"
    return html

def business_card(b):
    html = f"<div class='card'><b>{b['business_name']}</b><br><span class='gold'>{b['category']}</span><br><span class='small'>{b['postcode']} • {b['city']} • {b['country']}</span>"
    if b["image"]:
        html += f"<img src='/{b['image']}'>"
    html += f"<p>{b['description'] or ''}</p><p class='green'>{b['offer'] or ''}</p><a href='/business/{b['id']}'>Open</a></div>"
    return html

def event_card(e):
    html = f"<div class='card'><b>{e['title']}</b><br><span class='gold'>{e['event_type']} • {e['category']}</span><br><span class='small'>{e['event_date']} • {e['city']} • {e['postcode']}</span>"
    if e["image"]:
        html += f"<img src='/{e['image']}'>"
    html += f"<p>{e['description'] or ''}</p><a href='/event/{e['id']}'>Open</a></div>"
    return html

def product_card(p):
    html = f"<div class='card'><b>{p['title']}</b><br><span class='gold'>{p['price']}</span><br><span class='small'>{p['category']} • {p['supplier']} • {p['city']} • {p['country']}</span>"
    if p["image"]:
        html += f"<img src='/{p['image']}'>"
    html += f"<p>{p['description'] or ''}</p><a href='/product/{p['id']}'>Open</a></div>"
    return html

def creator_card(c):
    html = f"<div class='card'><b>{c['display_name']}</b><br><span class='gold'>{c['category']}</span><br><span class='small'>{c['city']} • {c['country']} • {c['postcode']}</span>"
    if c["image"]:
        html += f"<img src='/{c['image']}'>"
    html += f"<p>{c['bio'] or ''}</p></div>"
    return html

@app.route("/")
def home():
    conn = db()
    news = conn.execute("SELECT * FROM news_posts WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    events = conn.execute("SELECT * FROM events WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    businesses = conn.execute("SELECT * FROM business_profiles WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    products = conn.execute("SELECT * FROM products WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>✨👑Born Local🔥💨🚀✨Built Global💎💦</p>
    <p>Explorer + News + Business + Events + Retail + HRM</p>
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
    content += "<div class='card'><h2>🌍 Explorer Quick Links</h2><p><a href='/country/UK'>UK</a><a href='/country/Ghana'>Ghana</a><a href='/city/London'>London</a><a href='/postcode/CR4'>CR4</a><a href='/city/Begoro'>Begoro</a><a href='/city/KORADASO'>KORADASO</a></p></div>"

    content += "<div class='card'><h2>Events</h2><div class='grid'>"
    for e in events: content += event_card(e)
    content += "</div></div><div class='card'><h2>News</h2><div class='grid'>"
    for n in news: content += news_card(n)
    content += "</div></div><div class='card'><h2>Businesses</h2><div class='grid'>"
    for b in businesses: content += business_card(b)
    content += "</div></div><div class='card'><h2>Retail</h2><div class='grid'>"
    for p in products: content += product_card(p)
    content += "</div></div><div class='card'><h2>Feed</h2>"
    for p in posts:
        content += f"<div class='card'><b>@{p['username']}</b><p>{p['content']}</p>"
        if p["image"]: content += f"<img src='/{p['image']}'>"
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
    return render("<div class='card'><h2>Register</h2><form method='POST'><input name='username' required><input name='email' required><input name='password' type='password' required><button>Register</button></form></div>")

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
    return render("<div class='card'><h2>Login</h2><form method='POST'><input name='username' required><input name='password' type='password' required><button>Login</button></form></div>")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/post", methods=["POST"])
def post():
    if not session.get("user"): return redirect("/login")
    image = save_file(request.files.get("image"))
    conn = db()
    conn.execute("INSERT INTO posts(username,content,image,created_at) VALUES(?,?,?,?)", (session["user"], request.form["content"][:1000], image, now()))
    conn.commit()
    conn.close()
    log("Post created", session["user"])
    return redirect("/")

@app.route("/explorer")
def explorer():
    conn = db()
    countries = set()
    cities = set()
    postcodes = set()

    for table in ["business_profiles","events","products","news_posts","creator_profiles"]:
        try:
            for r in conn.execute(f"SELECT country, city, postcode FROM {table}").fetchall():
                if r["country"]: countries.add(r["country"])
                if r["city"]: cities.add(r["city"])
                if r["postcode"]: postcodes.add(r["postcode"])
        except Exception:
            pass

    conn.close()
    explorer_log("explorer", "home", "view", "Explorer opened")

    content = """
    <div class='card hero'>
    <h1>🌍 OAP Explorer / Globe</h1>
    <p class='green'>Countries → Cities → Postcodes → Community → Business → Events → Retail</p>
    </div>
    <div class='card'><h2>Search Areas</h2>
    <form method='GET' action='/search'>
    <input name='q' placeholder='Search country, city, postcode, business, event...'>
    <button>Search</button>
    </form></div>
    """

    content += "<div class='card'><h2>Countries</h2>"
    for c in sorted(countries):
        content += f"<a class='badge' href='/country/{c}'>{c}</a> "
    content += "</div><div class='card'><h2>Cities / Places</h2>"
    for c in sorted(cities):
        content += f"<a class='badge' href='/city/{c}'>{c}</a> "
    content += "</div><div class='card'><h2>Postcodes</h2>"
    for p in sorted(postcodes):
        content += f"<a class='badge' href='/postcode/{p}'>{p}</a> "
    content += "</div>"

    content += """
    <div class='card'>
    <h2>OAP Roots</h2>
    <p><a href='/city/Mitcham'>Mitcham</a> <a href='/city/Begoro'>Begoro</a> <a href='/city/KORADASO'>KORADASO</a> <a href='/city/Akyem'>Akyem</a> <a href='/country/Ghana'>Ghana</a></p>
    </div>
    """
    return render(content)

def area_page(area_type, area_value):
    like = f"%{area_value}%"
    conn = db()

    if area_type == "country":
        businesses = conn.execute("SELECT * FROM business_profiles WHERE country LIKE ? ORDER BY id DESC", (like,)).fetchall()
        events = conn.execute("SELECT * FROM events WHERE country LIKE ? OR country_focus LIKE ? ORDER BY id DESC", (like,like)).fetchall()
        products = conn.execute("SELECT * FROM products WHERE country LIKE ? ORDER BY id DESC", (like,)).fetchall()
        news = conn.execute("SELECT * FROM news_posts WHERE country LIKE ? ORDER BY id DESC", (like,)).fetchall()
        creators = conn.execute("SELECT * FROM creator_profiles WHERE country LIKE ? ORDER BY id DESC", (like,)).fetchall()
    elif area_type == "city":
        businesses = conn.execute("SELECT * FROM business_profiles WHERE city LIKE ? ORDER BY id DESC", (like,)).fetchall()
        events = conn.execute("SELECT * FROM events WHERE city LIKE ? ORDER BY id DESC", (like,)).fetchall()
        products = conn.execute("SELECT * FROM products WHERE city LIKE ? ORDER BY id DESC", (like,)).fetchall()
        news = conn.execute("SELECT * FROM news_posts WHERE city LIKE ? ORDER BY id DESC", (like,)).fetchall()
        creators = conn.execute("SELECT * FROM creator_profiles WHERE city LIKE ? ORDER BY id DESC", (like,)).fetchall()
    else:
        businesses = conn.execute("SELECT * FROM business_profiles WHERE postcode LIKE ? ORDER BY id DESC", (like,)).fetchall()
        events = conn.execute("SELECT * FROM events WHERE postcode LIKE ? ORDER BY id DESC", (like,)).fetchall()
        products = conn.execute("SELECT * FROM products WHERE postcode LIKE ? ORDER BY id DESC", (like,)).fetchall()
        news = conn.execute("SELECT * FROM news_posts WHERE postcode LIKE ? ORDER BY id DESC", (like,)).fetchall()
        creators = conn.execute("SELECT * FROM creator_profiles WHERE postcode LIKE ? ORDER BY id DESC", (like,)).fetchall()

    conn.close()
    explorer_log(area_type, area_value, "view", "Area page viewed")

    content = f"""
    <div class='card hero'>
    <h1>🌍 {area_value}</h1>
    <p class='green'>Area Type: {area_type}</p>
    </div>
    <div class='grid'>
    <div class='card'><h2>{len(businesses)}</h2><p>Businesses</p></div>
    <div class='card'><h2>{len(events)}</h2><p>Events</p></div>
    <div class='card'><h2>{len(products)}</h2><p>Products</p></div>
    <div class='card'><h2>{len(news)}</h2><p>News</p></div>
    <div class='card'><h2>{len(creators)}</h2><p>Creators</p></div>
    </div>
    """
    content += "<div class='card'><h2>Events</h2><div class='grid'>"
    for e in events: content += event_card(e)
    content += "</div></div><div class='card'><h2>Businesses</h2><div class='grid'>"
    for b in businesses: content += business_card(b)
    content += "</div></div><div class='card'><h2>Products</h2><div class='grid'>"
    for p in products: content += product_card(p)
    content += "</div></div><div class='card'><h2>News</h2><div class='grid'>"
    for n in news: content += news_card(n)
    content += "</div></div><div class='card'><h2>Creators</h2><div class='grid'>"
    for c in creators: content += creator_card(c)
    content += "</div></div>"
    return render(content)

@app.route("/country/<name>")
def country(name):
    return area_page("country", name)

@app.route("/city/<name>")
def city(name):
    return area_page("city", name)

@app.route("/postcode/<name>")
def postcode(name):
    return area_page("postcode", name)

@app.route("/globe_hrm")
def globe_hrm():
    conn = db()
    total_logs = conn.execute("SELECT COUNT(*) c FROM explorer_logs").fetchone()["c"]
    countries = conn.execute("SELECT country, COUNT(*) c FROM business_profiles GROUP BY country UNION ALL SELECT country, COUNT(*) FROM events GROUP BY country").fetchall()
    logs = conn.execute("SELECT * FROM explorer_logs ORDER BY id DESC LIMIT 50").fetchall()
    top_cities = []
    for table in ["business_profiles","events","products","news_posts","creator_profiles"]:
        try:
            for r in conn.execute(f"SELECT city, COUNT(*) c FROM {table} WHERE city != '' GROUP BY city").fetchall():
                top_cities.append((r["city"], r["c"], table))
        except Exception:
            pass
    conn.close()

    content = f"""
    <div class='card hero'><h1>🧠 Globe HRM</h1><p class='green'>Explorer activity, area intelligence, local-to-global records.</p></div>
    <div class='grid'>
    <div class='card'><h2>{total_logs}</h2><p>Explorer Logs</p></div>
    <div class='card'><h2>{len(top_cities)}</h2><p>City Signals</p></div>
    </div>
    <div class='card'><h2>City Signals</h2>
    """
    for city_name, count, table in top_cities[:50]:
        content += f"<div class='card'><b>{city_name}</b><br>{count} records in {table}</div>"
    content += "</div><div class='card'><h2>Explorer Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{l['area_type']}:</b> {l['area_value']}<br>{l['action']} • {l['username']}<br><span class='small'>{l['created_at']}</span></div>"
    content += "</div>"
    return render(content)

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method == "POST":
        if not session.get("user"): return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO events(username,title,event_type,category,country_focus,postcode,city,country,venue,event_date,event_time,description,ticket_price,capacity,contact,related_product_id,related_business_id,image,status,views,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (session["user"], request.form["title"], request.form["event_type"], request.form["category"], request.form["country_focus"], request.form["postcode"], request.form["city"], request.form["country"], request.form["venue"], request.form["event_date"], request.form["event_time"], request.form["description"], request.form["ticket_price"], request.form["capacity"], request.form["contact"], request.form.get("related_product_id") or 0, request.form.get("related_business_id") or 0, image, "pending", 0, now()))
        conn.commit(); conn.close(); log("Event submitted", session["user"]); return redirect("/events")
    conn = db(); rows = conn.execute("SELECT * FROM events ORDER BY id DESC").fetchall(); conn.close()
    content = """<div class='card'><h1>Events / Watch Parties</h1><form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'><option>Watch Party</option><option>Creator Meetup</option><option>Business Popup</option><option>Community Event</option><option>Sports Event</option><option>Music Event</option></select>
    <input name='category' placeholder='World Cup, Music, Business...' required>
    <input name='country_focus' placeholder='Ghana, England, Brazil...'>
    <input name='postcode' placeholder='Postcode'><input name='city' placeholder='City'><input name='country' placeholder='Country' value='UK'>
    <input name='venue' placeholder='Venue'><input name='event_date' placeholder='Date'><input name='event_time' placeholder='Time'>
    <textarea name='description' placeholder='Description'></textarea><input name='ticket_price' placeholder='Ticket price'><input name='capacity' placeholder='Capacity'><input name='contact' placeholder='Contact'>
    <input name='related_product_id' placeholder='Related product ID'><input name='related_business_id' placeholder='Related business ID'><input type='file' name='image'><button>Submit Event</button></form></div><div class='grid'>"""
    for e in rows: content += event_card(e)
    content += "</div>"
    return render(content)

@app.route("/event/<int:id>")
def event_detail(id):
    conn = db()
    e = conn.execute("SELECT * FROM events WHERE id=?", (id,)).fetchone()
    if not e: conn.close(); return "Event not found"
    conn.execute("UPDATE events SET views=views+1 WHERE id=?", (id,))
    conn.commit(); conn.close()
    content = f"<div class='card'><h1>{e['title']}</h1><p class='gold'>{e['event_type']} • {e['category']} • {e['country_focus']}</p><p>{e['event_date']} {e['event_time']} • {e['venue']} • {e['city']} • {e['postcode']}</p>"
    if e["image"]: content += f"<img src='/{e['image']}'>"
    content += f"<p>{e['description']}</p><p>Ticket: {e['ticket_price']} | Capacity: {e['capacity']}</p></div>"
    return render(content)

@app.route("/worldcup")
def worldcup():
    conn = db()
    events = conn.execute("SELECT * FROM events WHERE category LIKE '%World Cup%' OR country_focus != '' ORDER BY id DESC LIMIT 20").fetchall()
    products = conn.execute("SELECT * FROM products WHERE collection LIKE '%World Cup%' OR category LIKE '%World Cup%' ORDER BY id DESC LIMIT 12").fetchall()
    news = conn.execute("SELECT * FROM news_posts WHERE category LIKE '%World Cup%' OR title LIKE '%World Cup%' ORDER BY id DESC LIMIT 12").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>⚽ OAP World Cup Hub</h1><p class='green'>Country spaces, events, retail, news, community.</p></div><div class='card'><h2>Country Spaces</h2><p><a href='/country/Ghana'>Ghana</a><a href='/country/England'>England</a><a href='/country/Brazil'>Brazil</a><a href='/country/Nigeria'>Nigeria</a><a href='/country/France'>France</a></p></div><div class='card'><h2>Events</h2><div class='grid'>"
    for e in events: content += event_card(e)
    content += "</div></div><div class='card'><h2>Retail</h2><div class='grid'>"
    for p in products: content += product_card(p)
    content += "</div></div><div class='card'><h2>News</h2><div class='grid'>"
    for n in news: content += news_card(n)
    content += "</div></div>"
    return render(content)

@app.route("/business", methods=["GET","POST"])
def business():
    if request.method == "POST":
        if not session.get("user"): return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO business_profiles(username,business_name,category,postcode,city,country,description,offer,contact,website,image,status,views,clicks,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (session["user"], request.form["business_name"], request.form["category"], request.form["postcode"], request.form["city"], request.form["country"], request.form["description"], request.form["offer"], request.form["contact"], request.form["website"], image, "pending", 0, 0, now()))
        conn.commit(); conn.close(); log("Business submitted", session["user"]); return redirect("/business")
    conn = db(); rows = conn.execute("SELECT * FROM business_profiles ORDER BY id DESC").fetchall(); conn.close()
    content = """<div class='card'><h1>Business Board</h1><form method='POST' enctype='multipart/form-data'>
    <input name='business_name' placeholder='Business name' required><input name='category' placeholder='Category' required><input name='postcode' placeholder='Postcode'><input name='city' placeholder='City'><input name='country' placeholder='Country' value='UK'><textarea name='description' placeholder='Description'></textarea><textarea name='offer' placeholder='Offer'></textarea><input name='contact' placeholder='Contact'><input name='website' placeholder='Website'><input type='file' name='image'><button>Submit Business</button></form></div><div class='grid'>"""
    for b in rows: content += business_card(b)
    content += "</div>"
    return render(content)

@app.route("/business/<int:id>")
def business_detail(id):
    conn = db(); b = conn.execute("SELECT * FROM business_profiles WHERE id=?", (id,)).fetchone()
    if not b: conn.close(); return "Business not found"
    conn.execute("UPDATE business_profiles SET views=views+1 WHERE id=?", (id,)); conn.commit(); conn.close()
    content = f"<div class='card'><h1>{b['business_name']}</h1><p class='gold'>{b['category']}</p><p>{b['postcode']} • {b['city']} • {b['country']}</p>"
    if b["image"]: content += f"<img src='/{b['image']}'>"
    content += f"<p>{b['description']}</p><p class='green'>{b['offer']}</p><p>{b['contact']}</p></div>"
    return render(content)

@app.route("/creators", methods=["GET","POST"])
def creators():
    if request.method == "POST":
        if not session.get("user"): return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT OR REPLACE INTO creator_profiles(username,display_name,category,bio,image,link,country,city,postcode,status,views,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (session["user"], request.form["display_name"], request.form["category"], request.form["bio"], image, request.form["link"], request.form["country"], request.form["city"], request.form["postcode"], "approved", 0, now()))
        conn.commit(); conn.close(); log("Creator saved", session["user"]); return redirect("/creators")
    conn = db(); rows = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC").fetchall(); conn.close()
    content = """<div class='card'><h2>Creators</h2><form method='POST' enctype='multipart/form-data'>
    <input name='display_name' placeholder='Display name' required><input name='category' placeholder='Category' required><input name='country' placeholder='Country' value='UK'><input name='city' placeholder='City'><input name='postcode' placeholder='Postcode'><textarea name='bio' placeholder='Bio'></textarea><input name='link' placeholder='Link'><input type='file' name='image'><button>Save Creator</button></form></div><div class='grid'>"""
    for c in rows: content += creator_card(c)
    content += "</div>"
    return render(content)

@app.route("/media", methods=["GET","POST"])
def media():
    if request.method == "POST":
        if not session.get("user"): return redirect("/login")
        media_file = save_file(request.files.get("media_file")); cover_art = save_file(request.files.get("cover_art"))
        if not media_file: return "Blocked or invalid media file."
        conn = db()
        conn.execute("""INSERT INTO media_releases(username,title,category,description,media_file,cover_art,rights_note,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (session["user"], request.form["title"], request.form["category"], request.form["description"], media_file, cover_art, request.form["rights_note"], "pending", now()))
        conn.commit(); conn.close(); log("Media submitted", session["user"]); return redirect("/media")
    conn = db(); rows = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall(); conn.close()
    content = """<div class='card'><h2>Media</h2><form method='POST' enctype='multipart/form-data'><input name='title' placeholder='Title' required><input name='category' placeholder='Category' required><textarea name='description' placeholder='Description'></textarea><textarea name='rights_note' placeholder='Rights proof' required></textarea><input type='file' name='media_file' required><input type='file' name='cover_art'><button>Submit</button></form></div>"""
    for r in rows: content += f"<div class='card'><b>{r['title']}</b> — {r['status']}<br><a href='/release/{r['id']}'>Open</a></div>"
    return render(content)

@app.route("/release/<int:id>")
def release(id):
    conn = db(); r = conn.execute("SELECT * FROM media_releases WHERE id=?", (id,)).fetchone(); conn.close()
    if not r: return "Release not found"
    content = f"<div class='card'><h1>{r['title']}</h1><p>{r['description']}</p>"
    if r["cover_art"]: content += f"<img src='/{r['cover_art']}'>"
    if r["media_file"]:
        f = r["media_file"].lower()
        if f.endswith((".mp3",".wav",".ogg",".m4a")): content += f"<audio controls src='/{r['media_file']}'></audio>"
        elif f.endswith((".mp4",".webm",".mov")): content += f"<video controls src='/{r['media_file']}'></video>"
        else: content += f"<a href='/{r['media_file']}'>Open file</a>"
    content += f"<div class='card'><h2>Rights</h2><p>{r['rights_note']}</p></div></div>"
    return render(content)

@app.route("/retail", methods=["GET","POST"])
def retail():
    if request.method == "POST":
        if not session.get("user"): return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO products(username,title,category,price,supplier,sku,printful_id,printful_variant_id,description,image,product_link,status,stock_status,collection,country,city,postcode,views,clicks,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (session["user"], request.form["title"], request.form["category"], request.form["price"], request.form["supplier"], request.form["sku"], request.form["printful_id"], request.form["printful_variant_id"], request.form["description"], image, request.form["product_link"], "pending", request.form["stock_status"], request.form["collection"], request.form["country"], request.form["city"], request.form["postcode"], 0, 0, now()))
        conn.commit(); conn.close(); log("Product submitted", session["user"]); return redirect("/retail")
    conn = db(); rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall(); conn.close()
    content = """<div class='card'><h2>Retail</h2><form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Product title' required><input name='category' placeholder='Category' required><input name='price' placeholder='Price'><input name='supplier' placeholder='Supplier' required><input name='sku' placeholder='SKU'><input name='printful_id' placeholder='Printful ID'><input name='printful_variant_id' placeholder='Variant ID'><input name='collection' placeholder='Collection' value='General'><input name='country' placeholder='Country' value='UK'><input name='city' placeholder='City'><input name='postcode' placeholder='Postcode'><select name='stock_status'><option>available</option><option>limited</option><option>preorder</option><option>sold out</option></select><textarea name='description' placeholder='Description'></textarea><input name='product_link' placeholder='Product link'><input type='file' name='image'><button>Submit Product</button></form></div><div class='grid'>"""
    for p in rows: content += product_card(p)
    content += "</div>"
    return render(content)

@app.route("/product/<int:id>")
def product(id):
    conn = db(); p = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    if not p: conn.close(); return "Product not found"
    conn.execute("UPDATE products SET views=views+1 WHERE id=?", (id,)); conn.commit(); conn.close()
    content = f"<div class='card'><h1>{p['title']}</h1><p class='gold'>{p['price']}</p><p>{p['city']} • {p['country']} • {p['postcode']}</p>"
    if p["image"]: content += f"<img src='/{p['image']}'>"
    content += f"<p>{p['description']}</p>"
    if p["product_link"]: content += f"<a class='badge' href='{p['product_link']}'>Buy / Fulfilment Link</a>"
    content += "</div>"
    return render(content)

@app.route("/news", methods=["GET","POST"])
def news():
    if request.method == "POST":
        if not session.get("user"): return redirect("/login")
        image = save_file(request.files.get("image"))
        conn = db()
        conn.execute("""INSERT INTO news_posts(username,title,category,summary,body,source_note,verification_status,image,related_product_id,related_link,country,city,postcode,views,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (session["user"], request.form["title"], request.form["category"], request.form["summary"], request.form["body"], request.form["source_note"], request.form["verification_status"], image, request.form.get("related_product_id") or 0, request.form["related_link"], request.form["country"], request.form["city"], request.form["postcode"], 0, "pending", now()))
        conn.commit(); conn.close(); log("News submitted", session["user"]); return redirect("/news")
    conn = db(); rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC").fetchall(); conn.close()
    content = """<div class='card'><h1>News</h1><form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Title' required><input name='category' placeholder='Category' required><input name='country' placeholder='Country' value='UK'><input name='city' placeholder='City'><input name='postcode' placeholder='Postcode'><textarea name='summary' placeholder='Summary'></textarea><textarea name='body' placeholder='Story'></textarea><textarea name='source_note' placeholder='Source/proof'></textarea><select name='verification_status'><option>draft</option><option>verified</option><option>needs review</option></select><input name='related_product_id' placeholder='Related product ID'><input name='related_link' placeholder='Related link'><input type='file' name='image'><button>Submit News</button></form></div><div class='grid'>"""
    for n in rows: content += news_card(n)
    content += "</div>"
    return render(content)

@app.route("/news/<int:id>")
def news_detail(id):
    conn = db(); n = conn.execute("SELECT * FROM news_posts WHERE id=?", (id,)).fetchone()
    if not n: conn.close(); return "News not found"
    conn.execute("UPDATE news_posts SET views=views+1 WHERE id=?", (id,)); conn.commit(); conn.close()
    content = f"<div class='card'><h1>{n['title']}</h1><p class='gold'>{n['category']}</p><p>{n['city']} • {n['country']} • {n['postcode']}</p>"
    if n["image"]: content += f"<img src='/{n['image']}'>"
    content += f"<h3>{n['summary']}</h3><p>{n['body']}</p><div class='card'><h2>Verification</h2><p>{n['source_note']}</p></div></div>"
    return render(content)

@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    content = f"<div class='card'><h1>Search</h1><form method='GET'><input name='q' value='{q}' placeholder='Search OAP...'><button>Search</button></form></div>"
    if not q: return render(content)
    like = f"%{q}%"
    conn = db()
    events = conn.execute("SELECT * FROM events WHERE title LIKE ? OR category LIKE ? OR country_focus LIKE ? OR postcode LIKE ? OR city LIKE ? OR country LIKE ?", (like,like,like,like,like,like)).fetchall()
    businesses = conn.execute("SELECT * FROM business_profiles WHERE business_name LIKE ? OR category LIKE ? OR postcode LIKE ? OR city LIKE ? OR country LIKE ?", (like,like,like,like,like)).fetchall()
    products = conn.execute("SELECT * FROM products WHERE title LIKE ? OR category LIKE ? OR supplier LIKE ? OR postcode LIKE ? OR city LIKE ? OR country LIKE ?", (like,like,like,like,like,like)).fetchall()
    news_rows = conn.execute("SELECT * FROM news_posts WHERE title LIKE ? OR category LIKE ? OR summary LIKE ? OR postcode LIKE ? OR city LIKE ? OR country LIKE ?", (like,like,like,like,like,like)).fetchall()
    creators = conn.execute("SELECT * FROM creator_profiles WHERE display_name LIKE ? OR category LIKE ? OR city LIKE ? OR country LIKE ? OR postcode LIKE ?", (like,like,like,like,like)).fetchall()
    conn.close()
    content += "<div class='card'><h2>Events</h2>"
    for e in events: content += f"<p><a href='/event/{e['id']}'>{e['title']}</a> — {e['city']}</p>"
    content += "</div><div class='card'><h2>Businesses</h2>"
    for b in businesses: content += f"<p><a href='/business/{b['id']}'>{b['business_name']}</a> — {b['postcode']}</p>"
    content += "</div><div class='card'><h2>Products</h2>"
    for p in products: content += f"<p><a href='/product/{p['id']}'>{p['title']}</a> — {p['price']}</p>"
    content += "</div><div class='card'><h2>News</h2>"
    for n in news_rows: content += f"<p><a href='/news/{n['id']}'>{n['title']}</a> — {n['category']}</p>"
    content += "</div><div class='card'><h2>Creators</h2>"
    for c in creators: content += f"<p>{c['display_name']} — {c['category']}</p>"
    content += "</div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    events = conn.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
    businesses = conn.execute("SELECT * FROM business_profiles ORDER BY id DESC").fetchall()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    news_rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC").fetchall()
    releases = conn.execute("SELECT * FROM media_releases ORDER BY id DESC").fetchall()
    conn.close()
    content = "<div class='card'><h1>HRM Admin</h1></div><div class='card'><h2>Events</h2>"
    for e in events: content += f"<div class='card'>{e['title']} — {e['status']} <a href='/admin/event/{e['id']}/approved'>Approve</a> <a href='/admin/event/{e['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Businesses</h2>"
    for b in businesses: content += f"<div class='card'>{b['business_name']} — {b['status']} <a href='/admin/business/{b['id']}/approved'>Approve</a> <a href='/admin/business/{b['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Products</h2>"
    for p in products: content += f"<div class='card'>{p['title']} — {p['status']} <a href='/admin/product/{p['id']}/approved'>Approve</a> <a href='/admin/product/{p['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>News</h2>"
    for n in news_rows: content += f"<div class='card'>{n['title']} — {n['status']} <a href='/admin/news/{n['id']}/approved'>Approve</a> <a href='/admin/news/{n['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Media</h2>"
    for r in releases: content += f"<div class='card'>{r['title']} — {r['status']} <a href='/admin/release/{r['id']}/approved'>Approve</a> <a href='/admin/release/{r['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs: content += f"<div class='card'><b>{l['action']}</b><br>{l['username']}<br>{l['created_at']}</div>"
    content += "</div>"
    return render(content)

@app.route("/admin/event/<int:id>/<status>")
def admin_event(id, status):
    if status not in ["approved","rejected"]: return redirect("/admin")
    conn = db(); conn.execute("UPDATE events SET status=? WHERE id=?", (status,id)); conn.commit(); conn.close()
    log(f"Event {status}", session.get("user","admin")); return redirect("/admin")

@app.route("/admin/business/<int:id>/<status>")
def admin_business(id, status):
    if status not in ["approved","rejected"]: return redirect("/admin")
    conn = db(); conn.execute("UPDATE business_profiles SET status=? WHERE id=?", (status,id)); conn.commit(); conn.close()
    log(f"Business {status}", session.get("user","admin")); return redirect("/admin")

@app.route("/admin/product/<int:id>/<status>")
def admin_product(id, status):
    if status not in ["approved","rejected"]: return redirect("/admin")
    conn = db(); conn.execute("UPDATE products SET status=? WHERE id=?", (status,id)); conn.commit(); conn.close()
    log(f"Product {status}", session.get("user","admin")); return redirect("/admin")

@app.route("/admin/news/<int:id>/<status>")
def admin_news(id, status):
    if status not in ["approved","rejected"]: return redirect("/admin")
    conn = db(); conn.execute("UPDATE news_posts SET status=? WHERE id=?", (status,id)); conn.commit(); conn.close()
    log(f"News {status}", session.get("user","admin")); return redirect("/admin")

@app.route("/admin/release/<int:id>/<status>")
def admin_release(id, status):
    if status not in ["approved","rejected"]: return redirect("/admin")
    conn = db(); conn.execute("UPDATE media_releases SET status=? WHERE id=?", (status,id)); conn.commit(); conn.close()
    log(f"Release {status}", session.get("user","admin")); return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
