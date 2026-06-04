from flask import Flask, request, redirect
from datetime import datetime
import os
import sqlite3
from html import escape

app = Flask(__name__)
DB = "oap_final_v7.db"

ROOTS = {
    "world": ["🌍 World", "News, events, countries, weather, highlights and awards."],
    "my-world": ["👤 My World", "Profile, messages, mail, cards, awards, family tree and contribution records."],
    "community": ["🤝 Community", "Community Power, Community Voice, projects, mentorship, humanitarian and volunteering."],
    "real-education": ["🌱 Real Education", "Mind, body, purpose, nature, trades, technology, strategy, martial arts and service."],
    "culture": ["🎭 Culture", "Countries, languages, stories, proverbs, food, dance and heritage."],
    "music": ["🎵 Music", "Artists, releases, radio, playlists, charts, festivals and international song."],
    "sports": ["⚽ Sports", "World Cup, football, chess, martial arts, community sports and tournaments."],
    "business": ["🏪 Business", "Business Network, Creator Hub, Market, promotions and Affiliate Family Tree."],
    "experiences": ["🎪 Experiences", "Events, celebrations, comedy, games, festivals and watch parties."],
    "explorer": ["🗺 Explorer", "Search, discover, countries, creators, businesses, events, music, culture and sports."],
    "trust": ["🛡 Trust", "Privacy, security, terms, youth protection, policies, AI policy and finance policy."],
}

SYSTEMS = {
    "hrm": "🧠 HRM",
    "command": "🎛 Command",
    "sika": "💎 SIKA",
    "finance": "🏦 Finance",
    "connectivity": "📶 Connectivity",
    "mobility": "🛵 Mobility",
    "mail": "📧 Mail",
    "ollama": "🤖 Local AI / Ollama",
}

BRANCHES = {
    "world": ["Community News", "Events", "Countries", "Weather", "Highlights", "Awards"],
    "my-world": ["Profile", "Messages", "Mail", "Cards", "Awards", "Family Tree", "Contribution Records", "Settings"],
    "community": ["Community Power", "Community Voice", "Projects", "Mentorship", "Humanitarian", "Volunteering"],
    "real-education": ["Mind", "Body", "Purpose", "Nature", "Trades", "Technology", "Strategy", "Chess", "Martial Arts", "Muay Thai", "Business", "Service"],
    "culture": ["Countries", "Languages", "Food", "Stories", "Heritage", "Dance", "Proverbs", "United States of Africa (Black Stars)", "Ghana", "Akan", "KORADASO", "Begoro"],
    "music": ["Artists", "Releases", "Radio", "Playlists", "Charts", "Festivals", "International Song"],
    "sports": ["World Cup", "Football", "Chess", "IQ Arena", "Basketball", "Athletics", "Combat Sports", "Community Sports", "Tournaments"],
    "business": ["Business Network", "Creator Hub", "Market", "Promotions", "Affiliate Family Tree"],
    "experiences": ["Events", "Celebrations", "Comedy", "Games", "Watch Parties", "Festivals"],
    "explorer": ["Search", "Discover", "Countries", "Creators", "Businesses", "Events", "Music", "Culture", "Sports"],
    "trust": ["Privacy Promise", "Security", "Terms", "Youth Protection", "Community Standards", "Music & Media Policy", "AI Policy", "Finance Policy", "Contact & Reports"],
    "hrm": ["Dashboard", "Memory", "Learning", "Audit", "Risk", "Council", "Decisions", "Animals", "God Layer", "Youth Safety", "Ollama"],
    "command": ["Dashboard", "Operations", "Metrics", "Status", "Reports", "Logs", "Agents"],
    "sika": ["Trust Records", "Contribution Records", "Badges", "Verification", "Ledger Sandbox"],
    "finance": ["Dashboard", "Invoices", "Goals", "Pots", "Statements", "Activity"],
    "connectivity": ["eSIM", "Devices", "Coverage", "WiFi", "Signal Reports"],
    "mobility": ["Delivery", "E-Bikes", "Scooters", "Drivers", "Riders", "Logistics", "Community Transport", "Global Transport"],
    "mail": ["Inbox", "Sent", "Drafts", "Contacts", "Notifications"],
    "ollama": ["Local AI Status", "Prompts", "Memory Helper", "Risk Check", "Human Approval"],
}

TEAMS = [(f"slot-{i:02d}", f"Team Slot {i:02d}", "Qualification / Confirmed", "National anthem, team music, fan songs") for i in range(1, 49)]

CATS = ["Value Created", "Community Voice", "Music", "Culture", "Sport", "Business", "Real Education", "Experience", "Digital Card", "Mobility", "Finance", "Trust"]


def now():
    return datetime.utcnow().isoformat(timespec="seconds")


def safe(v):
    return escape((v or "").strip())


def slug(t):
    return t.lower().replace("&", "and").replace("/", "-").replace("(", "").replace(")", "").replace(" ", "-")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init():
    con = db()
    con.execute("CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT, root TEXT, branch TEXT, title TEXT, name TEXT, location TEXT, category TEXT, notes TEXT, status TEXT, created_at TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS voice(id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, voice_type TEXT, choice TEXT, reason TEXT, created_at TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, detail TEXT, created_at TEXT)")
    con.commit()
    con.close()


def add_audit(action, detail):
    con = db()
    con.execute("INSERT INTO audit(action,detail,created_at) VALUES(?,?,?)", (action, detail, now()))
    con.commit()
    con.close()


init()


def nav():
    return "<a href='/'>Home</a>" + "".join([f"<a href='/{k}'>{v[0]}</a>" for k, v in ROOTS.items()])


def sysnav():
    return "".join([f"<a href='/{k}'>{v}</a>" for k, v in SYSTEMS.items()])


