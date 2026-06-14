import sqlite3
from datetime import datetime

DB = "oap_world.db"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("INSERT INTO launch_actions(title, action_type, assigned_to, status, proof_note, created_at) VALUES(?,?,?,?,?,?)",
("Invite first local business", "First Business", "OAP", "Open", "Ask one barber/shop/food business to join Business Network.", now()))

c.execute("INSERT INTO launch_actions(title, action_type, assigned_to, status, proof_note, created_at) VALUES(?,?,?,?,?,?)",
("Create first OAP Experience", "First OAP Experience", "OAP", "Open", "Plan one small meetup/watch party/community session.", now()))

c.execute("INSERT INTO launch_actions(title, action_type, assigned_to, status, proof_note, created_at) VALUES(?,?,?,?,?,?)",
("Invite first creator", "First Creator", "OAP", "Open", "Ask one artist/creator to join Creator Hub.", now()))

c.execute("INSERT INTO launch_actions(title, action_type, assigned_to, status, proof_note, created_at) VALUES(?,?,?,?,?,?)",
("Record first Value Created", "First Value Created", "OAP", "Open", "Record first £5, £10, or £25 value signal.", now()))

conn.commit()
conn.close()

print("✅ OAP launch actions seeded.")
