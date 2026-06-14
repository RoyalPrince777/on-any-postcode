from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "oap_social_trust.db"

def now():
    return datetime.now().isoformat(timespec="seconds")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        username TEXT,
        postcode TEXT,
        country TEXT,
        created_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_name TEXT,
        post_type TEXT,
        area TEXT,
        title TEXT,
        body TEXT,
        respects INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        body TEXT,
        created_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS contributions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_name TEXT,
        action TEXT,
        area TEXT,
        points INTEGER DEFAULT 1,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()

def contribution(member, action, area="", points=1):
    conn = db()
    conn.execute("""INSERT INTO contributions(member_name, action, area, points, created_at)
                    VALUES (?, ?, ?, ?, ?)""", (member, action, area, points, now()))
    conn.commit()
    conn.close()

def badge(points):
    if points >= 100: return "🌍 Ambassador"
    if points >= 50: return "🏆 Champion"
    if points >= 25: return "🏗 Builder"
    if points >= 10: return "⚡ Contributor"
    return "🌱 New Member"

init_db()

BASE = """
<!doctype html>
<html>
<head>
<title>OAP Social Trust</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#06120b;color:white}
header{background:#0b2414;padding:18px;border-bottom:1px solid #22c55e}
nav a{color:#d7ffd7;margin:5px;text-decoration:none;font-weight:bold;display:inline-block}
.wrap{max-width:1000px;margin:auto;padding:18px}
.hero{text-align:center;padding:40px 18px;background:linear-gradient(135deg,#0b2414,#15552d)}
.card{background:#0b2414;border:1px solid #22c55e;border-radius:14px;padding:16px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
input,textarea,select{width:100%;padding:12px;margin:7px 0;border:0;border-radius:9px}
button,.btn{display:inline-block;background:#22c55e;color:#031008;padding:11px 15px;border:0;border-radius:10px;text-decoration:none;font-weight:bold}
.btn2{display:inline-block;border:1px solid #22c55e;color:#d7ffd7;padding:10px 14px;border-radius:10px;text-decoration:none}
small{color:#b8d8bf}
</style>
</head>
<body>
<header>
<b>🌍 ON ANY POSTCODE SOCIAL</b><br>
<nav>
<a href="/">Community Feed</a>
<a href="/join">Join OAP</a>
<a href="/post">Create Update</a>
<a href="/members">Members</a>
<a href="/contributions">Contribution Records</a>
<a href="/messages">Messenger</a>
<a href="/metrics">Metrics</a>
</nav>
</header>
{{content|safe}}
</body>
</html>
"""

def page(content):
    return render_template_string(BASE, content=content)

@app.route("/")
def feed():
    conn = db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()

    cards = ""
    for p in posts:
        cards += f"""
        <div class="card">
          <h2>{p['title']}</h2>
          <p><b>{p['post_type']}</b> · {p['area'] or 'OAP World'}</p>
          <p>{p['body']}</p>
          <small>By {p['member_name']} · {p['created_at']}</small><br><br>
          <a class="btn2" href="/respect/{p['id']}/{p['member_name']}">💚 Respect {p['respects']}</a>
        </div>
        """

    return page(f"""
    <section class="hero">
      <h1>🌍 OAP Social</h1>
      <p>Attention → Contribution. Likes → Respect. Followers → Circle. Profiles → My Worlds.</p>
      <a class="btn" href="/join">Join OAP</a>
      <a class="btn2" href="/post">Create Update</a>
    </section>
    <div class="wrap">
      <h2>Community Feed</h2>
      {cards or '<div class="card">No updates yet. Create the first OAP update.</div>'}
    </div>
    """)

@app.route("/join", methods=["GET","POST"])
def join():
    if request.method == "POST":
        name = request.form.get("nickname")
        area = request.form.get("postcode")
        conn = db()
        conn.execute("""INSERT INTO members(nickname, username, postcode, country, created_at)
                        VALUES (?, ?, ?, ?, ?)""", (
            name, request.form.get("username"), area, request.form.get("country"), now()
        ))
        conn.commit()
        conn.close()
        contribution(name, "Joined OAP", area, 5)
        return redirect(url_for("members"))

    return page("""
    <div class="wrap">
      <h1>👑 Join OAP</h1>
      <form method="post">
        <input name="nickname" placeholder="Nickname" required>
        <input name="username" placeholder="Username">
        <input name="postcode" placeholder="Postcode">
        <input name="country" placeholder="Country">
        <button>Join OAP</button>
      </form>
    </div>
    """)

