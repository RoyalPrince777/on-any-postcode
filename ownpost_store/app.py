from flask import Flask, Response, jsonify, render_template_string, request
import os

app = Flask(__name__)

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#050706">
<link rel="manifest" href="/manifest.webmanifest">
<title>OwnPost Store</title>
<style>
:root{--bg:#050706;--panel:#0c100e;--line:#1d2822;--green:#37f29a;--text:#f4fff9;--muted:#8ba096}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#0e261b 0,#050706 34%);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}.wrap{max-width:980px;margin:auto;padding:22px}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:24px}.brand{font-size:26px;font-weight:900;letter-spacing:-.7px}.pill{border:1px solid #25593e;background:#0d2419;color:var(--green);padding:8px 12px;border-radius:999px;font-size:12px}.hero,.card{background:rgba(12,16,14,.9);border:1px solid var(--line);border-radius:28px;box-shadow:0 24px 80px rgba(0,0,0,.28)}.hero{padding:28px}.hero h1{font-size:40px;line-height:1.02;margin:0 0 12px}.hero p{color:var(--muted);max-width:680px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}button,a.btn{appearance:none;border:0;text-decoration:none;cursor:pointer;padding:13px 18px;border-radius:16px;font-weight:800}.primary{background:var(--green);color:#04110a}.secondary{background:#111713;color:white;border:1px solid var(--line)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:18px}.card{padding:20px}.icon{height:52px;width:52px;border-radius:17px;display:grid;place-items:center;background:#11271c;border:1px solid #24553a;font-size:24px}.card h2{margin:14px 0 3px}.muted{color:var(--muted)}.security{margin-top:18px;padding:18px;border:1px solid var(--line);border-radius:20px;background:#09100c}.status{display:flex;gap:8px;align-items:center}.dot{width:9px;height:9px;border-radius:50%;background:var(--green);box-shadow:0 0 18px var(--green)}footer{color:#65756d;text-align:center;padding:28px 0}.install-note{font-size:12px;color:var(--muted);margin-top:10px}@media(max-width:700px){.grid{grid-template-columns:1fr}.hero h1{font-size:32px}.top{align-items:flex-start;flex-direction:column}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top"><div><div class="brand">OwnPost Store</div><div class="muted">Independent application distribution</div></div><div class="pill">● SELF-HOSTED CORE</div></div>
  <section class="hero">
    <div class="status"><span class="dot"></span><strong>Store online</strong></div>
    <h1>Your apps.<br>Your distribution.</h1>
    <p>Install the OwnPost Store directly on Android as a progressive web app. This first live release is the private distribution front door for OwnPost applications.</p>
    <div class="actions"><button id="install" class="primary">Install OwnPost Store</button><a class="btn secondary" href="#apps">Browse applications</a></div>
    <div class="install-note" id="installNote">On Android Chrome, choose “Install app” or “Add to Home screen” if the install button is unavailable.</div>
  </section>
  <div id="apps" class="grid">
    <article class="card"><div class="icon">🔐</div><h2>OwnPost Messenger</h2><div class="muted">Private messaging · groups · media · calls</div><p>Messaging shell for the independent communications network. Native end-to-end encryption and APK packaging are the next release gate.</p><button class="secondary" onclick="alert('Messenger native package is the next release gate.')">Release status</button></article>
    <article class="card"><div class="icon">📦</div><h2>OwnPost Store</h2><div class="muted">Version 0.1.0 · PWA</div><p>Installable store front door with controlled application catalog and update channel.</p><button class="primary" id="install2">Install</button></article>
  </div>
  <section class="security"><strong>Architecture rule</strong><p class="muted">No Firebase, Supabase, Twilio, or third-party chat provider in the core messaging path. The production messenger will use self-hosted identity, realtime transport, storage, database and device-side encryption.</p></section>
  <footer>OwnPost · Born Local. Built Global.</footer>
</div>
<script>
let deferredPrompt=null;window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;});async function install(){if(deferredPrompt){deferredPrompt.prompt();await deferredPrompt.userChoice;deferredPrompt=null}else{document.getElementById('installNote').textContent='Use your browser menu → Install app / Add to Home screen.'}}document.getElementById('install').onclick=install;document.getElementById('install2').onclick=install;if('serviceWorker'in navigator){navigator.serviceWorker.register('/sw.js')}
</script>
</body></html>'''

@app.get('/')
def index():
    return render_template_string(HTML)

@app.get('/health')
def health():
    return jsonify(status='ok', service='ownpost-store', version='0.1.0')

@app.get('/manifest.webmanifest')
def manifest():
    return jsonify({
        'name':'OwnPost Store','short_name':'OwnPost','start_url':'/','display':'standalone',
        'background_color':'#050706','theme_color':'#050706',
        'description':'Independent OwnPost application distribution.'
    })

@app.get('/sw.js')
def sw():
    code="""const C='ownpost-v1';const A=['/','/manifest.webmanifest'];self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>c.addAll(A))));self.addEventListener('fetch',e=>e.respondWith(fetch(e.request).catch(()=>caches.match(e.request))));"""
    return Response(code, mimetype='application/javascript')

if __name__ == '__main__':
    port=int(os.getenv('PORT','10000'))
    app.run(host='0.0.0.0',port=port)
