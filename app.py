from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

signal_posts = []
team_messages = []
flag_counts = {}
profiles = []

teams = [
    ("A","🇲🇽","Mexico","El Tri","Flag meaning: hope, unity, sacrifice, and ancient identity."),
    ("A","🇿🇦","South Africa","Bafana Bafana","Flag meaning: unity after struggle and many histories joining together."),
    ("A","🇰🇷","South Korea","Taegeuk Warriors","Flag meaning: balance, heaven, earth, water and fire."),
    ("A","🇨🇿","Czechia","Národní tým","Flag meaning: Bohemian colours and historic Czechoslovak identity."),

    ("B","🇨🇦","Canada","The Canucks","Flag meaning: maple leaf, nature, identity, red and white."),
    ("B","🇧🇦","Bosnia and Herzegovina","The Dragons","Flag meaning: Europe, peace, continuity and stars."),
    ("B","🇶🇦","Qatar","The Maroons","Flag meaning: maroon heritage, white peace, nine-point edge."),
    ("B","🇨🇭","Switzerland","The Nati","Flag meaning: unity, neutrality, white cross on red."),

    ("C","🇧🇷","Brazil","Seleção","Flag meaning: nature, wealth, sky, stars, Order and Progress."),
    ("C","🇲🇦","Morocco","Atlas Lions","Flag meaning: courage, heritage, wisdom, peace and tradition."),
    ("C","🇭🇹","Haiti","Les Grenadiers","Flag meaning: unity, sacrifice, liberty and independence."),
    ("C","🏴","Scotland","Tartan Army","Flag meaning: Saint Andrew, loyalty and Scottish identity."),

    ("D","🇺🇸","United States","Stars and Stripes","Flag meaning: states, colonies, courage, purity and justice."),
    ("D","🇵🇾","Paraguay","La Albirroja","Flag meaning: courage, peace, liberty and independence."),
    ("D","🇦🇺","Australia","Socceroos","Flag meaning: history, federation and Southern Cross."),
    ("D","🇹🇷","Türkiye","Crescent-Stars","Flag meaning: Turkish identity, crescent, star and pride."),

    ("E","🇩🇪","Germany","Die Mannschaft","Flag meaning: unity, freedom and democratic identity."),
    ("E","🇨🇼","Curaçao","La Familia Azul","Flag meaning: sea, sky, sun and the island stars."),
    ("E","🇨🇮","Ivory Coast","The Elephants","Flag meaning: land, peace, hope and forests."),
    ("E","🇪🇨","Ecuador","La Tri","Flag meaning: resources, sky, sea and sacrifice."),

    ("F","🇳🇱","Netherlands","Oranje","Flag meaning: Dutch identity with orange football heritage."),
    ("F","🇯🇵","Japan","Samurai Blue","Flag meaning: rising sun and Japanese identity."),
    ("F","🇸🇪","Sweden","Blågult","Flag meaning: blue and yellow national heritage."),
    ("F","🇹🇳","Tunisia","Eagles of Carthage","Flag meaning: sacrifice, peace and cultural identity."),

    ("G","🇧🇪","Belgium","Red Devils","Flag meaning: national colours from Belgian history."),
    ("G","🇪🇬","Egypt","The Pharaohs","Flag meaning: revolution, peace, strength and power."),
    ("G","🇮🇷","Iran","Team Melli","Flag meaning: faith, peace, courage and national identity."),
    ("G","🇳🇿","New Zealand","All Whites","Flag meaning: Southern Cross, history and geography."),

    ("H","🇪🇸","Spain","La Roja","Flag meaning: Spanish kingdoms, unity and heritage."),
    ("H","🇨🇻","Cape Verde","Blue Sharks","Flag meaning: ocean, islands, peace, effort and hope."),
    ("H","🇸🇦","Saudi Arabia","Green Falcons","Flag meaning: faith, strength and justice."),
    ("H","🇺🇾","Uruguay","La Celeste","Flag meaning: historic regions and the Sun of May."),

    ("I","🇫🇷","France","Les Bleus","Flag meaning: liberty, equality and fraternity."),
    ("I","🇸🇳","Senegal","Lions of Teranga","Flag meaning: hope, wealth, sacrifice and unity."),
    ("I","🇮🇶","Iraq","Lions of Mesopotamia","Flag meaning: courage, peace, hope and Arab identity."),
    ("I","🇳🇴","Norway","The Lions","Flag meaning: Nordic identity, freedom and heritage."),

    ("J","🇦🇷","Argentina","La Albiceleste","Flag meaning: sky blue, white and independence."),
    ("J","🇩🇿","Algeria","Desert Foxes","Flag meaning: hope, peace and cultural identity."),
    ("J","🇦🇹","Austria","Das Team","Flag meaning: red-white-red Austrian identity."),
    ("J","🇯🇴","Jordan","The Chivalrous","Flag meaning: Arab heritage, unity and faith."),

    ("K","🇵🇹","Portugal","Seleção das Quinas","Flag meaning: hope, sacrifice, shields and discovery."),
    ("K","🇨🇩","DR Congo","The Leopards","Flag meaning: peace, sacrifice, wealth, hope and unity."),
    ("K","🇺🇿","Uzbekistan","White Wolves","Flag meaning: sky, peace, nature, moon and stars."),
    ("K","🇨🇴","Colombia","Los Cafeteros","Flag meaning: wealth, seas, sky and courage."),

    ("L","🏴","England","Three Lions","Flag meaning: Saint George, bravery and protection."),
    ("L","🇭🇷","Croatia","Vatreni","Flag meaning: Slavic colours and Croatian checkerboard heritage."),
    ("L","🇬🇭","Ghana","Black Stars","Flag meaning: sacrifice, gold, land and African unity."),
    ("L","🇵🇦","Panama","Los Canaleros","Flag meaning: peace, honesty and political balance."),
]

