from flask import Flask, Response, jsonify, render_template_string, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, secrets, time

app = Flask(__name__)
app.secret_key = os.getenv('OWNPOST_SECRET', secrets.token_hex(32))
DB = os.getenv('OWNPOST_DB', os.path.join(os.path.dirname(__file__), 'ownpost.db'))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    con = db()
    con.executescript('''
    create table if not exists users(id integer primary key autoincrement, username text unique not null, display_name text not null, password_hash text not null, created_at integer not null);
    create table if not exists conversations(id integer primary key autoincrement, name text, kind text not null default 'direct', created_by integer not null, created_at integer not null);
    create table if not exists members(conversation_id integer not null, user_id integer not null, unique(conversation_id,user_id));
    create table if not exists messages(id integer primary key autoincrement, conversation_id integer not null, sender_id integer not null, body text not null, created_at integer not null);
    create table if not exists contacts(owner_id integer not null, contact_id integer not null, unique(owner_id,contact_id));
    ''')
    con.commit(); con.close()

init_db()

STYLE='''
:root{--bg:#050706;--panel:#0c100e;--line:#1d2822;--green:#37f29a;--text:#f4fff9;--muted:#8ba096}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#0e261b,#050706 34%);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}a{color:inherit}.wrap{max-width:1080px;margin:auto;padding:20px}.top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px}.brand{font-size:24px;font-weight:900}.tag{color:var(--green);font-size:12px}.card{background:rgba(12,16,14,.94);border:1px solid var(--line);border-radius:24px;padding:20px}.grid{display:grid;grid-template-columns:320px 1fr;gap:16px}.btn,button{border:0;border-radius:14px;padding:11px 14px;font-weight:800;cursor:pointer;text-decoration:none;display:inline-block}.primary{background:var(--green);color:#04110a}.secondary{background:#131915;color:white;border:1px solid var(--line)}input,textarea{width:100%;background:#070b09;color:white;border:1px solid var(--line);border-radius:14px;padding:12px;outline:none}.muted{color:var(--muted)}.list{display:flex;flex-direction:column;gap:8px}.item{padding:12px;border-radius:14px;background:#090d0b;border:1px solid var(--line);text-decoration:none}.msg{max-width:76%;padding:10px 12px;border-radius:16px;background:#141b17;margin:7px 0}.mine{margin-left:auto;background:#17452e}.chat{min-height:360px;max-height:55vh;overflow:auto;padding:8px}.row{display:flex;gap:8px;align-items:center}.hero h1{font-size:38px;line-height:1;margin:8px 0 10px}.apps{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:16px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--green);box-shadow:0 0 15px var(--green)}@media(max-width:760px){.grid{grid-template-columns:1fr}.apps{grid-template-columns:1fr}.hero h1{font-size:31px}}
'''

