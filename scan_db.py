import sqlite3

conn = sqlite3.connect("oap.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

print("\n=== OAP TABLES ===\n")

for t in tables:
    print(t[0])

print(f"\nTotal Tables: {len(tables)}")

conn.close()
