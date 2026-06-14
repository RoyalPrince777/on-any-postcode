from flask import Flask, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "oap_public.db"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def setup():
    conn = db()
    conn.execute("CREATE TABLE IF NOT EXISTS members(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, postcode TEXT, country TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, title TEXT, body TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS missions(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, area TEXT, body TEXT, created_at TEXT)")
    conn.commit()
    conn.close()

setup()

def layout(body):
    return f"""
    <html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ON ANY POSTCODE</title>
    <style>
    body{{font-family:Arial;background:#06120b;color:white;margin:0}}
    header{{background:#0b2414;padding:18px;border-bottom:1px solid #22c55e}}
    a{{color:#9fffb9;margin-right:12px;font-weight:bold}}
    .wrap{{padding:18px;max-width:900px;margin:auto}}
    .card{{background:#0b2414;border:1px solid #22c55e;border-radius:14px;padding:15px;margin:12px 0}}
    input,textarea{{width:100%;padding:12px;margin:7px 0;border-radius:9px;border:0}}
    button{{background:#22c55e;color:#031008;padding:12px 16px;border:0;border-radius:10px;font-weight:bold}}
    </style></head><body>
    <header>
    <h2>🌍 ON ANY POSTCODE</h2>
    <a href="/">Feed</a>
    <a href="/join">Join</a>
    <a href="/post">Post</a>
    <a href="/mission">Mission</a>
    <a href="/members">Members</a>
    </header>
    <div class="wrap">{body}</div>
    </body></html>
    """

@app.route("/")
def home():
    conn = db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    missions = conn.execute("SELECT * FROM missions ORDER BY id DESC").fetchall()
    conn.close()

    post_cards = "".join([f"<div class='card'><h2>{p['title']}</h2><p>{p['body']}</p><small>By {p['name']} · {p['created_at']}</small></div>" for p in posts])
    mission_cards = "".join([f"<div class='card'><h2>⚡ {m['title']}</h2><p>{m['body']}</p><small>{m['area']} · {m['created_at']}</small></div>" for m in missions])

    return layout(f"""
    <h1>🌍 OAP Public World</h1>
    <p>Born Local. Built Global. Earth is our turf.</p>
    <a href="/join"><button>Join OAP</button></a>
    <a href="/post"><button>Create Post</button></a>
    <a href="/mission"><button>Create Mission</button></a>
    <h2>📢 Community Feed</h2>
    {post_cards or "<div class='card'>No posts yet.</div>"}
    <h2>⚡ Community Missions</h2>
    {mission_cards or "<div class='card'>No missions yet.</div>"}
    """)

@app.route("/join", methods=["GET","POST"])
def join():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO members(name, postcode, country, created_at) VALUES(?,?,?,?)",
            (request.form["name"], request.form.get("postcode",""), request.form.get("country",""), now()))
        conn.commit()
        conn.close()
        return redirect(url_for("members"))
    return layout("""
    <h1>👑 Join OAP</h1>
    <form method="post">
    <input name="name" placeholder="Name / nickname" required>
    <input name="postcode" placeholder="Postcode">
    <input name="country" placeholder="Country">
    <button>Join OAP</button>
    </form>
    """)

@app.route("/post", methods=["GET","POST"])
def post():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO posts(name, title, body, created_at) VALUES(?,?,?,?)",
            (request.form["name"], request.form["title"], request.form["body"], now()))
        conn.commit()
        conn.close()
        return redirect(url_for("home"))
    return layout("""
    <h1>📢 Create Post</h1>
    <form method="post">
    <input name="name" placeholder="Your name" required>
    <input name="title" placeholder="Title" required>
    <textarea name="body" placeholder="Message" required></textarea>
    <button>Publish</button>
    </form>
    """)

@app.route("/mission", methods=["GET","POST"])
def mission():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO missions(title, area, body, created_at) VALUES(?,?,?,?)",
            (request.form["title"], request.form.get("area",""), request.form["body"], now()))
        conn.commit()
        conn.close()
        return redirect(url_for("home"))
    return layout("""
    <h1>⚡ Create Community Mission</h1>
    <form method="post">
    <input name="title" placeholder="Mission title" required>
    <input name="area" placeholder="Postcode / Borough / Country">
    <textarea name="body" placeholder="Mission details" required></textarea>
    <button>Create Mission</button>
    </form>
    """)

@app.route("/members")
def members():
    conn = db()
    rows = conn.execute("SELECT * FROM members ORDER BY id DESC").fetchall()
    conn.close()
    cards = "".join([f"<div class='card'><h2>👤 {m['name']}</h2><p>{m['postcode']} {m['country']}</p><small>Joined {m['created_at']}</small></div>" for m in rows])
    return layout(f"<h1>👥 Members</h1>{cards or '<div class=card>No members yet.</div>'}")

if __name__ == "__main__":
    print("🌍 OAP running")
    print("Open http://127.0.0.1:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
