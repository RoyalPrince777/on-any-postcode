from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from markupsafe import escape
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)

ADMIN_USERNAME = "N24-7"
ADMIN_EMAIL = "earthisourturf777@gmail.com"
ADMIN_PASSWORD = "2525"

ALLOWED = {"jpg","jpeg","png","webp","gif","mp3","wav","ogg","m4a","mp4","webm","mov","pdf"}

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def h(x):
    return escape(str(x or ""))

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
        related_product_id INTEGER DEFAULT 0,
        related_link TEXT,
        country TEXT DEFAULT 'Global',
        city TEXT DEFAULT '',
        postcode TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        status TEXT DEFAULT 'approved',
        created_at TEXT
    )""")
    for col, typ in [
        ("country","TEXT DEFAULT 'Global'"),("city","TEXT DEFAULT ''"),("postcode","TEXT DEFAULT ''"),
        ("related_product_id","INTEGER DEFAULT 0"),("related_link","TEXT"),("views","INTEGER DEFAULT 0"),
        ("status","TEXT DEFAULT 'approved'")
    ]:
        add_col(cur, "news_posts", col, typ)

    cur.execute("""CREATE TABLE IF NOT EXISTS hrm_match_reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        match_title TEXT,
        competition TEXT,
        teams TEXT,
        score TEXT,
        goals TEXT,
        match_status TEXT,
        source_note TEXT,
        tactical_notes TEXT,
        community_opportunity TEXT,
        monetization_note TEXT,
        swot_strength TEXT,
        swot_weakness TEXT,
        swot_opportunity TEXT,
        swot_threat TEXT,
        news_post_id INTEGER DEFAULT 0,
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
        country TEXT DEFAULT 'UK',
        city TEXT DEFAULT '',
        postcode TEXT DEFAULT '',
        status TEXT DEFAULT 'approved',
        views INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    for col, typ in [
        ("country","TEXT DEFAULT 'UK'"),("city","TEXT DEFAULT ''"),("postcode","TEXT DEFAULT ''"),
        ("status","TEXT DEFAULT 'approved'"),("views","INTEGER DEFAULT 0")
    ]:
        add_col(cur, "creator_profiles", col, typ)

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
    for col, typ in [
        ("printful_id","TEXT"),("printful_variant_id","TEXT"),("stock_status","TEXT DEFAULT 'available'"),
        ("collection","TEXT DEFAULT 'General'"),("country","TEXT DEFAULT 'UK'"),("city","TEXT DEFAULT ''"),
        ("postcode","TEXT DEFAULT ''"),("views","INTEGER DEFAULT 0"),("clicks","INTEGER DEFAULT 0")
    ]:
        add_col(cur, "products", col, typ)

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
        related_product_id INTEGER DEFAULT 0,
        related_business_id INTEGER DEFAULT 0,
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

    cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,))
    admin = cur.fetchone()
    if not admin:
        cur.execute(
            "INSERT INTO users(username,email,password,role,created_at) VALUES(?,?,?,?,?)",
            (ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", now())
        )

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
<a href="/hrm_match_scanner">HRM Match Scanner</a>
<a href="/match_reports">Match Reports</a>
<a href="/news">News</a>
<a href="/events">Events</a>
<a href="/worldcup">World Cup</a>
<a href="/business">Business</a>
<a href="/retail">Retail</a>
<a href="/media">Media</a>
<a href="/creators">Creators</a>
<a href="/explorer">Explorer</a>
<a href="/admin">HRM</a>
</div>
{{content|safe}}
</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def card_news(n):
    img = f"<img src='/{h(n['image'])}'>" if n["image"] else ""
    return f"""
    <div class='card'>
    <b>{h(n['title'])}</b><br>
    <span class='gold'>{h(n['category'])}</span><br>
    <span class='small'>{h(n['city'])} {h(n['country'])} {h(n['postcode'])}</span>
    {img}
    <p>{h(n['summary'])}</p>
    <a href='/news/{n['id']}'>Read</a>
    </div>
    """

def card_event(e):
    img = f"<img src='/{h(e['image'])}'>" if e["image"] else ""
    return f"""
    <div class='card'>
    <b>{h(e['title'])}</b><br>
    <span class='gold'>{h(e['event_type'])} • {h(e['category'])}</span><br>
    <span class='small'>{h(e['event_date'])} {h(e['event_time'])} • {h(e['city'])}</span>
    {img}
    <p>{h(e['description'])}</p>
    <a href='/event/{e['id']}'>Open</a>
    </div>
    """

def card_product(p):
    img = f"<img src='/{h(p['image'])}'>" if p["image"] else ""
    return f"""
    <div class='card'>
    <b>{h(p['title'])}</b><br>
    <span class='gold'>{h(p['price'])}</span><br>
    <span class='small'>{h(p['category'])} • {h(p['supplier'])}</span>
    {img}
    <p>{h(p['description'])}</p>
    <a href='/product/{p['id']}'>Open</a>
    </div>
    """

@app.route("/")
def home():
    conn = db()
    news = conn.execute("SELECT * FROM news_posts WHERE status='approved' ORDER BY id DESC LIMIT 6").fetchall()
    events = conn.execute("SELECT * FROM events WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    products = conn.execute("SELECT * FROM products WHERE status='approved' ORDER BY id DESC LIMIT 4").fetchall()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>HRM scans real events, writes news, records lessons.</p>
    <p>Views are observation. Value is participation, trust, orders, revenue, and community.</p>
    </div>
    <div class='card'>
    <h2>⚽ Quick Action</h2>
    <p><a class='badge' href='/hrm_quick_arsenal'>Generate PSG vs Arsenal HRM News</a></p>
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
        content += card_news(n)
    content += "</div></div><div class='card'><h2>⚽ Events</h2><div class='grid'>"
    for e in events:
        content += card_event(e)
    content += "</div></div><div class='card'><h2>🛍️ Retail</h2><div class='grid'>"
    for p in products:
        content += card_product(p)
    content += "</div></div><div class='card'><h2>Feed</h2>"
    for p in posts:
        content += f"<div class='card'><b>@{h(p['username'])}</b><p>{h(p['content'])}</p></div>"
    content += "</div>"
    return render(content)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        role = "admin" if username.lower() in ["admin", ADMIN_USERNAME.lower()] else "member"
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
    return render("<div class='card'><h2>Register</h2><form method='POST'><input name='username' placeholder='Username' required><input name='email' placeholder='Email' required><input name='password' type='password' placeholder='Password' required><button>Register</button></form></div>")

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
    return render("<div class='card'><h2>Login</h2><form method='POST'><input name='username' placeholder='Username' required><input name='password' type='password' placeholder='Password' required><button>Login</button></form><p class='small'>Default local admin: N24-7 / 2525</p></div>")

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

def create_match_news(data, username="HRM"):
    title = data["headline"]
    summary = data["summary"]
    body = f"""
MATCH:
{data['match_title']}

COMPETITION:
{data['competition']}

TEAMS:
{data['teams']}

SCORE:
{data['score']}

GOALS / KEY MOMENTS:
{data['goals']}

TACTICAL OBSERVATION:
{data['tactical_notes']}

COMMUNITY OPPORTUNITY:
{data['community_opportunity']}

MONETIZATION NOTE:
{data['monetization_note']}

HRM LAW:
Views are observation, not monetization.
Value comes from participation, attendance, product clicks, orders, revenue, repeat engagement, and trust records.

SWOT:
Strength: {data['swot_strength']}
Weakness: {data['swot_weakness']}
Opportunity: {data['swot_opportunity']}
Threat: {data['swot_threat']}
"""
    conn = db()
    cur = conn.cursor()
    cur.execute("""INSERT INTO news_posts(username,title,category,summary,body,source_note,verification_status,image,related_product_id,related_link,country,city,postcode,views,status,created_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (
        username, title, "Football / HRM Match Report", summary, body,
        data["source_note"], "needs review", "", 0, "", "Global", "", "", 0, "approved", now()
    ))
    news_id = cur.lastrowid

    cur.execute("""INSERT INTO hrm_match_reports(username,match_title,competition,teams,score,goals,match_status,source_note,tactical_notes,community_opportunity,monetization_note,swot_strength,swot_weakness,swot_opportunity,swot_threat,news_post_id,created_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (
        username, data["match_title"], data["competition"], data["teams"], data["score"],
        data["goals"], data["match_status"], data["source_note"], data["tactical_notes"],
        data["community_opportunity"], data["monetization_note"], data["swot_strength"],
        data["swot_weakness"], data["swot_opportunity"], data["swot_threat"], news_id, now()
    ))

    conn.commit()
    conn.close()
    log(f"HRM generated match news: {title}", username)
    return news_id

@app.route("/hrm_quick_arsenal")
def hrm_quick_arsenal():
    data = {
        "headline": "PSG and Arsenal Final Shows Why Football Energy Can Build Community Beyond the Scoreline",
        "summary": "HRM records the PSG vs Arsenal final as a major football attention event with strong community, creator, retail, business and watch-party potential.",
        "match_title": "PSG vs Arsenal Champions League Final",
        "competition": "UEFA Champions League Final",
        "teams": "Paris Saint-Germain vs Arsenal",
        "score": "Match completed — verify final score before public final-result claim",
        "goals": "Kai Havertz and Ousmane Dembélé were reported as major scoring moments in live coverage.",
        "match_status": "Completed / post-event review",
        "source_note": "Use verified sports sources before publishing final winner or final score. HRM record created as community intelligence, not official match authority.",
        "tactical_notes": "Arsenal showed structure, discipline and direct threat. PSG showed possession, speed and attacking pressure.",
        "community_opportunity": "Watch parties, creator debates, football news, local business promos, merch drops and community posts.",
        "monetization_note": "Views are not monetization. Real value comes from attendance, product clicks, orders, food, business promotion and repeat participation.",
        "swot_strength": "Global football attention and strong fan emotion.",
        "swot_weakness": "No guaranteed revenue unless connected to events, products, business offers or signups.",
        "swot_opportunity": "Turn football attention into OAP News, World Cup Hub, watch parties and local commerce.",
        "swot_threat": "Wrong score claims, fake news, copyright misuse, and chasing views instead of value."
    }
    news_id = create_match_news(data, session.get("user", "HRM"))
    return redirect(f"/news/{news_id}")

@app.route("/hrm_match_scanner", methods=["GET","POST"])
def hrm_match_scanner():
    if request.method == "POST":
        data = {
            "headline": request.form["headline"],
            "summary": request.form["summary"],
            "match_title": request.form["match_title"],
            "competition": request.form["competition"],
            "teams": request.form["teams"],
            "score": request.form["score"],
            "goals": request.form["goals"],
            "match_status": request.form["match_status"],
            "source_note": request.form["source_note"],
            "tactical_notes": request.form["tactical_notes"],
            "community_opportunity": request.form["community_opportunity"],
            "monetization_note": request.form["monetization_note"],
            "swot_strength": request.form["swot_strength"],
            "swot_weakness": request.form["swot_weakness"],
            "swot_opportunity": request.form["swot_opportunity"],
            "swot_threat": request.form["swot_threat"]
        }
        news_id = create_match_news(data, session.get("user", "HRM"))
        return redirect(f"/news/{news_id}")

    return render("""
    <div class='card hero'>
    <h1>🧠 HRM Match News Scanner</h1>
    <p class='green'>Turn real matches into OAP News + HRM learning records.</p>
    </div>
    <div class='card'>
    <form method='POST'>
    <input name='headline' placeholder='News headline' value='Football Final Creates Community Energy Beyond The Scoreline' required>
    <textarea name='summary' placeholder='Short summary'>HRM records this match as a high-attention football event with community, creator, business, event and retail potential.</textarea>
    <input name='match_title' placeholder='Match title' value='PSG vs Arsenal Champions League Final' required>
    <input name='competition' placeholder='Competition' value='UEFA Champions League Final'>
    <input name='teams' placeholder='Teams' value='PSG vs Arsenal'>
    <input name='score' placeholder='Score / result note' value='Completed — verify final result before official public claim'>
    <textarea name='goals' placeholder='Goals / key moments'>Kai Havertz and Ousmane Dembélé were reported as key scoring moments in live coverage.</textarea>
    <input name='match_status' placeholder='Status' value='Completed / post-event review'>
    <textarea name='source_note' placeholder='Source / verification note'>Verify final score using official or trusted sports sources before publishing final winner.</textarea>
    <textarea name='tactical_notes' placeholder='Tactical observation'>Arsenal showed structure and discipline. PSG showed possession, pressure and attacking quality.</textarea>
    <textarea name='community_opportunity' placeholder='Community opportunity'>Watch parties, creator debates, local business promotions, football news and merch drops.</textarea>
    <textarea name='monetization_note' placeholder='Monetization note'>Views are not monetization. Real value comes from attendance, product clicks, orders, business promotion and trust records.</textarea>
    <input name='swot_strength' placeholder='Strength' value='Global football attention'>
    <input name='swot_weakness' placeholder='Weakness' value='No revenue without offers, events, products or participation'>
    <input name='swot_opportunity' placeholder='Opportunity' value='Convert football attention into OAP community activity'>
    <input name='swot_threat' placeholder='Threat' value='Fake scores, copyright misuse and vanity metrics'>
    <button>Generate HRM News Record</button>
    </form>
    </div>
    """)

@app.route("/match_reports")
def match_reports():
    conn = db()
    rows = conn.execute("SELECT * FROM hrm_match_reports ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>⚽ HRM Match Reports</h1></div>"
    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['match_title'])}</b><br>
        <span class='gold'>{h(r['competition'])}</span><br>
        <p>{h(r['score'])}</p>
        <a href='/news/{r['news_post_id']}'>Open News Record</a>
        </div>
        """
    return render(content)

@app.route("/news", methods=["GET","POST"])
def news():
    if request.method == "POST":
        image = save_file(request.files.get("image"))
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO news_posts(username,title,category,summary,body,source_note,verification_status,image,related_product_id,related_link,country,city,postcode,views,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            username, request.form["title"], request.form["category"], request.form["summary"],
            request.form["body"], request.form["source_note"], request.form["verification_status"],
            image, request.form.get("related_product_id") or 0, request.form["related_link"],
            request.form["country"], request.form["city"], request.form["postcode"], 0, "pending", now()
        ))
        conn.commit()
        conn.close()
        log("News submitted", username)
        return redirect("/news")

    conn = db()
    rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>📰 OAP News</h1>
    <form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Title' required>
    <input name='category' placeholder='Category' value='Community'>
    <input name='country' placeholder='Country' value='Global'>
    <input name='city' placeholder='City'>
    <input name='postcode' placeholder='Postcode'>
    <textarea name='summary' placeholder='Summary'></textarea>
    <textarea name='body' placeholder='Story'></textarea>
    <textarea name='source_note' placeholder='Source/proof note'></textarea>
    <select name='verification_status'><option>draft</option><option>needs review</option><option>verified</option></select>
    <input name='related_product_id' placeholder='Related product ID'>
    <input name='related_link' placeholder='Related link'>
    <input type='file' name='image'>
    <button>Submit News</button>
    </form></div><div class='grid'>
    """
    for n in rows:
        content += card_news(n)
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
    content = f"""
    <div class='card'>
    <h1>{h(n['title'])}</h1>
    <p class='gold'>{h(n['category'])}</p>
    <p class='small'>{h(n['city'])} {h(n['country'])} {h(n['postcode'])} • Views: {h(n['views'])}</p>
    """
    if n["image"]:
        content += f"<img src='/{h(n['image'])}'>"
    content += f"""
    <h2>{h(n['summary'])}</h2>
    <pre style='white-space:pre-wrap;font-family:Arial'>{h(n['body'])}</pre>
    <div class='card'><h2>Verification</h2><p>{h(n['source_note'])}</p></div>
    </div>
    """
    return render(content)

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method == "POST":
        image = save_file(request.files.get("image"))
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO events(username,title,event_type,category,country_focus,postcode,city,country,venue,event_date,event_time,description,ticket_price,capacity,contact,related_product_id,related_business_id,image,status,views,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            username, request.form["title"], request.form["event_type"], request.form["category"],
            request.form["country_focus"], request.form["postcode"], request.form["city"], request.form["country"],
            request.form["venue"], request.form["event_date"], request.form["event_time"], request.form["description"],
            request.form["ticket_price"], request.form["capacity"], request.form["contact"],
            request.form.get("related_product_id") or 0, request.form.get("related_business_id") or 0,
            image, "pending", 0, now()
        ))
        conn.commit()
        conn.close()
        log("Event submitted", username)
        return redirect("/events")
    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
    conn.close()
    content = """
    <div class='card'><h1>⚽ OAP Events / Watch Parties</h1>
    <form method='POST' enctype='multipart/form-data'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'><option>Watch Party</option><option>Creator Meetup</option><option>Business Popup</option><option>Community Event</option></select>
    <input name='category' placeholder='Category' value='Football'>
    <input name='country_focus' placeholder='Country focus' value='Global'>
    <input name='postcode' placeholder='Postcode'>
    <input name='city' placeholder='City'>
    <input name='country' placeholder='Country' value='UK'>
    <input name='venue' placeholder='Venue'>
    <input name='event_date' placeholder='Date'>
    <input name='event_time' placeholder='Time'>
    <textarea name='description' placeholder='Description'></textarea>
    <input name='ticket_price' placeholder='Ticket price'>
    <input name='capacity' placeholder='Capacity'>
    <input name='contact' placeholder='Contact'>
    <input name='related_product_id' placeholder='Related product ID'>
    <input name='related_business_id' placeholder='Related business ID'>
    <input type='file' name='image'>
    <button>Submit Event</button>
    </form></div><div class='grid'>
    """
    for e in rows:
        content += card_event(e)
    content += "</div>"
    return render(content)

@app.route("/event/<int:id>")
def event_detail(id):
    conn = db()
    e = conn.execute("SELECT * FROM events WHERE id=?", (id,)).fetchone()
    if not e:
        conn.close()
        return "Event not found"
    conn.execute("UPDATE events SET views=views+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return render(f"<div class='card'><h1>{h(e['title'])}</h1><p>{h(e['event_date'])} {h(e['event_time'])} • {h(e['city'])}</p><p>{h(e['description'])}</p></div>")

@app.route("/worldcup")
def worldcup():
    conn = db()
    events = conn.execute("SELECT * FROM events WHERE category LIKE '%Football%' OR category LIKE '%World Cup%' OR country_focus != '' ORDER BY id DESC LIMIT 20").fetchall()
    news = conn.execute("SELECT * FROM news_posts WHERE category LIKE '%Football%' OR category LIKE '%World Cup%' OR title LIKE '%Arsenal%' OR title LIKE '%PSG%' ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>⚽ OAP Football / World Cup Hub</h1><p class='green'>News → Events → Community → Retail → Trust Records</p></div><div class='card'><h2>News</h2><div class='grid'>"
    for n in news:
        content += card_news(n)
    content += "</div></div><div class='card'><h2>Events</h2><div class='grid'>"
    for e in events:
        content += card_event(e)
    content += "</div></div>"
    return render(content)

@app.route("/business")
def business():
    conn = db()
    rows = conn.execute("SELECT * FROM business_profiles ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = "<div class='card'><h1>Business Board</h1></div>"
    for b in rows:
        content += f"<div class='card'><b>{h(b['business_name'])}</b><p>{h(b['category'])}</p></div>"
    return render(content)

@app.route("/retail")
def retail():
    conn = db()
    rows = conn.execute("SELECT * FROM products ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = "<div class='card'><h1>Retail</h1></div><div class='grid'>"
    for p in rows:
        content += card_product(p)
    content += "</div>"
    return render(content)

@app.route("/product/<int:id>")
def product(id):
    conn = db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    conn.close()
    if not p:
        return "Product not found"
    return render(card_product(p))

@app.route("/media")
def media():
    conn = db()
    rows = conn.execute("SELECT * FROM media_releases ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = "<div class='card'><h1>Media</h1></div>"
    for r in rows:
        content += f"<div class='card'><b>{h(r['title'])}</b> — {h(r['status'])}<br><a href='/release/{r['id']}'>Open</a></div>"
    return render(content)

@app.route("/release/<int:id>")
def release(id):
    conn = db()
    r = conn.execute("SELECT * FROM media_releases WHERE id=?", (id,)).fetchone()
    conn.close()
    if not r:
        return "Release not found"
    content = f"<div class='card'><h1>{h(r['title'])}</h1><p>{h(r['description'])}</p>"
    if r["cover_art"]:
        content += f"<img src='/{h(r['cover_art'])}'>"
    if r["media_file"]:
        f = r["media_file"].lower()
        if f.endswith((".mp3",".wav",".ogg",".m4a")):
            content += f"<audio controls src='/{h(r['media_file'])}'></audio>"
        elif f.endswith((".mp4",".webm",".mov")):
            content += f"<video controls src='/{h(r['media_file'])}'></video>"
    content += "</div>"
    return render(content)

@app.route("/creators")
def creators():
    conn = db()
    rows = conn.execute("SELECT * FROM creator_profiles ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    content = "<div class='card'><h1>Creators</h1></div>"
    for c in rows:
        content += f"<div class='card'><b>{h(c['display_name'])}</b><p>{h(c['category'])}</p></div>"
    return render(content)

@app.route("/explorer")
def explorer:
    return render("<div class='card hero'><h1>🌍 OAP Explorer</h1><p>Country, city and postcode discovery layer.</p></div><div class='card'><p><a href='/worldcup'>Football Hub</a><a href='/news'>News</a><a href='/events'>Events</a></p></div>")

@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    content = f"<div class='card'><h1>Search</h1><form><input name='q' value='{h(q)}'><button>Search</button></form></div>"
    if not q:
        return render(content)
    like = f"%{q}%"
    conn = db()
    news = conn.execute("SELECT * FROM news_posts WHERE title LIKE ? OR category LIKE ? OR body LIKE ?", (like,like,like)).fetchall()
    events = conn.execute("SELECT * FROM events WHERE title LIKE ? OR category LIKE ?", (like,like)).fetchall()
    conn.close()
    content += "<div class='card'><h2>News</h2>"
    for n in news:
        content += f"<p><a href='/news/{n['id']}'>{h(n['title'])}</a></p>"
    content += "</div><div class='card'><h2>Events</h2>"
    for e in events:
        content += f"<p><a href='/event/{e['id']}'>{h(e['title'])}</a></p>"
    content += "</div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    news = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 50").fetchall()
    events = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 60").fetchall()
    conn.close()
    content = "<div class='card'><h1>HRM Admin</h1></div><div class='card'><h2>News Review</h2>"
    for n in news:
        content += f"<div class='card'>{h(n['title'])} — {h(n['status'])} <a href='/admin/news/{n['id']}/approved'>Approve</a> <a href='/admin/news/{n['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Event Review</h2>"
    for e in events:
        content += f"<div class='card'>{h(e['title'])} — {h(e['status'])} <a href='/admin/event/{e['id']}/approved'>Approve</a> <a href='/admin/event/{e['id']}/rejected'>Reject</a></div>"
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    content += "</div>"
    return render(content)

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

@app.route("/admin/event/<int:id>/<status>")
def admin_event(id, status):
    if status not in ["approved","rejected"]:
        return redirect("/admin")
    conn = db()
    conn.execute("UPDATE events SET status=? WHERE id=?", (status,id))
    conn.commit()
    conn.close()
    log(f"Event {status}", session.get("user","admin"))
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