def page(body, title='ON ANY PLATFORM'):
    return render_template_string(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#050706"><link rel="manifest" href="/manifest.webmanifest"><title>{title}</title><style>{STYLE}</style></head><body><div class="wrap"><div class="top"><div><div class="brand">ON ANY PLATFORM</div><div class="tag">Powered by ON ANY POSTCODE · Earth Is Our Turf</div></div><div>{{% if session.get('uid') %}}<a class="btn secondary" href="/link">THE LINK</a> <a class="btn secondary" href="/logout">Logout</a>{{% else %}}<a class="btn secondary" href="/login">Login</a>{{% endif %}}</div></div>{body}</div><script>if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js')</script></body></html>''')

@app.get('/')
def home():
    body='''<section class="card hero"><div><span class="dot"></span> Store online</div><h1>Your apps. Your platform.</h1><p class="muted">Independent application distribution for the ON ANY POSTCODE ecosystem.</p><div class="row"><a class="btn primary" href="/link">Open THE LINK</a><button id="install" class="secondary">Install App Store</button></div></section><section class="apps"><article class="card"><h2>🔗 THE LINK</h2><p class="muted">Communication application</p><p>Open LINK UP for private one-to-one and group messaging.</p><a class="btn primary" href="/link">Open</a></article><article class="card"><h2>📲 ON ANY PLATFORM</h2><p class="muted">App Store · v0.2.0</p><p>The distribution front door for OAP applications.</p></article></section><script>let p=null;addEventListener('beforeinstallprompt',e=>{e.preventDefault();p=e});document.getElementById('install').onclick=async()=>{if(p){p.prompt();await p.userChoice;p=null}else alert('Use your browser menu → Install app / Add to Home screen.')}</script>'''
    return page(body)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        u=request.form.get('username','').strip().lower(); n=request.form.get('display_name','').strip(); pw=request.form.get('password','')
        if len(u)<3 or len(pw)<8 or not n: return page('<div class="card"><h2>Registration failed</h2><p>Username 3+ characters and password 8+ characters required.</p><a class="btn secondary" href="/register">Try again</a></div>')
        con=db()
        try:
            cur=con.execute('insert into users(username,display_name,password_hash,created_at) values(?,?,?,?)',(u,n,generate_password_hash(pw),int(time.time()))); con.commit(); session['uid']=cur.lastrowid
        except sqlite3.IntegrityError:
            con.close(); return page('<div class="card"><h2>Username already exists</h2><a class="btn secondary" href="/register">Choose another</a></div>')
        con.close(); return redirect('/link')
    return page('''<div class="card" style="max-width:480px;margin:auto"><h1>Create LINK UP account</h1><form method="post"><p><input name="display_name" placeholder="Display name" required></p><p><input name="username" placeholder="Username" required></p><p><input name="password" type="password" placeholder="Password (8+ characters)" required></p><button class="primary">Create account</button> <a class="btn secondary" href="/login">Login</a></form></div>''')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        con=db(); u=con.execute('select * from users where username=?',(request.form.get('username','').strip().lower(),)).fetchone(); con.close()
        if u and check_password_hash(u['password_hash'],request.form.get('password','')):
            session['uid']=u['id']; return redirect('/link')
        return page('<div class="card"><h2>Login failed</h2><a class="btn secondary" href="/login">Try again</a></div>')
    return page('''<div class="card" style="max-width:480px;margin:auto"><h1>LINK UP</h1><form method="post"><p><input name="username" placeholder="Username" required></p><p><input name="password" type="password" placeholder="Password" required></p><button class="primary">Login</button> <a class="btn secondary" href="/register">Create account</a></form></div>''')

@app.get('/logout')
def logout(): session.clear(); return redirect('/')

def need_user(): return session.get('uid')

@app.route('/link', methods=['GET','POST'])
def link():
    uid=need_user()
    if not uid:return redirect('/login')
    con=db()
    if request.method=='POST':
        target=request.form.get('username','').strip().lower(); other=con.execute('select id,display_name from users where username=?',(target,)).fetchone()
        if other and other['id']!=uid:
            existing=con.execute("select c.id from conversations c join members m1 on c.id=m1.conversation_id join members m2 on c.id=m2.conversation_id where c.kind='direct' and m1.user_id=? and m2.user_id=?",(uid,other['id'])).fetchone()
            if existing: cid=existing['id']
            else:
                cur=con.execute("insert into conversations(name,kind,created_by,created_at) values(?, 'direct', ?, ?)",(other['display_name'],uid,int(time.time()))); cid=cur.lastrowid; con.executemany('insert into members(conversation_id,user_id) values(?,?)',[(cid,uid),(cid,other['id'])]); con.commit()
            con.close(); return redirect(f'/chat/{cid}')
    rows=con.execute('''select c.id,c.kind,c.name,coalesce((select body from messages where conversation_id=c.id order by id desc limit 1),'No messages yet') last from conversations c join members m on m.conversation_id=c.id where m.user_id=? order by c.id desc''',(uid,)).fetchall()
    me=con.execute('select display_name,username from users where id=?',(uid,)).fetchone(); con.close()
    items=''.join([f'<a class="item" href="/chat/{r["id"]}"><strong>{r["name"] or "Conversation"}</strong><div class="muted">{r["kind"]} · {r["last"][:60]}</div></a>' for r in rows]) or '<div class="muted">No chats yet.</div>'
    body=f'''<div class="grid"><aside class="card"><h2>🔗 THE LINK</h2><div class="muted">LINK UP · @{me['username']}</div><hr style="border-color:#1d2822"><form method="post"><input name="username" placeholder="Start chat by username"><p><button class="primary">Link Up</button> <a class="btn secondary" href="/group/new">New group</a></p></form><div class="list">{items}</div></aside><main class="card"><h1>LINK UP</h1><p class="muted">Private messaging workspace.</p><p>Start a conversation from the left or create a group.</p><div class="card"><strong>Security status</strong><p class="muted">Passwords are hashed. Transport uses HTTPS on Render. End-to-end message encryption is NOT yet enabled in this build.</p></div></main></div>'''
    return page(body,'THE LINK · LINK UP')

@app.route('/group/new', methods=['GET','POST'])
def group_new():
    uid=need_user()
    if not uid:return redirect('/login')
    if request.method=='POST':
        name=request.form.get('name','').strip(); users=[x.strip().lower() for x in request.form.get('members','').split(',') if x.strip()]
        con=db(); cur=con.execute("insert into conversations(name,kind,created_by,created_at) values(?,'group',?,?)",(name or 'Group',uid,int(time.time()))); cid=cur.lastrowid; ids=[uid]
        for un in users:
            r=con.execute('select id from users where username=?',(un,)).fetchone()
            if r: ids.append(r['id'])
        con.executemany('insert or ignore into members(conversation_id,user_id) values(?,?)',[(cid,i) for i in set(ids)]); con.commit(); con.close(); return redirect(f'/chat/{cid}')
    return page('''<div class="card" style="max-width:560px;margin:auto"><h1>New LINK UP group</h1><form method="post"><p><input name="name" placeholder="Group name" required></p><p><textarea name="members" placeholder="Usernames, comma separated"></textarea></p><button class="primary">Create group</button></form></div>''')

@app.route('/chat/<int:cid>', methods=['GET','POST'])
def chat(cid):
    uid=need_user()
    if not uid:return redirect('/login')
    con=db(); member=con.execute('select 1 from members where conversation_id=? and user_id=?',(cid,uid)).fetchone()
    if not member: con.close(); return ('Forbidden',403)
    if request.method=='POST':
        body=request.form.get('body','').strip()
        if body: con.execute('insert into messages(conversation_id,sender_id,body,created_at) values(?,?,?,?)',(cid,uid,body,int(time.time()))); con.commit()
        con.close(); return redirect(f'/chat/{cid}')
    c=con.execute('select * from conversations where id=?',(cid,)).fetchone(); msgs=con.execute('''select m.*,u.display_name,u.username from messages m join users u on u.id=m.sender_id where m.conversation_id=? order by m.id asc limit 500''',(cid,)).fetchall(); con.close()
    bubbles=''.join([f'<div class="msg {"mine" if m["sender_id"]==uid else ""}"><strong>{m["display_name"]}</strong><div>{m["body"]}</div><small class="muted">@{m["username"]}</small></div>' for m in msgs]) or '<p class="muted">No messages yet. Say hello.</p>'
    body=f'''<div class="card"><div class="row"><a class="btn secondary" href="/link">← Chats</a><h2 style="margin:0">{c['name'] or 'LINK UP'}</h2></div><div class="chat" id="chat">{bubbles}</div><form method="post" class="row"><input name="body" autocomplete="off" placeholder="Message" required><button class="primary">Send</button></form><p class="muted">Server-delivered messaging · HTTPS transport · E2EE pending</p></div><script>document.getElementById('chat').scrollTop=999999;setTimeout(()=>location.reload(),5000)</script>'''
    return page(body,'LINK UP')

@app.get('/health')
def health(): return jsonify(status='ok',service='on-any-platform',link='link-up',version='0.2.0',features=['accounts','direct_messages','groups','pwa'])

@app.get('/manifest.webmanifest')
def manifest(): return jsonify({'name':'ON ANY PLATFORM','short_name':'OAP Platform','start_url':'/','display':'standalone','background_color':'#050706','theme_color':'#050706','description':'ON ANY PLATFORM App Store and THE LINK communications front door.'})

@app.get('/sw.js')
def sw():
    return Response("const C='oap-platform-v2';self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>c.addAll(['/','/manifest.webmanifest']))));self.addEventListener('fetch',e=>e.respondWith(fetch(e.request).catch(()=>caches.match(e.request))));",mimetype='application/javascript')

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','10000')))
