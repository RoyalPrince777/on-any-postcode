from flask import Flask, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "oap_public_live.db"

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
    conn.execute("CREATE TABLE IF NOT EXISTS fun(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, body TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS businesses(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, postcode TEXT, contact TEXT, body TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS creators(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, skill TEXT, postcode TEXT, link TEXT, bio TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS experiences(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, area TEXT, date_text TEXT, body TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS missions(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, area TEXT, body TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS contacts(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, contact TEXT, reason TEXT, body TEXT, created_at TEXT)")
    conn.commit()
    conn.close()

setup()

def layout(body):
    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ON ANY POSTCODE</title>
<style>
body{{font-family:Arial;background:#06120b;color:white;margin:0}}
header{{background:#0b2414;padding:18px;border-bottom:1px solid #22c55e}}
a{{color:#9fffb9;margin-right:12px;font-weight:bold}}
.wrap{{padding:18px;max-width:950px;margin:auto}}
.card{{background:#0b2414;border:1px solid #22c55e;border-radius:14px;padding:15px;margin:12px 0}}
input,textarea,select{{width:100%;padding:12px;margin:7px 0;border-radius:9px;border:0}}
button{{background:#22c55e;color:#031008;padding:12px 16px;border:0;border-radius:10px;font-weight:bold}}
</style>
</head>
<body>
<header>
<h2>🌍 ON ANY POSTCODE</h2>
<a href="/">OAP World</a>
<a href="/join">Join</a>
<a href="/fun">Fun</a>
<a href="/business">Business</a>
<a href="/creator">Creator</a>
<a href="/experience">Experiences</a>
<a href="/mission">Missions</a>
<a href="/members">Members</a>
<a href="/contact">Contact</a>
</header>
<div class="wrap">{body}</div>
</body>
</html>
"""

def save(table, fields, values):
    conn = db()
    q = ",".join(fields)
    marks = ",".join(["?"] * len(values))
    conn.execute(f"INSERT INTO {table}({q}) VALUES({marks})", values)
    conn.commit()
    conn.close()

def list_cards(table, title, emoji, title_col, body_col):
    conn = db()
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()
    conn.close()
    cards = ""
    for r in rows:
        cards += f"<div class='card'><h2>{emoji} {r[title_col]}</h2><p>{r[body_col]}</p><small>{r['created_at']}</small></div>"
    return layout(f"<h1>{emoji} {title}</h1>{cards or '<div class=card>Nothing here yet.</div>'}")

@app.route("/")
def home():
    return layout("""
<h1>🌍 OAP World</h1>
<p>Born Local. Built Global. Earth is our turf.</p>
<p>Every postcode has a story. Every community has a voice. Every member has a world.</p>

<a href="/join"><button>Join OAP</button></a>
<a href="/fun"><button>😂 Add Humor</button></a>
<a href="/business"><button>🏪 Add Business</button></a>
<a href="/creator"><button>👤 Add Creator</button></a>
<a href="/experience"><button>🎪 Add Experience</button></a>

<div class="card"><h2>⚡ Mission</h2><p>First member. First business. First creator. First experience. First value created.</p></div>
""")

@app.route("/join", methods=["GET","POST"])
def join():
    if request.method == "POST":
        save("members", ["name","postcode","country","created_at"], [request.form["name"], request.form.get("postcode",""), request.form.get("country",""), now()])
        return redirect(url_for("members"))
    return layout("""
<h1>👑 Join OAP</h1>
<form method="post" class="card">
<input name="name" placeholder="Name / nickname" required>
<input name="postcode" placeholder="Postcode">
<input name="country" placeholder="Country">
<button>Join OAP</button>
</form>
""")

@app.route("/members")
def members():
    return list_cards("members", "Members", "👥", "name", "postcode")

@app.route("/fun", methods=["GET","POST"])
def fun():
    if request.method == "POST":
        save("fun", ["name","category","body","created_at"], [request.form["name"], request.form["category"], request.form["body"], now()])
        return redirect(url_for("fun"))
    return layout("""
<h1>😂 OAP Fun Zone</h1>
<form method="post" class="card">
<input name="name" placeholder="Your name" required>
<select name="category">
<option>😂 Joke of the Day</option>
<option>🤣 Postcode Banter</option>
<option>🎭 Funny Story</option>
<option>⚽ Football Humor</option>
<option>🎵 Music Humor</option>
<option>🏪 Business Banter</option>
<option>👑 Royal Banter</option>
</select>
<textarea name="body" placeholder="Write something funny but respectful..." required></textarea>
<button>Add Laugh</button>
</form>
<a href="/fun/list"><button>View Laughs</button></a>
""")

@app.route("/fun/list")
def fun_list():
    return list_cards("fun", "Community Laughs", "😂", "category", "body")

@app.route("/business", methods=["GET","POST"])
def business():
    if request.method == "POST":
        save("businesses", ["name","category","postcode","contact","body","created_at"], [request.form["name"], request.form.get("category",""), request.form.get("postcode",""), request.form.get("contact",""), request.form["body"], now()])
        return redirect(url_for("business_list"))
    return layout("""
<h1>🏪 Business Network</h1>
<form method="post" class="card">
<input name="name" placeholder="Business name" required>
<input name="category" placeholder="Category">
<input name="postcode" placeholder="Postcode">
<input name="contact" placeholder="Contact / website / social">
<textarea name="body" placeholder="What does this business offer?" required></textarea>
<button>Add Business</button>
</form>
<a href="/business/list"><button>View Businesses</button></a>
""")

@app.route("/business/list")
def business_list():
    return list_cards("businesses", "Business Network", "🏪", "name", "body")

@app.route("/creator", methods=["GET","POST"])
def creator():
    if request.method == "POST":
        save("creators", ["name","skill","postcode","link","bio","created_at"], [request.form["name"], request.form.get("skill",""), request.form.get("postcode",""), request.form.get("link",""), request.form["bio"], now()])
        return redirect(url_for("creator_list"))
    return layout("""
<h1>👤 Creator Hub</h1>
<form method="post" class="card">
<input name="name" placeholder="Creator name" required>
<input name="skill" placeholder="Music / Comedy / Sport / Art / Fashion">
<input name="postcode" placeholder="Postcode">
<input name="link" placeholder="Link / social">
<textarea name="bio" placeholder="Creator story" required></textarea>
<button>Add Creator</button>
</form>
<a href="/creator/list"><button>View Creators</button></a>
""")

@app.route("/creator/list")
def creator_list():
    return list_cards("creators", "Creator Hub", "👤", "name", "bio")

@app.route("/experience", methods=["GET","POST"])
def experience():
    if request.method == "POST":
        save("experiences", ["title","area","date_text","body","created_at"], [request.form["title"], request.form.get("area",""), request.form.get("date_text",""), request.form["body"], now()])
        return redirect(url_for("experience_list"))
    return layout("""
<h1>🎪 Community Experiences</h1>
<form method="post" class="card">
<input name="title" placeholder="Experience title" required>
<input name="area" placeholder="Postcode / Borough / Country">
<input name="date_text" placeholder="Date / time">
<textarea name="body" placeholder="Experience details" required></textarea>
<button>Add Experience</button>
</form>
<a href="/experience/list"><button>View Experiences</button></a>
""")

@app.route("/experience/list")
def experience_list():
    return list_cards("experiences", "Community Experiences", "🎪", "title", "body")

@app.route("/mission", methods=["GET","POST"])
def mission():
    if request.method == "POST":
        save("missions", ["title","area","body","created_at"], [request.form["title"], request.form.get("area",""), request.form["body"], now()])
        return redirect(url_for("mission_list"))
    return layout("""
<h1>⚡ Community Missions</h1>
<form method="post" class="card">
<input name="title" placeholder="Mission title" required>
<input name="area" placeholder="Postcode / Borough / Country">
<textarea name="body" placeholder="Mission details" required></textarea>
<button>Create Mission</button>
</form>
<a href="/mission/list"><button>View Missions</button></a>
""")

@app.route("/mission/list")
def mission_list():
    return list_cards("missions", "Community Missions", "⚡", "title", "body")

@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == "POST":
        save("contacts", ["name","contact","reason","body","created_at"], [request.form["name"], request.form.get("contact",""), request.form.get("reason",""), request.form["body"], now()])
        return redirect(url_for("home"))
    return layout("""
<h1>💌 Contact OAP</h1>
<form method="post" class="card">
<input name="name" placeholder="Name" required>
<input name="contact" placeholder="Email / phone / social">
<select name="reason">
<option>General Contact</option>
<option>Business Interest</option>
<option>Creator Interest</option>
<option>Experience / Event Interest</option>
<option>Partnership</option>
</select>
<textarea name="body" placeholder="Message" required></textarea>
<button>Send Message</button>
</form>
""")

if __name__ == "__main__":
    print("🌍 OAP World running")
    print("Open http://127.0.0.1:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
