from flask import Blueprint, jsonify, request
import time

language = Blueprint('oap_language', __name__)


def register_oap_language(app, db, uid):
    def now(): return int(time.time())

    @language.get('/api/language')
    def language_map():
        return jsonify(
            ok=True,
            canonical={
                'feed':'Signals',
                'notifications':'Pulse',
                'verified':'Certified',
                'contribution':'Created Value'
            },
            deprecated=['Feed','Notifications','Pulse Notices'],
            authority='human_final'
        )

    @language.route('/api/pulse', methods=['GET','POST'])
    def pulse():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}
                try: target=int(d.get('user_id',u))
                except: target=u
                blocked=c.execute('select 1 from link_blocks where (owner_id=%s and blocked_id=%s) or (owner_id=%s and blocked_id=%s)',(u,target,target,u)).fetchone()
                if target!=u and blocked:return jsonify(error='blocked'),403
                c.execute('insert into link_notifications(user_id,kind,title,body,created_at) values(%s,%s,%s,%s,%s)',(
                    target,str(d.get('kind','system'))[:40],str(d.get('title','THE LINK'))[:120],str(d.get('body',''))[:500],now()))
            rows=c.execute('select id,kind,title,body,read_at,created_at from link_notifications where user_id=%s order by id desc limit 100',(u,)).fetchall()
        return jsonify(pulse=rows,canonical_name='Pulse',legacy_route='/api/notifications')

    @language.post('/api/pulse/<int:pid>/read')
    def pulse_read(pid):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:
            c.execute('update link_notifications set read_at=%s where id=%s and user_id=%s',(now(),pid,u))
        return jsonify(ok=True)

    @language.route('/api/signals', methods=['GET','POST'])
    def signals():
        with db() as c:
            if request.method=='POST':
                u=uid(); d=request.get_json(silent=True) or {}
                if not u:return jsonify(error='auth_required'),401
                scope=str(d.get('scope','postcode')).lower(); value=str(d.get('scope_value',''))[:100]; title=str(d.get('title',''))[:160]
                if scope not in {'postcode','borough','county','country','continent','global','universe'} or not title:return jsonify(error='invalid_signal'),400
                c.execute('insert into link_trends(title,scope,scope_value,score,source,created_at) values(%s,%s,%s,%s,%s,%s)',(
                    title,scope,value,int(d.get('score',1)),str(d.get('source','community'))[:40],now()))
            scope=request.args.get('scope','postcode'); value=request.args.get('scope_value','')
            if value:
                rows=c.execute('select id,title,scope,scope_value,score,source,created_at from link_trends where scope=%s and scope_value=%s order by score desc,created_at desc limit 100',(scope,value)).fetchall()
            else:
                rows=c.execute('select id,title,scope,scope_value,score,source,created_at from link_trends where scope=%s order by score desc,created_at desc limit 100',(scope,)).fetchall()
        return jsonify(signals=rows,canonical_name='Signals',legacy_route='/api/lit')

    app.register_blueprint(language)
