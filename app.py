from flask import Flask, request, redirect
from datetime import datetime
import os
import sqlite3

app = Flask(__name__)
DB = "oap_core_v2.db"

TEAMS = [
    ("ghana", "🇬🇭 Ghana", "Africa", "Highlife, Hiplife, Afrobeats, Gospel, Drill"),
    ("nigeria", "🇳🇬 Nigeria", "Africa", "Afrobeats, Fuji, Highlife, Street Pop"),
    ("morocco", "🇲🇦 Morocco", "Africa", "Gnawa, Chaabi, Rap, Amazigh sounds"),
    ("senegal", "🇸🇳 Senegal", "Africa", "Mbalax, Afrobeats, Hip Hop"),
    ("brazil", "🇧🇷 Brazil", "South America", "Samba, Funk, Bossa Nova, Pagode"),
    ("argentina", "🇦🇷 Argentina", "South America", "Cumbia, Tango, Rock Nacional"),
    ("france", "🇫🇷 France", "Europe", "Rap, Afro-French, Pop, Zouk links"),
    ("england", "🏴 England", "Europe", "Grime, UK Rap, Garage, Pop"),
    ("spain", "🇪🇸 Spain", "Europe", "Flamenco, Reggaeton, Pop"),
    ("germany", "🇩🇪 Germany", "Europe", "Hip Hop, Pop, Electronic"),
    ("italy", "🇮🇹 Italy", "Europe", "Pop, Trap, Opera heritage"),
    ("portugal", "🇵🇹 Portugal", "Europe", "Fado, Afro-Portuguese, Kuduro links"),
    ("usa", "🇺🇸 USA", "North America", "Hip Hop, R&B, Pop, Latin fusion"),
    ("mexico", "🇲🇽 Mexico", "North America", "Regional Mexican, Pop, Rap"),
    ("japan", "🇯🇵 Japan", "Asia", "J-Pop, City Pop, Hip Hop"),
    ("south-korea", "🇰🇷 South Korea", "Asia", "K-Pop, R&B, Hip Hop"),
    ("australia", "🇦🇺 Australia", "Oceania", "Pop, Rock, Hip Hop, First Nations music"),
    ("qatar", "🇶🇦 Qatar", "Middle East", "Khaleeji, Arabic Pop, Rap"),
]

PAGES = [
    ("/", "Home"),
    ("/social", "Social"),
    ("/create", "Create"),
    ("/world-cup", "World Cup"),
    ("/world-cup/teams", "Teams"),
    ("/votes", "Votes"),
    ("/music", "Music"),
    ("/media", "Media"),
    ("/business", "Business"),
    ("/creators", "Creators"),
    ("/events", "Events"),
    ("/market", "Market"),
    ("/mobility", "Mobility"),
    ("/connectivity", "eSIM"),
    ("/infrastructure", "Infrastructure"),
    ("/sika", "SIKA"),
    ("/bank", "Bank Core"),
    ("/hrm", "HRM"),
    ("/command", "Command"),
]

CATEGORIES = [
    "Text", "Image", "Video", "Film", "Lip Sync", "Motion/Dance",
    "Music", "Comedy", "World Cup", "Business", "Creator", "Event"
]