@app.route("/post", methods=["GET","POST"])
def post():
    if request.method == "POST":
        member = request.form.get("member_name")
        area = request.form.get("area")
        conn = db()
        conn.execute("""INSERT INTO posts(member_name, post_type, area, title, body, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)""", (
            member, request.form.get("post_type"), area,
            request.form.get("title"), request.form.get("body"), now()
        ))
        conn.commit()
        conn.close()
        contribution(member, "Created Update", area, 3)
        return redirect(url_for("feed"))

    return page("""
    <div class="wrap">
      <h1>📢 Create OAP Update</h1>
      <form method="post">
        <input name="member_name" placeholder="Your nickname" required>
        <select name="post_type">
          <option>📢 Community Update</option>
          <option>🎵 Music Release</option>
          <option>🏪 Business Offer</option>
          <option>🎪 Experience Invite</option>
          <option>🎭 Culture Story</option>
          <option>⚡ Mission Request</option>
          <option>📰 Good News</option>
          <option>🤝 Opportunity</option>
          <option>💚 Help Needed</option>
          <option>👑 Founder Message</option>
        </select>
        <input name="area" placeholder="Postcode / Borough / Country">
        <input name="title" placeholder="Update title" required>
        <textarea name="body" placeholder="Write your update..." required></textarea>
        <button>Publish Update</button>
      </form>
    </div>
    """)

@app.route("/respect/<int:post_id>/<member>")
def respect(post_id, member):
    conn = db()
    post = conn.execute("SELECT area FROM posts WHERE id=?", (post_id,)).fetchone()
    conn.execute("UPDATE posts SET respects = respects + 1 WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    contribution(member, "Received Respect", post["area"] if post else "", 1)
    return redirect(url_for("feed"))

@app.route("/members")
def members():
    conn = db()
    rows = conn.execute("""
        SELECT m.*, COALESCE(SUM(c.points),0) as points
        FROM members m
        LEFT JOIN contributions c ON c.member_name = m.nickname
        GROUP BY m.id
        ORDER BY m.id DESC
    """).fetchall()
    conn.close()

    cards = "".join([f"""
    <div class="card">
      <h2>👤 {m['nickname']}</h2>
      <p>@{m['username'] or 'oap-member'}</p>
      <p>{m['postcode'] or ''} {m['country'] or ''}</p>
      <p><b>{badge(m['points'])}</b></p>
      <p>⭐ {m['points']} contribution points</p>
      <small>Joined {m['created_at']}</small>
    </div>
    """ for m in rows])

    return page(f"<div class='wrap'><h1>👥 Members</h1><div class='grid'>{cards or '<div class=card>No members yet.</div>'}</div></div>")

@app.route("/contributions")
def contributions():
    conn = db()
    rows = conn.execute("SELECT * FROM contributions ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    cards = "".join([f"""
    <div class="card">
      <h3>🏆 {r['member_name']}</h3>
      <p>{r['action']}</p>
      <p>{r['area'] or 'OAP World'}</p>
      <p>⭐ {r['points']} points</p>
      <small>{r['created_at']}</small>
    </div>
    """ for r in rows])

    return page(f"<div class='wrap'><h1>🏆 Contribution Records</h1><div class='grid'>{cards or '<div class=card>No records yet.</div>'}</div></div>")

@app.route("/messages", methods=["GET","POST"])
def messages():
    if request.method == "POST":
        sender = request.form.get("sender")
        receiver = request.form.get("receiver")
        conn = db()
        conn.execute("""INSERT INTO messages(sender, receiver, body, created_at)
                        VALUES (?, ?, ?, ?)""", (
            sender, receiver, request.form.get("body"), now()
        ))
        conn.commit()
        conn.close()
        contribution(sender, "Sent Message", receiver, 1)
        return redirect(url_for("messages"))

    conn = db()
    rows = conn.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()

    cards = "".join([f"""
    <div class="card">
      <p><b>{m['sender']}</b> to <b>{m['receiver']}</b></p>
      <p>{m['body']}</p>
      <small>{m['created_at']}</small>
    </div>
    """ for m in rows])

    return page(f"""
    <div class="wrap">
      <h1>💬 OAP Messenger v1</h1>
      <form method="post" class="card">
        <input name="sender" placeholder="From" required>
        <input name="receiver" placeholder="To" required>
        <textarea name="body" placeholder="Message" required></textarea>
        <button>Send Message</button>
      </form>
      {cards or '<div class="card">No messages yet.</div>'}
    </div>
    """)

@app.route("/metrics")
def metrics():
    conn = db()
    members = conn.execute("SELECT COUNT(*) c FROM members").fetchone()["c"]
    posts = conn.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
    messages = conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"]
    respects = conn.execute("SELECT COALESCE(SUM(respects),0) c FROM posts").fetchone()["c"]
    points = conn.execute("SELECT COALESCE(SUM(points),0) c FROM contributions").fetchone()["c"]
    conn.close()

    return page(f"""
    <div class="wrap">
      <h1>📊 OAP Social Metrics</h1>
      <div class="grid">
        <div class="card"><h2>{members}</h2><p>Members</p></div>
        <div class="card"><h2>{posts}</h2><p>Updates</p></div>
        <div class="card"><h2>{messages}</h2><p>Messages</p></div>
        <div class="card"><h2>{respects}</h2><p>Respect Given</p></div>
        <div class="card"><h2>{points}</h2><p>Value Created Points</p></div>
      </div>
    </div>
    """)

if __name__ == "__main__":
    print("🌍 OAP Social Trust running")
    print("Open http://127.0.0.1:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
