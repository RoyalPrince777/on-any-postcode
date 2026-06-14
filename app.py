from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

signal_posts = []
room_messages = []
flag_counts = {}
profiles = []

teams = [
    ("A","🇲🇽","Mexico","El Tri"),("A","🇿🇦","South Africa","Bafana Bafana"),("A","🇰🇷","South Korea","Taegeuk Warriors"),("A","🇨🇿","Czechia","Národní tým"),
    ("B","🇨🇦","Canada","The Canucks"),("B","🇧🇦","Bosnia and Herzegovina","The Dragons"),("B","🇶🇦","Qatar","The Maroons"),("B","🇨🇭","Switzerland","The Nati"),
    ("C","🇧🇷","Brazil","Seleção"),("C","🇲🇦","Morocco","Atlas Lions"),("C","🇭🇹","Haiti","Les Grenadiers"),("C","🏴","Scotland","Tartan Army"),
    ("D","🇺🇸","United States","Stars and Stripes"),("D","🇵🇾","Paraguay","La Albirroja"),("D","🇦🇺","Australia","Socceroos"),("D","🇹🇷","Türkiye","Crescent-Stars"),
    ("E","🇩🇪","Germany","Die Mannschaft"),("E","🇨🇼","Curaçao","La Familia Azul"),("E","🇨🇮","Ivory Coast","The Elephants"),("E","🇪🇨","Ecuador","La Tri"),
    ("F","🇳🇱","Netherlands","Oranje"),("F","🇯🇵","Japan","Samurai Blue"),("F","🇸🇪","Sweden","Blågult"),("F","🇹🇳","Tunisia","Eagles of Carthage"),
    ("G","🇧🇪","Belgium","Red Devils"),("G","🇪🇬","Egypt","The Pharaohs"),("G","🇮🇷","Iran","Team Melli"),("G","🇳🇿","New Zealand","All Whites"),
    ("H","🇪🇸","Spain","La Roja"),("H","🇨🇻","Cape Verde","Blue Sharks"),("H","🇸🇦","Saudi Arabia","Green Falcons"),("H","🇺🇾","Uruguay","La Celeste"),
    ("I","🇫🇷","France","Les Bleus"),("I","🇸🇳","Senegal","Lions of Teranga"),("I","🇮🇶","Iraq","Lions of Mesopotamia"),("I","🇳🇴","Norway","The Lions"),
    ("J","🇦🇷","Argentina","La Albiceleste"),("J","🇩🇿","Algeria","Desert Foxes"),("J","🇦🇹","Austria","Das Team"),("J","🇯🇴","Jordan","The Chivalrous"),
    ("K","🇵🇹","Portugal","Seleção das Quinas"),("K","🇨🇩","DR Congo","The Leopards"),("K","🇺🇿","Uzbekistan","White Wolves"),("K","🇨🇴","Colombia","Los Cafeteros"),
    ("L","🏴","England","Three Lions"),("L","🇭🇷","Croatia","Vatreni"),("L","🇬🇭","Ghana","Black Stars"),("L","🇵🇦","Panama","Los Canaleros"),
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
nav{position:sticky;top:0;background:#092414;padding:14px;white-space:nowrap;overflow-x:auto}
nav a{color:white;text-decoration:none;font-weight:bold;margin-right:14px}
section{padding:22px;border-bottom:1px solid #1d4a2d}
.hero{background:linear-gradient(135deg,#092414,#14512b)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.card{background:#10281a;border:1px solid #245f38;border-radius:16px;padding:15px;margin:10px 0}
.badge{background:#27c267;color:#021;padding:5px 9px;border-radius:999px;font-weight:bold}
input,textarea,button{width:100%;box-sizing:border-box;padding:11px;margin:6px 0;border-radius:9px;border:0}
button{background:#27c267;color:#021;font-weight:bold}
.flag{font-size:36px}
table{width:100%;border-collapse:collapse;background:#10281a}
td,th{padding:10px;border-bottom:1px solid #245f38;text-align:left}
</style>
</head>
<body>

<nav>
<a href="#signal">📡 Signal</a>
<a href="#live">🔴 Live</a>
<a href="#rooms">⚽ Match Rooms</a>
<a href="#flags">🏳️ Flags</a>
<a href="#teams">🌍 Teams</a>
<a href="#tables">📊 Tables</a>
<a href="#replay">📜 Replay</a>
<a href="#anthems">🎶 Anthems</a>
<a href="#myworld">👤 My World</a>
<a href="#sovereign">👑 Sovereign</a>
</nav>

<section class="hero">
<h1>📺 OAP TV</h1>
<h2>📡 Signal First</h2>
<p>What's happening. What's lit. What's next.</p>
<p>Born Local. Built Global. Earth is our turf.</p>
</section>

<section id="signal">
<h2>📡 OAP Signal</h2>
<div class="grid">
<div class="card"><span class="badge">🔥 What's Lit</span><h3>World Cup signal is live</h3><p>Clean OAP TV starts here.</p></div>
<div class="card"><span class="badge">🇭🇹 Team Check</span><h3>Haiti included</h3><p>Haiti is in Group C.</p></div>
<div class="card"><span class="badge">🇬🇭 Group L</span><h3>Ghana ready</h3><p>Ghana, England, Croatia and Panama are locked.</p></div>
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
</div>
{% endfor %}
</div>
</section>

<section id="rooms">
<h2>⚽ Match Rooms</h2>
<div class="grid">
{% for state,date,group,home,away,score in matches %}
<div class="card">
<h3>{{home}} 🆚 {{away}}</h3>
<p>{{date}} | Group {{group}} | {{state}} | {{score}}</p>
<form method="post" action="/room">
<input type="hidden" name="room" value="{{home}} vs {{away}}">
<input name="name" placeholder="Nickname">
<input name="message" placeholder="Message">
<button>Post</button>
</form>
</div>
{% endfor %}
</div>

{% for m in room_messages %}
<div class="card"><b>{{m.room}}</b><br>{{m.name}}: {{m.message}}</div>
{% endfor %}
</section>

<section id="flags">
<h2>🏳️ Throw Your Flag Up</h2>
<div class="grid">
{% for group,flag,name,nick in teams %}
<div class="card">
<div class="flag">{{flag}}</div>
<h3>{{name}}</h3>
<p>{{nick}} | Group {{group}}</p>
<p>Energy: <b>{{flag_counts.get(name,0)}}</b></p>
<form method="post" action="/flag">
<input type="hidden" name="team" value="{{name}}">
<button>Throw {{flag}} Up</button>
</form>
</div>
{% endfor %}
</div>
</section>

<section id="teams">
<h2>🌍 Teams</h2>
<div class="grid">
{% for group,flag,name,nick in teams %}
<div class="card">
<div class="flag">{{flag}}</div>
<h3>{{name}}</h3>
<p><b>Nickname:</b> {{nick}}</p>
<p><b>Group:</b> {{group}}</p>
<p><b>Flag meaning:</b> Team culture and flag story section.</p>
<p>🎶 Anthem: manual play only.</p>
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
{% for group,flag,name,nick in teams if group == g %}
<tr><td>{{flag}} {{name}}</td><td>0</td></tr>
{% endfor %}
</table>
{% endfor %}
</section>

<section id="replay">
<h2>📜 Replay</h2>
<div class="grid">
{% for state,date,group,home,away,score in matches if state == "FT" %}
<div class="card">
<b>{{date}} | Group {{group}}</b>
<h3>{{home}} {{score}} {{away}}</h3>
<p>Player of the Match added after verification.</p>
</div>
{% endfor %}
</div>
</section>

<section id="anthems">
<h2>🎶 Anthems</h2>
<div class="card">Manual play only. Local owned/licensed files only. No autoplay.</div>
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
        room_messages=room_messages,
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
    room_messages.insert(0, {
        "room": request.form.get("room", "Match Room"),
        "name": request.form.get("name", "Visitor"),
        "message": request.form.get("message", "")
    })
    return redirect("/#rooms")

@app.route("/flag", methods=["POST"])
def flag():
    team = request.form.get("team", "")
    if team:
        flag_counts[team] = flag_counts.get(team, 0) + 1
    return redirect("/#flags")

@app.route("/myworld", methods=["POST"])
def myworld():
    profiles.insert(0, {
        "nickname": request.form.get("nickname", "OAP Visitor"),
        "country": request.form.get("country", "")
    })
    return redirect("/#myworld")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
