# ADD INSIDE init_db()

cur.execute("""CREATE TABLE IF NOT EXISTS founder_memberships(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    tier TEXT,
    note TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS market_products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    title TEXT,
    category TEXT,
    price TEXT,
    description TEXT,
    image TEXT,
    link TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT
)""")
