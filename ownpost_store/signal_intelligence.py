from flask import Blueprint, jsonify, request
import time

signal_intelligence = Blueprint('oap_signal_intelligence', __name__)

ALLOWED_SCOPES = ['postcode','borough','county','country','continent','global','universe']
SAFETY_SOURCES = {'community_safety','road_closure','weather_advisory','transport_update','movement_disruption','ride_safety','guardian'}
EVIDENCE_SOURCES = {'official','certified','guardian','hrm','safety','transport','weather','movement'}


def register_signal_intelligence(app, db):
    def now(): return int(time.time())

    @signal_intelligence.get('/api/signal-intelligence/health')
    def health():
        return jsonify(
            ok=True,
            service='signal-intelligence',
            canonical_channel='Signals',
            ranking_inputs=['geography_match','freshness','safety_importance','source_evidence'],
            excluded_inputs=['clicks','likes','dwell_time','rage','outrage','streaks','infinite_scroll_pressure'],
            local_first=True,
            precise_location=False,
            learning_state='purple_until_verified',
            authority='human_final'
        )

    @signal_intelligence.get('/api/signals/ranked')
    def ranked():
        scope=str(request.args.get('scope','postcode')).strip().lower()
        value=str(request.args.get('scope_value','')).strip()[:100]
        if scope not in ALLOWED_SCOPES:return jsonify(error='invalid_scope'),400
        if any(k in request.args for k in ('lat','lon','latitude','longitude','exact_address','precise_location')):
            return jsonify(error='precise_location_ranking_blocked'),403
        limit=request.args.get('limit','50')
        try: limit=max(1,min(100,int(limit)))
        except:return jsonify(error='invalid_limit'),400

        with db() as c:
            if value:
                rows=c.execute("select id,title,scope,scope_value,score,source,created_at from link_trends where (scope=%s and scope_value=%s) or scope in ('global','universe') order by created_at desc limit 300",(scope,value)).fetchall()
            else:
                rows=c.execute("select id,title,scope,scope_value,score,source,created_at from link_trends where scope=%s order by created_at desc limit 300",(scope,)).fetchall()

        ranked_rows=[]
        ts=now()
        for r in rows:
            r=dict(r)
            age=max(0,ts-int(r.get('created_at') or ts))
            freshness=max(0.0,1.0-(age/(72*3600.0)))
            exact_match=bool(value and r.get('scope')==scope and r.get('scope_value')==value)
            geography=1.0 if exact_match else (0.55 if r.get('scope')=='global' else 0.35 if r.get('scope')=='universe' else 0.5)
            source=str(r.get('source') or '').lower()
            safety=1.0 if source in SAFETY_SOURCES else 0.0
            evidence=1.0 if source in EVIDENCE_SOURCES else 0.35 if source in {'community','event_update'} else 0.2
            legacy=min(1.0,max(0.0,float(r.get('score') or 0)/10.0))
            # Legacy score is capped at 5% so historic engagement-like scoring cannot dominate.
            final=(geography*0.35)+(freshness*0.30)+(safety*0.20)+(evidence*0.10)+(legacy*0.05)
            r['rank_score']=round(final,4)
            r['rank_factors']={'geography_match':round(geography,2),'freshness':round(freshness,2),'safety_importance':round(safety,2),'source_evidence':round(evidence,2),'legacy_weight_capped':round(legacy*0.05,3)}
            r['evidence_state']='supported_source' if evidence>=1.0 else 'unverified_source'
            ranked_rows.append(r)
        ranked_rows.sort(key=lambda x:(x['rank_score'],x.get('created_at') or 0),reverse=True)
        return jsonify(
            signals=ranked_rows[:limit],
            canonical_name='Signals',
            ranking_policy='human_first_relevance_not_engagement_maximisation',
            precise_location_used=False,
            learning_state='purple_until_verified',
            authority='human_final'
        )

    app.register_blueprint(signal_intelligence)
