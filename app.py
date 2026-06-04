from flask import Flask
app=Flask(__name__)
PAGES=['World','Join OAP','News','Events','Business','Creators','Music','Media Radio TV Podcasts','Market','Community Power','Mobility Delivery E-Bike Scooter Taxi Logistics','Connectivity eSIM Devices Coverage','Infrastructure Maps Navigation Weather Search','SIKA Trust Records','Prince Sovereign Bank Core / SIKA Finance','Compliance Tracker','HRM AI Council','Command Center']
@app.route('/')
def home():
    cards=''.join([f"<div class=card><h2>{p}</h2><p>OAP Everything Structure v1 record and readiness module.</p></div>" for p in PAGES])
    return f"""<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>body{{font-family:Arial;background:#07130f;color:#f3fff8;padding:20px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.card{{background:#10251d;border:1px solid #24533e;border-radius:18px;padding:16px}}.hero{{background:#123c52;border-radius:22px;padding:25px;margin-bottom:15px}}</style></head><body><div class=hero><h1>ON ANY POSTCODE 🌍👑</h1><h2>Everything Structure v1</h2><p>Community, media, market, mobility, eSIM, infrastructure, SIKA trust, HRM, and Monzo-style finance core preparation.</p><p><b>Boundary:</b> live banking, cards, e-money, telecom/eSIM service, taxi/private-hire operations and regulated payments require lawful authorisation or regulated providers before activation.</p></div><div class=grid>{cards}</div></body></html>"""
if __name__=='__main__': app.run(host='0.0.0.0',port=5000,debug=True)
