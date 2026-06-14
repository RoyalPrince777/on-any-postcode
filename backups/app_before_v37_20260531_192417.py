    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS culture_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        culture_type TEXT,
        title TEXT,
        heritage_group TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        continent TEXT,
        body TEXT,
        source_note TEXT,
        status TEXT DEFAULT 'approved',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS artists(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        artist_name TEXT,
        genre TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        continent TEXT,
        bio TEXT,
        link TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        event_type TEXT,
        category TEXT,
        postcode TEXT,
        borough TEXT,
        country TEXT,
        continent TEXT,
        venue TEXT,
        event_date TEXT,
        event_time TEXT,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS awards(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        award_name TEXT,
        award_type TEXT,
        nominee_name TEXT,
        reason TEXT,
        geography_level TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS verification_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        requested_level TEXT,
        proof TEXT,
        contribution_note TEXT,
        status TEXT DEFAULT 'pending',
        reviewer_note TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        recipient TEXT,
        subject TEXT,
        body TEXT,
        status TEXT DEFAULT 'unread',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS revenues(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        customer_name TEXT,
        source TEXT,
        description TEXT,
        amount REAL DEFAULT 0,
        currency TEXT DEFAULT 'GBP',
        status TEXT DEFAULT 'recorded',
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS payouts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        recipient_name TEXT,
        reason TEXT,
        amount REAL DEFAULT 0,
        currency TEXT DEFAULT 'GBP',
        status TEXT DEFAULT 'pending',
        approved_by TEXT,
        paid_date TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS approvals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        approval_type TEXT,
        record_id INTEGER,
        status TEXT DEFAULT 'pending',
        reviewer TEXT,
        notes TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS hrm_memory_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_type TEXT,
        title TEXT,
        summary TEXT,
        lesson TEXT,
        next_action TEXT,
        visibility TEXT DEFAULT 'private',
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
        WHERE username=?""", ("N24-7", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "admin", "founder", ADMIN_USERNAME))
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
<title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#050505;color:white;font-family:Arial}
.top{background:#101010;padding:15px;border-bottom:1px solid #222;position:sticky;top:0;z-index:2}
.logo{font-size:22px;font-weight:900}
.wrap{padding:14px;max-width:1150px;margin:auto}
.card{background:#151515;border:1px solid #252525;border-radius:18px;padding:16px;margin:12px 0}
.hero{text-align:center;padding:30px 10px}
.green{color:#00dd99}.gold{color:#ffd166}.red{color:#ff6b6b}
a{color:#00dd99;text-decoration:none;margin-right:10px}
input,textarea,select{width:100%;padding:13px;margin:8px 0;background:#0b0b0b;color:white;border:1px solid #333;border-radius:12px;box-sizing:border-box}
button{background:#00dd99;color:#000;border:0;border-radius:12px;padding:13px 18px;font-weight:900}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.small{color:#aaa;font-size:13px}
.badge{display:inline-block;background:#00dd99;color:#000;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:bold;margin:3px}
.warn{background:#2b1600;border-color:#6b3b00}
</style>
</head>
<body>
<div class="top">
<div class="logo">ON ANY POSTCODE</div>
<div>
{% if session.get("user") %}
@{{session.get("user")}} <a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a> <a href="/signup">Join</a>
{% endif %}
</div>
<div style="margin-top:10px;line-height:2">
<a href="/">Home</a>
<a href="/my_world">My World</a>
<a href="/dashboard">Dashboard</a>
<a href="/culture">Culture</a>
<a href="/artists">Artists</a>
<a href="/events">Events</a>
<a href="/awards">Awards</a>
<a href="/verification">Verification</a>
<a href="/messages">Messenger</a>
<a href="/revenue">Revenue</a>
<a href="/payouts">Payouts</a>
<a href="/approvals">Approvals</a>
<a href="/hrm_memory">HRM</a>
<a href="/admin">Admin</a>
</div>
</div>
<div class="wrap">{{content|safe}}</div>
</body>
</html>
"""

