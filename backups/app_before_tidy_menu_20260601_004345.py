from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
ADMIN_USERNAME = "N24-7"
ADMIN_PASSWORD = "2525"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def h(x):
    return escape(str(x or ""))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def add_col(cur, table, col, typ):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")

def init_db():
    conn = db()
    cur = conn.cursor()

    tables = {
        "users": [
            ("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("nickname","TEXT"),("username","TEXT UNIQUE"),("password","TEXT"),
            ("postcode","TEXT"),("borough","TEXT"),("county_region","TEXT"),("country","TEXT"),("continent","TEXT"),
            ("weather_location","TEXT"),("verification_level","TEXT DEFAULT 'Starter'"),("role","TEXT DEFAULT 'member'"),("created_at","TEXT")
        ],
        "audit_logs": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("action","TEXT"),("username","TEXT"),("member","TEXT"),("created_at","TEXT")],
        "culture_posts": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("title","TEXT"),("category","TEXT"),("country","TEXT"),("body","TEXT"),("created_at","TEXT")],
        "artists": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("artist_name","TEXT"),("genre","TEXT"),("country","TEXT"),("bio","TEXT"),("link","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "events": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("title","TEXT"),("event_type","TEXT"),("postcode","TEXT"),("borough","TEXT"),("country","TEXT"),("venue","TEXT"),("event_date","TEXT"),("description","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "messages": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("sender","TEXT"),("recipient","TEXT"),("subject","TEXT"),("body","TEXT"),("status","TEXT DEFAULT 'unread'"),("created_at","TEXT")],
        "trust_badges": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("requested_level","TEXT"),("proof","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "opportunities": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("source","TEXT"),("description","TEXT"),("amount","REAL DEFAULT 0"),("currency","TEXT DEFAULT 'GBP'"),("status","TEXT DEFAULT 'recorded'"),("created_at","TEXT")],
        "payouts": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("recipient_name","TEXT"),("reason","TEXT"),("amount","REAL DEFAULT 0"),("currency","TEXT DEFAULT 'GBP'"),("status","TEXT DEFAULT 'pending'"),("approved_by","TEXT"),("paid_date","TEXT"),("created_at","TEXT")],
        "approvals": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("approval_type","TEXT"),("record_id","INTEGER"),("status","TEXT DEFAULT 'pending'"),("reviewer","TEXT"),("notes","TEXT"),("created_at","TEXT")],
        "businesses": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("business_name","TEXT"),("category","TEXT"),("postcode","TEXT"),("borough","TEXT"),("country","TEXT"),("description","TEXT"),("contact","TEXT"),("status","TEXT DEFAULT 'pending'"),("created_at","TEXT")],
        "products": [("id","INTEGER PRIMARY KEY AUTOINCREMENT"),("username","TEXT"),("business_name","TEXT"),("product_name","TEXT"),("category","TEXT"),("price","REAL DEFAULT 0"),("currency","TEXT DEFAULT 'GBP'"),("description","TEXT"),("status","TEXT DEFAULT 'draft'"),("created_at","TEXT")],
    }

    for table, cols in tables.items():
        col_defs = ", ".join([f"{c} {t}" for c, t in cols])
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table}({col_defs})")
        for c, t in cols:
            if c != "id":
                add_col(cur, table, c, t)

    found = cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,)).fetchone()
    if found:
        cur.execute("UPDATE users SET password=?, role=?, verification_level=? WHERE username=?",
                    (generate_password_hash(ADMIN_PASSWORD), "admin", "Founder", ADMIN_USERNAME))
    else:
        cur.execute("""INSERT INTO users(nickname,username,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("N24-7", ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), "CR4", "Merton", "Greater London", "UK", "Europe", "London", "Founder", "admin", now()))

    conn.commit()
    conn.close()

def log(action, username="system"):
    conn = db()
    conn.execute("INSERT INTO audit_logs(action,username,member,created_at) VALUES(?,?,?,?)", (action, username, username, now()))
    conn.commit()
    conn.close()

init_db()

def user():
    return session.get("user", "guest")

def render(content):
    return render_template_string(BASE, content=content)

BASE = """
<!DOCTYPE html><html><head><title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#050505;color:white;font-family:Arial}
.top{background:#101010;padding:15px;border-bottom:1px solid #222;position:sticky;top:0;z-index:5}
.logo{font-size:22px;font-weight:900}.wrap{padding:14px;max-width:1150px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:16px;margin:12px 0}
.hero{text-align:center;padding:30px 10px}.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:13px;margin:8px 0;background:#0b0b0b;color:white;border:1px solid #333;border-radius:12px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:12px;padding:13px 18px;font-weight:900}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.warn{background:#2b1600;border-color:#6b3b00}.badge{display:inline-block;background:#00dd99;color:#000;padding:7px 11px;border-radius:999px;font-weight:900;font-size:12px;margin:3px}
</style></head><body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/leave">Leave My World</a>
{% else %}
<a href="/join">Join OAP</a> <a href="/enter">Enter My World</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a><a href="/privacy">Privacy</a><a href="/my_world">My World</a><a href="/command_center">Command Center</a>
<a href="/community">Community</a><a href="/sports">Sports</a><a href="/culture">Culture</a><a href="/music">Music</a>
<a href="/artists">Artists</a><a href="/events">Events</a><a href="/business">Business</a><a href="/products">Products</a>
<a href="/messages">Messenger</a><a href="/trust_badge">Trust Badge</a><a href="/opportunity_board">Opportunity Board</a>
<a href="/payouts">Payouts</a><a href="/approvals">Approvals</a><a href="/search">Search</a><a href="/explorer">Explorer</a>
<a href="/routes">Routes</a><a href="/admin">Admin</a>
</div></div><div class="wrap">{{content|safe}}</div></body></html>
"""

@app.route("/favicon.ico")
def favicon():
    return ("", 204)

@app.route("/")
def home():
    conn=db()
    stats={
        "members":conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        "culture":conn.execute("SELECT COUNT(*) c FROM culture_posts").fetchone()["c"],
        "artists":conn.execute("SELECT COUNT(*) c FROM artists").fetchone()["c"],
        "events":conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        "businesses":conn.execute("SELECT COUNT(*) c FROM businesses").fetchone()["c"],
        "products":conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"],
        "opps":conn.execute("SELECT COALESCE(SUM(amount),0) c FROM opportunities").fetchone()["c"],
    }
    conn.close()
    return render(f"""
    <div class='card hero'><h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>Join OAP. Enter My World. Every member has a World.</p></div>
    <div class='grid'>
    <div class='card'><h2>{stats['members']}</h2><p>Members</p></div>
    <div class='card'><h2>{stats['culture']}</h2><p>Culture</p></div>
    <div class='card'><h2>{stats['artists']}</h2><p>Artists</p></div>
    <div class='card'><h2>{stats['events']}</h2><p>Events</p></div>
    <div class='card'><h2>{stats['businesses']}</h2><p>Businesses</p></div>
    <div class='card'><h2>{stats['products']}</h2><p>Products</p></div>
    <div class='card'><h2>£{stats['opps']:.2f}</h2><p>Opportunity Board</p></div>
    </div>
    """)

@app.route("/join", methods=["GET","POST"])
@app.route("/signup", methods=["GET","POST"])
def join():
    if request.method=="POST":
        conn=db()
        try:
            conn.execute("""INSERT INTO users(nickname,username,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (request.form["nickname"],request.form["username"],generate_password_hash(request.form["password"]),
             request.form.get("postcode",""),request.form.get("borough",""),request.form.get("county_region",""),
             request.form.get("country",""),request.form.get("continent",""),request.form.get("weather_location",""),
             "Starter","member",now()))
            conn.commit(); log("Member joined OAP", request.form["username"])
            return redirect("/welcome")
        except sqlite3.IntegrityError:
            return render("<div class='card'><h1>Username exists</h1><a href='/join'>Try again</a></div>")
        finally:
            conn.close()
    return render("""
    <div class='card hero'><h1>Join OAP</h1><p class='green'>Fast signup. More proof only needed for Trust Badge or monetization.</p></div>
    <div class='card'><form method='POST'>
    <input name='nickname' placeholder='Nickname' required><input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required><input name='postcode' placeholder='Postcode optional'>
    <input name='borough' placeholder='Borough optional'><input name='county_region' placeholder='County / Region optional'>
    <input name='country' placeholder='Country optional'><input name='continent' placeholder='Continent optional'>
    <input name='weather_location' placeholder='Weather location optional'><button>Join OAP</button></form></div>
    """)

@app.route("/welcome")
def welcome():
    return render("<div class='card hero'><h1>🌍 Your World Has Been Created</h1><p class='green'>Welcome to OAP.</p><a class='badge' href='/enter'>Enter My World</a></div>")

@app.route("/enter", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def enter():
    if request.method=="POST":
        conn=db(); row=conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone(); conn.close()
        if row and check_password_hash(row["password"], request.form["password"]):
            session["user"]=row["username"]; session["role"]=row["role"]; log("Entered My World", row["username"])
            return redirect("/my_world")
        return render("<div class='card'><h1>Invalid entry</h1><a href='/enter'>Try again</a></div>")
    return render("<div class='card hero'><h1>Enter My World</h1></div><div class='card'><form method='POST'><input name='username' placeholder='Username' required><input name='password' type='password' placeholder='Password' required><button>Enter My World</button></form><p>Founder: N24-7 / 2525</p></div>")

@app.route("/leave")
@app.route("/logout")
def leave():
    session.clear()
    return redirect("/")

@app.route("/privacy")
@app.route("/trust")
def privacy():
    return render("""
    <div class='card hero'><h1>🛡️ OAP Privacy & Trust Promise</h1><p class='green'>Human-first. Private-first. Community-first.</p></div>
    <div class='card'><h2>Your OAP Rights</h2>
    <p>✅ Your data belongs to you.</p><p>✅ Your profile belongs to you.</p><p>✅ Your content belongs to you.</p>
    <p>✅ Your messages belong to you.</p><p>✅ Your culture belongs to you.</p><p>✅ Your business belongs to you.</p></div>
    <div class='card warn'>OAP owns the core. We collaborate only where it fits the mission.</div>
    """)

@app.route("/my_world")
def my_world():
    u=user(); conn=db()
    culture=conn.execute("SELECT COUNT(*) c FROM culture_posts WHERE username=?", (u,)).fetchone()["c"]
    artists=conn.execute("SELECT COUNT(*) c FROM artists WHERE username=?", (u,)).fetchone()["c"]
    events=conn.execute("SELECT COUNT(*) c FROM events WHERE username=?", (u,)).fetchone()["c"]
    businesses=conn.execute("SELECT COUNT(*) c FROM businesses WHERE username=?", (u,)).fetchone()["c"]
    products=conn.execute("SELECT COUNT(*) c FROM products WHERE username=?", (u,)).fetchone()["c"]
    opp=conn.execute("SELECT COALESCE(SUM(amount),0) c FROM opportunities WHERE username=?", (u,)).fetchone()["c"]
    conn.close()
    return render(f"""
    <div class='card hero'><h1>🌍 My World</h1><p class='green'>Every member has a World.</p></div>
    <div class='grid'>
    <div class='card'><h2>{culture}</h2><p>My Culture</p><a href='/culture'>Open</a></div>
    <div class='card'><h2>{artists}</h2><p>My Artists</p><a href='/artists'>Open</a></div>
    <div class='card'><h2>{events}</h2><p>My Events</p><a href='/events'>Open</a></div>
    <div class='card'><h2>{businesses}</h2><p>My Businesses</p><a href='/business'>Open</a></div>
    <div class='card'><h2>{products}</h2><p>My Products</p><a href='/products'>Open</a></div>
    <div class='card'><h2>£{opp:.2f}</h2><p>My Opportunities</p><a href='/opportunity_board'>Open</a></div>
    </div>
    """)

@app.route("/community")
def community():
    return render("<div class='card hero'><h1>🌍 Community</h1><p class='green'>Postcode → Borough → County → Country → Continent → Global → Planet → Universe</p></div>")

@app.route("/sports")
def sports():
    return render("<div class='card hero'><h1>⚽ Sports</h1><p class='green'>World Cup, football, boxing, Olympics, chess.</p></div>")

@app.route("/music")
def music():
    return render("<div class='card hero'><h1>🎵 OAP Music</h1><p class='green'>Own Spotify-style destination later. Structure first.</p></div>")

@app.route("/culture", methods=["GET","POST"])
def culture():
    if request.method=="POST":
        conn=db(); conn.execute("INSERT INTO culture_posts(username,title,category,country,body,created_at) VALUES(?,?,?,?,?,?)",(user(),request.form["title"],request.form["category"],request.form["country"],request.form["body"],now()))
        conn.commit(); conn.close(); log("Culture created", user()); return redirect("/culture")
    conn=db(); rows=conn.execute("SELECT * FROM culture_posts ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>🎵 Culture</h1></div><div class='card'><form method='POST'><input name='title' placeholder='Title' required><select name='category'><option>Song</option><option>Story</option><option>Language</option><option>Proverb</option><option>Food</option><option>Dance</option><option>Festival</option></select><input name='country' placeholder='Country'><textarea name='body' placeholder='Record'></textarea><button>Save Culture</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['category'])} • {h(r['country'])}<p>{h(r['body'])}</p></div>"
    return render(content)

@app.route("/artists", methods=["GET","POST"])
def artists():
    if request.method=="POST":
        conn=db(); conn.execute("INSERT INTO artists(username,artist_name,genre,country,bio,link,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(user(),request.form["artist_name"],request.form["genre"],request.form["country"],request.form["bio"],request.form["link"],"pending",now()))
        conn.commit(); conn.close(); return redirect("/artists")
    conn=db(); rows=conn.execute("SELECT * FROM artists ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>🎤 Artists</h1></div><div class='card'><form method='POST'><input name='artist_name' placeholder='Artist name' required><input name='genre' placeholder='Genre'><input name='country' placeholder='Country'><textarea name='bio' placeholder='Bio'></textarea><input name='link' placeholder='Link'><button>Submit Artist</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['artist_name'])}</b><br>{h(r['genre'])} • {h(r['country'])} • {h(r['status'])}<p>{h(r['bio'])}</p></div>"
    return render(content)

@app.route("/events", methods=["GET","POST"])
def events():
    if request.method=="POST":
        conn=db(); conn.execute("INSERT INTO events(username,title,event_type,postcode,borough,country,venue,event_date,description,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(user(),request.form["title"],request.form["event_type"],request.form["postcode"],request.form["borough"],request.form["country"],request.form["venue"],request.form["event_date"],request.form["description"],"pending",now()))
        conn.commit(); conn.close(); return redirect("/events")
    conn=db(); rows=conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>📅 Events</h1></div><div class='card'><form method='POST'><input name='title' placeholder='Event title' required><select name='event_type'><option>Culture Event</option><option>Watch Party</option><option>Business Popup</option><option>Artist Event</option></select><input name='postcode' placeholder='Postcode'><input name='borough' placeholder='Borough'><input name='country' placeholder='Country'><input name='venue' placeholder='Venue'><input name='event_date' placeholder='Date'><textarea name='description' placeholder='Description'></textarea><button>Create Event</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['title'])}</b><br>{h(r['event_type'])} • {h(r['postcode'])} • {h(r['status'])}<p>{h(r['description'])}</p></div>"
    return render(content)

@app.route("/business", methods=["GET","POST"])
def business():
    if request.method=="POST":
        conn=db(); conn.execute("INSERT INTO businesses(username,business_name,category,postcode,borough,country,description,contact,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(user(),request.form["business_name"],request.form["category"],request.form["postcode"],request.form["borough"],request.form["country"],request.form["description"],request.form["contact"],"pending",now()))
        conn.commit(); conn.close(); log("Business submitted", user()); return redirect("/business")
    conn=db(); rows=conn.execute("SELECT * FROM businesses ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>🏪 Business Directory</h1><p class='green'>OAP Market starts here.</p></div><div class='card'><form method='POST'><input name='business_name' placeholder='Business name' required><select name='category'><option>Food</option><option>Clothing</option><option>Music</option><option>Events</option><option>Services</option><option>Creative</option><option>Other</option></select><input name='postcode' placeholder='Postcode'><input name='borough' placeholder='Borough'><input name='country' placeholder='Country'><input name='contact' placeholder='Contact / link'><textarea name='description' placeholder='Description'></textarea><button>Submit Business</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['business_name'])}</b><br>{h(r['category'])} • {h(r['postcode'])} • {h(r['country'])} • {h(r['status'])}<p>{h(r['description'])}</p><p>{h(r['contact'])}</p></div>"
    return render(content)

@app.route("/products", methods=["GET","POST"])
def products():
    if request.method=="POST":
        conn=db(); conn.execute("INSERT INTO products(username,business_name,product_name,category,price,currency,description,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(user(),request.form["business_name"],request.form["product_name"],request.form["category"],float(request.form.get("price") or 0),request.form["currency"],request.form["description"],"draft",now()))
        conn.commit(); conn.close(); log("Product added", user()); return redirect("/products")
    conn=db(); rows=conn.execute("SELECT * FROM products ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>🛍 Products</h1><p class='green'>Own Shopify-style layer starts with product records.</p></div><div class='card'><form method='POST'><input name='business_name' placeholder='Business name'><input name='product_name' placeholder='Product name' required><select name='category'><option>Clothing</option><option>Merch</option><option>Music</option><option>Ticket</option><option>Food</option><option>Service</option><option>Other</option></select><input name='price' placeholder='Price'><select name='currency'><option>GBP</option><option>GHS</option><option>EUR</option><option>SIKA</option></select><textarea name='description' placeholder='Description'></textarea><button>Add Product</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['product_name'])}</b><br>{h(r['business_name'])} • {h(r['category'])}<br>{h(r['currency'])} {h(r['price'])}<p>{h(r['description'])}</p></div>"
    return render(content)

@app.route("/messages", methods=["GET","POST"])
def messages():
    if request.method=="POST":
        conn=db(); conn.execute("INSERT INTO messages(sender,recipient,subject,body,status,created_at) VALUES(?,?,?,?,?,?)",(user(),request.form["recipient"],request.form["subject"],request.form["body"],"unread",now()))
        conn.commit(); conn.close(); return redirect("/messages")
    u=user(); conn=db(); rows=conn.execute("SELECT * FROM messages WHERE sender=? OR recipient=? OR recipient='admin' ORDER BY id DESC LIMIT 80",(u,u)).fetchall(); conn.close()
    content="<div class='card hero'><h1>💬 Messenger</h1></div><div class='card'><form method='POST'><input name='recipient' value='admin'><input name='subject' placeholder='Subject'><textarea name='body' placeholder='Message'></textarea><button>Send</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['subject'])}</b><br>{h(r['sender'])} → {h(r['recipient'])}<p>{h(r['body'])}</p></div>"
    return render(content)

@app.route("/trust_badge", methods=["GET","POST"])
@app.route("/verification", methods=["GET","POST"])
def trust_badge():
    if request.method=="POST":
        conn=db(); conn.execute("INSERT INTO trust_badges(username,requested_level,proof,status,created_at) VALUES(?,?,?,?,?)",(user(),request.form["requested_level"],request.form["proof"],"pending",now()))
        conn.commit(); conn.close(); return redirect("/trust_badge")
    conn=db(); rows=conn.execute("SELECT * FROM trust_badges ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>⭐ Trust Badge</h1></div><div class='card'><form method='POST'><select name='requested_level'><option>Postcode Badge</option><option>Borough Badge</option><option>Country Badge</option><option>Continent Badge</option><option>Global Badge</option><option>Planet Badge</option><option>Universe Badge</option></select><textarea name='proof' placeholder='Proof'></textarea><button>Request Trust Badge</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['requested_level'])}</b><br>@{h(r['username'])} • {h(r['status'])}<p>{h(r['proof'])}</p></div>"
    return render(content)

@app.route("/opportunity_board", methods=["GET","POST"])
@app.route("/revenue", methods=["GET","POST"])
def opportunity():
    if request.method=="POST":
        conn=db(); conn.execute("INSERT INTO opportunities(username,source,description,amount,currency,status,created_at) VALUES(?,?,?,?,?,?,?)",(request.form.get("username") or user(),request.form["source"],request.form["description"],float(request.form.get("amount") or 0),request.form["currency"],"recorded",now()))
        conn.commit(); conn.close(); return redirect("/opportunity_board")
    conn=db(); rows=conn.execute("SELECT * FROM opportunities ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>💰 Opportunity Board</h1></div><div class='card'><form method='POST'><input name='username' placeholder='Linked member optional'><select name='source'><option>Business Listing</option><option>Featured Promotion</option><option>Artist Promotion</option><option>Event Promotion</option><option>Vendor Slot</option><option>Founder Membership</option></select><input name='amount' placeholder='Amount'><select name='currency'><option>GBP</option><option>GHS</option><option>EUR</option><option>SIKA</option></select><textarea name='description' placeholder='Description'></textarea><button>Record Opportunity</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['source'])}</b><br>{h(r['currency'])} {h(r['amount'])} • @{h(r['username'])}<p>{h(r['description'])}</p></div>"
    return render(content)

@app.route("/payouts", methods=["GET","POST"])
def payouts():
    if request.method=="POST":
        conn=db(); cur=conn.cursor(); cur.execute("INSERT INTO payouts(username,recipient_name,reason,amount,currency,status,approved_by,paid_date,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(request.form.get("username") or user(),request.form["recipient_name"],request.form["reason"],float(request.form.get("amount") or 0),request.form["currency"],"pending","","",now()))
        pid=cur.lastrowid; cur.execute("INSERT INTO approvals(approval_type,record_id,status,reviewer,notes,created_at) VALUES(?,?,?,?,?,?)",("payout",pid,"pending","","Payout requires human approval.",now()))
        conn.commit(); conn.close(); return redirect("/payouts")
    conn=db(); rows=conn.execute("SELECT * FROM payouts ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>💸 Payouts</h1><p class='green'>Manual only. Human approval before money moves.</p></div><div class='card warn'>This does not send money. It records payout status.</div><div class='card'><form method='POST'><input name='username' placeholder='Linked member optional'><input name='recipient_name' placeholder='Recipient name'><input name='amount' placeholder='Amount'><select name='currency'><option>GBP</option><option>GHS</option><option>EUR</option><option>SIKA</option></select><textarea name='reason' placeholder='Reason'></textarea><button>Create Payout Request</button></form></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['recipient_name'])}</b><br>{h(r['currency'])} {h(r['amount'])} • {h(r['status'])}<p>{h(r['reason'])}</p></div>"
    return render(content)

@app.route("/approvals")
def approvals():
    conn=db(); rows=conn.execute("SELECT * FROM approvals ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>✅ Approvals</h1></div>"
    for r in rows: content+=f"<div class='card'><b>{h(r['approval_type'])} #{h(r['record_id'])}</b><br>{h(r['status'])}<p>{h(r['notes'])}</p><a href='/approval/{r['id']}/approved'>Approve</a><a href='/approval/{r['id']}/rejected'>Reject</a><a href='/approval/{r['id']}/paid'>Mark Paid</a></div>"
    return render(content)

@app.route("/approval/<int:id>/<status>")
def approval_action(id,status):
    if status not in ["approved","rejected","paid"]: return redirect("/approvals")
    reviewer=user(); conn=db(); a=conn.execute("SELECT * FROM approvals WHERE id=?",(id,)).fetchone()
    if a:
        conn.execute("UPDATE approvals SET status=?, reviewer=?, notes=? WHERE id=?",(status,reviewer,f"Reviewed as {status}",id))
        if a["approval_type"]=="payout":
            if status=="paid": conn.execute("UPDATE payouts SET status=?, approved_by=?, paid_date=? WHERE id=?",("paid",reviewer,now(),a["record_id"]))
            else: conn.execute("UPDATE payouts SET status=?, approved_by=? WHERE id=?",(status,reviewer,a["record_id"]))
        conn.commit()
    conn.close(); return redirect("/approvals")

@app.route("/search")
def search():
    q=request.args.get("q","").strip()
    content=f"<div class='card hero'><h1>🔎 OAP Search</h1><p class='green'>OAP-first search. Not Google.</p></div><div class='card'><form method='GET'><input name='q' value='{h(q)}' placeholder='Search culture, artists, events, businesses, products...'><button>Search</button></form></div>"
    if not q: return render(content)
    like=f"%{q}%"; results=[]; conn=db()
    queries=[
        ("Culture","SELECT title,category,body FROM culture_posts WHERE title LIKE ? OR body LIKE ? LIMIT 20"),
        ("Artist","SELECT artist_name,genre,bio FROM artists WHERE artist_name LIKE ? OR genre LIKE ? OR bio LIKE ? LIMIT 20"),
        ("Event","SELECT title,event_type,description FROM events WHERE title LIKE ? OR event_type LIKE ? OR description LIKE ? LIMIT 20"),
        ("Business","SELECT business_name,category,description FROM businesses WHERE business_name LIKE ? OR category LIKE ? OR description LIKE ? LIMIT 20"),
        ("Product","SELECT product_name,category,description FROM products WHERE product_name LIKE ? OR category LIKE ? OR description LIKE ? LIMIT 20"),
    ]
    for label, sql in queries:
        for r in conn.execute(sql, (like,like,like) if label!="Culture" else (like,like)):
            vals=list(r)
            results.append((label, vals[0], vals[1], vals[2]))
    conn.close()
    content+="<div class='card'><h2>Results</h2>"
    if not results: content+="<p>No results yet.</p>"
    for section,title,typ,text in results: content+=f"<div class='card'><b>{h(section)}: {h(title)}</b><br><span class='green'>{h(typ)}</span><p>{h(text)}</p></div>"
    content+="</div>"; return render(content)

@app.route("/explorer")
def explorer():
    return render("<div class='card hero'><h1>🧭 Explorer</h1><p class='green'>Explore OAP by community, culture, events, artists, business and opportunity.</p></div><div class='grid'><div class='card'><h2>🌍 Community</h2><a href='/community'>Open</a></div><div class='card'><h2>🎵 Culture</h2><a href='/culture'>Open</a></div><div class='card'><h2>🎤 Artists</h2><a href='/artists'>Open</a></div><div class='card'><h2>📅 Events</h2><a href='/events'>Open</a></div><div class='card'><h2>🏪 Business</h2><a href='/business'>Open</a></div><div class='card'><h2>🛍 Products</h2><a href='/products'>Open</a></div></div>")

@app.route("/command_center")
@app.route("/dashboard")
def command_center():
    conn=db()
    total=conn.execute("SELECT COALESCE(SUM(amount),0) c FROM opportunities").fetchone()["c"]
    pending=conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='pending'").fetchone()["c"]
    paid=conn.execute("SELECT COALESCE(SUM(amount),0) c FROM payouts WHERE status='paid'").fetchone()["c"]
    members=conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    businesses=conn.execute("SELECT COUNT(*) c FROM businesses").fetchone()["c"]
    products=conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
    conn.close()
    return render(f"<div class='card hero'><h1>🎯 Command Center</h1></div><div class='grid'><div class='card'><h2>{members}</h2><p>Members</p></div><div class='card'><h2>{businesses}</h2><p>Businesses</p></div><div class='card'><h2>{products}</h2><p>Products</p></div><div class='card'><h2>£{total:.2f}</h2><p>Opportunity Board</p></div><div class='card'><h2>£{pending:.2f}</h2><p>Pending Payouts</p></div><div class='card'><h2>£{paid:.2f}</h2><p>Paid Payouts</p></div></div>")

@app.route("/routes")
def routes():
    links=sorted(set(str(r.rule) for r in app.url_map.iter_rules() if "GET" in r.methods))
    content="<div class='card hero'><h1>🧪 Route Checker</h1></div><div class='card'>"
    for link in links: content+=f"<p><a href='{h(link)}'>{h(link)}</a></p>"
    return render(content+"</div>")

@app.route("/admin")
def admin():
    conn=db(); users=conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 80").fetchall(); logs=conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall(); conn.close()
    content="<div class='card hero'><h1>⚙ Admin</h1></div><div class='card'><h2>Members</h2>"
    for m in users: content+=f"<div class='card'>@{h(m['username'])} — {h(m['verification_level'])}<br>{h(m['postcode'])} → {h(m['country'])}</div>"
    content+="</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs: content+=f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    return render(content+"</div>")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
