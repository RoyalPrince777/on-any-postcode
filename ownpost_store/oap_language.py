from flask import Blueprint, jsonify, request
import time
from signal_intelligence import rank_signals, PRECISE_KEYS

language = Blueprint('oap_language', __name__)

PULSE_PRIORITY = {
    'safety':1.0,
    'account':0.9,
    'mentions':0.68,
    'replies':0.64,
    'ride':0.60,
    'movement':0.55,
    'transport':0.52,
    'weather':0.50,
    'community':0.45,
    'system':0.40,
    'other':0.35,
}
PROTECTED_PULSE = {'safety','account'}


def pulse_category(kind):
    k=str(kind or '').strip().lower()
    if any(x in k for x in ('safety','guardian','emergency','unsafe')): return 'safety'
    if any(x in k for x in ('account','security','identity')): return 'account'
    if 'mention' in k: return 'mentions'
    if 'reply' in k: return 'replies'
    if 'ride' in k: return 'ride'
    if 'movement' in k: return 'movement'
    if 'transport' in k: return 'transport'
    if 'weather' in k: return 'weather'
    if any(x in k for x in ('community','event')): return 'community'
    if k in {'system','notification','notice'}: return 'system'
    return 'other'


def rank_pulse_rows(rows, ts=None):
    ts=int(ts or time.time())
    ranked=[]
    for row in rows:
        r=dict(row)
        category=pulse_category(r.get('kind'))
        age=max(0,ts-int(r.get('created_at') or ts))
        freshness=max(0.0,1.0-(age/(72*3600.0)))
        unread=1.0 if not r.get('read_at') else 0.0
        importance=PULSE_PRIORITY[category]
        final=(importance*0.65)+(unread*0.20)+(freshness*0.15)
        r['category']=category
        r['rank_score']=round(final,4)
        r['rank_factors']={'personal_importance':round(importance,2),'unread':round(unread,2),'freshness':round(freshness,2)}
        ranked.append(r)
    ranked.sort(key=lambda x:(x['rank_score'],x.get('created_at') or 0,x.get('id') or 0),reverse=True)
    return ranked


def register_oap_language(app, db, uid):
    def now(): return int(time.time())
    def pulse_enabled(c,user_id,category):
        if category in PROTECTED_PULSE:return True
        r=c.execute('select enabled from oap_pulse_preferences where user_id=%s and category=%s',(user_id,category)).fetchone()
        return True if not r else bool(r['enabled'])

    @language.get('/api/language')
    def language_map():
        return jsonify(ok=True,canonical={'feed':'Signals','notifications':'Pulse','verified':'Certified','contribution':'Created Value'},deprecated=['Feed','Notifications','Pulse Notices'],authority='human_final')

    @language.get('/api/pulse/intelligence/health')
    def pulse_intelligence_health():
        return jsonify(ok=True,service='pulse-intelligence',canonical_channel='Pulse',ranking_inputs=['personal_importance','unread','freshness'],protected_priority=['safety','account'],protected_cross_user_spoofing=False,preference_aware_delivery=True,excluded_inputs=['clicks','likes','dwell_time','rage','outrage','streaks','infinite_scroll_pressure'],ranking_policy='human_first_personal_priority_not_engagement_maximisation',authority='human_final')

    @language.route('/api/pulse', methods=['GET','POST'])
    def pulse():
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        delivery=None
        with db() as c:
            if request.method=='POST':
                d=request.get_json(silent=True) or {}
                try: target=int(d.get('user_id',u))
                except: target=u
                kind=str(d.get('kind','system'))[:40]
                category=pulse_category(kind)
                blocked=c.execute('select 1 from link_blocks where (owner_id=%s and blocked_id=%s) or (owner_id=%s and blocked_id=%s)',(u,target,target,u)).fetchone()
                if target!=u and blocked:return jsonify(error='blocked'),403
                if target!=u and category in PROTECTED_PULSE:return jsonify(error='protected_pulse_spoof_blocked',category=category,delivery='use_authorised_event_bridge'),403
                enabled=pulse_enabled(c,target,category)
                if enabled:c.execute('insert into link_notifications(user_id,kind,title,body,created_at) values(%s,%s,%s,%s,%s)',(target,kind,str(d.get('title','THE LINK'))[:120],str(d.get('body',''))[:500],now()))
                delivery={'target_user_id':target,'category':category,'delivered':enabled,'suppressed_by_preference':not enabled,'protected':category in PROTECTED_PULSE}
            rows=c.execute('select id,kind,title,body,read_at,created_at from link_notifications where user_id=%s order by id desc limit 100',(u,)).fetchall()
        return jsonify(pulse=rank_pulse_rows(rows),delivery=delivery,canonical_name='Pulse',legacy_route='/api/notifications',ranking_policy='human_first_personal_priority_not_engagement_maximisation',authority='human_final')

    @language.post('/api/pulse/<int:pid>/read')
    def pulse_read(pid):
        u=uid()
        if not u:return jsonify(error='auth_required'),401
        with db() as c:c.execute('update link_notifications set read_at=%s where id=%s and user_id=%s',(now(),pid,u))
        return jsonify(ok=True)

    @language.route('/api/signals', methods=['GET','POST'])
    def signals():
        if any(k in request.args for k in PRECISE_KEYS):return jsonify(error='precise_location_ranking_blocked'),403
        claimed_source=None
        if request.method=='POST':
            u=uid(); d=request.get_json(silent=True) or {}
            if not u:return jsonify(error='auth_required'),401
            scope=str(d.get('scope','postcode')).lower(); value=str(d.get('scope_value',''))[:100]; title=str(d.get('title',''))[:160]
            if scope not in {'postcode','borough','county','country','continent','global','universe'} or not title:return jsonify(error='invalid_signal'),400
            if any(k in d for k in PRECISE_KEYS):return jsonify(error='precise_public_location_blocked'),403
            claimed_source=str(d.get('source','')).strip()[:40] or None
            with db() as c:c.execute('insert into link_trends(title,scope,scope_value,score,source,created_at) values(%s,%s,%s,%s,%s,%s)',(title,scope,value,int(d.get('score',1)),'community',now()))
        try: rows=rank_signals(db,request.args.get('scope','postcode'),request.args.get('scope_value',''),request.args.get('limit','100'))
        except ValueError as e:return jsonify(error=str(e)),400
        return jsonify(signals=rows,canonical_name='Signals',legacy_route='/api/lit',ranking_policy='human_first_relevance_not_engagement_maximisation',user_source_policy='community_until_certified',claimed_source_ignored=bool(claimed_source),precise_location_used=False,learning_state='purple_until_verified',authority='human_final')

    app.register_blueprint(language)
