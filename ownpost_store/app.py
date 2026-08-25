from flask import Flask, Response, jsonify, render_template_string, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, secrets, time

app=Flask(__name__); app.secret_key=os.getenv('OWNPOST_SECRET',secrets.token_hex(32)); DB=os.getenv('OWNPOST_DB',os.path.join(os.path.dirname(__file__),'ownpost.db'))
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
 c=db(); c.executescript('''create table if not exists users(id integer primary key autoincrement,username text unique not null,display_name text not null,password_hash text not null,created_at integer not null);create table if not exists conversations(id integer primary key autoincrement,name text,kind text not null default 'direct',created_by integer not null,created_at integer not null);create table if not exists members(conversation_id integer not null,user_id integer not null,unique(conversation_id,user_id));create table if not exists messages(id integer primary key autoincrement,conversation_id integer not null,sender_id integer not null,body text not null,created_at integer not null);'''); c.commit(); c.close()
init_db()
STYLE=''':root{--b:#050706;--p:#0c100e;--l:#1d2822;--g:#37f29a;--t:#f4fff9;--m:#8ba096}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#0e261b,#050706 34%);color:var(--t);font:15px/1.5 system-ui,sans-serif}a{color:inherit}.wrap{max-width:1100px;margin:auto;padding:18px}.top,.row{display:flex;align-items:center;gap:9px}.top{justify-content:space-between;margin-bottom:18px}.brand{font-size:24px;font-weight:900}.tag,.muted{color:var(--m)}.tag{font-size:12px}.card{background:#0c100ef2;border:1px solid var(--l);border-radius:24px;padding:19px}.grid{display:grid;grid-template-columns:330px 1fr;gap:15px}.btn,button{border:0;border-radius:14px;padding:11px 14px;font-weight:800;cursor:pointer;text-decoration:none;display:inline-block}.primary{background:var(--g);color:#04110a}.secondary{background:#131915;color:white;border:1px solid var(--l)}input,textarea{width:100%;background:#070b09;color:white;border:1px solid var(--l);border-radius:14px;padding:12px}.list,.features{display:flex;flex-direction:column;gap:8px}.item,.feature{padding:12px;border-radius:14px;background:#090d0b;border:1px solid var(--l);text-decoration:none}.feature{display:flex;justify-content:space-between}.msg{max-width:76%;padding:10px 12px;border-radius:16px;background:#141b17;margin:7px 0}.mine{margin-left:auto;background:#17452e}.chat{min-height:360px;max-height:55vh;overflow:auto;padding:8px}.hero h1{font-size:38px;line-height:1;margin:8px 0}.apps{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:16px}.live{color:var(--g)}@media(max-width:760px){.grid,.apps{grid-template-columns:1fr}.hero h1{font-size:31px}.top{align-items:flex-start;flex-direction:column}}'''
def page(body,title='ON ANY PLATFORM'):
 return render_template_string(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#050706"><link rel="manifest" href="/manifest.webmanifest"><title>{title}</title><style>{STYLE}</style></head><body><div class="wrap"><div class="top"><div><div class="brand">ON ANY PLATFORM</div><div class="tag">Powered by ON ANY POSTCODE · Earth Is Our Turf</div></div><div>{{% if session.get('uid') %}}<a class="btn secondary" href="/link">THE LINK</a> <a class="btn secondary" href="/logout">Logout</a>{{% else %}}<a class="btn secondary" href="/login">Login</a>{{% endif %}}</div></div>{body}</div><script>if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js')</script></body></html>''')
@app.get('/')
def home():
 return page('''<section class="card hero"><div class="live">● Store online</div><h1>Your apps. Your platform.</h1><p class="muted">Independent application distribution for the ON ANY POSTCODE ecosystem.</p><a class="btn primary" href="/link">Open THE LINK</a></section><section class="apps"><article class="card"><h2>🔗 THE LINK</h2><p>South London-born communications. Link Up, Bell Me, My Lot and more.</p><a class="btn primary" href="/link">Open</a></article><article class="card"><h2>📲 ON ANY PLATFORM</h2><p class="muted">App Store · v0.3.0</p><p>Your distribution front door.</p></article></section>''')
@app.route('/register',methods=['GET','POST'])
def register():
 if request.method=='POST':
  u=request.form.get('username','').strip().lower(); n=request.form.get('display_name','').strip(); pw=request.form.get('password','')
  if len(u)<3 or len(pw)<8 or not n:return page('<div class="card">Username 3+ and password 8+ required. <a href="/register">Try again</a></div>')
  c=db()
  try: cur=c.execute('insert into users(username,display_name,password_hash,created_at) values(?,?,?,?)',(u,n,generate_password_hash(pw),int(time.time())));c.commit();session['uid']=cur.lastrowid
  except sqlite3.IntegrityError:c.close();return page('<div class="card">Username exists. <a href="/register">Try another</a></div>')
  c.close();return redirect('/link')
 return page('''<div class="card" style="max-width:480px;margin:auto"><h1>Join THE LINK</h1><form method="post"><p><input name="display_name" placeholder="Display name" required></p><p><input name="username" placeholder="Username" required></p><p><input name="password" type="password" placeholder="Password (8+)" required></p><button class="primary">Create account</button></form></div>''')
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  c=db();u=c.execute('select * from users where username=?',(request.form.get('username','').strip().lower(),)).fetchone();c.close()
  if u and check_password_hash(u['password_hash'],request.form.get('password','')):session['uid']=u['id'];return redirect('/link')
 return page('''<div class="card" style="max-width:480px;margin:auto"><h1>THE LINK</h1><form method="post"><p><input name="username" placeholder="Username" required></p><p><input name="password" type="password" placeholder="Password" required></p><button class="primary">Login</button> <a class="btn secondary" href="/register">Join</a></form></div>''')
@app.get('/logout')
def logout():session.clear();return redirect('/')
@app.route('/link',methods=['GET','POST'])
def link():
 uid=session.get('uid')
 if not uid:return redirect('/login')
 c=db()
 if request.method=='POST':
  other=c.execute('select id,display_name from users where username=?',(request.form.get('username','').strip().lower(),)).fetchone()
  if other and other['id']!=uid:
   ex=c.execute("select c.id from conversations c join members a on c.id=a.conversation_id join members b on c.id=b.conversation_id where c.kind='direct' and a.user_id=? and b.user_id=?",(uid,other['id'])).fetchone()
   if ex:cid=ex['id']
   else:
    cur=c.execute("insert into conversations(name,kind,created_by,created_at) values(?,'direct',?,?)",(other['display_name'],uid,int(time.time())));cid=cur.lastrowid;c.executemany('insert into members(conversation_id,user_id) values(?,?)',[(cid,uid),(cid,other['id'])]);c.commit()
   c.close();return redirect(f'/chat/{cid}')
 rows=c.execute("select c.id,c.kind,c.name,coalesce((select body from messages where conversation_id=c.id order by id desc limit 1),'No messages yet') last from conversations c join members m on c.id=m.conversation_id where m.user_id=? order by c.id desc",(uid,)).fetchall();me=c.execute('select username from users where id=?',(uid,)).fetchone();c.close()
 items=''.join(f'<a class="item" href="/chat/{r["id"]}"><strong>{r["name"] or "Chat"}</strong><div class="muted">{"My Lot" if r["kind"]=="group" else "Link Up"} · {r["last"][:55]}</div></a>' for r in rows) or '<div class="muted">No chats yet.</div>'
 features='''<div class="features"><div class="feature"><b>💬 Link Up</b><span class="live">LIVE</span></div><div class="feature"><b>👥 My Lot</b><span class="live">LIVE</span></div><div class="feature"><b>📞 Bell Me</b><span class="muted">NEXT</span></div><div class="feature"><b>📍 Where You At?</b><span class="muted">NEXT</span></div><div class="feature"><b>📸 Drop It</b><span class="muted">NEXT</span></div><div class="feature"><b>🎙️ Say Suttin</b><span class="muted">NEXT</span></div><div class="feature"><b>📡 Live & Direct</b><span class="muted">NEXT</span></div><div class="feature"><b>🔥 What's Poppin'</b><span class="muted">NEXT</span></div><div class="feature"><b>📅 What's On?</b><span class="muted">NEXT</span></div><div class="feature"><b>🏘️ Ends</b><span class="muted">NEXT</span></div><div class="feature"><b>👤 My People</b><span class="muted">NEXT</span></div></div>'''
 return page(f'''<div class="grid"><aside class="card"><h2>🔗 THE LINK</h2><div class="muted">@{me['username']}</div><h3>Link Up</h3><form method="post"><input name="username" placeholder="Username"><p><button class="primary">Link Up</button> <a class="btn secondary" href="/my-lot/new">My Lot +</a></p></form><div class="list">{items}</div></aside><main class="card"><h1>THE LINK</h1><p class="muted">South London-born. Built to travel globally.</p>{features}</main></div>''','THE LINK')
@app.route('/my-lot/new',methods=['GET','POST'])
def mylot():
 uid=session.get('uid')
 if not uid:return redirect('/login')
 if request.method=='POST':
  c=db();cur=c.execute("insert into conversations(name,kind,created_by,created_at) values(?,'group',?,?)",(request.form.get('name','').strip() or 'My Lot',uid,int(time.time())));cid=cur.lastrowid;ids={uid}
  for un in request.form.get('members','').split(','):
   r=c.execute('select id from users where username=?',(un.strip().lower(),)).fetchone()
   if r:ids.add(r['id'])
  c.executemany('insert or ignore into members(conversation_id,user_id) values(?,?)',[(cid,i) for i in ids]);c.commit();c.close();return redirect(f'/chat/{cid}')
 return page('''<div class="card" style="max-width:560px;margin:auto"><h1>👥 My Lot</h1><p class="muted">Start a group.</p><form method="post"><p><input name="name" placeholder="Name your lot" required></p><p><textarea name="members" placeholder="Usernames, comma separated"></textarea></p><button class="primary">Create My Lot</button></form></div>''')
@app.route('/chat/<int:cid>',methods=['GET','POST'])
def chat(cid):
 uid=session.get('uid')
 if not uid:return redirect('/login')
 c=db();m=c.execute('select 1 from members where conversation_id=? and user_id=?',(cid,uid)).fetchone()
 if not m:c.close();return('Forbidden',403)
 if request.method=='POST':
  b=request.form.get('body','').strip()
  if b:c.execute('insert into messages(conversation_id,sender_id,body,created_at) values(?,?,?,?)',(cid,uid,b,int(time.time())));c.commit()
  c.close();return redirect(f'/chat/{cid}')
 cv=c.execute('select * from conversations where id=?',(cid,)).fetchone();ms=c.execute('select m.*,u.display_name,u.username from messages m join users u on u.id=m.sender_id where conversation_id=? order by m.id limit 500',(cid,)).fetchall();c.close();bs=''.join(f'<div class="msg {"mine" if x["sender_id"]==uid else ""}"><b>{x["display_name"]}</b><div>{x["body"]}</div><small class="muted">@{x["username"]}</small></div>' for x in ms) or '<p class="muted">Say suttin 👋</p>'
 return page(f'''<div class="card"><div class="row"><a class="btn secondary" href="/link">← THE LINK</a><h2>{cv['name'] or 'Link Up'}</h2></div><div class="chat" id="chat">{bs}</div><form method="post" class="row"><input name="body" placeholder="Say suttin..." required><button class="primary">Send</button></form><p class="muted">HTTPS transport · E2EE still pending</p></div><script>document.getElementById('chat').scrollTop=999999;setTimeout(()=>location.reload(),5000)</script>''','LINK UP')
@app.get('/health')
def health():return jsonify(status='ok',service='on-any-platform',app='the-link',version='0.3.0',live=['link_up','my_lot'],next=['bell_me','where_you_at','drop_it','say_suttin','live_direct','whats_poppin','whats_on','ends','my_people'])
@app.get('/manifest.webmanifest')
def manifest():return jsonify({'name':'ON ANY PLATFORM','short_name':'OAP Platform','start_url':'/','display':'standalone','background_color':'#050706','theme_color':'#050706'})
@app.get('/sw.js')
def sw():return Response("const C='oap-v3';self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>c.addAll(['/','/manifest.webmanifest']))));self.addEventListener('fetch',e=>e.respondWith(fetch(e.request).catch(()=>caches.match(e.request))));",mimetype='application/javascript')
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','10000')))
