from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_oap_secret_key"

DB = "oap.db"
ADMIN_USERNAME = "N24-7"
ADMIN_EMAIL = "oap@onanypostcode.local"
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

def log(action, username="system"):
    conn = db()
    conn.execute(
        "INSERT INTO audit_logs(action,username,created_at) VALUES(?,?,?)",
        (action, username, now())
    )
    conn.commit()
    conn.close()

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        username TEXT UNIQUE,
        oap_email TEXT,
        password TEXT,
        postcode TEXT,
        borough TEXT,
        county_region TEXT,
        country TEXT,
        continent TEXT,
        weather_location TEXT,
        verification_level TEXT DEFAULT 'starter',
        role TEXT DEFAULT 'member',
        created_at TEXT
    )""")

    for col, typ in [
        ("nickname","TEXT"),("oap_email","TEXT"),("postcode","TEXT"),
        ("borough","TEXT"),("county_region","TEXT"),("country","TEXT"),
        ("continent","TEXT"),("weather_location","TEXT"),
        ("verification_level","TEXT DEFAULT 'starter'")
    ]:
        add_col(cur, "users", col, typ)

    cur.execute("""CREATE TABLE IF NOT EXISTS ai_council_tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        mission TEXT,
        task_type TEXT,
        priority TEXT,
        status TEXT DEFAULT 'draft',
        final_decision TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS ai_council_reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        model_name TEXT,
        council_role TEXT,
        review TEXT,
        risk_note TEXT,
        recommendation TEXT,
        status TEXT DEFAULT 'submitted',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS hrm_memory_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_type TEXT,
        title TEXT,
        summary TEXT,
        lesson TEXT,
        next_action TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )""")

    cur.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,))
    user = cur.fetchone()

    if user:
        cur.execute("""UPDATE users SET nickname=?, oap_email=?, password=?, role=?, verification_level=?
                       WHERE username=?""",
            ("N24-7", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", "founder", ADMIN_USERNAME))
    else:
        cur.execute("""INSERT INTO users(nickname,username,oap_email,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("N24-7", ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD),
         "CR4", "Merton", "Greater London", "UK", "Europe", "London", "founder", "admin", now()))

    conn.commit()
    conn.close()

