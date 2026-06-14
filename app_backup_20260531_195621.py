from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-oap-secret"
DB = "oap.db"


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        nickname TEXT,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'member',
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        body TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        detail TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hrm_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal TEXT,
        lesson TEXT,
        created_at TEXT
    )
    """)

    con.commit()
    con.close()


def audit(action, detail):
    con = db()
    con.execute(
        "INSERT INTO audit_logs(action, detail, created_at) VALUES (?, ?, ?)",
        (action, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    con.commit()
    con.close()


def current_user():
    if "user_id" not in session:
        return None
    con = db()
    user = con.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    con.close()
    return user


BASE = """
<!doctype html>
<html>
<head>
<title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:#07120d;color:#f4fff8;margin:0}
header{background:#00a86b;padding:16px;color:#001b10}
nav a{color:white;margin:6px;text-decoration:none;font-weight:bold}
.card{background:#10281b;margin:14px;padding:16px;border-radius:14px}
input,textarea,button{width:100%;padding:12px;margin:7px 0;border-radius:10px;border:0}
button{background:#00a86b;color:white;font-weight:bold}
a{color:#58ffb0}
.small{color:#b7d9c5}
</style>
</head>
<body>
<header>
<h2>👑 ON ANY POSTCODE</h2>
<div>Born Local. Built Global. Earth Is Our Turf.</div>
<nav>
<a href="/">Home</a>
<a href="/dashboard">Dashboard</a>
<a href="/my_world">My World</a>
<a href="/messages">Messages</a>
<a href="/verification">Verification</a>
<a href="/revenue">Revenue</a>
<a href="/hrm_memory">HRM</a>
<a href="/admin">Admin</a>
{% if user %}
<a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a>
<a href="/signup">Signup</a>
{% endif %}
</nav>
</header>
{{content|safe}}
</body>
</html>
"""


def page(content):
    return render_template_string(BASE, content=content, user=current_user())


@app.route("/")
def home():
    return page("""
    <div class="card">
    <h1>🌍 OAP Core Live</h1>
    <p>Public browsing is open. Login is only needed for trust, posts, messages, verification, revenue, HRM and admin actions.</p>
    <p><a href="/signup">Create account</a> or <a href="/login">login</a>.</p>
    </div>
    """)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        nickname = request.form.get("nickname", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return page("<div class='card'>Username and password required.</div>")

        hashed = generate_password_hash(password)

        try:
            con = db()
            con.execute(
                "INSERT INTO users(username,nickname,email,password,role,created_at) VALUES(?,?,?,?,?,?)",
                (username, nickname, email, hashed, "member", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            con.commit()
            con.close()
            audit("signup", f"New user: {username}")
            return redirect("/login")
        except sqlite3.IntegrityError:
            return page("<div class='card'>Username already exists.</div>")

    return page("""
    <div class="card">
    <h2>Signup</h2>
    <form method="post">
    <input name="username" placeholder="Username">
    <input name="nickname" placeholder="Nickname">
    <input name="email" placeholder="Email optional">
    <input name="password" type="password" placeholder="Password">
    <button>Create Account</button>
    </form>
    </div>
    """)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        con = db()
        user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        con.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            audit("login", f"{username} logged in")
            return redirect("/my_world")

        return page("<div class='card'>Invalid login.</div>")

    return page("""
    <div class="card">
    <h2>Login</h2>
    <form method="post">
    <input name="username" placeholder="Username">
    <input name="password" type="password" placeholder="Password">
    <button>Login</button>
    </form>
    </div>
    """)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    con = db()
    users = con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    posts = con.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
    messages = con.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"]
    logs = con.execute("SELECT COUNT(*) c FROM audit_logs").fetchone()["c"]
    con.close()

    return page(f"""
    <div class="card"><h2>📊 Dashboard</h2>
    <p>Users: {users}</p>
    <p>Posts: {posts}</p>
    <p>Messages: {messages}</p>
    <p>Audit Logs: {logs}</p>
    </div>
    """)


@app.route("/my_world", methods=["GET", "POST"])
def my_world():
    user = current_user()
    if not user:
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title", "")
        body = request.form.get("body", "")
        con = db()
        con.execute(
            "INSERT INTO posts(user_id,title,body,created_at) VALUES(?,?,?,?)",
            (user["id"], title, body, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        con.commit()
        con.close()
        audit("post_created", f"{user['username']} created post")
        return redirect("/my_world")

    con = db()
    posts = con.execute("""
        SELECT posts.*, users.username FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.id DESC
    """).fetchall()
    con.close()

    post_html = "".join([
        f"<div class='card'><h3>{p['title']}</h3><p>{p['body']}</p><p class='small'>By {p['username']} — {p['created_at']}</p></div>"
        for p in posts
    ])

    return page(f"""
    <div class="card">
    <h2>🌍 My World</h2>
    <p>Welcome {user['username']}.</p>
    <form method="post">
    <input name="title" placeholder="Post title">
    <textarea name="body" placeholder="What is happening on your postcode?"></textarea>
    <button>Post</button>
    </form>
    </div>
    {post_html}
    """)


@app.route("/messages", methods=["GET", "POST"])
def messages():
    user = current_user()
    if not user:
        return redirect("/login")

    if request.method == "POST":
        msg = request.form.get("message", "")
        con = db()
        con.execute(
            "INSERT INTO messages(sender,message,created_at) VALUES(?,?,?)",
            (user["username"], msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        con.commit()
        con.close()
        audit("message_sent", f"{user['username']} sent message")
        return redirect("/messages")

    con = db()
    rows = con.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    con.close()

    html = "".join([
        f"<div class='card'><b>{m['sender']}</b><p>{m['message']}</p><p class='small'>{m['created_at']}</p></div>"
        for m in rows
    ])

    return page(f"""
    <div class="card">
    <h2>💬 Messages</h2>
    <form method="post">
    <textarea name="message" placeholder="Send OAP message"></textarea>
    <button>Send</button>
    </form>
    </div>
    {html}
    """)


@app.route("/verification")
def verification():
    return page("""
    <div class="card">
    <h2>✅ Verification</h2>
    <p>Verification badges come after proof, review, audit logs and human approval.</p>
    <p>Status: foundation ready.</p>
    </div>
    """)


@app.route("/revenue")
def revenue():
    return page("""
    <div class="card">
    <h2>💷 Revenue Board</h2>
    <p>Fastest path: community → creators → business promo → events → products → SIKA trust records later.</p>
    <p>No bank claims. No debt-first system. Real value first.</p>
    </div>
    """)


@app.route("/hrm_memory", methods=["GET", "POST"])
def hrm_memory():
    if request.method == "POST":
        signal = request.form.get("signal", "")
        lesson = request.form.get("lesson", "")
        con = db()
        con.execute(
            "INSERT INTO hrm_memory(signal,lesson,created_at) VALUES(?,?,?)",
            (signal, lesson, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        con.commit()
        con.close()
        audit("hrm_memory", signal)
        return redirect("/hrm_memory")

    con = db()
    rows = con.execute("SELECT * FROM hrm_memory ORDER BY id DESC").fetchall()
    con.close()

    html = "".join([
        f"<div class='card'><h3>{r['signal']}</h3><p>{r['lesson']}</p><p class='small'>{r['created_at']}</p></div>"
        for r in rows
    ])

    return page(f"""
    <div class="card">
    <h2>🧠 HRM Memory</h2>
    <form method="post">
    <input name="signal" placeholder="Signal">
    <textarea name="lesson" placeholder="Lesson learned"></textarea>
    <button>Save Memory</button>
    </form>
    </div>
    {html}
    """)


@app.route("/admin")
def admin():
    con = db()
    logs = con.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 30").fetchall()
    con.close()

    html = "".join([
        f"<div class='card'><b>{l['action']}</b><p>{l['detail']}</p><p class='small'>{l['created_at']}</p></div>"
        for l in logs
    ])

    return page(f"""
    <div class="card">
    <h2>🛡️ Admin / Audit</h2>
    <p>Guardian: review. Chancellor: record. Sentinel: security note.</p>
    </div>
    {html}
    """)


@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    init_db()
    print("OAP CORE running: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
