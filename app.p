from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "oap_public.db"

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            username TEXT,
            email TEXT,
            postcode TEXT,
            borough TEXT,
            country TEXT,
            circle TEXT DEFAULT 'Community Member',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            message TEXT NOT NULL,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

BASE = """
<!doctype html>
<html>
<head>
  <title>ON ANY POSTCODE</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body{margin:0;font-family:Arial;background:#07120c;color:#fff}
    header{padding:20px;background:#0b1f13;border-bottom:1px solid #1f7a3a}
    nav a{color:#d7ffd7;margin:0 8px;text-decoration:none;font-weight:bold}
    .hero{padding:45px 20px;text-align:center;background:linear-gradient(135deg,#0b1f13,#123d22)}
    .hero h1{font-size:38px;margin:0}
    .hero p{font-size:18px;color:#d7ffd7}
    .btn{display:inline-block;background:#23c55e;color:#041007;padding:12px 18px;margin:8px;border-radius:10px;text-decoration:none;font-weight:bold}
    .btn2{display:inline-block;border:1px solid #23c55e;color:#d7ffd7;padding:12px 18px;margin:8px;border-radius:10px;text-decoration:none}
    .wrap{max-width:1100px;margin:auto;padding:20px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
    .card{background:#0b1f13;border:1px solid #1f7a3a;border-radius:14px;padding:18px}
    input,select,textarea{width:100%;padding:12px;margin:8px 0;border-radius:8px;border:0}
    button{background:#23c55e;color:#041007;border:0;padding:12px 18px;border-radius:10px;font-weight:bold}
    footer{text-align:center;padding:25px;color:#b8d8bf}
    .signal{color:#23c55e;font-weight:bold}
  </style>
</head>
<body>
<header>
  <b>🌍 ON ANY POSTCODE</b>
  <nav>
    <a href="/">Home</a>
    <a href="/join">Join OAP</a>
    <a href="/news">News</a>
    <a href="/events">Events</a>
    <a href="/culture">Culture</a>
    <a href="/music">Music</a>
    <a href="/businesses">Businesses</a>
    <a href="/market">Market</a>
    <a href="/explorer">Explorer</a>
    <a href="/privacy">Privacy</a>
  </nav>
</header>
{{content|safe}}
<footer>
  Born Local. Built Global. Earth is our turf. 💚
</footer>
</body>
</html>
"""

def page(content):
    return render_template_string(BASE, content=content)