def now():
    return datetime.utcnow().isoformat(timespec="seconds")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            creator TEXT,
            postcode TEXT,
            category TEXT,
            team TEXT,
            media_type TEXT,
            content TEXT,
            rights_proof TEXT,
            safety_status TEXT,
            created_at TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT,
            vote_type TEXT,
            choice TEXT,
            reason TEXT,
            created_at TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT,
            title TEXT,
            name TEXT,
            location TEXT,
            notes TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            detail TEXT,
            created_at TEXT
        )
    """)
    con.commit()
    con.close()


def audit(action, detail):
    con = db()
    con.execute(
        "INSERT INTO audit_logs(action, detail, created_at) VALUES (?, ?, ?)",
        (action, detail, now())
    )
    con.commit()
    con.close()


init_db()


def slug_label(slug):
    for s, label, region, music in TEAMS:
        if s == slug:
            return label
    return slug.replace("-", " ").title()


def layout(title, body):
    nav = "".join([f"<a href='{url}'>{label}</a>" for url, label in PAGES])
    return f"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root {{
  --bg:#06130f;
  --card:#10251d;
  --line:#24533e;
  --hero:#123c52;
  --text:#f3fff8;
  --muted:#bde6d4;
  --gold:#ffd166;
  --green:#52d98f;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  font-family:Arial, Helvetica, sans-serif;
  background:var(--bg);
  color:var(--text);
}}
header {{
  background:#071b14;
  border-bottom:1px solid var(--line);
  position:sticky;
  top:0;
  z-index:5;
  padding:16px;
}}
.brand {{
  font-size:24px;
  font-weight:900;
  letter-spacing:2px;
}}
nav {{
  display:flex;
  gap:8px;
  overflow:auto;
  margin-top:12px;
  padding-bottom:4px;
}}
nav a {{
  white-space:nowrap;
  color:var(--text);
  text-decoration:none;
  background:var(--card);
  border:1px solid var(--line);
  padding:9px 12px;
  border-radius:999px;
  font-weight:700;
}}
main {{
  max-width:1200px;
  margin:auto;
  padding:18px;
}}
.hero {{
  background:var(--hero);
  border-radius:24px;
  padding:24px;
  margin-bottom:16px;
  box-shadow:0 10px 30px #0005;
}}
.grid {{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:14px;
}}
.card {{
  background:var(--card);
  border:1px solid var(--line);
  border-radius:20px;
  padding:18px;
  color:var(--text);
  text-decoration:none;
  display:block;
}}
.card h2 {{ margin-top:0; }}
.pill {{
  display:inline-block;
  background:#203d31;
  border:1px solid var(--line);
  border-radius:999px;
  padding:7px 10px;
  margin:4px;
  color:var(--muted);
}}
input, select, textarea, button {{
  width:100%;
  padding:12px;
  margin:6px 0;
  border-radius:14px;
  border:1px solid var(--line);
  background:#07130f;
  color:var(--text);
  font-size:15px;
}}
button, .btn {{
  background:#1d8f5f;
  font-weight:900;
  cursor:pointer;
  color:white;
  text-align:center;
  text-decoration:none;
  display:inline-block;
}}
table {{
  width:100%;
  border-collapse:collapse;
  background:var(--card);
  border-radius:18px;
  overflow:hidden;
  margin:12px 0;
}}
th, td {{
  border-bottom:1px solid var(--line);
  padding:10px;
  text-align:left;
  vertical-align:top;
}}
.warn {{
  background:#3b2b0d;
  border:1px solid #ffc857;
  border-radius:18px;
  padding:14px;
  margin:12px 0;
}}
.ok {{ color:var(--green); font-weight:900; }}
.gold {{ color:var(--gold); font-weight:900; }}
.small {{ color:var(--muted); font-size:14px; }}
footer {{
  padding:25px;
  text-align:center;
  color:var(--muted);
}}
</style>
</head>
<body>
<header>
  <div class="brand">ON ANY POSTCODE 🌍👑</div>
  <nav>{nav}</nav>
</header>
<main>{body}</main>
<footer>Born Local. Built Global. Earth Is Our Turf. No bets. No fake claims. Contribution Recorded.</footer>
</body>
</html>"""


def latest_posts(limit=30, team=None, category=None):
    con = db()
    q = "SELECT * FROM posts"
    args = []
    clauses = []

    if team:
        clauses.append("team=?")
        args.append(team)

    if category:
        clauses.append("category=?")
        args.append(category)

    if clauses:
        q += " WHERE " + " AND ".join(clauses)

    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)

    rows = con.execute(q, args).fetchall()
    con.close()
    return rows


def post_cards(rows):
    if not rows:
        return "<div class='card'><h2>No posts yet</h2><p>Create the first OAP record.</p></div>"

    html = ""
    for p in rows:
        team = slug_label(p["team"]) if p["team"] else "OAP"
        html += f"""
        <div class="card">
          <h2>{p["title"]}</h2>
          <p class="small">{p["category"]} • {p["media_type"]} • {team} • {p["postcode"]} • {p["created_at"]}</p>
          <p>{p["content"]}</p>
          <p><b>Creator:</b> {p["creator"]}</p>
          <p><b>Rights proof:</b> {p["rights_proof"] or "Review needed"}</p>
          <p><b>Safety:</b> <span class="gold">{p["safety_status"]}</span></p>
        </div>
        """
    return html


