from flask import Flask, render_template_string, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "oap_secret_key"

DB = "oap.db"


def connect_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'user',
        created_at TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT,
        created_at TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        location TEXT,
        event_date TEXT,
        created_at TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        description TEXT,
        created_at TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        username TEXT,
        created_at TEXT
    )
    ''')

    conn.commit()
    conn.close()


init_db()

BASE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ON ANY POSTCODE</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            background: #0a0a0a;
            color: white;
            font-family: Arial;
            margin: 0;
            padding: 0;
        }

        .topbar {
            background: #111;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #222;
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
        }

        .container {
            padding: 20px;
        }

        .card {
            background: #151515;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 15px;
            border: 1px solid #222;
        }

        input, textarea {
            width: 100%;
            padding: 12px;
            margin-top: 10px;
            margin-bottom: 10px;
            background: #0f0f0f;
            color: white;
            border: 1px solid #333;
            border-radius: 10px;
        }

        button {
            background: #00cc88;
            color: black;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            font-weight: bold;
        }

        a {
            color: #00cc88;
            text-decoration: none;
        }

        .hero {
            text-align: center;
            padding: 50px 20px;
        }

        .hero h1 {
            font-size: 38px;
        }

        .tagline {
            color: #00cc88;
            margin-top: 15px;
            font-size: 18px;
        }

        .section-title {
            font-size: 22px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>

<div class="topbar">
    <div class="logo">ON ANY POSTCODE</div>

    <div>
        {% if session.get('user') %}
            Welcome {{ session.get('user') }} |
            <a href="/logout">Logout</a>
        {% else %}
            <a href="/login">Login</a>
        {% endif %}
    </div>
</div>

<div class="container">
    {{ content|safe }}
</div>

</body>
</html>
'''


@app.route('/')
def home():
    conn = connect_db()

    posts = conn.execute(
        "SELECT * FROM posts ORDER BY id DESC LIMIT 5"
    ).fetchall()

    events = conn.execute(
        "SELECT * FROM events ORDER BY id DESC LIMIT 5"
    ).fetchall()

    businesses = conn.execute(
        "SELECT * FROM businesses ORDER BY id DESC LIMIT 5"
    ).fetchall()

    content = '''
    <div class="hero">
        <h1>🌍 ON ANY POSTCODE 👑</h1>
        <div class="tagline">
            ✨👑Born Local🔥💨🚀✨Built Global💎💦
        </div>
        <p>Earth Is Our Turf</p>
    </div>

    <div class="card">
        <div class="section-title">📰 LIVE FEED</div>
    '''

    for post in posts:
        content += f'''
        <div class="card">
            <b>@{post['username']}</b><br><br>
            {post['content']}<br><br>
            <small>{post['created_at']}</small>
        </div>
        '''

    content += '''</div>'''

    content += '''
    <div class="card">
        <div class="section-title">⚽ EVENTS</div>
    '''

    for event in events:
        content += f'''
        <div class="card">
            <b>{event['title']}</b><br>
            📍 {event['location']}<br>
            📅 {event['event_date']}
        </div>
        '''

    content += '''</div>'''

    content += '''
    <div class="card">
        <div class="section-title">🏪 BUSINESS BOARD</div>
    '''

    for business in businesses:
        content += f'''
        <div class="card">
            <b>{business['name']}</b><br>
            🏷️ {business['category']}<br><br>
            {business['description']}
        </div>
        '''

    content += '''</div>'''

    if session.get("user"):
        content += '''
        <div class="card">
            <div class="section-title">✍️ CREATE POST</div>
            <form method="POST" action="/create_post">
                <textarea name="content" required placeholder="What's happening?"></textarea>
                <button type="submit">Post</button>
            </form>
        </div>
        '''

    return render_template_string(BASE_HTML, content=content)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = connect_db()

        try:
            conn.execute(
                "INSERT INTO users (username, email, password, created_at) VALUES (?, ?, ?, ?)",
                (username, email, password, str(datetime.now()))
            )

            conn.execute(
                "INSERT INTO audit_logs (action, username, created_at) VALUES (?, ?, ?)",
                ("User Registered", username, str(datetime.now()))
            )

            conn.commit()

            return redirect('/login')

        except:
            return "Username already exists"

    content = '''
    <div class="card">
        <h2>Create Account</h2>

        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>

            <button type="submit">Register</button>
        </form>
    </div>
    '''

    return render_template_string(BASE_HTML, content=content)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user'] = username

            conn.execute(
                "INSERT INTO audit_logs (action, username, created_at) VALUES (?, ?, ?)",
                ("User Login", username, str(datetime.now()))
            )

            conn.commit()

            return redirect('/')

        return "Invalid login"

    content = '''
    <div class="card">
        <h2>Login</h2>

        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>

            <button type="submit">Login</button>
        </form>

        <br>
        <a href="/register">Create account</a>
    </div>
    '''

    return render_template_string(BASE_HTML, content=content)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/create_post', methods=['POST'])
