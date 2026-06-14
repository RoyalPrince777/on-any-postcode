import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DB = "oap.db"
USERNAME = "N24-7"
EMAIL = "earthisourturf777@gmail.com"
PASSWORD = "2525"
ROLE = "admin"

conn = sqlite3.connect(DB)
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

cur.execute("SELECT id FROM users WHERE username=?", (USERNAME,))
user = cur.fetchone()

if user:
    cur.execute(
        "UPDATE users SET email=?, password=?, role=? WHERE username=?",
        (EMAIL, generate_password_hash(PASSWORD), ROLE, USERNAME)
    )
    print("✅ Login fixed:", USERNAME)
else:
    cur.execute(
        "INSERT INTO users(username,email,password,role,created_at) VALUES(?,?,?,?,?)",
        (USERNAME, EMAIL, generate_password_hash(PASSWORD), ROLE, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    print("✅ Admin created:", USERNAME)

conn.commit()
conn.close()
