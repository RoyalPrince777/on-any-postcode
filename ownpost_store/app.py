from flask import Flask, Response, jsonify, render_template_string, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg import connect
from psycopg.rows import dict_row
from markupsafe import escape
import os, time, json, base64

app=Flask(__name__)
app.secret_key=os.environ.get('OWNPOST_SECRET','dev-only-change-me')
DATABASE_URL=os.environ['DATABASE_URL']

def db(): return connect(DATABASE_URL,autocommit=True,row_factory=dict_row)

def init_db():
    with db() as c:
        c.execute('create table if not exists link_users(id bigserial primary key,username text unique not null,display_name text not null,password_hash text not null,created_at bigint not null)')
        c.execute("create table if not exists link_conversations(id bigserial primary key,name text,kind text not null default 'direct',created_by bigint not null,created_at bigint not null)")
        c.execute('create table if not exists link_members(conversation_id bigint not null,user_id bigint not null,unique(conversation_id,user_id))')
        c.execute('create table if not exists link_messages(id bigserial primary key,conversation_id bigint not null,sender_id bigint not null,body text not null,encrypted boolean not null default false,created_at bigint not null)')
        c.execute('create table if not exists link_user_keys(user_id bigint primary key,public_jwk text not null,updated_at bigint not null)')
        c.execute('create table if not exists link_group_keys(conversation_id bigint not null,user_id bigint not null,version integer not null,creator_pub_jwk text not null,wrapped_key text not null,wrap_iv text not null,created_at bigint not null,primary key(conversation_id,user_id,version))')
        c.execute("create table if not exists link_media(id bigserial primary key,conversation_id bigint not null,sender_id bigint not null,kind text not null,mime text not null,name text not null,ciphertext text not null,iv text not null,created_at bigint not null)")
        c.execute('create index if not exists link_messages_conv_id_idx on link_messages(conversation_id,id)')
        c.execute('create index if not exists link_media_conv_id_idx on link_media(conversation_id,id)')
init_db()

STYLE='''
:root{--b:#050706;--p:#0c100e;--l:#1d2822;--g:#37f29a;--t:#f4fff9;--m:#8ba096;--a:#f0b429}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#0e261b,#050706 34%);color:var(--t);font:15px/1.5 system-ui,sans-serif}a{color:inherit}.wrap{max-width:1100px;margin:auto;padding:18px}.top,.row{display:flex;align-items:center;gap:9px}.top{justify-content:space-between;margin-bottom:18px}.brand{font-size:24px;font-weight:900}.tag,.muted{color:var(--m)}.tag{font-size:12px}.card{background:#0c100ef2;border:1px solid var(--l);border-radius:24px;padding:19px}.grid{display:grid;grid-template-columns:330px 1fr;gap:15px}.btn,button{border:0;border-radius:14px;padding:11px 14px;font-weight:800;cursor:pointer;text-decoration:none;display:inline-block}.primary{background:var(--g);color:#04110a}.secondary{background:#131915;color:white;border:1px solid var(--l)}input,textarea{width:100%;background:#070b09;color:white;border:1px solid var(--l);border-radius:14px;padding:12px}.list,.features{display:flex;flex-direction:column;gap:8px}.item,.feature{padding:12px;border-radius:14px;background:#090d0b;border:1px solid var(--l);text-decoration:none}.feature{display:flex;justify-content:space-between}.msg{max-width:76%;padding:10px 12px;border-radius:16px;background:#141b17;margin:7px 0}.mine{margin-left:auto;background:#17452e}.chat{min-height:360px;max-height:55vh;overflow:auto;padding:8px}.hero h1{font-size:38px;line-height:1;margin:8px 0}.apps{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:16px}.live{color:var(--g)}.next{color:var(--a)}.security{font-size:12px;border:1px solid #24553a;background:#0b1a12;padding:9px 12px;border-radius:12px}.media{padding:10px;border:1px solid var(--l);border-radius:12px;margin:8px 0}.toolbar{display:flex;gap:8px;flex-wrap:wrap}@media(max-width:760px){.grid,.apps{grid-template-columns:1fr}.hero h1{font-size:31px}.top{align-items:flex-start;flex-direction:column}}
'''

