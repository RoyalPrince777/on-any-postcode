import sqlite3
from werkzeug.security import generate_password_hash

DB = "oap.db"
USERNAME = "N24-7"
NEW_PASSWORD = "2525"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT id, username FROM users WHERE username=?", (USERNAME,))
user = cur.fetchone()

if not user:
    print("User not found:", USERNAME)
else:
    cur.execute(
        "UPDATE users SET password=? WHERE username=?",
        (generate_password_hash(NEW_PASSWORD), USERNAME)
    )
    conn.commit()
    print("Password reset complete for:", USERNAME)

conn.close()
