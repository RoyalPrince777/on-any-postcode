from flask import Flask, request, session, redirect, render_template_string, jsonify, Response
from werkzeug.security import check_password_hash
from psycopg import connect
from psycopg.rows import dict_row
import os, time, json, secrets

app=Flask(__name__)
app.secret_key=os.environ.get('BELL_ME_SECRET', secrets.token_hex(32))
DB=os.environ['DATABASE_URL']

def db(): return connect(DB, autocommit=True, row_factory=dict_row)

def init_db():
    with db() as c:
        c.execute('create table if not exists link_call_signals(id bigserial primary key, room text not null, sender_id bigint not null, target_id bigint not null, kind text not null, payload text not null, created_at bigint not null)')
        c.execute('create index if not exists link_call_signals_room_idx on link_call_signals(room,id)')
init_db()

STYLE='''body{margin:0;background:#050706;color:#f4fff9;font:15px/1.5 system-ui,sans-serif}.wrap{max-width:920px;margin:auto;padding:18px}.card{background:#0c100e;border:1px solid #1d2822;border-radius:24px;padding:18px;margin-bottom:14px}.btn,button{border:0;border-radius:14px;padding:11px 14px;font-weight:800;cursor:pointer;text-decoration:none;display:inline-block}.primary{background:#37f29a;color:#04110a}.secondary{background:#131915;color:#fff;border:1px solid #1d2822}.danger{background:#7d1d1d;color:#fff}input{width:100%;box-sizing:border-box;background:#070b09;color:#fff;border:1px solid #1d2822;border-radius:14px;padding:12px}.row{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}video{width:100%;background:#000;border-radius:18px;min-height:220px}.muted{color:#8ba096}.live{color:#37f29a}@media(max-width:700px){.grid{grid-template-columns:1fr}}'''

def page(body,title='Bell Me'):
    return render_template_string(f'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{STYLE}</style></head><body><div class="wrap"><h1>📞 Bell Me</h1><p class="muted">THE LINK · peer-to-peer WebRTC calling</p>{body}</div></body></html>''')

@app.route('/',methods=['GET','POST'])
def home():
    if request.method=='POST' and 'uid' not in session:
        with db() as c:u=c.execute('select * from link_users where username=%s',(request.form.get('username','').strip().lower(),)).fetchone()
        if u and check_password_hash(u['password_hash'],request.form.get('password','')):session['uid']=u['id'];return redirect('/')
    if 'uid' not in session:
        return page('''<div class="card"><h2>Use your THE LINK account</h2><form method="post"><p><input name="username" placeholder="Username" required></p><p><input name="password" type="password" placeholder="Password" required></p><button class="primary">Enter Bell Me</button></form></div>''')
    uid=session['uid']
    with db() as c:me=c.execute('select username,display_name from link_users where id=%s',(uid,)).fetchone();people=c.execute('select id,username,display_name from link_users where id<>%s order by display_name limit 100',(uid,)).fetchall()
    cards=''.join(f'<div class="card"><b>{p["display_name"]}</b><div class="muted">@{p["username"]}</div><p><a class="btn primary" href="/call/{p["id"]}">📞 Bell Me</a></p></div>' for p in people) or '<div class="card">No other THE LINK accounts yet.</div>'
    return page(f'<div class="card"><b>{me["display_name"]}</b> <span class="muted">@{me["username"]}</span> · <a href="/logout">Logout</a></div>{cards}')

@app.get('/logout')
def logout():session.clear();return redirect('/')

def room_for(a,b):return f'{min(a,b)}-{max(a,b)}'