def page(body,title='ON ANY PLATFORM',scripts=''):
    return render_template_string(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#050706"><link rel="manifest" href="/manifest.webmanifest"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><title>{title}</title><style>{STYLE}</style></head><body><div class="wrap"><div class="top"><div><div class="brand">ON ANY PLATFORM</div><div class="tag">Powered by ON ANY POSTCODE · Earth Is Our Turf</div></div><div>{{% if session.get('uid') %}}<a class="btn secondary" href="/link">THE LINK</a> <a class="btn secondary" href="/logout">Logout</a>{{% else %}}<a class="btn secondary" href="/login">Login</a>{{% endif %}}</div></div>{body}</div><script>if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js')</script>{scripts}</body></html>''')

KEY_JS='''<script>
const IDKEY='the-link-identity-v1';
const b64=b=>btoa(String.fromCharCode(...new Uint8Array(b))); const unb64=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function ensureIdentity(){let saved=localStorage.getItem(IDKEY),pair;if(saved){let o=JSON.parse(saved);pair={privateKey:await crypto.subtle.importKey('jwk',o.priv,{name:'ECDH',namedCurve:'P-256'},true,['deriveKey']),publicKey:await crypto.subtle.importKey('jwk',o.pub,{name:'ECDH',namedCurve:'P-256'},true,[])}}else{pair=await crypto.subtle.generateKey({name:'ECDH',namedCurve:'P-256'},true,['deriveKey']);let pub=await crypto.subtle.exportKey('jwk',pair.publicKey),priv=await crypto.subtle.exportKey('jwk',pair.privateKey);localStorage.setItem(IDKEY,JSON.stringify({pub,priv}));saved=localStorage.getItem(IDKEY)}let pub=JSON.parse(saved).pub;await fetch('/api/key',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({public_jwk:pub})});return {pair,pub}}
async function derive(priv,pubjwk){let pub=await crypto.subtle.importKey('jwk',pubjwk,{name:'ECDH',namedCurve:'P-256'},false,[]);return crypto.subtle.deriveKey({name:'ECDH',public:pub},priv,{name:'AES-GCM',length:256},false,['encrypt','decrypt'])}
async function encryptWithKey(key,data){let iv=crypto.getRandomValues(new Uint8Array(12));let ct=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,data);return {ciphertext:b64(ct),iv:b64(iv)}}
async function decryptWithKey(key,ciphertext,iv){return crypto.subtle.decrypt({name:'AES-GCM',iv:unb64(iv)},key,unb64(ciphertext))}
</script>'''

@app.get('/')
def home():
    return page('''<section class="card hero"><div class="live">● Store online</div><h1>Your apps. Your platform.</h1><p class="muted">Independent application distribution for the ON ANY POSTCODE ecosystem.</p><a class="btn primary" href="/link">Open THE LINK</a></section><section class="apps"><article class="card"><h2>🔗 THE LINK</h2><p>South London-born communications.</p><a class="btn primary" href="/link">Open</a></article><article class="card"><h2>📲 ON ANY PLATFORM</h2><p class="muted">App Store · v0.5.0</p><p>Group E2EE + encrypted media foundations.</p></article></section>''')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        u=request.form.get('username','').strip().lower(); n=request.form.get('display_name','').strip(); pw=request.form.get('password','')
        if len(u)<3 or len(pw)<8 or not n:return page('<div class="card">Username 3+ and password 8+ required. <a href="/register">Try again</a></div>')
        try:
            with db() as c:r=c.execute('insert into link_users(username,display_name,password_hash,created_at) values(%s,%s,%s,%s) returning id',(u,n,generate_password_hash(pw),int(time.time()))).fetchone();session['uid']=r['id']
            return redirect('/link')
        except Exception:return page('<div class="card">Username already exists or registration failed. <a href="/register">Try another</a></div>')
    return page('''<div class="card" style="max-width:480px;margin:auto"><h1>Join THE LINK</h1><form method="post"><p><input name="display_name" placeholder="Display name" required></p><p><input name="username" placeholder="Username" required></p><p><input name="password" type="password" placeholder="Password (8+)" required></p><button class="primary">Create account</button></form></div>''')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        with db() as c:u=c.execute('select * from link_users where username=%s',(request.form.get('username','').strip().lower(),)).fetchone()
        if u and check_password_hash(u['password_hash'],request.form.get('password','')):session['uid']=u['id'];return redirect('/link')
    return page('''<div class="card" style="max-width:480px;margin:auto"><h1>THE LINK</h1><form method="post"><p><input name="username" placeholder="Username" required></p><p><input name="password" type="password" placeholder="Password" required></p><button class="primary">Login</button> <a class="btn secondary" href="/register">Join</a></form></div>''')

@app.get('/logout')
def logout():session.clear();return redirect('/')

@app.route('/link',methods=['GET','POST'])
def link():
    uid=session.get('uid')
    if not uid:return redirect('/login')
    if request.method=='POST':
        with db() as c:
            other=c.execute('select id,display_name from link_users where username=%s',(request.form.get('username','').strip().lower(),)).fetchone()
            if other and other['id']!=uid:
                ex=c.execute("select c.id from link_conversations c join link_members a on c.id=a.conversation_id join link_members b on c.id=b.conversation_id where c.kind='direct' and a.user_id=%s and b.user_id=%s",(uid,other['id'])).fetchone()
                if ex:cid=ex['id']
                else:
                    cid=c.execute("insert into link_conversations(name,kind,created_by,created_at) values(%s,'direct',%s,%s) returning id",(other['display_name'],uid,int(time.time()))).fetchone()['id'];c.execute('insert into link_members(conversation_id,user_id) values(%s,%s),(%s,%s)',(cid,uid,cid,other['id']))
                return redirect(f'/chat/{cid}')
    with db() as c:
        rows=c.execute("select c.id,c.kind,c.name,coalesce((select case when encrypted then '🔐 Encrypted message' else body end from link_messages where conversation_id=c.id order by id desc limit 1),'No messages yet') last from link_conversations c join link_members m on c.id=m.conversation_id where m.user_id=%s order by c.id desc",(uid,)).fetchall();me=c.execute('select username from link_users where id=%s',(uid,)).fetchone()
    items=''.join(f'<a class="item" href="/chat/{r["id"]}"><strong>{escape(r["name"] or "Chat")}</strong><div class="muted">{"My Lot" if r["kind"]=="group" else "Link Up"} · {escape(str(r["last"])[:55])}</div></a>' for r in rows) or '<div class="muted">No chats yet.</div>'
    features='''<div class="features"><div class="feature"><b>💬 Link Up</b><span class="live">LIVE</span></div><div class="feature"><b>👥 My Lot group E2EE</b><span class="live">LIVE</span></div><div class="feature"><b>📸 Drop It</b><span class="live">ENCRYPTED</span></div><div class="feature"><b>🎙️ Say Suttin</b><span class="live">ENCRYPTED</span></div><div class="feature"><b>⚡ Realtime</b><span class="live">LIVE</span></div><div class="feature"><b>🗄️ Persistent storage</b><span class="live">LIVE</span></div><div class="feature"><b>📞 Bell Me</b><span class="next">NEXT</span></div><div class="feature"><b>📍 Where You At?</b><span class="next">NEXT</span></div></div>'''
    return page(f'''<div class="grid"><aside class="card"><h2>🔗 THE LINK</h2><div class="muted">@{escape(me['username'])}</div><h3>Link Up</h3><form method="post"><input name="username" placeholder="Username"><p><button class="primary">Link Up</button> <a class="btn secondary" href="/my-lot/new">My Lot +</a></p></form><div class="list">{items}</div></aside><main class="card"><h1>THE LINK</h1><p class="muted">South London-born. Built to travel globally.</p>{features}<p class="security">Direct and My Lot chats use browser-held device keys. The server stores ciphertext for encrypted messages and media.</p></main></div>''','THE LINK',KEY_JS+'<script>ensureIdentity().catch(console.error)</script>')

@app.route('/my-lot/new',methods=['GET','POST'])
def mylot():
    uid=session.get('uid')
    if not uid:return redirect('/login')
    if request.method=='POST':
        with db() as c:
            cid=c.execute("insert into link_conversations(name,kind,created_by,created_at) values(%s,'group',%s,%s) returning id",(request.form.get('name','').strip() or 'My Lot',uid,int(time.time()))).fetchone()['id'];ids={uid}
            for un in request.form.get('members','').split(','):
                r=c.execute('select id from link_users where username=%s',(un.strip().lower(),)).fetchone()
                if r:ids.add(r['id'])
            for i in ids:c.execute('insert into link_members(conversation_id,user_id) values(%s,%s) on conflict do nothing',(cid,i))
        return redirect(f'/chat/{cid}?bootstrap=1')
    return page('''<div class="card" style="max-width:560px;margin:auto"><h1>👥 My Lot</h1><p class="security">Members must have opened THE LINK once so their device key exists. Membership is fixed after creation in this release, preventing unrotated-key membership changes.</p><form method="post"><p><input name="name" placeholder="Name your lot" required></p><p><textarea name="members" placeholder="Usernames, comma separated"></textarea></p><button class="primary">Create My Lot</button></form></div>''')

@app.get('/chat/<int:cid>')
def chat(cid):
    uid=session.get('uid')
    if not uid:return redirect('/login')
    with db() as c:
        member=c.execute('select 1 from link_members where conversation_id=%s and user_id=%s',(cid,uid)).fetchone();cv=c.execute('select * from link_conversations where id=%s',(cid,)).fetchone()
    if not member or not cv:return('Forbidden',403)
    direct=cv['kind']=='direct'
    badge='🔐 Device E2EE · ciphertext on server' if direct else '🔐 My Lot group E2EE · fixed membership'
    body=f'''<div class="card"><div class="row"><a class="btn secondary" href="/link">← THE LINK</a><h2>{escape(cv['name'] or 'Link Up')}</h2></div><p class="security">{badge}</p><div class="chat" id="chat"></div><form id="send" class="row"><input id="body" autocomplete="off" placeholder="Say suttin..." required><button class="primary">Send</button></form><div class="toolbar"><label class="btn secondary">📸 Drop It<input id="file" type="file" hidden></label><button id="record" class="secondary">🎙️ Say Suttin</button></div><div id="media"></div><div id="status" class="muted"></div></div>'''
    scripts=KEY_JS+f'''<script>
const CID={cid}, DIRECT={str(direct).lower()}, ME={int(uid)};let identity=null,convKey=null,last=0,lastMedia=0,rec=null,chunks=[];
async function getDirectKey(){{let r=await fetch('/api/peer-key/'+CID);if(!r.ok)throw new Error('Other person must open THE LINK once.');let p=await r.json();return derive(identity.pair.privateKey,p.public_jwk)}}
async function bootstrapGroup(){{let r=await fetch('/api/group-members/'+CID);let g=await r.json();if(g.has_keys)return; if(g.created_by!==ME)return;for(let m of g.members)if(!m.public_jwk)throw new Error('@'+m.username+' must open THE LINK once.');let raw=crypto.getRandomValues(new Uint8Array(32));let groupKey=await crypto.subtle.importKey('raw',raw,'AES-GCM',true,['encrypt','decrypt']);for(let m of g.members){{let wrap=await derive(identity.pair.privateKey,m.public_jwk),e=await encryptWithKey(wrap,raw);await fetch('/api/group-key/'+CID,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{user_id:m.id,creator_pub_jwk:identity.pub,wrapped_key:e.ciphertext,wrap_iv:e.iv,version:1}})}})}}localStorage.setItem('group-key-'+CID,b64(raw));return groupKey}}
async function getGroupKey(){{let local=localStorage.getItem('group-key-'+CID);if(local)return crypto.subtle.importKey('raw',unb64(local),'AES-GCM',true,['encrypt','decrypt']);await bootstrapGroup();local=localStorage.getItem('group-key-'+CID);if(local)return crypto.subtle.importKey('raw',unb64(local),'AES-GCM',true,['encrypt','decrypt']);let r=await fetch('/api/group-key/'+CID);if(!r.ok)throw new Error('Group encryption key not ready yet.');let e=await r.json(),wrap=await derive(identity.pair.privateKey,e.creator_pub_jwk),raw=await decryptWithKey(wrap,e.wrapped_key,e.wrap_iv);localStorage.setItem('group-key-'+CID,b64(raw));return crypto.subtle.importKey('raw',raw,'AES-GCM',true,['encrypt','decrypt'])}}
async function start(){{identity=await ensureIdentity();convKey=DIRECT?await getDirectKey():await getGroupKey();listen();loadMedia();document.getElementById('status').textContent='🔐 Encryption ready'}}
async function sendText(txt){{let e=await encryptWithKey(convKey,new TextEncoder().encode(txt));await fetch('/api/messages/'+CID,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{body:e.ciphertext,encrypted:true,iv:e.iv}})}})}}
document.getElementById('send').onsubmit=async e=>{{e.preventDefault();let i=document.getElementById('body');if(!i.value.trim())return;await sendText(i.value.trim());i.value=''}};
async function renderMsg(m){{try{{let o=JSON.parse(m.body),pt=await decryptWithKey(convKey,o.ct,o.iv),txt=new TextDecoder().decode(pt);let d=document.createElement('div');d.className='msg '+(m.sender_id===ME?'mine':'');d.innerHTML='<b>'+m.display_name.replace(/[<>]/g,'')+'</b><div></div>';d.querySelector('div').textContent=txt;document.getElementById('chat').appendChild(d);document.getElementById('chat').scrollTop=999999}}catch(e){{console.error(e)}}}}
async function listen(){{let es=new EventSource('/events/'+CID+'?after='+last);es.onmessage=async e=>{{let m=JSON.parse(e.data);last=Math.max(last,m.id);await renderMsg(m)}};es.onerror=()=>{{es.close();setTimeout(listen,1500)}}}}
async function uploadBlob(blob,name,kind){{let buf=await blob.arrayBuffer(),e=await encryptWithKey(convKey,buf);await fetch('/api/media/'+CID,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{kind,mime:blob.type||'application/octet-stream',name,ciphertext:e.ciphertext,iv:e.iv}})}});await loadMedia()}}
document.getElementById('file').onchange=async e=>{{let f=e.target.files[0];if(f)await uploadBlob(f,f.name,'file');e.target.value=''}};
document.getElementById('record').onclick=async()=>{{if(!rec){{let s=await navigator.mediaDevices.getUserMedia({{audio:true}});chunks=[];rec=new MediaRecorder(s);rec.ondataavailable=e=>chunks.push(e.data);rec.onstop=async()=>{{let b=new Blob(chunks,{{type:rec.mimeType||'audio/webm'}});s.getTracks().forEach(t=>t.stop());rec=null;document.getElementById('record').textContent='🎙️ Say Suttin';await uploadBlob(b,'voice-note.webm','voice')}};rec.start();document.getElementById('record').textContent='⏹ Stop'}}else rec.stop()}};
async function loadMedia(){{let r=await fetch('/api/media/'+CID+'?after='+lastMedia),arr=await r.json();for(let m of arr){{lastMedia=Math.max(lastMedia,m.id);try{{let raw=await decryptWithKey(convKey,m.ciphertext,m.iv),blob=new Blob([raw],{{type:m.mime}}),url=URL.createObjectURL(blob),d=document.createElement('div');d.className='media';if(m.kind==='voice')d.innerHTML='<b>🎙️ '+m.name+'</b><br><audio controls src="'+url+'"></audio>';else d.innerHTML='<b>📎 '+m.name+'</b> <a class="btn secondary" download="'+m.name.replace(/"/g,'')+'" href="'+url+'">Open</a>';document.getElementById('media').appendChild(d)}}catch(e){{console.error(e)}}}}}}
start().catch(e=>document.getElementById('status').textContent='⚠️ '+e.message)
</script>'''
    return page(body,'LINK UP',scripts)

@app.post('/api/key')
def api_key():
    uid=session.get('uid'); d=request.get_json(silent=True) or {}
    if not uid:return('',401)
    with db() as c:c.execute('insert into link_user_keys(user_id,public_jwk,updated_at) values(%s,%s,%s) on conflict(user_id) do update set public_jwk=excluded.public_jwk,updated_at=excluded.updated_at',(uid,json.dumps(d.get('public_jwk',{})),int(time.time())))
    return jsonify(ok=True)

@app.get('/api/peer-key/<int:cid>')
def peer_key(cid):
    uid=session.get('uid')
    if not uid:return('',401)
    with db() as c:r=c.execute('select k.public_jwk from link_members m join link_user_keys k on k.user_id=m.user_id where m.conversation_id=%s and m.user_id<>%s limit 1',(cid,uid)).fetchone()
    if not r:return('',404)
    return jsonify(public_jwk=json.loads(r['public_jwk']))

@app.get('/api/group-members/<int:cid>')
def group_members(cid):
    uid=session.get('uid')
    if not uid:return('',401)
    with db() as c:
        ok=c.execute('select 1 from link_members where conversation_id=%s and user_id=%s',(cid,uid)).fetchone();cv=c.execute('select created_by from link_conversations where id=%s and kind=%s',(cid,'group')).fetchone()
        if not ok or not cv:return('',403)
        rows=c.execute('select u.id,u.username,k.public_jwk from link_members m join link_users u on u.id=m.user_id left join link_user_keys k on k.user_id=u.id where m.conversation_id=%s order by u.id',(cid,)).fetchall();has=c.execute('select 1 from link_group_keys where conversation_id=%s limit 1',(cid,)).fetchone()
    return jsonify(created_by=cv['created_by'],has_keys=bool(has),members=[{'id':r['id'],'username':r['username'],'public_jwk':json.loads(r['public_jwk']) if r['public_jwk'] else None} for r in rows])

@app.route('/api/group-key/<int:cid>',methods=['GET','POST'])
def group_key(cid):
    uid=session.get('uid')
    if not uid:return('',401)
    with db() as c:
        member=c.execute('select 1 from link_members where conversation_id=%s and user_id=%s',(cid,uid)).fetchone();cv=c.execute('select created_by from link_conversations where id=%s and kind=%s',(cid,'group')).fetchone()
        if not member or not cv:return('',403)
        if request.method=='POST':
            if cv['created_by']!=uid:return('',403)
            d=request.get_json(silent=True) or {};target=int(d.get('user_id',0));allowed=c.execute('select 1 from link_members where conversation_id=%s and user_id=%s',(cid,target)).fetchone()
            if not allowed:return('',400)
            c.execute('insert into link_group_keys(conversation_id,user_id,version,creator_pub_jwk,wrapped_key,wrap_iv,created_at) values(%s,%s,%s,%s,%s,%s,%s) on conflict(conversation_id,user_id,version) do update set creator_pub_jwk=excluded.creator_pub_jwk,wrapped_key=excluded.wrapped_key,wrap_iv=excluded.wrap_iv',(cid,target,int(d.get('version',1)),json.dumps(d.get('creator_pub_jwk',{})),d.get('wrapped_key',''),d.get('wrap_iv',''),int(time.time())))
            return jsonify(ok=True)
        r=c.execute('select creator_pub_jwk,wrapped_key,wrap_iv,version from link_group_keys where conversation_id=%s and user_id=%s order by version desc limit 1',(cid,uid)).fetchone()
    if not r:return('',404)
    return jsonify(creator_pub_jwk=json.loads(r['creator_pub_jwk']),wrapped_key=r['wrapped_key'],wrap_iv=r['wrap_iv'],version=r['version'])

@app.post('/api/messages/<int:cid>')
def post_message(cid):
    uid=session.get('uid');d=request.get_json(silent=True) or {}
    if not uid:return('',401)
    with db() as c:
        if not c.execute('select 1 from link_members where conversation_id=%s and user_id=%s',(cid,uid)).fetchone():return('',403)
        payload=json.dumps({'ct':d.get('body',''),'iv':d.get('iv','')}) if d.get('encrypted') else str(d.get('body',''))
        r=c.execute('insert into link_messages(conversation_id,sender_id,body,encrypted,created_at) values(%s,%s,%s,%s,%s) returning id',(cid,uid,payload,bool(d.get('encrypted')),int(time.time()))).fetchone()
    return jsonify(ok=True,id=r['id'])

@app.get('/events/<int:cid>')
def events(cid):
    uid=session.get('uid');after=int(request.args.get('after','0') or 0)
    if not uid:return('',401)
    with db() as c:
        if not c.execute('select 1 from link_members where conversation_id=%s and user_id=%s',(cid,uid)).fetchone():return('',403)
    def gen():
        last=after
        for _ in range(45):
            with db() as c:rows=c.execute('select m.id,m.sender_id,m.body,m.encrypted,u.display_name from link_messages m join link_users u on u.id=m.sender_id where m.conversation_id=%s and m.id>%s order by m.id limit 100',(cid,last)).fetchall()
            for r in rows:last=r['id'];yield 'data: '+json.dumps(r)+'\n\n'
            yield ': ping\n\n';time.sleep(1)
    return Response(gen(),mimetype='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.route('/api/media/<int:cid>',methods=['GET','POST'])
def media(cid):
    uid=session.get('uid')
    if not uid:return('',401)
    with db() as c:
        if not c.execute('select 1 from link_members where conversation_id=%s and user_id=%s',(cid,uid)).fetchone():return('',403)
        if request.method=='POST':
            d=request.get_json(silent=True) or {};ct=d.get('ciphertext','')
            if len(ct)>8_000_000:return jsonify(error='file too large'),413
            r=c.execute('insert into link_media(conversation_id,sender_id,kind,mime,name,ciphertext,iv,created_at) values(%s,%s,%s,%s,%s,%s,%s,%s) returning id',(cid,uid,d.get('kind','file'),d.get('mime','application/octet-stream'),d.get('name','file'),ct,d.get('iv',''),int(time.time()))).fetchone();return jsonify(ok=True,id=r['id'])
        after=int(request.args.get('after','0') or 0);rows=c.execute('select id,sender_id,kind,mime,name,ciphertext,iv,created_at from link_media where conversation_id=%s and id>%s order by id limit 100',(cid,after)).fetchall()
    return jsonify(rows)

@app.get('/health')
def health():return jsonify(status='ok',service='on-any-platform',app='the-link',version='0.5.0',green=['persistent_neon','realtime_sse','direct_device_e2ee','my_lot_group_e2ee','drop_it_encrypted_media','say_suttin_encrypted_voice'],next=['bell_me','where_you_at','my_people','signed_apk','signed_updates','live_direct','whats_poppin','whats_on','ends'])
@app.get('/manifest.webmanifest')
def manifest():return jsonify({'name':'ON ANY PLATFORM','short_name':'OAP Platform','start_url':'/','display':'standalone','background_color':'#050706','theme_color':'#050706'})
@app.get('/sw.js')
def sw():return Response("const C='oap-v5';self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>c.addAll(['/','/manifest.webmanifest']))));self.addEventListener('fetch',e=>e.respondWith(fetch(e.request).catch(()=>caches.match(e.request))));",mimetype='application/javascript')
@app.get('/favicon.svg')
def favicon():return Response('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#050706"/><path d="M16 32h32M32 16v32" stroke="#37f29a" stroke-width="7" stroke-linecap="round"/></svg>',mimetype='image/svg+xml')
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','10000')),threaded=True)
