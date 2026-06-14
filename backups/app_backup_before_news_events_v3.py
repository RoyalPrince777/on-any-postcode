from flask import Flask, render_template_string

app = Flask(__name__)

STYLE = """
<style>
body{margin:0;font-family:Arial;background:#070807;color:#fff8e6}
header{padding:22px;background:#111006;border-bottom:1px solid #5b451c}
nav a{color:#ffd76b;margin-right:12px;text-decoration:none;font-weight:bold}
.wrap{padding:18px;max-width:1100px;margin:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card{background:#12120d;border:1px solid #4d3b18;border-radius:18px;padding:18px;margin:14px 0}
.hero{background:#181005;border-color:#ffd76b}
a{color:#ffd76b}
.small{opacity:.75;font-size:13px}
.badge{display:inline-block;background:#30240c;color:#ffd76b;padding:6px 10px;border-radius:20px;margin:4px}
button{background:#ffd76b;color:#080806;border:0;border-radius:12px;padding:12px 16px;font-weight:bold}
</style>
"""

NAV = """
<nav>
<a href="/">🌍 Home</a>
<a href="/news">📰 News</a>
<a href="/events">🎪 Events</a>
<a href="/culture">🎭 Culture</a>
<a href="/music">🎵 Music</a>
<a href="/creators">🎨 Creators</a>
<a href="/businesses">🏪 Businesses</a>
<a href="/market">🛒 Market</a>
<a href="/explorer">🔍 Explorer</a>
<a href="/weather">🌦 Weather</a>
<a href="/my-world">👤 My World</a>
<a href="/royal-dashboard">👑 Royal</a>
</nav>
"""