@app.route("/")
def home():
    return page("""
    <section class="hero">
      <h1>🌍 ON ANY POSTCODE</h1>
      <p>Community. Culture. Business. Music. Events. Trust.</p>
      <p class="signal">Public first. Trust second. Money later. Experiments isolated always.</p>
      <a class="btn" href="/join">Join OAP</a>
      <a class="btn2" href="/enter">Enter My World</a>
    </section>

    <div class="wrap">
      <h2>Public Front Door</h2>
      <div class="grid">
        <div class="card"><h3>📰 News</h3><p>Community-safe updates, culture, sports, opportunities.</p><a class="btn2" href="/news">Open</a></div>
        <div class="card"><h3>🎪 Events</h3><p>Gatherings, meetups, experiences, local missions.</p><a class="btn2" href="/events">Open</a></div>
        <div class="card"><h3>🎭 Culture</h3><p>Every postcode has a story. Every culture has a song.</p><a class="btn2" href="/culture">Open</a></div>
        <div class="card"><h3>🎵 Music</h3><p>OAP-owned music destination. Cleared media only.</p><a class="btn2" href="/music">Open</a></div>
        <div class="card"><h3>🏪 Businesses</h3><p>Local listings and future promotion packages.</p><a class="btn2" href="/businesses">Open</a></div>
        <div class="card"><h3>🛒 Market</h3><p>OAP commerce preview before full Market engine.</p><a class="btn2" href="/market">Open</a></div>
      </div>
    </div>
    """)

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        conn = db()
        conn.execute("""
            INSERT INTO members
            (nickname, username, email, postcode, borough, country, circle, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("nickname"),
            request.form.get("username"),
            request.form.get("email"),
            request.form.get("postcode"),
            request.form.get("borough"),
            request.form.get("country"),
            request.form.get("circle"),
            datetime.now().isoformat(timespec="seconds")
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("welcome"))

    return page("""
    <div class="wrap">
      <h1>👑 Join OAP</h1>
      <p>Create your public OAP identity. Keep it light, safe, and launch-ready.</p>
      <form method="post">
        <input name="nickname" placeholder="Nickname" required>
        <input name="username" placeholder="Username">
        <input name="email" placeholder="Email optional">
        <input name="postcode" placeholder="Postcode">
        <input name="borough" placeholder="Borough">
        <input name="country" placeholder="Country">
        <select name="circle">
          <option>Community Member - Free</option>
          <option>Postcode Founder - £5/month</option>
          <option>Borough Builder - £10/month</option>
          <option>Country Champion - £25/month</option>
        </select>
        <button>Join OAP</button>
      </form>
    </div>
    """)

@app.route("/welcome")
def welcome():
    return page("""
    <div class="wrap">
      <h1>🌍 Your World has been created.</h1>
      <p>Next step: explore OAP or enter My World when private identity features are ready.</p>
      <a class="btn" href="/">Back to OAP World</a>
      <a class="btn2" href="/enter">Enter My World</a>
    </div>
    """)

@app.route("/enter")
def enter():
    return page("""
    <div class="wrap">
      <h1>👤 Enter My World</h1>
      <div class="card">
        <p>This public build keeps My World protected.</p>
        <p>Later this button connects to <b>my.oap.world</b>.</p>
        <p class="signal">Public browsing stays open. Private actions require identity.</p>
      </div>
    </div>
    """)

@app.route("/news")
def news():
    return simple("📰 OAP News", "Human-centered news: community, culture, sports, opportunities, businesses, creators, and safe awareness.")

@app.route("/events")
def events():
    return simple("🎪 Community Events", "Gatherings, experiences, meetups, matchdays, cultural events, and postcode missions.")

@app.route("/culture")
def culture():
    return simple("🎭 Culture", "Every postcode has a story. Every culture has a song. Every community has a voice.")

@app.route("/music")
def music():
    return simple("🎵 OAP Music", "First-party artist pages, release pages, playlists, culture songs, and cleared media only.")

@app.route("/creators")
def creators():
    return simple("🎨 Creators", "Creator profiles, promotion, awards, media links, and future monetization tools.")

@app.route("/businesses")
def businesses():
    return simple("🏪 Businesses", "Local business discovery, promo slots, trusted listings, and postcode commerce.")

@app.route("/market")
def market():
    return simple("🛒 OAP Market", "Public preview for products, merch, creator goods, business offers, and future checkout.")

@app.route("/explorer")
def explorer():
    return simple("🧭 Explorer", "Search by postcode, borough, country, culture, creator, business, event, and opportunity.")

@app.route("/weather")
def weather():
    return simple("🌦 Weather Preview", "Public weather preview only. Full maps/navigation should stay separate later.")

@app.route("/sika")
def sika():
    return simple("💎 SIKA", "SIKA starts as trust, contribution, and value records. Not bank money, not legal tender, not investment.")

@app.route("/privacy")
def privacy():
    return page("""
    <div class="wrap">
      <h1>🛡 Privacy & Trust</h1>
      <div class="card">
        <p>Your data belongs to you.</p>
        <p>Your profile belongs to you.</p>
        <p>Your content belongs to you.</p>
        <p>Your messages belong to you.</p>
        <p>Your culture belongs to you.</p>
        <p>Your business belongs to you.</p>
      </div>
      <div class="card">
        <h3>OAP Safety Rule</h3>
        <p>No hidden selling of member data. No unnecessary personal information. No money claims without compliance.</p>
      </div>
    </div>
    """)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        conn = db()
        conn.execute("""
            INSERT INTO messages (name, email, message, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            request.form.get("name"),
            request.form.get("email"),
            request.form.get("message"),
            datetime.now().isoformat(timespec="seconds")
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return page("""
    <div class="wrap">
      <h1>📨 Contact OAP</h1>
      <form method="post">
        <input name="name" placeholder="Name" required>
        <input name="email" placeholder="Email">
        <textarea name="message" placeholder="Message" required></textarea>
        <button>Send</button>
      </form>
    </div>
    """)

def simple(title, text):
    return page(f"""
    <div class="wrap">
      <h1>{title}</h1>
      <div class="card">
        <p>{text}</p>
      </div>
      <a class="btn" href="/join">Join OAP</a>
      <a class="btn2" href="/">Back Home</a>
    </div>
    """)

@app.route("/admin-public")
def admin_public():
    conn = db()
    members = conn.execute("SELECT * FROM members ORDER BY id DESC LIMIT 50").fetchall()
    messages = conn.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()

    member_rows = "".join([
        f"<tr><td>{m['nickname']}</td><td>{m['username'] or ''}</td><td>{m['postcode'] or ''}</td><td>{m['circle']}</td><td>{m['created_at']}</td></tr>"
        for m in members
    ])

    message_rows = "".join([
        f"<tr><td>{x['name']}</td><td>{x['email'] or ''}</td><td>{x['message']}</td><td>{x['created_at']}</td></tr>"
        for x in messages
    ])

    return page(f"""
    <div class="wrap">
      <h1>👑 Public Launch Records</h1>
      <p>This is temporary local admin. Do not expose publicly without PIN/login.</p>

      <h2>Members</h2>
      <div class="card">
        <table width="100%" border="1" cellpadding="6">
          <tr><th>Nickname</th><th>Username</th><th>Postcode</th><th>Circle</th><th>Joined</th></tr>
          {member_rows}
        </table>
      </div>

      <h2>Messages</h2>
      <div class="card">
        <table width="100%" border="1" cellpadding="6">
          <tr><th>Name</th><th>Email</th><th>Message</th><th>Date</th></tr>
          {message_rows}
        </table>
      </div>
    </div>
    """)

if __name__ == "__main__":
    print("🌍 OAP Public Front Door running")
    print("Open: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