def layout(title, body):
    return f"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root {{
  --bg:#050505; --card:#101010; --gold:#d4af37; --blue:#00eaff;
  --text:#f7f0dd; --muted:#c9b987; --line:#6d5520; --green:#52d98f;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  background:radial-gradient(circle at top,#161616 0,#050505 55%,#000 100%);
  color:var(--text);
  font-family:Arial,Helvetica,sans-serif;
}}
header {{
  position:sticky; top:0; z-index:9;
  background:#050505ee;
  border-bottom:1px solid var(--gold);
  padding:14px;
}}
.brand {{
  font-family:Impact,Arial Black,sans-serif;
  color:var(--gold);
  font-size:26px;
  letter-spacing:3px;
  text-transform:uppercase;
}}
.tag {{ color:var(--muted); font-size:13px; letter-spacing:1px; }}
nav,.sys {{ display:flex; gap:8px; overflow:auto; padding-top:10px; }}
nav a,.sys a,.btn {{
  white-space:nowrap;
  text-decoration:none;
  color:var(--text);
  background:#111;
  border:1px solid var(--line);
  border-radius:999px;
  padding:9px 12px;
  font-weight:900;
}}
main,footer {{ max-width:1200px; margin:auto; padding:18px; }}
.hero {{
  background:linear-gradient(135deg,#090909,#161616,#123c52);
  border:1px solid var(--gold);
  border-radius:26px;
  padding:26px;
  margin-bottom:16px;
  box-shadow:0 0 30px #d4af3738;
}}
h1 {{ font-size:34px; margin-top:0; }}
.grid {{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:14px;
}}
.card {{
  display:block;
  background:linear-gradient(160deg,#090909,#111);
  border:1px solid var(--line);
  border-radius:20px;
  padding:18px;
  color:var(--text);
  text-decoration:none;
  box-shadow:0 0 18px #000;
}}
.card h2 {{ margin-top:0; }}
.metric {{ font-size:32px; color:var(--gold); font-weight:900; }}
.signal-green {{ color:var(--green); font-weight:900; }}
.neon {{ color:var(--blue); text-shadow:0 0 12px var(--blue); }}
input,select,textarea,button {{
  width:100%;
  padding:12px;
  margin:6px 0;
  border-radius:14px;
  border:1px solid var(--line);
  background:#050505;
  color:var(--text);
  font-size:15px;
}}
button {{ background:#1d8f5f; font-weight:900; cursor:pointer; }}
table {{
  width:100%;
  border-collapse:collapse;
  background:#101010;
  border-radius:18px;
  overflow:hidden;
  margin-top:14px;
}}
td,th {{
  border-bottom:1px solid var(--line);
  padding:10px;
  text-align:left;
  vertical-align:top;
}}
.warn {{
  background:#2c2108;
  border:1px solid var(--gold);
  border-radius:18px;
  padding:14px;
  margin:12px 0;
}}
.small {{ color:var(--muted); }}
</style>
</head>
<body>
<header>
  <div class="brand">ON ANY POSTCODE 🌍👑</div>
  <div class="tag">Born Local. Built Global. EARTH IS OUR TURF. One Race. Human Race.</div>
  <nav>{nav()}</nav>
</header>
<main>{body}</main>
<footer>
  <h3>System Engines</h3>
  <div class="sys">{sysnav()}</div>
  <p>💎 Create Value. 🤝 Build Trust. 🌱 Grow Community. 🏆 Leave A Legacy.</p>
  <p>3 IDENTITIES. 1 LEGACY. Global Luxury • Street Royalty • Future Sovereign</p>
</footer>
</body>
</html>"""


def records(root=None, branch=None):
    con = db()
    if root and branch:
        rows = con.execute("SELECT * FROM records WHERE root=? AND branch=? ORDER BY id DESC LIMIT 50", (root, branch)).fetchall()
    elif root:
        rows = con.execute("SELECT * FROM records WHERE root=? ORDER BY id DESC LIMIT 50", (root,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM records ORDER BY id DESC LIMIT 80").fetchall()
    con.close()
    return rows


def table(rows):
    if not rows:
        return "<div class='card'><h2>No records yet</h2><p>Create the first contribution record.</p></div>"
    body = "".join([f"<tr><td>{r['created_at']}</td><td>{r['root']}</td><td>{r['branch']}</td><td>{r['title']}</td><td>{r['status']}</td><td>{r['notes']}</td></tr>" for r in rows])
    return f"<table><tr><th>Time</th><th>Root</th><th>Branch</th><th>Title</th><th>Status</th><th>Notes</th></tr>{body}</table>"


def form(root, branch="General"):
    opts = "".join([f"<option>{c}</option>" for c in CATS])
    return f"""
<div class="card">
  <h2>Contribution Record</h2>
  <form method="post" action="/add-record">
    <input type="hidden" name="root" value="{root}">
    <input type="hidden" name="branch" value="{branch}">
    <input name="title" placeholder="Title / idea / action / content" required>
    <input name="name" placeholder="Name / creator / business / team / person">
    <input name="location" placeholder="Postcode / country / global">
    <select name="category">{opts}</select>
    <select name="status">
      <option>Idea</option>
      <option>Review</option>
      <option>Ready</option>
      <option>Active Record</option>
      <option>Completed</option>
      <option>Blocked</option>
    </select>
    <textarea name="notes" placeholder="Notes, rights proof, safety check, next action"></textarea>
    <button>Contribution Recorded</button>
  </form>
</div>
"""


@app.route("/")
def home():
    cards = "".join([f"<a class='card' href='/{k}'><h2>{v[0]}</h2><p>{v[1]}</p></a>" for k, v in ROOTS.items()])
    body = f"""
<section class="hero">
  <h1>OAP Final Roots v7 💎</h1>
  <h2>3 Identities. 1 Legacy.</h2>
  <p><b>Global Luxury</b> • <b>Street Royalty</b> • <span class="neon"><b>Future Sovereign</b></span></p>
  <p><b>EARTH IS OUR TURF.</b> One Race. Human Race.</p>
  <p>Every postcode has a story. Every culture has a song. Every community has a voice.</p>
  <div class="warn">Public systems create value today. Regulated systems such as banking, cards, e-money, telecom/eSIM service, taxi/private-hire operations and regulated payments require lawful authorisation or regulated providers before activation.</div>
</section>

<section class="grid">
  <div class="card"><div class="metric">💎</div><h2>Value Created</h2><p>Primary metric before revenue.</p></div>
  <div class="card"><div class="metric">🤝</div><h2>Trust Earned</h2><p>Proof, safety, contribution.</p></div>
  <div class="card"><div class="metric">🌱</div><h2>Communities Grown</h2><p>Local roots, global connection.</p></div>
  <div class="card"><div class="metric">🏆</div><h2>Legacy Created</h2><p>Cards, awards, culture, impact.</p></div>
</section>

<section class="grid">
  <div class="card"><h2 class="signal-green">🟢 Launch Signal</h2><p>No red lights if homepage, World Cup, Command and Trust open.</p></div>
  <div class="card"><h2>🎛 Dashboard Signal</h2><p>Command Center records actions, Community Voice and audit logs.</p></div>
  <div class="card"><h2>🤖 Ollama Signal</h2><p>Local AI is suggestions only. Human approval before action.</p></div>
  <div class="card"><h2>🛡 Trust Signal</h2><p>Privacy, youth safety, finance policy and media rights stay visible.</p></div>
</section>

<h2>Menu Roots</h2>
<section class="grid">{cards}</section>
"""
    return layout("OAP Final Roots v7", body)


@app.route("/<root>")
def root_page(root):
    if root == "sports":
        return sports()
    if root == "command":
        return command()
    if root == "trust":
        return trust()
    data = ROOTS.get(root) or [SYSTEMS.get(root, "Page"), "System engine for OAP operations and records."]
    branches = BRANCHES.get(root, [])
    cards = "".join([f"<a class='card' href='/{root}/{slug(b)}'><h2>{b}</h2><p>{data[0]} branch.</p></a>" for b in branches])
    return layout(data[0], f"<section class='hero'><h1>{data[0]}</h1><p>{data[1]}</p></section><section class='grid'>{cards}</section><h2>Record Value</h2>{form(root)}<h2>Latest Records</h2>{table(records(root))}")


@app.route("/<root>/<branch>")
def branch_page(root, branch):
    if root == "sports" and branch == "world-cup":
        return worldcup()
    if root == "sports" and branch in ["chess", "iq-arena"]:
        return chess()
    if root == "real-education" and branch in ["martial-arts", "muay-thai"]:
        return martial()
    title = branch.replace("-", " ").title()
    return layout(title, f"<section class='hero'><h1>{title}</h1><p>{root.replace('-', ' ').title()} branch inside OAP World.</p></section>{form(root, title)}<h2>Latest {title}</h2>{table(records(root, title))}")


def sports():
    cards = "".join([f"<a class='card' href='/sports/{slug(b)}'><h2>{b}</h2><p>Sports and tournament branch.</p></a>" for b in BRANCHES["sports"]])
    return layout("Sports", f"<section class='hero'><h1>⚽ Sports</h1><p>World Cup, football, chess, martial arts, tournaments and community sport.</p></section><section class='grid'>{cards}</section>{form('sports')}{table(records('sports'))}")


def worldcup():
    teamcards = "".join([f"<a class='card' href='/world-cup/team/{s}'><h2>{n}</h2><p>{r}</p><p><b>Music:</b> {m}</p></a>" for s, n, r, m in TEAMS])
    tournament = """
<section class="grid">
  <a class="card" href="/sports/world-cup"><h2>🏠 Tournament Home</h2><p>Overview, law, latest records.</p></a>
  <a class="card" href="/sports/world-cup/groups"><h2>🧩 Groups</h2><p>Group stage records.</p></a>
  <a class="card" href="/sports/world-cup/fixtures"><h2>📅 Fixtures</h2><p>Match schedule and matchday checklist.</p></a>
  <a class="card" href="/sports/world-cup/match-centre"><h2>⚽ Match Centre</h2><p>Preview, fan energy, manager notes.</p></a>
  <a class="card" href="/sports/world-cup/knockout"><h2>🔥 Knockout Rounds</h2><p>Round of 32 to semi finals.</p></a>
  <a class="card" href="/sports/world-cup/final"><h2>🏆 Final</h2><p>Final match centre and legacy records.</p></a>
  <a class="card" href="/community/community-voice"><h2>🌍 Community Voice</h2><p>Participation, not betting.</p></a>
  <a class="card" href="/cards"><h2>🏆 Digital Cards</h2><p>Team, anthem, culture and legacy cards.</p></a>
</section>
"""
    return layout("World Cup", f"<section class='hero'><h1>⚽ World Cup Tournament</h1><p>48-team ready: groups, fixtures, match centre, knockout rounds, final, team pages, national anthems, team music, Community Voice, watch parties, cards and awards.</p><div class='warn'>Compete with honor. No betting. No gambling. No loot boxes. No pay-to-win.</div></section>{tournament}<h2>Team Spaces</h2><section class='grid'>{teamcards}</section>")


@app.route("/world-cup/team/<team>")
def team_page(team):
    info = next((t for t in TEAMS if t[0] == team), None)
    if not info:
        return layout("Team Not Found", "<section class='hero'><h1>Team not found</h1></section>")
    s, n, r, m = info
    cards = "".join([f"<a class='card' href='/world-cup/team/{s}/{x}'><h2>{x.replace('-', ' ').title()}</h2><p>{n} section.</p></a>" for x in ["national-anthem", "team-music", "fan-songs", "manager-board", "fixtures", "matchday-checklist", "community-voice", "watch-parties", "cards", "awards"]])
    return layout(n, f"<section class='hero'><h1>{n} Team Space</h1><p><b>Region:</b> {r}</p><p><b>International Music:</b> {m}</p></section><section class='grid'>{cards}</section>{form('sports', n)}{table(records('sports', n))}")


@app.route("/world-cup/team/<team>/<section>", methods=["GET", "POST"])
def team_section(team, section):
    info = next((t for t in TEAMS if t[0] == team), None)
    if not info:
        return layout("Team Not Found", "<section class='hero'><h1>Team not found</h1></section>")
    s, n, r, m = info
    title = section.replace("-", " ").title()
    extra = ""
    if section == "national-anthem":
        extra = """<div class='card'><h2>🎵 National Anthem Player</h2><p>Default: Paused. User chooses play. Rights proof required.</p><audio controls preload='none'><source src='' type='audio/mpeg'>Your browser does not support audio.</audio><p class='small'>Add official/source link and rights proof as a contribution record below.</p></div>"""
    if request.method == "POST":
        con = db()
        con.execute("INSERT INTO voice(target,voice_type,choice,reason,created_at) VALUES(?,?,?,?,?)", (f"{n}/{title}", safe(request.form.get("voice_type")), safe(request.form.get("choice")), safe(request.form.get("reason")), now()))
        con.commit()
        con.close()
        add_audit("community_voice", f"{n}/{title}")
        return redirect(request.path)
    vf = ""
    if section == "community-voice":
        vf = """<div class='card'><h2>Community Voice</h2><form method='post'><select name='voice_type'><option>Best Team Energy</option><option>Best National Anthem</option><option>Best Team Music</option><option>Best Culture</option><option>Best Fans</option><option>Best Watch Party</option></select><input name='choice' placeholder='Your choice'><textarea name='reason' placeholder='Why?'></textarea><button>Voice Recorded</button></form></div>"""
    return layout(f"{n} {title}", f"<section class='hero'><h1>{n} / {title}</h1><p><b>Music identity:</b> {m}</p></section>{extra}{vf}{form('sports', f'{n} / {title}')}{table(records('sports', f'{n} / {title}'))}")


def chess():
    return layout("Chess / IQ Arena", f"<section class='hero'><h1>♟️ Chess / IQ Arena</h1><p>Chess, Ludo, Connect 4, logic, debates, strategy and mastery.</p></section>{form('real-education', 'Strategy / Chess')}{table(records('real-education', 'Strategy / Chess'))}")


def martial():
    return layout("Martial Arts", f"<section class='hero'><h1>🥋 Martial Arts</h1><p>Muay Thai, boxing, wrestling, judo, discipline, fitness, respect and self-control.</p></section>{form('real-education', 'Martial Arts')}{table(records('real-education', 'Martial Arts'))}")


def trust():
    return layout("Trust Center", f"<section class='hero'><h1>🛡 Trust Center</h1><p>Your data belongs to you. Your profile belongs to you. Your content belongs to you. Your culture belongs to you.</p><p>Privacy, security, youth protection, community standards, media rights, AI/HRM and finance readiness policies.</p></section>{form('trust')}{table(records('trust'))}")


def command():
    con = db()
    rc = con.execute("SELECT COUNT(*) c FROM records").fetchone()["c"]
    vc = con.execute("SELECT COUNT(*) c FROM voice").fetchone()["c"]
    aud = con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 30").fetchall()
    con.close()
    rows = "".join([f"<tr><td>{a['created_at']}</td><td>{a['action']}</td><td>{a['detail']}</td></tr>" for a in aud]) or "<tr><td colspan=3>No logs yet.</td></tr>"
    return layout("Command", f"<section class='hero'><h1>🎛 Command Center</h1><p>Agents, HRM, Local AI/Ollama, animals, God layer, youth safety, audit and launch status.</p></section><section class='grid'><div class='card'><div class='metric'>{rc}</div><h2>Records</h2></div><div class='card'><div class='metric'>{vc}</div><h2>Community Voice</h2></div><div class='card'><h2 class='signal-green'>🟢 Green</h2><p>No red lights if home, World Cup, Trust and Command open.</p></div><div class='card'><h2>🤖 Ollama</h2><p>Local AI suggestions only. Human approval before action.</p></div></section><h2>Audit Logs</h2><table><tr><th>Time</th><th>Action</th><th>Detail</th></tr>{rows}</table>")


@app.route("/cards")
def cards():
    return layout("Digital Cards", f"<section class='hero'><h1>🏆 Digital Cards</h1><p>Football cards, team cards, culture cards, music cards, fan cards, creator cards, heritage cards and contribution cards. No loot boxes. No gambling. No pay-to-win.</p></section>{form('experiences','Digital Cards')}{table(records('experiences','Digital Cards'))}")


@app.route("/add-record", methods=["POST"])
def add_record():
    vals = (
        safe(request.form.get("root")),
        safe(request.form.get("branch")),
        safe(request.form.get("title")),
        safe(request.form.get("name")),
        safe(request.form.get("location")),
        safe(request.form.get("category")),
        safe(request.form.get("notes")),
        safe(request.form.get("status")),
        now(),
    )
    con = db()
    con.execute("INSERT INTO records(root,branch,title,name,location,category,notes,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)", vals)
    con.commit()
    con.close()
    add_audit("record_added", f"{vals[0]} / {vals[2]}")
    return redirect("/" + (vals[0] or ""))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
from datetime import datetime
import os
import sqlite3
from html import escape

app = Flask(__name__)
DB = "oap_final_v7.db"

ROOTS = {"business-network": ["🏪 Business Network","Merchants and services."],
"creator-hub": ["👤 Creator Hub","Creators and artists."],
"delivery": ["🚚 Delivery","Bookings and logistics."],
"family-tree": ["🌳 Family Tree","Heritage and relationships."],
"affiliate-tree": ["🌿 Affiliate Tree","Direct value referrals."],
"awards": ["🏅 Awards","Recognition and achievements."],
"sika-records": ["💎 SIKA Records","Trust and contribution records."],
    "world": ["🌍 World", "News, events, countries, weather, highlights and awards."],
    "my-world": ["👤 My World", "Profile, messages, mail, cards, awards, family tree and contribution records."],
    "community": ["🤝 Community", "Community Power, Community Voice, projects, mentorship, humanitarian and volunteering."],
    "real-education": ["🌱 Real Education", "Mind, body, purpose, nature, trades, technology, strategy, martial arts and service."],
    "culture": ["🎭 Culture", "Countries, languages, stories, proverbs, food, dance and heritage."],
    "music": ["🎵 Music", "Artists, releases, radio, playlists, charts, festivals and international song."],
    "sports": ["⚽ Sports", "World Cup, football, chess, martial arts, community sports and tournaments."],
    "business": ["🏪 Business", "Business Network, Creator Hub, Market, promotions and Affiliate Family Tree."],
    "experiences": ["🎪 Experiences", "Events, celebrations, comedy, games, festivals and watch parties."],
    "explorer": ["🗺 Explorer", "Search, discover, countries, creators, businesses, events, music, culture and sports."],
    "trust": ["🛡 Trust", "Privacy, security, terms, youth protection, policies, AI policy and finance policy."],
}

SYSTEMS = {
    "hrm": "🧠 HRM",
    "command": "🎛 Command",
    "sika": "💎 SIKA",
    "finance": "🏦 Finance",
    "connectivity": "📶 Connectivity",
    "mobility": "🛵 Mobility",
    "mail": "📧 Mail",
    "ollama": "🤖 Local AI / Ollama",
}

BRANCHES = {
    "world": ["Community News", "Events", "Countries", "Weather", "Highlights", "Awards"],
    "my-world": ["Profile", "Messages", "Mail", "Cards", "Awards", "Family Tree", "Contribution Records", "Settings"],
    "community": ["Community Power", "Community Voice", "Projects", "Mentorship", "Humanitarian", "Volunteering"],
    "real-education": ["Mind", "Body", "Purpose", "Nature", "Trades", "Technology", "Strategy", "Chess", "Martial Arts", "Muay Thai", "Business", "Service"],
    "culture": ["Countries", "Languages", "Food", "Stories", "Heritage", "Dance", "Proverbs", "United States of Africa (Black Stars)", "Ghana", "Akan", "KORADASO", "Begoro"],
    "music": ["Artists", "Releases", "Radio", "Playlists", "Charts", "Festivals", "International Song"],
    "sports": ["World Cup", "Football", "Chess", "IQ Arena", "Basketball", "Athletics", "Combat Sports", "Community Sports", "Tournaments"],
    "business": ["Business Network", "Creator Hub", "Market", "Promotions", "Affiliate Family Tree"],
    "experiences": ["Events", "Celebrations", "Comedy", "Games", "Watch Parties", "Festivals"],
    "explorer": ["Search", "Discover", "Countries", "Creators", "Businesses", "Events", "Music", "Culture", "Sports"],
    "trust": ["Privacy Promise", "Security", "Terms", "Youth Protection", "Community Standards", "Music & Media Policy", "AI Policy", "Finance Policy", "Contact & Reports"],
    "hrm": ["Dashboard", "Memory", "Learning", "Audit", "Risk", "Council", "Decisions", "Animals", "God Layer", "Youth Safety", "Ollama"],
    "command": ["Dashboard", "Operations", "Metrics", "Status", "Reports", "Logs", "Agents"],
    "sika": ["Trust Records", "Contribution Records", "Badges", "Verification", "Ledger Sandbox"],
    "finance": ["Dashboard", "Invoices", "Goals", "Pots", "Statements", "Activity"],
    "connectivity": ["eSIM", "Devices", "Coverage", "WiFi", "Signal Reports"],
    "mobility": ["Delivery", "E-Bikes", "Scooters", "Drivers", "Riders", "Logistics", "Community Transport", "Global Transport"],
    "mail": ["Inbox", "Sent", "Drafts", "Contacts", "Notifications"],
    "ollama": ["Local AI Status", "Prompts", "Memory Helper", "Risk Check", "Human Approval"],
}

TEAMS = [(f"slot-{i:02d}", f"Team Slot {i:02d}", "Qualification / Confirmed", "National anthem, team music, fan songs") for i in range(1, 49)]

CATS = ["Value Created", "Community Voice", "Music", "Culture", "Sport", "Business", "Real Education", "Experience", "Digital Card", "Mobility", "Finance", "Trust"]


def now():
    return datetime.utcnow().isoformat(timespec="seconds")


def safe(v):
    return escape((v or "").strip())


def slug(t):
    return t.lower().replace("&", "and").replace("/", "-").replace("(", "").replace(")", "").replace(" ", "-")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

<div class="card">
  <div class="metric">🏪</div>
  <h2>Business Network</h2>
  <p>Businesses Connected</p>
</div>

<div class="card">
  <div class="metric">👤</div>
  <h2>Creator Hub</h2>
  <p>Creators Connected</p>
</div>

<div class="card">
  <div class="metric">🚚</div>
  <h2>Delivery</h2>
  <p>Bookings Recorded</p>
</div>

<div class="card">
  <div class="metric">💎</div>
  <h2>SIKA Records</h2>
  <p>Trust Earned</p>
</div>
def init():
    con = db()
    con.execute("CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT, root TEXT, branch TEXT, title TEXT, name TEXT, location TEXT, category TEXT, notes TEXT, status TEXT, created_at TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS voice(id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, voice_type TEXT, choice TEXT, reason TEXT, created_at TEXT)")
    con.execute("""
CREATE TABLE IF NOT EXISTS businesses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
category TEXT,
location TEXT,
status TEXT,
notes TEXT,
created_at TEXT
)
""")

con.execute("""
CREATE TABLE IF NOT EXISTS creators(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
category TEXT,
location TEXT,
bio TEXT,
created_at TEXT
)
""")

con.execute("""
CREATE TABLE IF NOT EXISTS delivery_bookings(
id INTEGER PRIMARY KEY AUTOINCREMENT,
customer TEXT,
pickup TEXT,
dropoff TEXT,
item TEXT,
status TEXT,
created_at TEXT
)
""")

con.execute("""
CREATE TABLE IF NOT EXISTS family_tree(
id INTEGER PRIMARY KEY AUTOINCREMENT,
person TEXT,
relationship TEXT,
connected_to TEXT,
created_at TEXT
)
""")

con.execute("""
CREATE TABLE IF NOT EXISTS affiliate_tree(
id INTEGER PRIMARY KEY AUTOINCREMENT,
member TEXT,
referred_by TEXT,
status TEXT,
created_at TEXT
)
""")

con.execute("""
CREATE TABLE IF NOT EXISTS awards(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
recipient TEXT,
reason TEXT,
created_at TEXT
)
""")

con.execute("""
CREATE TABLE IF NOT EXISTS sika_records(
id INTEGER PRIMARY KEY AUTOINCREMENT,
member TEXT,
record_type TEXT,
points INTEGER,
notes TEXT,
created_at TEXT
)
""")
    con.execute("CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, detail TEXT, created_at TEXT)")
    con.commit()
    con.close()


def add_audit(action, detail):
    con = db()
    con.execute("INSERT INTO audit(action,detail,created_at) VALUES(?,?,?)", (action, detail, now()))
    con.commit()
    con.close()


init()


def nav():
    return "<a href='/'>Home</a>" + "".join([f"<a href='/{k}'>{v[0]}</a>" for k, v in ROOTS.items()])


def sysnav():
    return "".join([f"<a href='/{k}'>{v}</a>" for k, v in SYSTEMS.items()])


def layout(title, body):
    return f"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root {{
  --bg:#050505; --card:#101010; --gold:#d4af37; --blue:#00eaff;
  --text:#f7f0dd; --muted:#c9b987; --line:#6d5520; --green:#52d98f;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  background:radial-gradient(circle at top,#161616 0,#050505 55%,#000 100%);
  color:var(--text);
  font-family:Arial,Helvetica,sans-serif;
}}
header {{
  position:sticky; top:0; z-index:9;
  background:#050505ee;
  border-bottom:1px solid var(--gold);
  padding:14px;
}}
.brand {{
  font-family:Impact,Arial Black,sans-serif;
  color:var(--gold);
  font-size:26px;
  letter-spacing:3px;
  text-transform:uppercase;
}}
.tag {{ color:var(--muted); font-size:13px; letter-spacing:1px; }}
nav,.sys {{ display:flex; gap:8px; overflow:auto; padding-top:10px; }}
nav a,.sys a,.btn {{
  white-space:nowrap;
  text-decoration:none;
  color:var(--text);
  background:#111;
  border:1px solid var(--line);
  border-radius:999px;
  padding:9px 12px;
  font-weight:900;
}}
main,footer {{ max-width:1200px; margin:auto; padding:18px; }}
.hero {{
  background:linear-gradient(135deg,#090909,#161616,#123c52);
  border:1px solid var(--gold);
  border-radius:26px;
  padding:26px;
  margin-bottom:16px;
  box-shadow:0 0 30px #d4af3738;
}}
h1 {{ font-size:34px; margin-top:0; }}
.grid {{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:14px;
}}
.card {{
  display:block;
  background:linear-gradient(160deg,#090909,#111);
  border:1px solid var(--line);
  border-radius:20px;
  padding:18px;
  color:var(--text);
  text-decoration:none;
  box-shadow:0 0 18px #000;
}}
.card h2 {{ margin-top:0; }}
.metric {{ font-size:32px; color:var(--gold); font-weight:900; }}
.signal-green {{ color:var(--green); font-weight:900; }}
.neon {{ color:var(--blue); text-shadow:0 0 12px var(--blue); }}
input,select,textarea,button {{
  width:100%;
  padding:12px;
  margin:6px 0;
  border-radius:14px;
  border:1px solid var(--line);
  background:#050505;
  color:var(--text);
  font-size:15px;
}}
button {{ background:#1d8f5f; font-weight:900; cursor:pointer; }}
table {{
  width:100%;
  border-collapse:collapse;
  background:#101010;
  border-radius:18px;
  overflow:hidden;
  margin-top:14px;
}}
td,th {{
  border-bottom:1px solid var(--line);
  padding:10px;
  text-align:left;
  vertical-align:top;
}}
.warn {{
  background:#2c2108;
  border:1px solid var(--gold);
  border-radius:18px;
  padding:14px;
  margin:12px 0;
}}
.small {{ color:var(--muted); }}
</style>
</head>
<body>
<header>
  <div class="brand">ON ANY POSTCODE 🌍👑</div>
  <div class="tag">Born Local. Built Global. EARTH IS OUR TURF. One Race. Human Race.</div>
  <nav>{nav()}</nav>
</header>
<main>{body}</main>
<footer>
  <h3>System Engines</h3>
  <div class="sys">{sysnav()}</div>
  <p>💎 Create Value. 🤝 Build Trust. 🌱 Grow Community. 🏆 Leave A Legacy.</p>
  <p>3 IDENTITIES. 1 LEGACY. Global Luxury • Street Royalty • Future Sovereign</p>
</footer>
</body>
</html>"""


def records(root=None, branch=None):
    con = db()
    if root and branch:
        rows = con.execute("SELECT * FROM records WHERE root=? AND branch=? ORDER BY id DESC LIMIT 50", (root, branch)).fetchall()
    elif root:
        rows = con.execute("SELECT * FROM records WHERE root=? ORDER BY id DESC LIMIT 50", (root,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM records ORDER BY id DESC LIMIT 80").fetchall()
    con.close()
    return rows


def table(rows):
    if not rows:
        return "<div class='card'><h2>No records yet</h2><p>Create the first contribution record.</p></div>"
    body = "".join([f"<tr><td>{r['created_at']}</td><td>{r['root']}</td><td>{r['branch']}</td><td>{r['title']}</td><td>{r['status']}</td><td>{r['notes']}</td></tr>" for r in rows])
    return f"<table><tr><th>Time</th><th>Root</th><th>Branch</th><th>Title</th><th>Status</th><th>Notes</th></tr>{body}</table>"


def form(root, branch="General"):
    opts = "".join([f"<option>{c}</option>" for c in CATS])
    return f"""
<div class="card">
  <h2>Contribution Record</h2>
  <form method="post" action="/add-record">
    <input type="hidden" name="root" value="{root}">
    <input type="hidden" name="branch" value="{branch}">
    <input name="title" placeholder="Title / idea / action / content" required>
    <input name="name" placeholder="Name / creator / business / team / person">
    <input name="location" placeholder="Postcode / country / global">
    <select name="category">{opts}</select>
    <select name="status">
      <option>Idea</option>
      <option>Review</option>
      <option>Ready</option>
      <option>Active Record</option>
      <option>Completed</option>
      <option>Blocked</option>
    </select>
    <textarea name="notes" placeholder="Notes, rights proof, safety check, next action"></textarea>
    <button>Contribution Recorded</button>
  </form>
</div>
"""


@app.route("/")
def home():
    cards = "".join([f"<a class='card' href='/{k}'><h2>{v[0]}</h2><p>{v[1]}</p></a>" for k, v in ROOTS.items()])
    body = f"""
<section class="hero">
  <h1>OAP Final Roots v7 💎</h1>
  <h2>3 Identities. 1 Legacy.</h2>
  <p><b>Global Luxury</b> • <b>Street Royalty</b> • <span class="neon"><b>Future Sovereign</b></span></p>
  <p><b>EARTH IS OUR TURF.</b> One Race. Human Race.</p>
  <p>Every postcode has a story. Every culture has a song. Every community has a voice.</p>
  <div class="warn">Public systems create value today. Regulated systems such as banking, cards, e-money, telecom/eSIM service, taxi/private-hire operations and regulated payments require lawful authorisation or regulated providers before activation.</div>
</section>

<section class="grid">
  <div class="card"><div class="metric">💎</div><h2>Value Created</h2><p>Primary metric before revenue.</p></div>
  <div class="card"><div class="metric">🤝</div><h2>Trust Earned</h2><p>Proof, safety, contribution.</p></div>
  <div class="card"><div class="metric">🌱</div><h2>Communities Grown</h2><p>Local roots, global connection.</p></div>
  <div class="card"><div class="metric">🏆</div><h2>Legacy Created</h2><p>Cards, awards, culture, impact.</p></div>
</section>

<section class="grid">
  <div class="card"><h2 class="signal-green">🟢 Launch Signal</h2><p>No red lights if homepage, World Cup, Command and Trust open.</p></div>
  <div class="card"><h2>🎛 Dashboard Signal</h2><p>Command Center records actions, Community Voice and audit logs.</p></div>
  <div class="card"><h2>🤖 Ollama Signal</h2><p>Local AI is suggestions only. Human approval before action.</p></div>
  <div class="card"><h2>🛡 Trust Signal</h2><p>Privacy, youth safety, finance policy and media rights stay visible.</p></div>
</section>

<h2>Menu Roots</h2>
<section class="grid">{cards}</section>
"""
    return layout("OAP Final Roots v7", body)


@app.route("/<root>")
def root_page(root):
    if root == "sports":
        return sports()
    if root == "command":
        return command()
    if root == "trust":
        return trust()
    data = ROOTS.get(root) or [SYSTEMS.get(root, "Page"), "System engine for OAP operations and records."]
    branches = BRANCHES.get(root, [])
    cards = "".join([f"<a class='card' href='/{root}/{slug(b)}'><h2>{b}</h2><p>{data[0]} branch.</p></a>" for b in branches])
    return layout(data[0], f"<section class='hero'><h1>{data[0]}</h1><p>{data[1]}</p></section><section class='grid'>{cards}</section><h2>Record Value</h2>{form(root)}<h2>Latest Records</h2>{table(records(root))}")


@app.route("/<root>/<branch>")
def branch_page(root, branch):
    if root == "sports" and branch == "world-cup":
        return worldcup()
    if root == "sports" and branch in ["chess", "iq-arena"]:
        return chess()
    if root == "real-education" and branch in ["martial-arts", "muay-thai"]:
        return martial()
    title = branch.replace("-", " ").title()
    return layout(title, f"<section class='hero'><h1>{title}</h1><p>{root.replace('-', ' ').title()} branch inside OAP World.</p></section>{form(root, title)}<h2>Latest {title}</h2>{table(records(root, title))}")


def sports():
    cards = "".join([f"<a class='card' href='/sports/{slug(b)}'><h2>{b}</h2><p>Sports and tournament branch.</p></a>" for b in BRANCHES["sports"]])
    return layout("Sports", f"<section class='hero'><h1>⚽ Sports</h1><p>World Cup, football, chess, martial arts, tournaments and community sport.</p></section><section class='grid'>{cards}</section>{form('sports')}{table(records('sports'))}")


def worldcup():
    teamcards = "".join([f"<a class='card' href='/world-cup/team/{s}'><h2>{n}</h2><p>{r}</p><p><b>Music:</b> {m}</p></a>" for s, n, r, m in TEAMS])
    tournament = """
<section class="grid">
  <a class="card" href="/sports/world-cup"><h2>🏠 Tournament Home</h2><p>Overview, law, latest records.</p></a>
  <a class="card" href="/sports/world-cup/groups"><h2>🧩 Groups</h2><p>Group stage records.</p></a>
  <a class="card" href="/sports/world-cup/fixtures"><h2>📅 Fixtures</h2><p>Match schedule and matchday checklist.</p></a>
  <a class="card" href="/sports/world-cup/match-centre"><h2>⚽ Match Centre</h2><p>Preview, fan energy, manager notes.</p></a>
  <a class="card" href="/sports/world-cup/knockout"><h2>🔥 Knockout Rounds</h2><p>Round of 32 to semi finals.</p></a>
  <a class="card" href="/sports/world-cup/final"><h2>🏆 Final</h2><p>Final match centre and legacy records.</p></a>
  <a class="card" href="/community/community-voice"><h2>🌍 Community Voice</h2><p>Participation, not betting.</p></a>
  <a class="card" href="/cards"><h2>🏆 Digital Cards</h2><p>Team, anthem, culture and legacy cards.</p></a>
</section>
"""
    return layout("World Cup", f"<section class='hero'><h1>⚽ World Cup Tournament</h1><p>48-team ready: groups, fixtures, match centre, knockout rounds, final, team pages, national anthems, team music, Community Voice, watch parties, cards and awards.</p><div class='warn'>Compete with honor. No betting. No gambling. No loot boxes. No pay-to-win.</div></section>{tournament}<h2>Team Spaces</h2><section class='grid'>{teamcards}</section>")


@app.route("/world-cup/team/<team>")
def team_page(team):
    info = next((t for t in TEAMS if t[0] == team), None)
    if not info:
        return layout("Team Not Found", "<section class='hero'><h1>Team not found</h1></section>")
    s, n, r, m = info
    cards = "".join([f"<a class='card' href='/world-cup/team/{s}/{x}'><h2>{x.replace('-', ' ').title()}</h2><p>{n} section.</p></a>" for x in ["national-anthem", "team-music", "fan-songs", "manager-board", "fixtures", "matchday-checklist", "community-voice", "watch-parties", "cards", "awards"]])
    return layout(n, f"<section class='hero'><h1>{n} Team Space</h1><p><b>Region:</b> {r}</p><p><b>International Music:</b> {m}</p></section><section class='grid'>{cards}</section>{form('sports', n)}{table(records('sports', n))}")


@app.route("/world-cup/team/<team>/<section>", methods=["GET", "POST"])
def team_section(team, section):
    info = next((t for t in TEAMS if t[0] == team), None)
    if not info:
        return layout("Team Not Found", "<section class='hero'><h1>Team not found</h1></section>")
    s, n, r, m = info
    title = section.replace("-", " ").title()
    extra = ""
    if section == "national-anthem":
        extra = """<div class='card'><h2>🎵 National Anthem Player</h2><p>Default: Paused. User chooses play. Rights proof required.</p><audio controls preload='none'><source src='' type='audio/mpeg'>Your browser does not support audio.</audio><p class='small'>Add official/source link and rights proof as a contribution record below.</p></div>"""
    if request.method == "POST":
        con = db()
        con.execute("INSERT INTO voice(target,voice_type,choice,reason,created_at) VALUES(?,?,?,?,?)", (f"{n}/{title}", safe(request.form.get("voice_type")), safe(request.form.get("choice")), safe(request.form.get("reason")), now()))
        con.commit()
        con.close()
        add_audit("community_voice", f"{n}/{title}")
        return redirect(request.path)
    vf = ""
    if section == "community-voice":
        vf = """<div class='card'><h2>Community Voice</h2><form method='post'><select name='voice_type'><option>Best Team Energy</option><option>Best National Anthem</option><option>Best Team Music</option><option>Best Culture</option><option>Best Fans</option><option>Best Watch Party</option></select><input name='choice' placeholder='Your choice'><textarea name='reason' placeholder='Why?'></textarea><button>Voice Recorded</button></form></div>"""
    return layout(f"{n} {title}", f"<section class='hero'><h1>{n} / {title}</h1><p><b>Music identity:</b> {m}</p></section>{extra}{vf}{form('sports', f'{n} / {title}')}{table(records('sports', f'{n} / {title}'))}")


def chess():
    return layout("Chess / IQ Arena", f"<section class='hero'><h1>♟️ Chess / IQ Arena</h1><p>Chess, Ludo, Connect 4, logic, debates, strategy and mastery.</p></section>{form('real-education', 'Strategy / Chess')}{table(records('real-education', 'Strategy / Chess'))}")


def martial():
    return layout("Martial Arts", f"<section class='hero'><h1>🥋 Martial Arts</h1><p>Muay Thai, boxing, wrestling, judo, discipline, fitness, respect and self-control.</p></section>{form('real-education', 'Martial Arts')}{table(records('real-education', 'Martial Arts'))}")


def trust():
    return layout("Trust Center", f"<section class='hero'><h1>🛡 Trust Center</h1><p>Your data belongs to you. Your profile belongs to you. Your content belongs to you. Your culture belongs to you.</p><p>Privacy, security, youth protection, community standards, media rights, AI/HRM and finance readiness policies.</p></section>{form('trust')}{table(records('trust'))}")


def command():
    con = db()
    rc = con.execute("SELECT COUNT(*) c FROM records").fetchone()["c"]
    vc = con.execute("SELECT COUNT(*) c FROM voice").fetchone()["c"]
    aud = con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 30").fetchall()
    con.close()
    rows = "".join([f"<tr><td>{a['created_at']}</td><td>{a['action']}</td><td>{a['detail']}</td></tr>" for a in aud]) or "<tr><td colspan=3>No logs yet.</td></tr>"
    return layout("Command", f"<section class='hero'><h1>🎛 Command Center</h1><p>Agents, HRM, Local AI/Ollama, animals, God layer, youth safety, audit and launch status.</p></section><section class='grid'><div class='card'><div class='metric'>{rc}</div><h2>Records</h2></div><div class='card'><div class='metric'>{vc}</div><h2>Community Voice</h2></div><div class='card'><h2 class='signal-green'>🟢 Green</h2><p>No red lights if home, World Cup, Trust and Command open.</p></div><div class='card'><h2>🤖 Ollama</h2><p>Local AI suggestions only. Human approval before action.</p></div></section><h2>Audit Logs</h2><table><tr><th>Time</th><th>Action</th><th>Detail</th></tr>{rows}</table>")


@app.route("/cards")
def cards():
    return layout("Digital Cards", f"<section class='hero'><h1>🏆 Digital Cards</h1><p>Football cards, team cards, culture cards, music cards, fan cards, creator cards, heritage cards and contribution cards. No loot boxes. No gambling. No pay-to-win.</p></section>{form('experiences','Digital Cards')}{table(records('experiences','Digital Cards'))}")


@app.route("/add-record", methods=["POST"])
def add_record():
    vals = (
        safe(request.form.get("root")),
        safe(request.form.get("branch")),
        safe(request.form.get("title")),
        safe(request.form.get("name")),
        safe(request.form.get("location")),
        safe(request.form.get("category")),
        safe(request.form.get("notes")),
        safe(request.form.get("status")),
        now(),
    )
    con = db()
    con.execute("INSERT INTO records(root,branch,title,name,location,category,notes,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)", vals)
    con.commit()
    con.close()
    add_audit("record_added", f"{vals[0]} / {vals[2]}")
    return redirect("/" + (vals[0] or ""))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