init_db()

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>OAP AI Council</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#050505;color:white;font-family:Arial}
.top{background:#101010;padding:15px;border-bottom:1px solid #222;position:sticky;top:0;z-index:2}
.logo{font-size:22px;font-weight:900}
.wrap{padding:14px;max-width:1100px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:16px;margin:12px 0}
.hero{text-align:center;padding:30px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:13px;margin:8px 0;background:#0b0b0b;color:white;border:1px solid #333;border-radius:12px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:12px;padding:13px 18px;font-weight:900}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:bold;margin:3px}
pre{white-space:pre-wrap;font-family:Arial}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE — AI Council</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a> <a href="/signup">Join</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/ai_council">AI Council</a>
<a href="/new_task">New Task</a>
<a href="/hrm_memory">HRM Memory</a>
<a href="/profile">Profile</a>
<a href="/admin">Admin</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE, content=content)

def council_prompt(task):
    return f"""
MISSION:
{task['mission']}

TASK TYPE:
{task['task_type']}

OAP AI COUNCIL ROLES:
GPT = Chief Architect
Claude = Chancellor / Governance
Gemini = Archivist / Ecosystem Memory
Kimi = Expansion Strategist
Grok = Challenger / Stress Tester
HRM = Local Record Keeper
You = Final Decision Maker

RULES:
Research has no ceiling.
Deployment has boundaries.
Proof before execution.
Verification before sharing.
Compliance before claims.
Audit before automation.
Human approval before real-world action.

OUTPUT NEEDED:
1. Architecture
2. Risks
3. Recommendation
4. Next safe action
"""

def memory(memory_type, title, summary, lesson, next_action):
    conn = db()
    conn.execute("""INSERT INTO hrm_memory_logs(memory_type,title,summary,lesson,next_action,created_at)
    VALUES(?,?,?,?,?,?)""", (memory_type, title, summary, lesson, next_action, now()))
    conn.commit()
    conn.close()

@app.route("/")
def home():
    conn = db()
    tasks = conn.execute("SELECT COUNT(*) c FROM ai_council_tasks").fetchone()["c"]
    reviews = conn.execute("SELECT COUNT(*) c FROM ai_council_reviews").fetchone()["c"]
    memories = conn.execute("SELECT COUNT(*) c FROM hrm_memory_logs").fetchone()["c"]
    recent = conn.execute("SELECT * FROM ai_council_tasks ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    content = f"""
    <div class='card hero'>
    <h1>👑 OAP AI Council Core</h1>
    <p class='green'>AI advises. HRM remembers. You decide.</p>
    <p>GPT • Claude • Gemini • Kimi • Grok • HRM • Human Final Approval</p>
    </div>

    <div class='grid'>
    <div class='card'><h2>{tasks}</h2><p>Council Tasks</p></div>
    <div class='card'><h2>{reviews}</h2><p>AI Reviews</p></div>
    <div class='card'><h2>{memories}</h2><p>HRM Memories</p></div>
    </div>

    <div class='card'>
    <h2>Council Roles</h2>
    <p><b>GPT</b> = Chief Architect</p>
    <p><b>Claude</b> = Chancellor / Governance</p>
    <p><b>Gemini</b> = Archivist / Ecosystem Memory</p>
    <p><b>Kimi</b> = Expansion Strategist</p>
    <p><b>Grok</b> = Challenger / Stress Tester</p>
    <p><b>HRM</b> = Local Record Keeper</p>
    <p><b>You</b> = Final Decision Maker</p>
    </div>

    <div class='card'>
    <a class='badge' href='/new_task'>Create Council Task</a>
    <a class='badge' href='/ai_council'>Open Council Board</a>
    <a class='badge' href='/hrm_memory'>HRM Memory</a>
    </div>

    <div class='card'><h2>Recent Tasks</h2>
    """
    for t in recent:
        content += f"""
        <div class='card'>
        <b>{h(t['title'])}</b><br>
        {h(t['task_type'])} • {h(t['priority'])} • {h(t['status'])}<br>
        <a href='/task/{t['id']}'>Open</a>
        </div>
        """
    content += "</div>"
    return render(content)

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        conn = db()
        try:
            conn.execute("""INSERT INTO users(nickname,username,oap_email,password,postcode,borough,county_region,country,continent,weather_location,verification_level,role,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                request.form["nickname"], request.form["username"], request.form["oap_email"],
                generate_password_hash(request.form["password"]),
                request.form["postcode"], request.form["borough"], request.form["county_region"],
                request.form["country"], request.form["continent"], request.form["weather_location"],
                "starter", "member", now()
            ))
            conn.commit()
            log("User joined OAP", request.form["username"])
            return redirect("/login")
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()

    return render("""
    <div class='card hero'><h1>Join OAP</h1><p class='green'>Fast signup now. Verification and monetization later.</p></div>
    <div class='card'>
    <form method='POST'>
    <input name='nickname' placeholder='Nickname' required>
    <input name='username' placeholder='Username' required>
    <input name='oap_email' placeholder='OAP email optional e.g. name@oap.local'>
    <input name='password' type='password' placeholder='Password' required>
    <input name='postcode' placeholder='Postcode optional'>
    <input name='borough' placeholder='Borough optional'>
    <input name='county_region' placeholder='County / Region optional'>
    <input name='country' placeholder='Country optional'>
    <input name='continent' placeholder='Continent optional'>
    <input name='weather_location' placeholder='Weather location optional'>
    <button>Join</button>
    </form>
    </div>
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
    </form>
    <p class='small'>Default admin: N24-7 / 2525</p>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/profile")
def profile():
    username = session.get("user")
    if not username:
        return redirect("/login")
    conn = db()
    u = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    if not u:
        return "Profile not found"
    return render(f"""
    <div class='card hero'><h1>@{h(u['username'])}</h1><p class='green'>{h(u['verification_level'])}</p></div>
    <div class='card'>
    <p><b>Nickname:</b> {h(u['nickname'])}</p>
    <p><b>OAP Email:</b> {h(u['oap_email'])}</p>
    <p><b>Postcode:</b> {h(u['postcode'])}</p>
    <p><b>Borough:</b> {h(u['borough'])}</p>
    <p><b>County / Region:</b> {h(u['county_region'])}</p>
    <p><b>Country:</b> {h(u['country'])}</p>
    <p><b>Continent:</b> {h(u['continent'])}</p>
    <p><b>Weather:</b> {h(u['weather_location'])}</p>
    </div>
    """)

@app.route("/new_task", methods=["GET","POST"])
def new_task():
    if request.method == "POST":
        username = session.get("user", "guest")
        conn = db()
        conn.execute("""INSERT INTO ai_council_tasks(username,title,mission,task_type,priority,status,final_decision,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (
            username, request.form["title"], request.form["mission"],
            request.form["task_type"], request.form["priority"], "draft", "", now()
        ))
        conn.commit()
        conn.close()
        log("AI Council task created", username)
        memory("ai_council", request.form["title"], "New council task created", "Council review needed before action.", "Collect model reviews.")
        return redirect("/ai_council")

    return render("""
    <div class='card hero'><h1>Create AI Council Task</h1></div>
    <div class='card'>
    <form method='POST'>
    <input name='title' placeholder='Task title' required>
    <select name='task_type'>
    <option>Architecture</option>
    <option>Coding</option>
    <option>Governance</option>
    <option>Security</option>
    <option>Expansion</option>
    <option>Stress Test</option>
    <option>HRM Memory</option>
    <option>Monetization</option>
    <option>Compliance</option>
    </select>
    <select name='priority'>
    <option>Low</option>
    <option>Medium</option>
    <option>High</option>
    <option>Critical</option>
    </select>
    <textarea name='mission' placeholder='Mission / problem / build goal' required></textarea>
    <button>Create Task</button>
    </form>
    </div>
    """)

@app.route("/ai_council")
def ai_council():
    conn = db()
    rows = conn.execute("SELECT * FROM ai_council_tasks ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>AI Council Board</h1></div>"
    for t in rows:
        content += f"""
        <div class='card'>
        <b>{h(t['title'])}</b><br>
        {h(t['task_type'])} • {h(t['priority'])} • {h(t['status'])}<br>
        <p>{h(t['mission'])}</p>
        <a class='badge' href='/task/{t['id']}'>Open Task</a>
        </div>
        """
    return render(content)

@app.route("/task/<int:id>", methods=["GET","POST"])
def task_detail(id):
    conn = db()
    task = conn.execute("SELECT * FROM ai_council_tasks WHERE id=?", (id,)).fetchone()
    if not task:
        conn.close()
        return "Task not found"

    if request.method == "POST":
        conn.execute("""INSERT INTO ai_council_reviews(task_id,model_name,council_role,review,risk_note,recommendation,status,created_at)
        VALUES(?,?,?,?,?,?,?,?)""", (
            id, request.form["model_name"], request.form["council_role"],
            request.form["review"], request.form["risk_note"], request.form["recommendation"],
            "submitted", now()
        ))
        conn.commit()
        conn.close()
        log("AI Council review added", session.get("user","guest"))
        return redirect(f"/task/{id}")

    reviews = conn.execute("SELECT * FROM ai_council_reviews WHERE task_id=? ORDER BY id DESC", (id,)).fetchall()
    conn.close()

    content = f"""
    <div class='card hero'><h1>{h(task['title'])}</h1><p class='green'>{h(task['task_type'])} • {h(task['priority'])}</p></div>
    <div class='card'>
    <h2>Mission</h2>
    <p>{h(task['mission'])}</p>
    <h2>Council Prompt</h2>
    <pre>{h(council_prompt(task))}</pre>
    </div>

    <div class='card'>
    <h2>Add Council Review</h2>
    <form method='POST'>
    <select name='model_name'>
    <option>GPT</option>
    <option>Claude</option>
    <option>Gemini</option>
    <option>Kimi</option>
    <option>Grok</option>
    <option>HRM</option>
    <option>Human</option>
    </select>
    <select name='council_role'>
    <option>Chief Architect</option>
    <option>Chancellor / Governance</option>
    <option>Archivist / Ecosystem Memory</option>
    <option>Expansion Strategist</option>
    <option>Challenger / Stress Tester</option>
    <option>Local Record Keeper</option>
    <option>Final Decision Maker</option>
    </select>
    <textarea name='review' placeholder='Review / analysis'></textarea>
    <textarea name='risk_note' placeholder='Risks / warnings'></textarea>
    <textarea name='recommendation' placeholder='Recommendation'></textarea>
    <button>Add Review</button>
    </form>
    </div>

    <div class='card'>
    <h2>Final Decision</h2>
    <form method='POST' action='/task/{id}/decision'>
    <textarea name='final_decision' placeholder='Your final human decision'></textarea>
    <button>Save Final Decision</button>
    </form>
    </div>

    <div class='card'><h2>Reviews</h2>
    """
    for r in reviews:
        content += f"""
        <div class='card'>
        <b>{h(r['model_name'])}</b> — {h(r['council_role'])}<br>
        <p>{h(r['review'])}</p>
        <p class='red'><b>Risk:</b> {h(r['risk_note'])}</p>
        <p class='green'><b>Recommendation:</b> {h(r['recommendation'])}</p>
        </div>
        """
    content += "</div>"
    return render(content)

@app.route("/task/<int:id>/decision", methods=["POST"])
def task_decision(id):
    decision = request.form["final_decision"]
    conn = db()
    task = conn.execute("SELECT * FROM ai_council_tasks WHERE id=?", (id,)).fetchone()
    conn.execute("UPDATE ai_council_tasks SET final_decision=?, status=? WHERE id=?", (decision, "decided", id))
    conn.commit()
    conn.close()
    log("Final human decision saved", session.get("user","guest"))
    if task:
        memory("decision", task["title"], "Final decision saved", decision, "Execute only after human-approved next step.")
    return redirect(f"/task/{id}")

@app.route("/hrm_memory")
def hrm_memory():
    conn = db()
    rows = conn.execute("SELECT * FROM hrm_memory_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    content = "<div class='card hero'><h1>HRM Memory Logs</h1><p class='green'>Local record keeper.</p></div>"
    for m in rows:
        content += f"""
        <div class='card'>
        <b>{h(m['title'])}</b> — {h(m['memory_type'])}<br>
        <p>{h(m['summary'])}</p>
        <p><b>Lesson:</b> {h(m['lesson'])}</p>
        <p><b>Next:</b> {h(m['next_action'])}</p>
        <span class='small'>{h(m['created_at'])}</span>
        </div>
        """
    return render(content)

@app.route("/admin")
def admin():
    conn = db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 100").fetchall()
    tasks = conn.execute("SELECT * FROM ai_council_tasks ORDER BY id DESC LIMIT 50").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 80").fetchall()
    conn.close()

    content = "<div class='card hero'><h1>Admin</h1></div><div class='card'><h2>Users</h2>"
    for u in users:
        content += f"""
        <div class='card'>
        @{h(u['username'])} — {h(u['verification_level'])}<br>
        {h(u['postcode'])} → {h(u['borough'])} → {h(u['county_region'])} → {h(u['country'])} → {h(u['continent'])}
        </div>
        """
    content += "</div><div class='card'><h2>Tasks</h2>"
    for t in tasks:
        content += f"<div class='card'><b>{h(t['title'])}</b> — {h(t['status'])}<br><a href='/task/{t['id']}'>Open</a></div>"
    content += "</div><div class='card'><h2>Audit Logs</h2>"
    for l in logs:
        content += f"<div class='card'><b>{h(l['action'])}</b><br>{h(l['username'])}<br>{h(l['created_at'])}</div>"
    content += "</div>"
    return render(content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