@app.get('/call/<int:peer_id>')
def call(peer_id):
    uid=session.get('uid')
    if not uid:return redirect('/')
    with db() as c:peer=c.execute('select id,username,display_name from link_users where id=%s',(peer_id,)).fetchone()
    if not peer or peer_id==uid:return redirect('/')
    room=room_for(uid,peer_id)
    body=f'''<div class="card"><h2>Calling {peer['display_name']}</h2><div class="muted">@{peer['username']} · Room {room}</div><p id="status" class="live">Ready</p></div><div class="grid"><div class="card"><b>You</b><video id="local" autoplay muted playsinline></video></div><div class="card"><b>{peer['display_name']}</b><video id="remote" autoplay playsinline></video></div></div><div class="card row"><button id="start" class="primary">Start Call</button><button id="accept" class="secondary">Accept</button><button id="mute" class="secondary">Mute</button><button id="cam" class="secondary">Camera Off</button><button id="hang" class="danger">Hang Up</button></div><div class="card muted">No commercial call provider is used. Signaling is stored on your OAP database. Media is WebRTC peer-to-peer. TURN relay is not configured yet, so some mobile/NAT networks may not connect.</div><script>
const ME={uid},PEER={peer_id},ROOM='{room}';let pc=null,stream=null,last=0,started=false;
const S=document.getElementById('status'),L=document.getElementById('local'),R=document.getElementById('remote');
async function sig(kind,payload){{await fetch('/api/signal/'+ROOM,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{target_id:PEER,kind,payload}})}})}}
async function media(){{if(!stream){{stream=await navigator.mediaDevices.getUserMedia({{audio:true,video:true}});L.srcObject=stream}}return stream}}
async function makePC(){{if(pc)return pc;pc=new RTCPeerConnection({{iceServers:[]}});(await media()).getTracks().forEach(t=>pc.addTrack(t,stream));pc.ontrack=e=>R.srcObject=e.streams[0];pc.onicecandidate=e=>{{if(e.candidate)sig('ice',e.candidate)}};pc.onconnectionstatechange=()=>S.textContent='Connection: '+pc.connectionState;return pc}}
async function offer(){{let p=await makePC(),o=await p.createOffer();await p.setLocalDescription(o);await sig('offer',o);started=true;S.textContent='Ringing…'}}
async function handle(m){{if(m.kind==='offer'){{let p=await makePC();await p.setRemoteDescription(m.payload);S.textContent='Incoming call from {peer['display_name']}';window.pendingOffer=true}}else if(m.kind==='answer'){{await pc.setRemoteDescription(m.payload)}}else if(m.kind==='ice'){{try{{await (await makePC()).addIceCandidate(m.payload)}}catch(e){{}}}}else if(m.kind==='hangup')hang(false)}}
async function poll(){{try{{let r=await fetch('/api/signals/'+ROOM+'?after='+last),a=await r.json();for(let m of a){{last=Math.max(last,m.id);await handle(m)}}}}catch(e){{}}setTimeout(poll,1000)}}
async function accept(){{if(!window.pendingOffer)return;let a=await pc.createAnswer();await pc.setLocalDescription(a);await sig('answer',a);window.pendingOffer=false;S.textContent='Connecting…'}}
function hang(send=true){{if(send)sig('hangup',{{}});if(pc)pc.close();pc=null;if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;L.srcObject=null;R.srcObject=null;S.textContent='Call ended'}}
document.getElementById('start').onclick=offer;document.getElementById('accept').onclick=accept;document.getElementById('mute').onclick=()=>{{if(stream)stream.getAudioTracks().forEach(t=>t.enabled=!t.enabled)}};document.getElementById('cam').onclick=()=>{{if(stream)stream.getVideoTracks().forEach(t=>t.enabled=!t.enabled)}};document.getElementById('hang').onclick=()=>hang(true);poll();
</script>'''
    return page(body,'Bell Me')

@app.post('/api/signal/<room>')
def post_signal(room):
    uid=session.get('uid');d=request.get_json(silent=True) or {}
    if not uid:return('',401)
    target=int(d.get('target_id',0));kind=str(d.get('kind',''))
    if kind not in {'offer','answer','ice','hangup'}:return('',400)
    if room!=room_for(uid,target):return('',403)
    with db() as c:r=c.execute('insert into link_call_signals(room,sender_id,target_id,kind,payload,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(room,uid,target,kind,json.dumps(d.get('payload',{})),int(time.time()))).fetchone()
    return jsonify(ok=True,id=r['id'])

@app.get('/api/signals/<room>')
def get_signals(room):
    uid=session.get('uid');after=int(request.args.get('after','0') or 0)
    if not uid:return('',401)
    with db() as c:rows=c.execute('select id,sender_id,target_id,kind,payload,created_at from link_call_signals where room=%s and target_id=%s and id>%s order by id limit 100',(room,uid,after)).fetchall()
    for r in rows:r['payload']=json.loads(r['payload'])
    return jsonify(rows)

@app.get('/health')
def health():return jsonify(status='ok',service='bell-me',signaling='green',webrtc='peer-to-peer',turn='not-configured')
