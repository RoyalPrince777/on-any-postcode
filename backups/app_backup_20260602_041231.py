from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>🌍 OAP RESTORED ✅</h1><p>Open /feed /join /messages</p>"

@app.route("/feed")
def feed():
    return "<h1>🌍 Community Feed</h1>"

@app.route("/join")
def join():
    return "<h1>👑 Join OAP</h1>"

@app.route("/messages")
def messages():
    return "<h1>💬 Messenger</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