def create_post():
    if not session.get('user'):
        return redirect('/login')

    content = request.form['content']

    conn = connect_db()

    conn.execute(
        "INSERT INTO posts (username, content, created_at) VALUES (?, ?, ?)",
        (session['user'], content, str(datetime.now()))
    )

    conn.execute(
        "INSERT INTO audit_logs (action, username, created_at) VALUES (?, ?, ?)",
        ("Created Post", session['user'], str(datetime.now()))
    )

    conn.commit()

    return redirect('/')


@app.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'POST':
        title = request.form['title']
        location = request.form['location']
        event_date = request.form['event_date']

        conn = connect_db()

        conn.execute(
            "INSERT INTO events (title, location, event_date, created_at) VALUES (?, ?, ?, ?)",
            (title, location, event_date, str(datetime.now()))
        )

        conn.commit()

        return redirect('/events')

    conn = connect_db()

    events = conn.execute(
        "SELECT * FROM events ORDER BY id DESC"
    ).fetchall()

    content = '''
    <div class="card">
        <h2>⚽ Events</h2>

        <form method="POST">
            <input type="text" name="title" placeholder="Event title" required>
            <input type="text" name="location" placeholder="Location" required>
            <input type="date" name="event_date" required>

            <button type="submit">Create Event</button>
        </form>
    </div>
    '''

    for event in events:
        content += f'''
        <div class="card">
            <b>{event['title']}</b><br>
            📍 {event['location']}<br>
            📅 {event['event_date']}
        </div>
        '''

    return render_template_string(BASE_HTML, content=content)


@app.route('/businesses', methods=['GET', 'POST'])
def businesses():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']

        conn = connect_db()

        conn.execute(
            "INSERT INTO businesses (name, category, description, created_at) VALUES (?, ?, ?, ?)",
            (name, category, description, str(datetime.now()))
        )

        conn.commit()

        return redirect('/businesses')

    conn = connect_db()

    businesses = conn.execute(
        "SELECT * FROM businesses ORDER BY id DESC"
    ).fetchall()

    content = '''
    <div class="card">
        <h2>🏪 Business Board</h2>

        <form method="POST">
            <input type="text" name="name" placeholder="Business name" required>
            <input type="text" name="category" placeholder="Category" required>
            <textarea name="description" placeholder="Description"></textarea>

            <button type="submit">Add Business</button>
        </form>
    </div>
    '''

    for business in businesses:
        content += f'''
        <div class="card">
            <b>{business['name']}</b><br>
            🏷️ {business['category']}<br><br>
            {business['description']}
        </div>
        '''

    return render_template_string(BASE_HTML, content=content)


@app.route('/admin')
def admin():
    conn = connect_db()

    logs = conn.execute(
        "SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50"
    ).fetchall()

    content = '''
    <div class="card">
        <h2>🛡️ HRM AUDIT LOGS</h2>
    '''

    for log in logs:
        content += f'''
        <div class="card">
            <b>{log['action']}</b><br>
            👤 {log['username']}<br>
            🕒 {log['created_at']}
        </div>
        '''

    content += '</div>'

    return render_template_string(BASE_HTML, content=content)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
