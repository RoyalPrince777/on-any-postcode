from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
ADMIN_USERNAME = "N24-7"
ADMIN_EMAIL = "earthisourturf777@gmail.com"
ADMIN_PASSWORD = "2525"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def h(x):
    return escape(str(x or ""))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def add_col(cur, table, col, coltype):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")

def log(action, username="system"):
    conn = db()
    conn.execute(
        "INSERT INTO audit_logs(action, username, created_at) VALUES(?,?,?)",
        (action, username, now())
    )
    conn.commit()
    conn.close()

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'member',
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS news_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        category TEXT,
        summary TEXT,
        body TEXT,
        source_note TEXT,
        verification_status TEXT DEFAULT 'needs review',
        country TEXT DEFAULT 'Global',
        city TEXT DEFAULT '',
        postcode TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        status TEXT DEFAULT 'approved',
        created_at TEXT
    )
    """)

    for col, typ in [
        ("source_note", "TEXT"),
        ("verification_status", "TEXT DEFAULT 'needs review'"),
        ("country", "TEXT DEFAULT 'Global'"),
        ("city", "TEXT DEFAULT ''"),
        ("postcode", "TEXT DEFAULT ''"),
        ("views", "INTEGER DEFAULT 0"),
        ("status", "TEXT DEFAULT 'approved'")
    ]:
        add_col(cur, "news_posts", col, typ)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hrm_match_reports(
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
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events(
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
        status TEXT DEFAULT 'pending',
        views INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )
    """)

    cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,))
    user = cur.fetchone()

    if user:
        cur.execute(
            "UPDATE users SET email=?, password=?, role=? WHERE username=?",
            (ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", ADMIN_USERNAME)
        )
    else:
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
.wrap{padding:18px;max-width:1100px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:18px;margin:15px 0}
.hero{text-align:center;padding:35px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:12px;margin:8px 0;background:#0c0c0c;color:white;border:1px solid #333;border-radius:10px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:10px;padding:12px 18px;font-weight:800}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:5px 9px;border-radius:999px;font-size:12px;font-weight:bold}
pre{white-space:pre-wrap;font-family:Arial}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/hrm_match_scanner">HRM Match Scanner</a>
<a href="/hrm_quick_arsenal">Quick Arsenal Report</a>
<a href="/match_reports">Match Reports</a>
<a href="/news">News</a>
<a href="/events">Events</a>
<a href="/worldcup">Football Hub</a>
<a href="/admin">HRM Admin</a>
</div>
</div>
<div class="wrap">
{{content|safe}}
</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def create_match_news(data, username="HRM"):
    body = f"""
MATCH:
{data['match_title']}

COMPETITION:
{data['competition']}

TEAMS:
{data['teams']}

SCORE / RESULT NOTE:
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
Value comes from attendance, participation, product clicks, orders, revenue, repeat engagement, trust records and real-world outcomes.

SWOT:
Strength: {data['swot_strength']}
Weakness: {data['swot_weakness']}
Opportunity: {data['swot_opportunity']}
Threat: {data['swot_threat']}
"""

    conn = db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO news_posts(username,title,category,summary,body,source_note,verification_status,country,city,postcode,views,status,created_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        username,
        data["headline"],
        "Football / HRM Match Report",
        data["summary"],
        body,
        data["source_note"],
        "needs review",
        "Global",
        "",
        "",
        0,
        "approved",
        now()
    ))

    news_id = cur.lastrowid

    cur.execute("""
    INSERT INTO hrm_match_reports(
        username, match_title, competition, teams, score, goals, match_status,
        source_note, tactical_notes, community_opportunity, monetization_note,
        swot_strength, swot_weakness, swot_opportunity, swot_threat,
        news_post_id, created_at
    )
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        username,
        data["match_title"],
        data["competition"],
        data["teams"],
        data["score"],
        data["goals"],
        data["match_status"],
        data["source_note"],
        data["tactical_notes"],
        data["community_opportunity"],
        data["monetization_note"],
        data["swot_strength"],
        data["swot_weakness"],
        data["swot_opportunity"],
        data["swot_threat"],
        news_id,
        now()
    ))

    conn.commit()
    conn.close()

    log("HRM generated match news", username)
    return news_id

@app.route("/")
def home():
    conn = db()
    news = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 8").fetchall()
    reports = conn.execute("SELECT * FROM hrm_match_reports ORDER BY id DESC LIMIT 4").fetchall()
    events = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 4").fetchall()
    conn.close()

    content = """
    <div class='card hero'>
    <h1>🌍 ON ANY POSTCODE 👑</h1>
    <p class='green'>HRM Match News Scanner</p>
    <p>Views are observation. Value is participation, orders, revenue, trust, and community.</p>
    </div>
    <div class='card'>
    <h2>Quick Actions</h2>
    <a class='badge' href='/hrm_quick_arsenal'>Generate PSG vs Arsenal HRM News</a>
    <a class='badge' href='/hrm_match_scanner'>Open Scanner</a>
    </div>
    <div class='card'><h2>Latest News</h2>
    """

    for n in news:
        content += f"""
        <div class='card'>
        <b>{h(n['title'])}</b><br>
        <span class='gold'>{h(n['category'])}</span>
        <p>{h(n['summary'])}</p>
        <a href='/news/{n['id']}'>Read</a>
        </div>
        """

    content += "</div><div class='card'><h2>Match Reports</h2>"

    for r in reports:
        content += f"""
        <div class='card'>
        <b>{h(r['match_title'])}</b>
        <p>{h(r['score'])}</p>
        <a href='/news/{r['news_post_id']}'>Open News</a>
        </div>
        """

    content += "</div><div class='card'><h2>Events</h2>"

    for e in events:
        content += f"""
        <div class='card'>
        <b>{h(e['title'])}</b><br>
        {h(e['event_date'])} {h(e['event_time'])}
        </div>
        """

    content += "</div>"
    return render(content)

@app.route("/login", methods=["GET", "POST"])
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
    <div class='card'>
    <h2>Login</h2>
    <form method='POST'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button>Login</button>
    </form>
    <p class='small'>Default local admin: N24-7 / 2525</p>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/hrm_quick_arsenal")
def hrm_quick_arsenal():
    data = {
        "headline": "PSG vs Arsenal Final Shows How Football Energy Can Build Community Beyond The Scoreline",
        "summary": "HRM records PSG vs Arsenal as a high-attention football event with strong potential for OAP News, creator reactions, watch parties, retail, business promotion and community growth.",
        "match_title": "PSG vs Arsenal Champions League Final",
        "competition": "UEFA Champions League Final",
        "teams": "Paris Saint-Germain vs Arsenal",
        "score": "Completed — verify official final score before making final-result claim",
        "goals": "Kai Havertz and Ousmane Dembélé were reported as major scoring moments in live coverage.",
        "match_status": "Completed / post-event review",
        "source_note": "Use official UEFA or trusted sports sources before publishing final winner or exact final score. This HRM report is a community intelligence record.",
        "tactical_notes": "Arsenal showed structure, defensive discipline and direct attacking threat. PSG showed possession, pressure and attacking quality.",
        "community_opportunity": "Create football news, watch-party records, creator debates, business promos, merchandise campaigns and future event planning.",
        "monetization_note": "Views are not monetization. Real value comes from attendance, product clicks, orders, food, business promotion, signups and repeat participation.",
        "swot_strength": "Global attention and strong fan emotion.",
        "swot_weakness": "No revenue unless connected to products, events, business offers, signups or trust records.",
        "swot_opportunity": "Turn football attention into OAP community activity, World Cup Hub growth and local commerce.",
        "swot_threat": "Fake scores, copyright misuse, overclaiming, and chasing views instead of value."
    }

    news_id = create_match_news(data, session.get("user", "HRM"))
    return redirect(f"/news/{news_id}")

@app.route("/hrm_match_scanner", methods=["GET", "POST"])
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
    <p class='green'>Turn real games into OAP News + HRM learning records.</p>
    </div>

    <div class='card'>
    <form method='POST'>
    <input name='headline' placeholder='Headline' value='Football Final Creates Community Energy Beyond The Scoreline' required>
    <textarea name='summary'>HRM records this match as a high-attention football event with community, creator, business, event and retail potential.</textarea>
    <input name='match_title' value='PSG vs Arsenal Champions League Final' required>
    <input name='competition' value='UEFA Champions League Final'>
    <input name='teams' value='PSG vs Arsenal'>
    <input name='score' value='Completed — verify official final score before final-result claim'>
    <textarea name='goals'>Kai Havertz and Ousmane Dembélé were reported as key scoring moments.</textarea>
    <input name='match_status' value='Completed / post-event review'>
    <textarea name='source_note'>Verify final score using official or trusted sports sources before publishing final winner.</textarea>
    <textarea name='tactical_notes'>Arsenal showed structure and discipline. PSG showed possession, pressure and attacking quality.</textarea>
    <textarea name='community_opportunity'>Watch parties, creator debates, local business promotions, football news and merch drops.</textarea>
    <textarea name='monetization_note'>Views are not monetization. Real value comes from attendance, product clicks, orders, business promotion and trust records.</textarea>
    <input name='swot_strength' value='Global football attention'>
    <input name='swot_weakness' value='No revenue without offers, events, products or participation'>
    <input name='swot_opportunity' value='Convert football attention into OAP community activity'>
    <input name='swot_threat' value='Fake scores, copyright misuse and vanity metrics'>
    <button>Generate HRM News Record</button>
    </form>
    </div>
    """)

@app.route("/match_reports")
def match_reports():
    conn = db()
    rows = conn.execute("SELECT * FROM hrm_match_reports ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = "<div class='card hero'><h1>⚽ HRM Match Reports</h1></div>"

    for r in rows:
        content += f"""
        <div class='card'>
        <b>{h(r['match_title'])}</b><br>
        <span class='gold'>{h(r['competition'])}</span>
        <p>{h(r['score'])}</p>
        <a href='/news/{r['news_post_id']}'>Open News Record</a>
        </div>
        """

    return render(content)

@app.route("/news", methods=["GET", "POST"])
def news():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""
        INSERT INTO news_posts(username,title,category,summary,body,source_note,verification_status,country,city,postcode,views,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            username,
            request.form["title"],
            request.form["category"],
            request.form["summary"],
            request.form["body"],
            request.form["source_note"],
            request.form["verification_status"],
            request.form["country"],
            request.form["city"],
            request.form["postcode"],
            0,
            "pending",
            now()
        ))
        conn.commit()
        conn.close()
        log("News submitted", username)
        return redirect("/news")

    conn = db()
    rows = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card'>
    <h1>📰 OAP News</h1>
    <form method='POST'>
    <input name='title' placeholder='Title' required>
    <input name='category' value='Community'>
    <input name='country' value='Global'>
    <input name='city' placeholder='City'>
    <input name='postcode' placeholder='Postcode'>
    <textarea name='summary' placeholder='Summary'></textarea>
    <textarea name='body' placeholder='Story'></textarea>
    <textarea name='source_note' placeholder='Source/proof note'></textarea>
    <select name='verification_status'>
    <option>needs review</option>
    <option>verified</option>
    <option>draft</option>
    </select>
    <button>Submit News</button>
    </form>
    </div>
    """

    for n in rows:
        content += f"""
        <div class='card'>
        <b>{h(n['title'])}</b><br>
        <span class='gold'>{h(n['category'])}</span>
        <p>{h(n['summary'])}</p>
        <a href='/news/{n['id']}'>Read</a>
        </div>
        """

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

    return render(f"""
    <div class='card'>
    <h1>{h(n['title'])}</h1>
    <p class='gold'>{h(n['category'])}</p>
    <p class='small'>{h(n['country'])} {h(n['city'])} {h(n['postcode'])} • Views: {h(n['views'])}</p>
    <h2>{h(n['summary'])}</h2>
    <pre>{h(n['body'])}</pre>
    <div class='card'>
    <h2>Verification</h2>
    <p>{h(n['source_note'])}</p>
    <p>Status: {h(n['verification_status'])}</p>
    </div>
    </div>
    """)

@app.route("/events", methods=["GET", "POST"])
def events():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""
        INSERT INTO events(username,title,event_type,category,country_focus,postcode,city,country,venue,event_date,event_time,description,ticket_price,capacity,contact,status,views,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            username,
            request.form["title"],
            request.form["event_type"],
            request.form["category"],
            request.form["country_focus"],
            request.form["postcode"],
            request.form["city"],
            request.form["country"],
            request.form["venue"],
            request.form["event_date"],
            request.form["event_time"],
            request.form["description"],
            request.form["ticket_price"],
            request.form["capacity"],
            request.form["contact"],
            "pending",
            0,
            now()
        ))
        conn.commit()
        conn.close()
        log("Event submitted", username)
        return redirect("/events")

    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    content = """
    <div class='card'>
    <h1>⚽ Events / Watch Parties</h1>
    <form method='POST'>
    <input name='title' placeholder='Event title' required>
    <select name='event_type'>
    <option>Watch Party</option>
    <option>Creator Meetup</option>
    <option>Business Popup</option>
    <option>Community Event</option>
    </select>
    <input name='category' value='Football'>
    <input name='country_focus' value='Global'>
    <input name='postcode' placeholder='Postcode'>
    <input name='city' placeholder='City'>
    <input name='country' value='UK'>
    <input name='venue' placeholder='Venue'>
    <input name='event_date' placeholder='Date'>
    <input name='event_time' placeholder='Time'>
    <textarea name='description' placeholder='Description'></textarea>
    <input name='ticket_price' placeholder='Ticket price'>
    <input name='capacity' placeholder='Capacity'>
    <input name='contact' placeholder='Contact'>
    <button>Submit Event</button>
    </form>
    </div>
    """

    for e in rows:
        content += f"""
        <div class='card'>
        <b>{h(e['title'])}</b><br>
        <span class='gold'>{h(e['event_type'])} • {h(e['category'])}</span>
        <p>{h(e['event_date'])} {h(e['event_time'])} • {h(e['city'])}</p>
        <p>{h(e['description'])}</p>
        </div>
        """

    return render(content)

@app.route("/worldcup")
def worldcup():
    conn = db()
    news = conn.execute("""
    SELECT * FROM news_posts
    WHERE category LIKE '%Football%' OR title LIKE '%Arsenal%' OR title LIKE '%PSG%' OR body LIKE '%football%'
    ORDER BY id DESC LIMIT 30
    """).fetchall()

    events = conn.execute("""
    SELECT * FROM events
    WHERE category LIKE '%Football%' OR event_type LIKE '%Watch%'
    ORDER BY id DESC LIMIT 30
    """).fetchall()

    conn.close()

    content = """
    <div class='card hero'>
    <h1>⚽ OAP Football Hub</h1>
    <p class='green'>News → Events → Community → Retail → Trust Records</p>
    </div>
    <div class='card'><h2>Football News</h2>
    """

    for n in news:
        content += f"<div class='card'><b>{h(n['title'])}</b><p>{h(n['summary'])}</p><a href='/news/{n['id']}'>Read</a></div>"

    content += "</div><div class='card'><h2>Football Events</h2>"

    for e in events:
        content += f"<div class='card'><b>{h(e['title'])}</b><p>{h(e['event_date'])} {h(e['event_time'])}</p></div>"

    content += "</div>"
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    news = conn.execute("SELECT * FROM news_posts ORDER BY id DESC LIMIT 80").fetchall()
    events = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 80").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card'><h1>🧠 HRM Admin</h1></div><div class='card'><h2>News Review</h2>"

    for n in news:
        content += f"""
        <div class='card'>
        {h(n['title'])} — {h(n['status'])}
        <a href='/admin/news/{n['id']}/approved'>Approve</a>
        <a href='/admin/news/{n['id']}/rejected'>Reject</a>
        </div>
        """

    content += "</div><div class='card'><h2>Event Review</h2>"

    for e in events:
        content += f"""
        <div class='card'>
        {h(e['title'])} — {h(e['status'])}
        <a href='/admin/event/{e['id']}/approved'>Approve</a>
        <a href='/admin/event/{e['id']}/rejected'>Reject</a>
        </div>
        """

    content += "</div><div class='card'><h2>Audit Logs</h2>"

    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"

    content += "</div>"
    return render(content)

@app.route("/admin/news/<int:id>/<status>")
def admin_news(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")

    conn = db()
    conn.execute("UPDATE news_posts SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()

    log(f"News {status}", session.get("user", "admin"))
    return redirect("/admin")

@app.route("/admin/event/<int:id>/<status>")
def admin_event(id, status):
    if status not in ["approved", "rejected"]:
        return redirect("/admin")

    conn = db()
    conn.execute("UPDATE events SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()

    log(f"Event {status}", session.get("user", "admin"))
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
