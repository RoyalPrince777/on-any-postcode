from flask import Flask, request, redirect, render_template_string
from datetime import datetime

app = Flask(__name__)

energy_posts = []
watch_parties = []
predictions = []

matches = [
    {"date":"11 Jun","state":"FT","group":"A","home":"🇲🇽 Mexico","away":"🇿🇦 South Africa","score":"2-0"},
    {"date":"11 Jun","state":"FT","group":"A","home":"🇰🇷 South Korea","away":"🇨🇿 Czechia","score":"2-1"},
    {"date":"12 Jun","state":"FT","group":"B","home":"🇨🇦 Canada","away":"🇧🇦 Bosnia","score":"1-1"},
    {"date":"12 Jun","state":"FT","group":"D","home":"🇺🇸 USA","away":"🇵🇾 Paraguay","score":"4-1"},
    {"date":"13 Jun","state":"FT","group":"C","home":"🇧🇷 Brazil","away":"🇲🇦 Morocco","score":"1-1"},
    {"date":"14 Jun","state":"LIVE","group":"D","home":"🇦🇺 Australia","away":"🇹🇷 Turkey","score":"2-0"},
    {"date":"17 Jun","state":"UPCOMING","group":"L","home":"🏴 England","away":"🇭🇷 Croatia","score":"16:00"},
    {"date":"17 Jun","state":"UPCOMING","group":"L","home":"🇬🇭 Ghana","away":"🇵🇦 Panama","score":"19:00"},
]

rankings = [
    ("1","🇦🇷","Argentina"),("2","🇫🇷","France"),("3","🇪🇸","Spain"),
    ("4","🏴","England"),("5","🇧🇷","Brazil"),("42","🇬🇭","Ghana")
]

tables = {
    "Group L":[("🏴 England",0),("🇭🇷 Croatia",0),("🇬🇭 Ghana",0),("🇵🇦 Panama",0)],
    "Group A":[("🇲🇽 Mexico",3),("🇰🇷 South Korea",3),("🇨🇿 Czechia",0),("🇿🇦 South Africa",0)]
}