@app.route("/")
def home():
    cards = [
        ("/social", "📱 Social Feed", "Text, images, video, films, lip-sync, motion, comedy and creator posts."),
        ("/world-cup", "⚽ World Cup Command", "All teams, team music boards, manager boards, votes and watch parties."),
        ("/create", "📝 Create Post", "Add a post, media idea, music concept, team record or business promo."),
        ("/votes", "🗳 No-Bet Votes", "Fan votes only. No betting, odds, staking or gambling."),
        ("/music", "🎵 OAP Music", "Artist, anthem, team music and international culture records."),
        ("/media", "🎬 OAP Media Studio", "Images, long videos, films, motion, scripts and rights proof."),
        ("/mobility", "🛵 Mobility", "Delivery, e-bikes, scooters, taxi requests and logistics records."),
        ("/bank", "🏦 Bank Core Readiness", "Monzo-style finance structure, manual readiness records only."),
        ("/command", "🎛 Command Center", "Audit logs, HRM memory, records and system status."),
    ]

    grid = "".join([f"<a class='card' href='{u}'><h2>{h}</h2><p>{d}</p></a>" for u, h, d in cards])

    body = f"""
    <section class="hero">
      <h1>OAP Core v2 🚀</h1>
      <p>Social media, creative studio, World Cup team music, manager boards, no-bet voting, infrastructure, SIKA trust, HRM and bank-core readiness.</p>
      <div class="warn">
        <b>Boundary:</b> live banking, cards, e-money, telecom/eSIM service, taxi/private-hire operations and regulated payments require lawful authorisation or regulated providers before activation.
      </div>
    </section>
    <div class="grid">{grid}</div>
    """

    return layout("OAP Core v2", body)


