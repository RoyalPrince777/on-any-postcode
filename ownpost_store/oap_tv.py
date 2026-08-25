from flask import Blueprint, jsonify, request
import time

tv=Blueprint('oap_tv',__name__)

def register_tv(app,db,uid):
    def now(): return int(time.time())
    with db() as c:
        # Internal channel_id/table names are intentionally retained for migration stability.
        c.execute("create table if not exists oap_tv_channels(id bigserial primary key,owner_id bigint not null,name text not null,slug text not null unique,description text not null default '',scope text not null default 'global',scope_value text,age_rating text not null default 'all',active boolean not null default true,created_at bigint not null)")
        c.execute("create table if not exists oap_tv_shows(id bigserial primary key,channel_id bigint not null,title text not null,description text not null default '',category text not null default 'general',age_rating text not null default 'all',created_at bigint not null)")
        c.execute("create table if not exists oap_tv_episodes(id bigserial primary key,show_id bigint not null,title text not null,description text not null default '',media_url text,thumbnail_url text,duration_seconds integer not null default 0,published boolean not null default false,published_at bigint,created_at bigint not null)")
        c.execute("create table if not exists oap_tv_schedule(id bigserial primary key,channel_id bigint not null,episode_id bigint,title text not null,starts_at bigint not null,ends_at bigint not null,live boolean not null default false,status text not null default 'scheduled',created_at bigint not null)")
        c.execute("create table if not exists oap_tv_watchlist(user_id bigint not null,episode_id bigint not null,created_at bigint not null,primary key(user_id,episode_id))")
        c.execute("create table if not exists oap_tv_views(id bigserial primary key,user_id bigint,episode_id bigint not null,progress_seconds integer not null default 0,completed boolean not null default false,created_at bigint not null,updated_at bigint not null)")
        c.execute("create table if not exists oap_tv_reactions(user_id bigint not null,episode_id bigint not null,reaction text not null,created_at bigint not null,primary key(user_id,episode_id))")
        c.execute('create index if not exists oap_tv_schedule_time_idx on oap_tv_schedule(starts_at,ends_at)')
        c.execute('create index if not exists oap_tv_channels_scope_idx on oap_tv_channels(scope,scope_value)')

    @tv.get('/api/tv/health')
    def tv_health():
        return jsonify(ok=True,service='oap-tv',product_language='My World',layers=['my_world','shows','episodes','schedule','watchlist','views','reactions','discovery'],media_transport='separate')

    def worlds_response(rows):
        return jsonify(my_worlds=rows,hierarchy=['postcode','borough','county_region','country','continent','global','universe'])

    @tv.route('/api/tv/my-world',methods=['GET','POST'])
    @tv.route('/api/tv/channels',methods=['GET','POST']) # compatibility alias; UI says My World
    def my_world():
        with db() as c:
            if request.method=='POST':
                u=uid()
                if not u:return jsonify(error='auth_required'),401
                d=request.get_json(silent=True) or {}; name=str(d.get('name','')).strip()[:120]; slug=str(d.get('slug','')).strip().lower()[:80]
                if not name or not slug or not slug.replace('-','').isalnum():return jsonify(error='invalid_my_world'),400
                scope=str(d.get('scope','global')).lower()
                if scope not in {'postcode','borough','county','country','continent','global','universe'}:return jsonify(error='invalid_scope'),400
                r=c.execute('insert into oap_tv_channels(owner_id,name,slug,description,scope,scope_value,age_rating,created_at) values(%s,%s,%s,%s,%s,%s,%s,%s) returning id',(u,name,slug,str(d.get('description',''))[:1000],scope,str(d.get('scope_value',''))[:120],str(d.get('age_rating','all'))[:20],now())).fetchone();return jsonify(ok=True,my_world_id=r['id']),201
            scope=request.args.get('scope'); val=request.args.get('scope_value')
            if scope and val: rows=c.execute('select id as my_world_id,name,slug,description,scope,scope_value,age_rating from oap_tv_channels where active=true and scope=%s and scope_value=%s order by id desc limit 100',(scope,val)).fetchall()
            elif scope: rows=c.execute('select id as my_world_id,name,slug,description,scope,scope_value,age_rating from oap_tv_channels where active=true and scope=%s order by id desc limit 100',(scope,)).fetchall()
            else: rows=c.execute('select id as my_world_id,name,slug,description,scope,scope_value,age_rating from oap_tv_channels where active=true order by id desc limit 100').fetchall()
        return worlds_response(rows)

    @tv.route('/api/tv/shows',methods=['GET','POST'])
    def shows():
        with db() as c:
            if request.method=='POST':
                if not uid():return jsonify(error='auth_required'),401
                d=request.get_json(silent=True) or {}; title=str(d.get('title','')).strip()[:160]
                raw=d.get('my_world_id',d.get('channel_id',0))
                try:cid=int(raw)
                except:cid=0
                if not title or cid<=0:return jsonify(error='invalid_show'),400
                r=c.execute('insert into oap_tv_shows(channel_id,title,description,category,age_rating,created_at) values(%s,%s,%s,%s,%s,%s) returning id',(cid,title,str(d.get('description',''))[:1000],str(d.get('category','general'))[:60],str(d.get('age_rating','all'))[:20],now())).fetchone();return jsonify(ok=True,show_id=r['id'],my_world_id=cid),201
            wid=request.args.get('my_world_id',request.args.get('channel_id')); cid=int(wid) if wid and wid.isdigit() else None
            rows=c.execute('select id,channel_id as my_world_id,title,description,category,age_rating from oap_tv_shows where (%s is null or channel_id=%s) order by id desc limit 100',(cid,cid)).fetchall()
        return jsonify(shows=rows)

    @tv.route('/api/tv/episodes',methods=['GET','POST'])
    def episodes():
        with db() as c:
            if request.method=='POST':
                if not uid():return jsonify(error='auth_required'),401
                d=request.get_json(silent=True) or {}; title=str(d.get('title','')).strip()[:160]
                try:sid=int(d.get('show_id',0));dur=max(0,int(d.get('duration_seconds',0)))
                except:return jsonify(error='invalid_episode'),400
                if not title or sid<=0:return jsonify(error='invalid_episode'),400
                published=bool(d.get('published',False)); pa=now() if published else None
                r=c.execute('insert into oap_tv_episodes(show_id,title,description,media_url,thumbnail_url,duration_seconds,published,published_at,created_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id',(sid,title,str(d.get('description',''))[:1000],str(d.get('media_url',''))[:1000] or None,str(d.get('thumbnail_url',''))[:1000] or None,dur,published,pa,now())).fetchone();return jsonify(ok=True,episode_id=r['id']),201
            sid=request.args.get('show_id'); args=(int(sid),) if sid and sid.isdigit() else ()
            if args: rows=c.execute('select id,show_id,title,description,media_url,thumbnail_url,duration_seconds,published,published_at from oap_tv_episodes where show_id=%s and published=true order by published_at desc nulls last,id desc limit 100',args).fetchall()
            else: rows=c.execute('select id,show_id,title,description,media_url,thumbnail_url,duration_seconds,published,published_at from oap_tv_episodes where published=true order by published_at desc nulls last,id desc limit 100').fetchall()
        return jsonify(episodes=rows)

    @tv.route('/api/tv/schedule',methods=['GET','POST'])
    def schedule():
        with db() as c:
            if request.method=='POST':
                if not uid():return jsonify(error='auth_required'),401
                d=request.get_json(silent=True) or {}
                try:cid=int(d.get('my_world_id',d.get('channel_id',0)));start=int(d['starts_at']);end=int(d['ends_at']);eid=int(d['episode_id']) if d.get('episode_id') else None
                except:return jsonify(error='invalid_schedule'),400
                if cid<=0 or end<=start:return jsonify(error='invalid_schedule'),400
                clash=c.execute("select 1 from oap_tv_schedule where channel_id=%s and status<>'cancelled' and starts_at<%s and ends_at>%s limit 1",(cid,end,start)).fetchone()
                if clash:return jsonify(error='schedule_conflict'),409
                r=c.execute("insert into oap_tv_schedule(channel_id,episode_id,title,starts_at,ends_at,live,status,created_at) values(%s,%s,%s,%s,%s,%s,'scheduled',%s) returning id",(cid,eid,str(d.get('title','OAP TV'))[:160],start,end,bool(d.get('live',False)),now())).fetchone();return jsonify(ok=True,schedule_id=r['id'],my_world_id=cid),201
            t=now(); rows=c.execute("select id,channel_id as my_world_id,episode_id,title,starts_at,ends_at,live,status from oap_tv_schedule where status<>'cancelled' and ends_at>=%s order by starts_at limit 200",(t,)).fetchall()
        return jsonify(schedule=rows)

    @tv.route('/api/tv/watchlist/<int:episode_id>',methods=['POST','DELETE'])
    def watchlist(episode_id):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':c.execute('insert into oap_tv_watchlist(user_id,episode_id,created_at) values(%s,%s,%s) on conflict do nothing',(u,episode_id,now()))
            else:c.execute('delete from oap_tv_watchlist where user_id=%s and episode_id=%s',(u,episode_id))
        return jsonify(ok=True)

    @tv.get('/api/tv/watchlist')
    def watchlist_get():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:rows=c.execute('select w.episode_id,e.title,e.thumbnail_url,e.duration_seconds from oap_tv_watchlist w join oap_tv_episodes e on e.id=w.episode_id where w.user_id=%s order by w.created_at desc limit 100',(u,)).fetchall()
        return jsonify(watchlist=rows)

    @tv.post('/api/tv/watch/<int:episode_id>')
    def watch_progress(episode_id):
        u=uid();d=request.get_json(silent=True) or {}
        try:progress=max(0,int(d.get('progress_seconds',0)))
        except:return jsonify(error='invalid_progress'),400
        with db() as c:r=c.execute('insert into oap_tv_views(user_id,episode_id,progress_seconds,completed,created_at,updated_at) values(%s,%s,%s,%s,%s,%s) returning id',(u,episode_id,progress,bool(d.get('completed',False)),now(),now())).fetchone()
        return jsonify(ok=True,view_id=r['id'])

    @tv.post('/api/tv/react/<int:episode_id>')
    def react(episode_id):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        d=request.get_json(silent=True) or {}; reaction=str(d.get('reaction','')).strip()[:30]
        allowed={'fire','love','laugh','safe','say_less','patterned'}
        if reaction not in allowed:return jsonify(error='invalid_reaction'),400
        with db() as c:c.execute('insert into oap_tv_reactions(user_id,episode_id,reaction,created_at) values(%s,%s,%s,%s) on conflict(user_id,episode_id) do update set reaction=excluded.reaction,created_at=excluded.created_at',(u,episode_id,reaction,now()))
        return jsonify(ok=True,reaction=reaction)

    app.register_blueprint(tv)