HTML = """
<!doctype html>
<title>OAP World Cup Energy</title>
<style>
body{font-family:Arial;background:#07140d;color:#f4fff7;margin:0}
nav{background:#0b2b17;padding:14px;position:sticky;top:0}
nav a{color:#fff;margin:0 10px;text-decoration:none;font-weight:bold}
section{padding:20px;border-bottom:1px solid #244}
.card{background:#10281a;border:1px solid #245f38;border-radius:14px;padding:14px;margin:10px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
input,select,textarea,button{width:100%;padding:10px;margin:6px 0;border-radius:8px;border:0}
button{background:#27c267;color:#021;font-weight:bold}
table{width:100%;border-collapse:collapse;background:#10281a}
td,th{padding:10px;border-bottom:1px solid #245f38;text-align:left}
.badge{padding:4px 8px;border-radius:999px;background:#27c267;color:#021;font-weight:bold}
.pitch{white-space:pre;text-align:center;background:#0d3b1e;border-radius:14px;padding:15px}
</style>

<nav>
<a href="#matches">⚽ Match Centre</a>
<a href="#vs">⚔️ VS Board</a>
<a href="#pitch">🟩 Pitch</a>
<a href="#energy">⚡ OAP Energy</a>
<a href="#watch">🎪 Watch Parties</a>
<a href="#predictions">🏆 Predictions</a>
</nav>

<section>
<h1>🌍⚽ OAP World Cup Energy v1</h1>
<p>Movement gives direction. Energy gives life. HRM remembers. Community creates value.</p>
</section>

<section id="matches">
<h2>🌍 World Rankings</h2>
<div class="grid">
{% for r,f,c in rankings %}
<div class="card"><b>{{r}}</b> {{f}} {{c}} <span class="badge">World Rank</span></div>
{% endfor %}
</div>

<h2>⚽ Match Centre</h2>
<div class="grid">
{% for m in matches %}
<div class="card">
<b>{{m.state}}</b> | {{m.date}} | {{m.group}}<br>
<h3>{{m.home}} 🆚 {{m.away}}</h3>
<p>Score/Time: <b>{{m.score}}</b></p>
</div>
{% endfor %}
</div>

<h2>📊 Group Tables</h2>
{% for group, rows in tables.items() %}
<h3>{{group}}</h3>
<table><tr><th>Team</th><th>PTS</th></tr>
{% for team, pts in rows %}
<tr><td>{{team}}</td><td>{{pts}}</td></tr>
{% endfor %}
</table>
{% endfor %}

<h2>🏆 Knockout Journey</h2>
<div class="card">Round of 32 → Round of 16 → Quarter Finals → Semi Finals → Third Place → Final</div>
</section>

<section id="vs">
<h2>⚔️ VS Board</h2>
<div class="card">
<h3>🏴 England 🆚 🇭🇷 Croatia</h3>
<p><b>Key Duel:</b> Jude Bellingham vs Luka Modrić</p>
<p><b>Opportunity:</b> England attack wide. Croatia control tempo.</p>
<p><b>Threat:</b> Transitions, set pieces, midfield overloads.</p>
</div>
</section>

<section id="pitch">
<h2>⚽🟩 Pitch Board</h2>
<div class="grid">
<div class="card"><h3>🏴 England 4-2-3-1</h3><div class="pitch">
Kane

Gordon  Bellingham  Saka

Rice  Mainoo

Shaw Guehi Stones Walker

Pickford
</div></div>
<div class="card"><h3>🇭🇷 Croatia 4-3-3</h3><div class="pitch">
Petković

Perišić Kramarić Majer

Modrić Kovačić

Sosa Gvardiol Šutalo Juranović

Livaković
</div></div>
</div>

<h2>📋 Team Lineups + Manager Board</h2>
<div class="card">
<b>Opportunities:</b> 🟢 flank attacks | 🔵 midfield overload | 🟡 set pieces<br>
<b>Manager Notes:</b> Press, protect transitions, watch key duels.
</div>
</section>

<section>
<h2>🎖 Top Performers</h2>
<div class="card">
<h3>🏅 Player of the Match</h3>
<p>👤 Name: TBD</p>
<p>🌍 Country Flag: TBD</p>
<p>🛡 National Team: TBD</p>
<p>🏟 Club Team: TBD</p>
<p>🎽 Position: TBD</p>
<p>⭐ Rating: TBD</p>
<p>📖 Reason: Added after match verification.</p>
</div>

<h2>🎌 International Anthems</h2>
<div class="card">
<p>Manual play only. Local owned/licensed files only. No autoplay.</p>
<button>▶️ Ghana Anthem Placeholder</button>
<button>▶️ England Anthem Placeholder</button>
</div>
</section>

<section id="energy">
<h2>⚡ OAP Energy</h2>
<form method="post" action="/energy">
<input name="name" placeholder="Name / nickname">
<select name="type">
<option>🔥 Reaction</option><option>😂 Banter</option><option>🎤 Voice</option><option>📸 Moment</option><option>🕺 Culture</option>
</select>
<textarea name="body" placeholder="Drop the energy..."></textarea>
<button>Post Energy</button>
</form>
{% for p in energy_posts %}
<div class="card"><b>{{p.name}}</b> {{p.type}}<br>{{p.body}}</div>
{% endfor %}
</section>

<section id="watch">
<h2>🎪 Watch Parties</h2>
<form method="post" action="/watch">
<input name="match" placeholder="Match e.g. 🇬🇭 Ghana vs 🇵🇦 Panama">
<input name="postcode" placeholder="Postcode">
<input name="venue" placeholder="Venue">
<input name="time" placeholder="Date / Time">
<input name="host" placeholder="Host">
<input name="capacity" placeholder="Capacity">
<button>Create Watch Party</button>
</form>
{% for w in watch_parties %}
<div class="card"><b>{{w.match}}</b><br>📍 {{w.postcode}} | {{w.venue}} | {{w.time}} | Host: {{w.host}} | Cap: {{w.capacity}}</div>
{% endfor %}
</section>

<section id="predictions">
<h2>🏆 Prediction Board</h2>
<form method="post" action="/predict">
<input name="name" placeholder="Name">
<input name="match" placeholder="Match">
<input name="prediction" placeholder="Prediction e.g. 🇬🇭 2-1 🇵🇦">
<button>Submit Prediction</button>
</form>
{% for p in predictions %}
<div class="card"><b>{{p.name}}</b>: {{p.match}} → {{p.prediction}}</div>
{% endfor %}
</section>
"""

@app.route("/")
def home():
    return render_template_string(HTML, matches=matches, rankings=rankings, tables=tables,
                                  energy_posts=energy_posts, watch_parties=watch_parties,
                                  predictions=predictions)

@app.route("/energy", methods=["POST"])
def energy():
    energy_posts.insert(0, {
        "name": request.form.get("name","OAP"),
        "type": request.form.get("type","⚡ Energy"),
        "body": request.form.get("body","")
    })
    return redirect("/#energy")

@app.route("/watch", methods=["POST"])
def watch():
    watch_parties.insert(0, {
        "match": request.form.get("match",""),
        "postcode": request.form.get("postcode",""),
        "venue": request.form.get("venue",""),
        "time": request.form.get("time",""),
        "host": request.form.get("host",""),
        "capacity": request.form.get("capacity","")
    })
    return redirect("/#watch")

@app.route("/predict", methods=["POST"])
def predict():
    predictions.insert(0, {
        "name": request.form.get("name",""),
        "match": request.form.get("match",""),
        "prediction": request.form.get("prediction","")
    })
    return redirect("/#predictions")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