@app.route("/social")
def social():
    body = """
    <section class="hero">
      <h1>OAP Social Feed 📱</h1>
      <p>Postcode social media with rights proof, safety review and HRM records.</p>
      <a class="btn" href="/create">Create Post</a>
    </section>
    <div class="grid">
    """ + post_cards(latest_posts()) + "</div>"
    return layout("Social Feed", body)


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        creator = request.form.get("creator", "").strip()
        postcode = request.form.get("postcode", "").strip()
        category = request.form.get("category", "Text")
        media_type = request.form.get("media_type", "Text")
        team = request.form.get("team", "")
        content = request.form.get("content", "").strip()
        rights = request.form.get("rights_proof", "").strip()
        safety = "Review Needed"

        con = db()
        con.execute("""
            INSERT INTO posts(
                title, creator, postcode, category, team, media_type,
                content, rights_proof, safety_status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, creator, postcode, category, team, media_type, content, rights, safety, now()))
        con.commit()
        con.close()

        audit("post_created", f"{category}: {title}")
        return redirect("/social")

    team_options = "<option value=''>General OAP</option>" + "".join([
        f"<option value='{s}'>{label}</option>" for s, label, region, music in TEAMS
    ])
    cat_options = "".join([f"<option>{c}</option>" for c in CATEGORIES])

    body = f"""
    <section class="hero">
      <h1>Create OAP Post 📝</h1>
      <p>For social, media, music, World Cup, business, events and creative ideas.</p>
    </section>

    <div class="card">
      <form method="post">
        <input name="title" placeholder="Title" required>
        <input name="creator" placeholder="Creator / artist / business / member name">
        <input name="postcode" placeholder="Postcode / country / continent">

        <select name="category">{cat_options}</select>

        <select name="media_type">
          <option>Text</option>
          <option>Image</option>
          <option>Video</option>
          <option>Long Film</option>
          <option>Lip Sync</option>
          <option>Motion/Dance</option>
          <option>Music/Anthem</option>
          <option>Podcast</option>
          <option>Live</option>
        </select>

        <select name="team">{team_options}</select>

        <textarea name="content" placeholder="Post, script, concept, music idea, manager note, fan energy, business promo"></textarea>
        <textarea name="rights_proof" placeholder="Rights proof / consent / source / owned or cleared media notes"></textarea>

        <button>Contribution Recorded</button>
      </form>
    </div>
    """

    return layout("Create Post", body)


@app.route("/world-cup")
def world_cup():
    body = """
    <section class="hero">
      <h1>World Cup Command ⚽🌍</h1>
      <p>Team spaces, international music, culture, manager boards, votes and watch parties. No bets.</p>
      <a class="btn" href="/world-cup/teams">Open Team Spaces</a>
    </section>
    <div class="warn">
      <b>No-bet law:</b> no odds, no staking, no gambling, no pay-to-win votes.
    </div>
    """
    body += team_grid()
    return layout("World Cup Command", body)


def team_grid():
    cards = "".join([
        f"""
        <a class="card" href="/world-cup/team/{s}">
          <h2>{label}</h2>
          <p>{region}</p>
          <p><b>Music:</b> {music}</p>
        </a>
        """
        for s, label, region, music in TEAMS
    ])
    return f"<div class='grid'>{cards}</div>"


@app.route("/world-cup/teams")
def teams():
    return layout(
        "World Cup Teams",
        "<section class='hero'><h1>All Team Spaces 🌍⚽</h1><p>Click a team to open its music, culture, manager board, votes and posts.</p></section>" + team_grid()
    )


@app.route("/world-cup/team/<slug>")
def team_page(slug):
    team = next((t for t in TEAMS if t[0] == slug), None)
    if not team:
        return layout("Team Not Found", "<section class='hero'><h1>Team not found</h1></section>")

    s, label, region, music = team
    rows = latest_posts(team=s)

    body = f"""
    <section class="hero">
      <h1>{label} Team Space</h1>
      <p><b>Region:</b> {region}</p>
      <p><b>International music board:</b> {music}</p>
      <p>Fan posts, anthem ideas, culture notes, manager board, votes and watch-party records.</p>
    </section>

    <div class="grid">
      <a class="card" href="/world-cup/team/{s}/music">
        <h2>🎵 Team Music</h2>
        <p>Anthems, artists, sounds and fan chants.</p>
      </a>

      <a class="card" href="/world-cup/team/{s}/manager">
        <h2>👔 Manager Board</h2>
        <p>Tactics, lineups, decisions and fan notes.</p>
      </a>

      <a class="card" href="/world-cup/team/{s}/votes">
        <h2>🗳 Vote</h2>
        <p>No-bet fan voting.</p>
      </a>

      <a class="card" href="/create">
        <h2>📝 Add Post</h2>
        <p>Create a team post or music idea.</p>
      </a>
    </div>

    <h2>Latest {label} Posts</h2>
    <div class="grid">{post_cards(rows)}</div>
    """

    return layout(label, body)


@app.route("/world-cup/team/<slug>/music")
def team_music(slug):
    label = slug_label(slug)
    body = f"""
    <section class="hero">
      <h1>{label} International Music 🎵</h1>
      <p>Submit anthems, artists, fan chants, culture sounds and rights-proof notes.</p>
      <a class="btn" href="/create">Submit Team Music</a>
    </section>
    <div class="grid">{post_cards(latest_posts(team=slug, category="Music"))}</div>
    """
    return layout(f"{label} Music", body)


@app.route("/world-cup/team/<slug>/manager")
def manager(slug):
    return record_page(
        "manager",
        f"{slug_label(slug)} Manager Board 👔",
        "Lineup ideas, tactics, manager decisions, fan notes and matchday review.",
        slug
    )


@app.route("/world-cup/team/<slug>/votes", methods=["GET", "POST"])
def team_votes(slug):
    if request.method == "POST":
        vt = request.form.get("vote_type", "Team Energy")
        choice = request.form.get("choice", "").strip()
        reason = request.form.get("reason", "").strip()

        con = db()
        con.execute(
            "INSERT INTO votes(team, vote_type, choice, reason, created_at) VALUES (?, ?, ?, ?, ?)",
            (slug, vt, choice, reason, now())
        )
        con.commit()
        con.close()

        audit("vote_recorded", f"{slug}: {vt} - {choice}")
        return redirect(f"/world-cup/team/{slug}/votes")

    con = db()
    votes = con.execute("SELECT * FROM votes WHERE team=? ORDER BY id DESC LIMIT 50", (slug,)).fetchall()
    con.close()

    rows = "".join([
        f"<tr><td>{v['created_at']}</td><td>{v['vote_type']}</td><td>{v['choice']}</td><td>{v['reason']}</td></tr>"
        for v in votes
    ]) or "<tr><td colspan=4>No votes yet.</td></tr>"

    body = f"""
    <section class="hero">
      <h1>{slug_label(slug)} No-Bet Votes 🗳</h1>
      <p>Fan voting only. No odds, no staking, no gambling.</p>
    </section>

    <div class="card">
      <form method="post">
        <select name="vote_type">
          <option>Team Energy</option>
          <option>Best Anthem</option>
          <option>Best Culture</option>
          <option>Best Fans</option>
          <option>Best Manager Decision</option>
          <option>Best Watch Party</option>
        </select>
        <input name="choice" placeholder="Your vote / choice">
        <textarea name="reason" placeholder="Reason"></textarea>
        <button>Record Vote</button>
      </form>
    </div>

    <table>
      <tr><th>Time</th><th>Vote</th><th>Choice</th><th>Reason</th></tr>
      {rows}
    </table>
    """

    return layout("Votes", body)


@app.route("/votes")
def votes_home():
    return layout(
        "Votes",
        "<section class='hero'><h1>No-Bet Vote System 🗳</h1><p>Choose a World Cup team page to vote. No betting, no odds, no staking.</p></section>" + team_grid()
    )


def record_page(module, title, desc, team=""):
    con = db()
    rows = con.execute(
        "SELECT * FROM records WHERE module=? AND (location=? OR ?='') ORDER BY id DESC LIMIT 50",
        (module, team, team)
    ).fetchall()
    con.close()

    table = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['title']}</td><td>{r['name']}</td><td>{r['status']}</td><td>{r['notes']}</td></tr>"
        for r in rows
    ]) or "<tr><td colspan=5>No records yet.</td></tr>"

    body = f"""
    <section class="hero">
      <h1>{title}</h1>
      <p>{desc}</p>
    </section>

    <div class="card">
      <form method="post" action="/add-record">
        <input type="hidden" name="module" value="{module}">
        <input type="hidden" name="location" value="{team}">
        <input name="title" placeholder="Title" required>
        <input name="name" placeholder="Name / creator / manager / business">
        <select name="status">
          <option>Idea</option>
          <option>Review</option>
          <option>Approved</option>
          <option>Active Record</option>
          <option>Blocked</option>
        </select>
        <textarea name="notes" placeholder="Notes"></textarea>
        <button>Contribution Recorded</button>
      </form>
    </div>

    <table>
      <tr><th>Time</th><th>Title</th><th>Name</th><th>Status</th><th>Notes</th></tr>
      {table}
    </table>
    """

    return layout(title, body)


@app.route("/add-record", methods=["POST"])
def add_record():
    module = request.form.get("module", "general")
    title = request.form.get("title", "").strip()
    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    notes = request.form.get("notes", "").strip()
    status = request.form.get("status", "Review")

    con = db()
    con.execute(
        "INSERT INTO records(module, title, name, location, notes, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (module, title, name, location, notes, status, now())
    )
    con.commit()
    con.close()

    audit("record_added", f"{module}: {title}")

    if module == "manager" and location:
        return redirect(f"/world-cup/team/{location}/manager")

    return redirect("/command")


def simple(title, desc, module):
    con = db()
    rows = con.execute("SELECT * FROM records WHERE module=? ORDER BY id DESC LIMIT 50", (module,)).fetchall()
    con.close()

    table = "".join([
        f"<tr><td>{r['created_at']}</td><td>{r['title']}</td><td>{r['name']}</td><td>{r['status']}</td><td>{r['notes']}</td></tr>"
        for r in rows
    ]) or "<tr><td colspan=5>No records yet.</td></tr>"

    body = f"""
    <section class="hero">
      <h1>{title}</h1>
      <p>{desc}</p>
    </section>

    <div class="card">
      <form method="post" action="/add-record">
        <input type="hidden" name="module" value="{module}">
        <input name="title" placeholder="Title" required>
        <input name="name" placeholder="Name / creator / business / member">
        <input name="location" placeholder="Postcode / country / global">
        <select name="status">
          <option>Idea</option>
          <option>Review</option>
          <option>Approved</option>
          <option>Active Record</option>
          <option>Blocked</option>
        </select>
        <textarea name="notes" placeholder="Notes, proof, next action"></textarea>
        <button>Contribution Recorded</button>
      </form>
    </div>

    <table>
      <tr><th>Time</th><th>Title</th><th>Name</th><th>Status</th><th>Notes</th></tr>
      {table}
    </table>
    """

    return layout(title, body)


@app.route("/music")
def music():
    return simple("OAP Music 🎵", "Artists, releases, team anthems, international boards, rights proof and campaign records.", "music")


@app.route("/media")
def media():
    return simple("OAP Media Studio 🎬", "Images, videos, long films, lip-sync, motion, scripts, TV, radio and podcasts.", "media")


@app.route("/business")
def business():
    return simple("Business Network 🏪", "Business listings, promo records, services, local offers and merchant readiness.", "business")


@app.route("/creators")
def creators():
    return simple("Creator Hub 🎨", "Creator profiles, channels, campaigns, collaborations and proof records.", "creators")


@app.route("/events")
def events():
    return simple("Community Events 🎪", "Gatherings, experiences, watch parties, meetups and event records.", "events")


@app.route("/market")
def market():
    return simple("OAP Market 🛒", "Products, services, tickets, creator stores and business commerce records.", "market")


@app.route("/mobility")
def mobility():
    return simple("Mobility Core 🛵", "Delivery, e-bikes, scooters, taxi requests, logistics and community transport records.", "mobility")


@app.route("/connectivity")
def connectivity():
    return simple("Connectivity / eSIM 📶", "eSIM requests, devices, coverage notes, signal logs and field operations.", "connectivity")


@app.route("/infrastructure")
def infrastructure():
    return simple("Infrastructure 🗺", "Maps, navigation, weather, search, routes, hubs and postcode intelligence.", "infrastructure")


@app.route("/sika")
def sika():
    return simple("SIKA Trust Records 💎", "Contribution records, badges, trust signals and audit-ready value history.", "sika")


@app.route("/bank")
def bank():
    return simple(
        "Prince Sovereign Bank Core 🏦",
        "Monzo-style finance readiness, KYC/KYB, compliance, ledger sandbox and manual approvals only. No live bank claim.",
        "bank"
    )


@app.route("/hrm")
def hrm():
    return simple("HRM / AI Council 🧠", "Memory logs, council notes, decision records, risk records and learning history.", "hrm")


@app.route("/command")
def command():
    con = db()
    post_count = con.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
    vote_count = con.execute("SELECT COUNT(*) c FROM votes").fetchone()["c"]
    record_count = con.execute("SELECT COUNT(*) c FROM records").fetchone()["c"]
    audits = con.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 40").fetchall()
    con.close()

    aud = "".join([
        f"<tr><td>{a['created_at']}</td><td>{a['action']}</td><td>{a['detail']}</td></tr>"
        for a in audits
    ]) or "<tr><td colspan=3>No audit logs yet.</td></tr>"

    body = f"""
    <section class="hero">
      <h1>Command Center 🎛</h1>
      <p>OAP Core v2 status, HRM memory, social records, World Cup votes and audit logs.</p>
    </section>

    <div class="grid">
      <div class="card"><h2>{post_count}</h2><p>Social / creative posts</p></div>
      <div class="card"><h2>{vote_count}</h2><p>No-bet votes</p></div>
      <div class="card"><h2>{record_count}</h2><p>Module records</p></div>
      <div class="card"><h2 class="ok">GREEN</h2><p>Core v2 active after deployment</p></div>
    </div>

    <h2>Audit Logs</h2>
    <table>
      <tr><th>Time</th><th>Action</th><th>Detail</th></tr>
      {aud}
    </table>
    """

    return layout("Command Center", body)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
