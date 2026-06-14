from flask import Flask, render_template_string

app = Flask(__name__)

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>ON ANY POSTCODE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body{
    background:#080808;
    color:white;
    font-family:Arial;
    margin:0;
}

.top{
    background:#111;
    padding:15px;
    border-bottom:1px solid #222;
}

.logo{
    font-size:22px;
    font-weight:bold;
}

.wrap{
    padding:20px;
    max-width:900px;
    margin:auto;
}

.card{
    background:#151515;
    border:1px solid #252525;
    border-radius:18px;
    padding:20px;
    margin-bottom:20px;
}

.green{
    color:#00dd99;
}

.nav a{
    color:#00dd99;
    text-decoration:none;
    margin-right:12px;
}

.hero{
    text-align:center;
    padding:40px 20px;
}

button{
    background:#00dd99;
    color:black;
    border:none;
    padding:12px 20px;
    border-radius:10px;
    font-weight:bold;
}
</style>

</head>

<body>

<div class="top">
    <div class="logo">ON ANY POSTCODE</div>
</div>

<div class="wrap">

<div class="nav">
<a href="/">Home</a>
<a href="/creators">Creators</a>
<a href="/events">Events</a>
<a href="/businesses">Businesses</a>
<a href="/messages">Messages</a>
<a href="/verify">Verify</a>
<a href="/promos">Promo Slots</a>
<a href="/founder">Founder</a>
<a href="/market">Market</a>
<a href="/admin">HRM</a>
</div>

{{content|safe}}

</div>

</body>
</html>
"""

@app.route("/")
def home():

    content = """

    <div class='card hero'>
        <h1>🌍 ON ANY POSTCODE 👑</h1>

        <p class='green'>
        ✨👑Born Local🔥💨🚀✨Built Global💎💦
        </p>

        <p>Earth Is Our Turf</p>

        <button>ENTER OAP</button>
    </div>

    <div class='card'>
        <h2>📰 Feed + News</h2>
        <p>OAP community feed system loading...</p>
    </div>

    <div class='card'>
        <h2>🎤 Creator Profiles</h2>
        <p>Creator ecosystem active...</p>
    </div>

    <div class='card'>
        <h2>⚽ Events</h2>
        <p>Events module active...</p>
    </div>

    <div class='card'>
        <h2>🏪 Business Board</h2>
        <p>Business ecosystem active...</p>
    </div>

    <div class='card'>
        <h2>💰 OAP Market</h2>
        <p>Commerce layer initializing...</p>
    </div>

    <div class='card'>
        <h2>🧠 HRM Review Core</h2>

        <ul>
            <li>Proof before execution</li>
            <li>Verification before sharing</li>
            <li>Audit before automation</li>
            <li>Human approval before action</li>
        </ul>
    </div>

    """

    return render_template_string(BASE, content=content)

@app.route("/creators")
def creators():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>🎤 Creator Profiles</h1>
        <p>Creator system ready.</p>
        </div>
        """
    )

@app.route("/events")
def events():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>⚽ Events</h1>
        <p>Events system ready.</p>
        </div>
        """
    )

@app.route("/businesses")
def businesses():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>🏪 Businesses</h1>
        <p>Business board ready.</p>
        </div>
        """
    )

@app.route("/messages")
def messages():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>💬 Messenger</h1>
        <p>Messenger module ready.</p>
        </div>
        """
    )

@app.route("/verify")
def verify():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>🛡️ Verification</h1>
        <p>Verification system ready.</p>
        </div>
        """
    )

@app.route("/promos")
def promos():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>💰 Promo Slots</h1>
        <p>Promo system ready.</p>
        </div>
        """
    )

@app.route("/founder")
def founder():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>👑 Founder Memberships</h1>
        <p>Founder system ready.</p>
        </div>
        """
    )

@app.route("/market")
def market():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>🛍️ OAP Market</h1>
        <p>Market system ready.</p>
        </div>
        """
    )

@app.route("/admin")
def admin():
    return render_template_string(
        BASE,
        content="""
        <div class='card'>
        <h1>🧠 HRM Admin Core</h1>
        <p>Guardian • Chancellor • Sentinel</p>
        </div>
        """
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
