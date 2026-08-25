from flask import Blueprint, jsonify, request
import time

signal_intelligence = Blueprint('oap_signal_intelligence', __name__)

ALLOWED_SCOPES = ['postcode','borough','county','country','continent','global','universe']
SAFETY_SOURCES = {'community_safety','road_closure','weather_advisory','transport_update','movement_disruption','ride_safety','guardian'}
PRECISE_KEYS = ('lat','lon','latitude','longitude','exact_address','precise_location')


def rank_signals(db, scope='postcode', value='', limit=50):
    scope=str(scope or 'postcode').strip().lower()
    value=str(value or '').strip()[:100]
    if scope not in ALLOWED_SCOPES: raise ValueError('invalid_scope')
    try: limit=max(1,min(100,int(limit)))
    except Exception: raise ValueError('invalid_limit')
    select="select t.id,t.title,t.scope,t.scope_value,t.score,t.source,t.created_at,coalesce(s.trust_state,'unverified') as trust_state,s.evidence_ref from link_trends t left join oap_signal_trust s on s.signal_id=t.id"
    with db() as c:
        if value:
            rows=c.execute(select+" where (t.scope=%s and t.scope_value=%s) or t.scope in ('global','universe') order by t.created_at desc limit 300",(scope,value)).fetchall()
        else:
            rows=c.execute(select+" where t.scope=%s order by t.created_at desc limit 300",(scope,)).fetchall()
    ranked=[]; ts=int(time.time())
    for row in rows:
        r=dict(row); age=max(0,ts-int(r.get('created_at') or ts)); freshness=max(0.0,1.0-(age/(72*3600.0)))
        exact=bool(value and r.get('scope')==scope and r.get('scope_value')==value)
        geography=1.0 if exact else (0.55 if r.get('scope')=='global' else 0.35 if r.get('scope')=='universe' else 0.5)
        source=str(r.get('source') or '').lower(); certified=r.get('trust_state')=='certified'
        safety=1.0 if certified and source in SAFETY_SOURCES else 0.0
        evidence=1.0 if certified else 0.25
        legacy=min(1.0,max(0.0,float(r.get('score') or 0)/10.0))
        final=(geography*.35)+(freshness*.30)+(safety*.20)+(evidence*.10)+(legacy*.05)
        r['rank_score']=round(final,4)
        r['rank_factors']={'geography_match':round(geography,2),'freshness':round(freshness,2),'safety_importance':round(safety,2),'source_evidence':round(evidence,2),'legacy_weight_capped':round(legacy*.05,3)}
        r['evidence_state']='certified_source' if certified else 'unverified_source'; r['source_label_grants_trust']=False
        ranked.append(r)
    ranked.sort(key=lambda x:(x['rank_score'],x.get('created_at') or 0),reverse=True)
    return ranked[:limit]


def register_signal_intelligence(app, db):
    @signal_intelligence.get('/api/signal-intelligence/health')
    def health():
        return jsonify(ok=True,service='signal-intelligence',canonical_channel='Signals',ranking_inputs=['geography_match','freshness','certified_safety_importance','certified_source_evidence'],excluded_inputs=['clicks','likes','dwell_time','rage','outrage','streaks','infinite_scroll_pressure'],source_label_alone_grants_trust=False,local_first=True,precise_location=False,learning_state='purple_until_verified',authority='human_final')
    @signal_intelligence.get('/api/signals/ranked')
    def ranked_route():
        if any(k in request.args for k in PRECISE_KEYS): return jsonify(error='precise_location_ranking_blocked'),403
        try: rows=rank_signals(db,request.args.get('scope','postcode'),request.args.get('scope_value',''),request.args.get('limit','50'))
        except ValueError as e: return jsonify(error=str(e)),400
        return jsonify(signals=rows,canonical_name='Signals',ranking_policy='human_first_relevance_not_engagement_maximisation',trust_policy='certified_evidence_required_for_authority_boost',precise_location_used=False,learning_state='purple_until_verified',authority='human_final')
    app.register_blueprint(signal_intelligence)