def page(title, body):
    return render_template_string(f"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{{{title}}}}</title>
{STYLE}
</head>
<body>
<header>
<h1>🌍 ON ANY POSTCODE</h1>
<p class="small">Born Local. Built Global. Earth Is Our Turf.</p>
{NAV}
</header>
<div class="wrap">
{{{{body|safe}}}}
</div>
</body>
</html>
""", title=title, body=body)

@app.route("/")
def home():
    return page("OAP Gateway", """
<div class="card hero">
<h2>👑 OAP Gateway</h2>
<p>One brand. One front door. One identity.</p>
<p>Community, culture, music, business, events, news, trust and My World — all through OAP.</p>
<a href="/join"><button>🌍 Join OAP</button></a>
<a href="/enter"><button>👤 Enter My World</button></a>
</div>

<div class="grid">
<div class="card"><h3>📰 News</h3><p>Daily community, sports, culture, business and opportunity updates.</p><a href="/news">Open News</a></div>
<div class="card"><h3>🎪 Events</h3><p>Watch parties, meetups, tournaments, community missions.</p><a href="/events">Open Events</a></div>
<div class="card"><h3>🎭 Culture</h3><p>Africa → Ghana → Akyem → Begoro → Koradaso and global culture spaces.</p><a href="/culture">Open Culture</a></div>
<div class="card"><h3>🎵 Music</h3><p>Artists, releases, campaigns, culture sound and OAP-owned media.</p><a href="/music">Open Music</a></div>
<div class="card"><h3>🎨 Creators</h3><p>Creator pages, profiles, promotion and community reach.</p><a href="/creators">Open Creators</a></div>
<div class="card"><h3>🏪 Businesses</h3><p>Business listings, merchant profiles and promo slots.</p><a href="/businesses">Open Businesses</a></div>
<div class="card"><h3>🛒 Market</h3><p>Products, merchants, orders and revenue records.</p><a href="/market">Open Market</a></div>
<div class="card"><h3>👤 My World</h3><p>Your identity hub: messages, mail, awards, SIKA, family tree, wallet and royalty.</p><a href="/my-world">Enter My World</a></div>
</div>
""")

@app.route("/join")
def join():
    return page("Join OAP", """
<div class="card hero">
<h2>🌍 Join OAP</h2>
<p>Create your OAP identity and prepare your World.</p>
<p><b>Launch language:</b> Join OAP → Create My World → Enter My World.</p>
</div>
""")

@app.route("/enter")
def enter():
    return page("Enter My World", """
<div class="card hero">
<h2>👤 Enter My World</h2>
<p>Member access starts here.</p>
<a href="/my-world"><button>Open My World</button></a>
</div>
""")

@app.route("/my-world")
def my_world():
    return page("My World", """
<div class="card hero">
<h2>👤 My World</h2>
<p>Your personal OAP hub.</p>
</div>
<div class="grid">
<div class="card"><h3>🪪 Identity</h3><a href="http://127.0.0.1:5019">Open Identity</a></div>
<div class="card"><h3>💬 Messenger</h3><a href="http://127.0.0.1:5004">Open Messenger</a></div>
<div class="card"><h3>📧 Mail</h3><a href="http://127.0.0.1:5005">Open Mail</a></div>
<div class="card"><h3>🏆 Awards</h3><a href="http://127.0.0.1:5008">Open Awards</a></div>
<div class="card"><h3>🌳 Family Tree</h3><a href="http://127.0.0.1:5009">Open Family Tree</a></div>
<div class="card"><h3>💎 SIKA</h3><a href="http://127.0.0.1:5010">Open SIKA Core</a></div>
<div class="card"><h3>💳 Wallet</h3><a href="http://127.0.0.1:5011">Open Wallet</a></div>
<div class="card"><h3>👑 Royal Dashboard</h3><a href="/royal-dashboard">Open Royal Dashboard</a></div>
</div>
""")

@app.route("/news")
def news():
    return page("OAP News", """
<div class="card hero">
<h2>📰 OAP News</h2>
<p>Human-centered operational news. No doom-scrolling. No panic. Community-first awareness.</p>
</div>
<div class="grid">
<div class="card"><h3>🌍 Community</h3><p>Local updates, postcode stories, member highlights.</p></div>
<div class="card"><h3>⚽ Sports</h3><p>Matches, watch parties, tournaments, community sports.</p></div>
<div class="card"><h3>🎭 Culture</h3><p>Heritage, music, food, language, festivals.</p></div>
<div class="card"><h3>🏪 Business</h3><p>Local businesses, offers, launches, merchant updates.</p></div>
<div class="card"><h3>🎨 Creators</h3><p>Artists, creators, campaigns, releases.</p></div>
<div class="card"><h3>🎪 Events</h3><p>Upcoming events, meetups, OAP missions.</p></div>
<div class="card"><h3>🌦 Weather</h3><p>Weather notes and field awareness.</p></div>
<div class="card"><h3>💡 Opportunities</h3><p>Jobs, skills, volunteering, learning, community chances.</p></div>
</div>
""")

@app.route("/events")
def events():
    return page("OAP Events", """
<div class="card hero">
<h2>🎪 OAP Events</h2>
<p>Events connect online community to real-world action.</p>
</div>
<div class="grid">
<div class="card"><h3>⚽ Watch Parties</h3><p>Football, boxing, tournaments and major moments.</p></div>
<div class="card"><h3>🤝 Community Meetups</h3><p>Local connection, clean community building.</p></div>
<div class="card"><h3>🎵 Music Events</h3><p>Artists, listening sessions, cultural nights.</p></div>
<div class="card"><h3>🏪 Business Events</h3><p>Pop-ups, markets, promo days.</p></div>
<div class="card"><h3>🐝 Bee Missions</h3><p>Coordination tasks and community missions.</p></div>
</div>
""")

@app.route("/culture")
def culture():
    return page("Culture", """
<div class="card hero">
<h2>🎭 OAP Culture</h2>
<p>Every postcode has a story. Every culture has a song. Every community has a voice.</p>
</div>
<div class="grid">
<div class="card"><h3>🌍 Africa</h3><p>Includes Ghana, Akan, Akyem, Begoro, Koradaso.</p><a href="/culture/africa/ghana">Open Ghana</a></div>
<div class="card"><h3>🇪🇺 Europe</h3><p>UK, London, boroughs, postcode culture.</p></div>
<div class="card"><h3>🌎 Americas</h3><p>North America, South America, Caribbean.</p></div>
<div class="card"><h3>🌏 Asia / Oceania / Middle East</h3><p>Global communities inside OAP.</p></div>
</div>
""")

@app.route("/culture/africa/ghana")
def ghana():
    return page("Ghana Layer", """
<div class="card hero">
<h2>🇬🇭 Ghana Layer</h2>
<p>Ghana sits inside Africa, connected to culture, heritage, music, business, events and community intelligence.</p>
</div>
<div class="grid">
<div class="card"><h3>Akan / Akyem</h3><p>Heritage, language, proverbs, stories.</p></div>
<div class="card"><h3>Begoro</h3><p>Community records and local roots.</p></div>
<div class="card"><h3>Koradaso</h3><p>Heritage, identity and legacy layer.</p></div>
<div class="card"><h3>Ghana News</h3><p>Culture, creators, business and community updates.</p></div>
</div>
""")

@app.route("/music")
def music():
    return page("Music", """
<div class="card hero">
<h2>🎵 OAP Music</h2>
<p>OAP-owned music destination first. External platforms are optional routes, not the core.</p>
</div>
""")

@app.route("/creators")
def creators():
    return page("Creators", """
<div class="card hero">
<h2>🎨 OAP Creators</h2>
<p>Creator pages, campaigns, promotion, media and trust records.</p>
</div>
""")

@app.route("/businesses")
def businesses():
    return page("Businesses", """
<div class="card hero">
<h2>🏪 OAP Businesses</h2>
<p>Business listings, merchant pages and local promotion.</p>
<a href="http://127.0.0.1:5006/merchants">Open Merchant Engine</a>
</div>
""")

@app.route("/market")
def market():
    return page("Market", """
<div class="card hero">
<h2>🛒 OAP Market</h2>
<p>Your Shopify-style commerce layer.</p>
<a href="http://127.0.0.1:5006">Open Market Engine</a>
</div>
""")

@app.route("/explorer")
def explorer():
    return page("Explorer", """
<div class="card hero">
<h2>🔍 OAP Explorer</h2>
<p>Search creators, businesses, events, news, postcodes and communities.</p>
<a href="http://127.0.0.1:5026">Open Explorer Engine</a>
</div>
""")

@app.route("/weather")
def weather():
    return page("Weather", """
<div class="card hero">
<h2>🌦 Weather / Navigation</h2>
<p>Local field awareness, weather intelligence and movement support.</p>
<a href="http://127.0.0.1:5013">Open Weather Engine</a>
</div>
""")

@app.route("/sika")
def sika():
    return page("SIKA", """
<div class="card hero">
<h2>💎 SIKA Core</h2>
<p>Trust records first. Money later. No bank claims without lawful authorization.</p>
<a href="http://127.0.0.1:5010">Open SIKA Core</a>
</div>
""")

@app.route("/wallet")
def wallet():
    return page("SIKA Wallet", """
<div class="card hero">
<h2>💳 SIKA Wallet</h2>
<p>Wallet-style UX for internal trust/value records. Not legal tender. Not licensed banking.</p>
<a href="http://127.0.0.1:5011">Open Wallet</a>
</div>
""")

@app.route("/royal-dashboard")
def royal_dashboard():
    return page("Royal Dashboard", """
<div class="card hero">
<h2>👑 Royal Dashboard</h2>
<p>Royalty means service, stewardship, dignity, legacy, culture and responsibility.</p>
</div>
<div class="grid">
<div class="card"><h3>📜 Heritage Records</h3><p>Family, culture, roots and continuity.</p></div>
<div class="card"><h3>🌳 Family Tree</h3><p>Roots, relationships, mentorship and legacy.</p></div>
<div class="card"><h3>🏆 Awards</h3><p>Recognition through contribution, not fame alone.</p></div>
<div class="card"><h3>💎 SIKA Trust</h3><p>Contribution and trust record history.</p></div>
<div class="card"><h3>🧠 HRM Legacy</h3><p>Memory, decisions, lessons and records.</p></div>
<div class="card"><h3>🎭 Culture Stewardship</h3><p>Protect culture. Preserve dignity. Build hope.</p></div>
<div class="card"><h3>🤝 Community Service</h3><p>Royalty protects and serves the people.</p></div>
<div class="card"><h3>📚 Archive</h3><p>Proof, records, stories and long-term memory.</p></div>
</div>
""")

@app.route("/dashboard")
def dashboard():
    return page("Dashboard", """
<div class="card hero">
<h2>👑 Sovereign Dashboard</h2>
<p>Operational overview and admin command view.</p>
<a href="http://127.0.0.1:5024">Open Dashboard Engine</a>
</div>
""")

@app.route("/admin")
def admin():
    return page("Admin", """
<div class="card hero">
<h2>⚙ Admin Tools</h2>
<p>Hidden/internal systems. Not for normal public browsing.</p>
</div>
<div class="grid">
<div class="card"><a href="http://127.0.0.1:5002">🧠 HRM Core</a></div>
<div class="card"><a href="http://127.0.0.1:5003">🎛 Command Center</a></div>
<div class="card"><a href="http://127.0.0.1:5014">🤖 AI Router</a></div>
<div class="card"><a href="http://127.0.0.1:5018">🦍 Sentinel</a></div>
<div class="card"><a href="http://127.0.0.1:5020">📊 Analytics</a></div>
<div class="card"><a href="http://127.0.0.1:5021">💾 Storage</a></div>
<div class="card"><a href="http://127.0.0.1:5022">🔄 Recovery</a></div>
<div class="card"><a href="http://127.0.0.1:5033">🚦 Launch Center</a></div>
</div>
""")

@app.route("/health")
def health():
    return {"status": "ok", "service": "oap_gateway", "port": 5000}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