matches = [
    ("FT","11 Jun","A","🇲🇽 Mexico","🇿🇦 South Africa","2-0"),
    ("FT","11 Jun","A","🇰🇷 South Korea","🇨🇿 Czechia","2-1"),
    ("FT","12 Jun","B","🇨🇦 Canada","🇧🇦 Bosnia and Herzegovina","1-1"),
    ("FT","12 Jun","D","🇺🇸 United States","🇵🇾 Paraguay","4-1"),
    ("FT","13 Jun","C","🇧🇷 Brazil","🇲🇦 Morocco","1-1"),
    ("FT","13 Jun","C","🇭🇹 Haiti","🏴 Scotland","0-1"),
    ("FT","14 Jun","D","🇦🇺 Australia","🇹🇷 Türkiye","2-0"),
    ("NEXT","14 Jun","E","🇩🇪 Germany","🇨🇼 Curaçao","13:00"),
    ("NEXT","14 Jun","F","🇳🇱 Netherlands","🇯🇵 Japan","16:00"),
    ("NEXT","17 Jun","L","🏴 England","🇭🇷 Croatia","16:00"),
    ("NEXT","17 Jun","L","🇬🇭 Ghana","🇵🇦 Panama","19:00"),
]

HTML = """
<!doctype html>
<html>
<head>
<title>OAP TV</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#06120b;color:#f5fff7;font-family:Arial}
nav{position:sticky;top:0;background:#092414;padding:14px;white-space:nowrap;overflow-x:auto;z-index:10}
nav a{color:white;text-decoration:none;font-weight:bold;margin-right:14px}
section{padding:22px;border-bottom:1px solid #1d4a2d}
.hero{background:linear-gradient(135deg,#092414,#14512b)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:12px}
.card{background:#10281a;border:1px solid #245f38;border-radius:16px;padding:15px;margin:10px 0}
.badge{background:#27c267;color:#021;padding:5px 9px;border-radius:999px;font-weight:bold;display:inline-block}
input,textarea,button{width:100%;box-sizing:border-box;padding:11px;margin:6px 0;border-radius:9px;border:0}
button{background:#27c267;color:#021;font-weight:bold}
.flag{font-size:42px}
.small{opacity:.82}
table{width:100%;border-collapse:collapse;background:#10281a;margin-bottom:15px}
td,th{padding:10px;border-bottom:1px solid #245f38;text-align:left}
.team{border-left:5px solid #27c267}
</style>
</head>
<body>

<nav>
<a href="#signal">📡 Signal</a>
<a href="#live">🔴 Live</a>
<a href="#teams">🌍 Teams</a>
<a href="#myworld">👤 My World</a>
<a href="#sovereign">👑 Sovereign</a>
</nav>

<section class="hero">
<h1>📺 OAP TV</h1>
<h2>Signal → Live → Teams → My World</h2>
<p>Born Local. Built Global. Earth is our turf.</p>
</section>

<section id="signal">
<h2>📡 OAP Signal</h2>
<div class="grid">
<div class="card"><span class="badge">🔥 What's Lit</span><h3>Clean OAP TV is live</h3><p>No Watch Parties. No Predictions. No extra boards.</p></div>
<div class="card"><span class="badge">🌍 Teams</span><h3>Everything now lives inside Teams</h3><p>Flags, meaning, rooms, fixtures, results, replay, anthem, cards and team book.</p></div>
<div class="card"><span class="badge">🇭🇹 Team Check</span><h3>Haiti included</h3><p>Haiti is in Group C.</p></div>
</div>

<form method="post" action="/signal">
<input name="name" placeholder="Nickname">
<textarea name="body" placeholder="Drop OAP Signal..."></textarea>
<button>Post Signal</button>
</form>

{% for p in signal_posts %}
<div class="card"><b>{{p.name}}</b><p>{{p.body}}</p></div>
{% endfor %}
</section>

<section id="live">
<h2>🔴 Live / Next</h2>
<div class="grid">
{% for state,date,group,home,away,score in matches if state != "FT" %}
<div class="card">
<b>{{state}}</b> | {{date}} | Group {{group}}
<h3>{{home}} 🆚 {{away}}</h3>
<p><b>{{score}}</b></p>
<p class="small">Tap the team below to enter its match room.</p>
</div>
{% endfor %}
</div>
</section>

<section id="teams">
<h2>🌍 Teams</h2>
<p class="small">Every nation has a home. Everything lives inside the team.</p>

<div class="grid">
{% for group,flag,name,nick,meaning in teams %}
<div class="card team" id="{{name|replace(' ','-')}}">
<div class="flag">{{flag}}</div>
<h2>{{name}}</h2>
<p><b>{{nick}}</b> | Group {{group}}</p>

<h3>🏳️ Throw Your Flag Up</h3>
<p>Support: <b>{{flag_counts.get(name,0)}}</b></p>
<form method="post" action="/flag">
<input type="hidden" name="team" value="{{name}}">
<button>Throw {{flag}} Up</button>
</form>

<h3>🌍 Flag Meaning</h3>
<p>{{meaning}}</p>

<h3>⚽ Team Match Room</h3>
<form method="post" action="/room">
<input type="hidden" name="room" value="{{name}} Team Room">
<input name="name" placeholder="Nickname">
<input name="message" placeholder="Message for {{name}}">
<button>Post in {{name}} Room</button>
</form>

<h3>📅 Fixtures / Results</h3>
{% for state,date,mgroup,home,away,score in matches if name in home or name in away %}
<div class="card">
<b>{{state}}</b> | {{date}} | Group {{mgroup}}<br>
{{home}} 🆚 {{away}}<br>
<b>{{score}}</b>
</div>
{% endfor %}

<h3>📜 Replay</h3>
<p>Key moments and Player of the Match added after verification.</p>

<h3>🎶 Anthem</h3>
<p>Manual play only. Local owned/licensed files only. No autoplay.</p>
<button>▶️ {{name}} Anthem Placeholder</button>

<h3>🃏 Digital Cards</h3>
<p>Team Card · Hero Card · Legend Card · Icon Card</p>

<h3>📖 Team Book</h3>
<p>□ Team Card · □ Hero Card · □ Legend Card · □ Icon Card</p>
</div>
{% endfor %}
</div>
</section>

<section id="tables">
<h2>📊 Tables</h2>
{% for g in "ABCDEFGHIJKL" %}
<h3>Group {{g}}</h3>
<table>
<tr><th>Team</th><th>PTS</th></tr>
{% for group,flag,name,nick,meaning in teams if group == g %}
<tr><td>{{flag}} {{name}}</td><td>0</td></tr>
{% endfor %}
</table>
{% endfor %}
</section>

<section>
<h2>💬 Latest Team Room Messages</h2>
{% for m in team_messages %}
<div class="card"><b>{{m.room}}</b><br>{{m.name}}: {{m.message}}</div>
{% endfor %}
</section>

<section id="myworld">
<h2>👤 My World</h2>
<form method="post" action="/myworld">
<input name="nickname" placeholder="Nickname">
<input name="country" placeholder="Country / Flag">
<button>Enter My World</button>
</form>
{% for p in profiles %}
<div class="card">👤 {{p.nickname}} | {{p.country}}</div>
{% endfor %}
</section>

<section id="sovereign">
<h2>👑 Sovereign Prince Dashboard</h2>
<div class="grid">
<div class="card">📡 Signal Agent</div>
<div class="card">⚽ Match Agent</div>
<div class="card">🌍 Community Agent</div>
<div class="card">🛡 Guardian Agent</div>
<div class="card">📜 HRM Agent</div>
<div class="card">🎯 Mission Agent</div>
</div>
<div class="card">👑 Sovereign Veto: Green continue. Yellow review. Red stop.</div>
</section>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(
        HTML,
        teams=teams,
        matches=matches,
        signal_posts=signal_posts,
        team_messages=team_messages,
        flag_counts=flag_counts,
        profiles=profiles
    )

@app.route("/signal", methods=["POST"])
def signal():
    signal_posts.insert(0, {
        "name": request.form.get("name", "OAP"),
        "body": request.form.get("body", "")
    })
    return redirect("/#signal")

@app.route("/room", methods=["POST"])
def room():
    team_messages.insert(0, {
        "room": request.form.get("room", "Team Room"),
        "name": request.form.get("name", "Visitor"),
        "message": request.form.get("message", "")
    })
    return redirect("/#teams")

@app.route("/flag", methods=["POST"])
def flag():
    team = request.form.get("team", "")
    if team:
        flag_counts[team] = flag_counts.get(team, 0) + 1
    return redirect("/#teams")

@app.route("/myworld", methods=["POST"])
def myworld():
    profiles.insert(0, {
        "nickname": request.form.get("nickname", "OAP Visitor"),
        "country": request.form.get("country", "")
    })
    return redirect("/#myworld")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
