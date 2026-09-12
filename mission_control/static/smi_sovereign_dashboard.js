(()=>{
'use strict';
const cfg=window.OAP_SMI_UI||{};
const CORE_SIGNALS=[
['healthy','🟢','Healthy','health'],['starting','🔵','Starting','activity'],['warning','🟡','Warning','health'],['critical','🔴','Critical','health'],['offline','⚪','Offline','system'],['learning','🟣','Learning','cognition'],['maintenance','🟤','Maintenance','state'],['high_performance','⚡','High Performance','system'],['connected','📡','Connected','system'],['synchronising','🔄','Synchronising','cognition'],['memory_active','💾','Memory Active','system'],['thinking','🧠','Thinking','cognition'],['mind_healthy','❤️','Mind Healthy','health'],['body_healthy','💪','Body Healthy','health'],['soul_healthy','✨','Soul Healthy','health'],['protected','🛡','Protected','state'],['improving','📈','Improving','state'],['alert','🚨','Alert','state'],['complete','✅','Complete','state'],['working','⏳','Active / Working','activity'],['idle','💤','Idle','activity']
];
const esc=(value)=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const stateClass=(value)=>{const v=String(value||'').toLowerCase();if(['green','ready','healthy','live','complete','connected'].some(x=>v.includes(x)))return'green';if(['critical','red','failed','error','offline','blocked'].some(x=>v.includes(x)))return'red';if(['learning','purple'].some(x=>v.includes(x)))return'purple';return'yellow'};
const stateLabel=(ready,configured)=>ready?'PROVEN':configured?'CONFIGURED':'ATTENTION';
const fetchJson=async(url)=>{if(!url)throw new Error('route_not_configured');const response=await fetch(url,{credentials:'same-origin',headers:{Accept:'application/json'},cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json()};
const goChat=()=>{document.body.classList.remove('smi-dashboard-mode');document.body.classList.add('smi-chat-mode');const input=document.getElementById('message');if(input)setTimeout(()=>input.focus(),50)};
const goDashboard=()=>{document.body.classList.remove('smi-chat-mode');document.body.classList.add('smi-dashboard-mode');window.scrollTo({top:0,behavior:'instant'})};
const scrollToPanel=(id)=>{const el=document.getElementById(id);if(el)el.scrollIntoView({behavior:'smooth',block:'start'})};
function command(icon,label,detail,href,extra=''){
 if(extra==='chat')return `<button class="smi-command" type="button" data-smi-chat><span class="smi-command-icon">${icon}</span><span><strong>${esc(label)}</strong><small>${esc(detail)}</small></span></button>`;
 return `<a class="smi-command" href="${esc(href||'#')}"><span class="smi-command-icon">${icon}</span><span><strong>${esc(label)}</strong><small>${esc(detail)}</small></span></a>`;
}
function shell(){
 const layer=document.createElement('section');layer.className='smi-dashboard-layer';layer.id='smi-dashboard';layer.setAttribute('aria-label','Sovereign Megaverse Intelligence dashboard');
 layer.innerHTML=`<div class="smi-dashboard-shell">
 <aside class="smi-rail"><div class="smi-brand"><span class="smi-brand-mark">🧠</span><strong>SOVEREIGN MEGAVERSE INTELLIGENCE</strong><small>Founder command surface · evidence before green</small></div>
 <nav class="smi-rail-nav" aria-label="SMI dashboard navigation"><button class="smi-rail-button active" type="button" data-smi-dashboard>▦ Dashboard</button><button class="smi-rail-button" type="button" data-smi-chat>✦ SMI Chat</button><button class="smi-rail-button" type="button" data-scroll="smi-live-monitor">◉ Live Monitor</button><button class="smi-rail-button" type="button" data-scroll="smi-signal-intelligence">◌ Signal Intelligence</button><a class="smi-rail-link" href="${esc(cfg.warRoomUrl)}">⚔ War Room</a><a class="smi-rail-link" href="${esc(cfg.missionUrl)}">👑 Mission Control</a><a class="smi-rail-link" href="${esc(cfg.infrastructureUrl)}">🏗 Infrastructure</a></nav>
 <div class="smi-rail-footer"><strong>Human Authority final</strong><br>Dashboard clicks do not deploy, spend, dispatch, migrate or approve consequential actions.</div></aside>
 <section class="smi-dashboard-main"><header class="smi-dashboard-top"><div><p class="smi-kicker">FOUNDER-ONLY · PRIMARY SMI SCREEN</p><h1>Sovereign Megaverse Intelligence</h1><p>One clean command view for live evidence, 21 OAP signals, intelligence readiness, infrastructure and governed action routes.</p></div><div class="smi-top-actions"><button class="smi-button" id="smi-refresh" type="button">↻ Refresh evidence</button><button class="smi-button primary" type="button" data-smi-chat>Open SMI Chat</button></div></header>
 <section class="smi-summary-strip" id="smi-summary-strip" aria-label="SMI status summary"><article class="smi-summary-card"><small>SMI</small><strong><i class="smi-dot"></i>Reading</strong><span>Governed runtime evidence</span></article><article class="smi-summary-card"><small>Identity</small><strong><i class="smi-dot"></i>Checking</strong><span>Founder boundary</span></article><article class="smi-summary-card"><small>Memory / HRM</small><strong><i class="smi-dot"></i>Checking</strong><span>Durable evidence</span></article><article class="smi-summary-card"><small>War Room</small><strong><i class="smi-dot"></i>Checking</strong><span>Evidence projection</span></article><article class="smi-summary-card"><small>21 Signals</small><strong><i class="smi-dot green"></i>21 locked</strong><span>OAP first-party language</span></article></section>
 <div class="smi-dashboard-grid"><div class="smi-stack">
 <section class="smi-panel"><div class="smi-panel-head"><h2>Command</h2><span>Working doors only</span></div><div class="smi-command-grid">${command('✦','SMI Chat','Governed intelligence conversation','#','chat')}${command('⚔','War Room','Proof, risk, weakest link',cfg.warRoomUrl)}${command('◉','Mission Control','Founder command deck',cfg.missionUrl)}${command('🧠','Brain','Readiness and intelligence state',cfg.brainUrl)}${command('🐺','Agents','Registered OAP intelligence',cfg.agentsUrl)}${command('🏗','Infrastructure','Runtime and service readiness',cfg.infrastructureUrl)}${command('👑','Judgement','Human Authority decision gate',cfg.judgementUrl)}${command('📈','Improvement','Governed improvement loop',cfg.improvementUrl)}${command('📡','ISAC','Spatial intelligence proof',cfg.isacUrl)}${command('◎','Alignment','Provider and system alignment',cfg.alignmentUrl)}${command('🌍','OAP World','Public front door',cfg.publicOapUrl)}${command('🔐','Founder Recovery','Independent emergency access',cfg.founderRecoveryUrl)}</div><div class="smi-truth"><strong>Default deny.</strong> Buttons open real registered surfaces; they do not silently execute consequential actions.</div></section>
 <section class="smi-panel smi-scroll-target" id="smi-signal-intelligence"><div class="smi-panel-head"><h2>Signal Intelligence · 21 Core</h2><span>🟣 Learning is not a warning</span></div><div class="smi-signal-grid">${CORE_SIGNALS.map(([id,emoji,label,group])=>`<article class="smi-signal" data-signal-id="${id}" title="Canonical OAP ${esc(label)} signal"><span class="emoji">${emoji}</span><strong>${esc(label)}</strong><small>${esc(group)}</small></article>`).join('')}</div><div class="smi-truth">These are the canonical OAP signal states. The live monitor below reports only states supported by runtime evidence; the dashboard never marks all 21 as active at once.</div></section>
 <section class="smi-panel"><div class="smi-panel-head"><h2>Capabilities</h2><span id="smi-capability-count">Reading evidence…</span></div><div class="smi-capability-grid" id="smi-capabilities"></div></section>
 </div><div class="smi-stack">
 <section class="smi-panel smi-scroll-target" id="smi-live-monitor"><div class="smi-panel-head"><h2>Live Intelligence Monitor</h2><span id="smi-last-refresh">Not refreshed</span></div><div class="smi-monitor-list" id="smi-monitor-list"><div class="smi-monitor-item"><span>🔄</span><span><strong>Reading governed evidence</strong><small>Workbench, health and War Room</small></span><span class="smi-state yellow">CHECKING</span></div></div></section>
 <section class="smi-panel"><div class="smi-panel-head"><h2>Connected Systems</h2><span>Secret-safe</span></div><div class="smi-connector-grid" id="smi-connectors"></div></section>
 <section class="smi-panel"><div class="smi-panel-head"><h2>Next Gate</h2><span>Strongest actionable weakness</span></div><div id="smi-next-gate" class="smi-truth">Reading live evidence before naming the next gate.</div></section>
 </div></div></section></div>`;
 return layer;
}
function renderSummary(workbench,health,war){
 const cards=document.querySelectorAll('#smi-summary-strip .smi-summary-card');
 const caps=Array.isArray(workbench?.capabilities)?workbench.capabilities:[];
 const memory=caps.find(x=>x.id==='memory');
 const warCap=caps.find(x=>x.id==='war-room');
 const runtimeReady=String(workbench?.status||'').toLowerCase()==='ready';
 const identityReady=Boolean(workbench?.runtime_gate&&!workbench.runtime_gate.fail_closed);
 const healthReady=['green','ready','healthy','ok'].includes(String(health?.status||'').toLowerCase());
 const warReady=Boolean(warCap?.ready)||(war?.validation?.passed===true);
 const values=[['SMI',runtimeReady&&healthReady?'Healthy':'Attention',runtimeReady&&healthReady?'green':'yellow','Governed runtime evidence'],['Identity',identityReady?'Available':'Fail closed',identityReady?'green':'yellow','Founder boundary'],['Memory / HRM',memory?.ready?'Active':'Attention',memory?.ready?'green':'yellow','Durable evidence'],['War Room',warReady?'Available':'Attention',warReady?'green':'yellow','Evidence projection'],['21 Signals','21 locked','green','OAP first-party language']];
 cards.forEach((card,i)=>{const [name,value,color,detail]=values[i];card.innerHTML=`<small>${name}</small><strong><i class="smi-dot ${color}"></i>${esc(value)}</strong><span>${esc(detail)}</span>`})
}
function renderCapabilities(workbench){
 const caps=Array.isArray(workbench?.capabilities)?workbench.capabilities:[];
 const host=document.getElementById('smi-capabilities');const label=document.getElementById('smi-capability-count');
 if(!host)return;host.innerHTML=caps.map(item=>`<article class="smi-capability"><strong>${item.ready?'🟢':'🟡'} ${esc(item.name)}</strong><small>${esc(item.ready?item.evidence:(item.blocked_reason||item.evidence||'Runtime proof required.'))}</small></article>`).join('')||'<div class="smi-truth">No capability projection returned.</div>';
 if(label){const ready=caps.filter(x=>x.ready).length;label.textContent=`${ready}/${caps.length} runtime-proven`}
}
function renderConnectors(workbench){
 const items=Array.isArray(workbench?.connectors)?workbench.connectors:[];const host=document.getElementById('smi-connectors');if(!host)return;
 host.innerHTML=items.map(item=>`<article class="smi-connector"><strong>${item.ready?'🟢':item.configured?'🟡':'⚪'} ${esc(item.name)}</strong><small>${esc(item.purpose||item.mode||'Provider evidence')}</small>${item.inspect_url?`<a href="${esc(item.inspect_url)}">Inspect →</a>`:''}</article>`).join('')||'<div class="smi-truth">No connector projection returned.</div>'
}
function monitorRow(icon,name,detail,state,color){return `<div class="smi-monitor-item"><span>${icon}</span><span><strong>${esc(name)}</strong><small>${esc(detail)}</small></span><span class="smi-state ${color}">${esc(state)}</span></div>`}
function renderMonitor(workbench,health,war,errors){
 const host=document.getElementById('smi-monitor-list');if(!host)return;const caps=Array.isArray(workbench?.capabilities)?workbench.capabilities:[];const connectors=Array.isArray(workbench?.connectors)?workbench.connectors:[];
 const runtimeState=workbench?.status||health?.status||'unknown';const gate=workbench?.runtime_gate||{};const rows=[];
 rows.push(monitorRow('🧠','SMI Runtime',gate.summary||'Governed runtime status.',String(runtimeState).toUpperCase(),stateClass(runtimeState)));
 caps.slice(0,6).forEach(item=>rows.push(monitorRow(item.ready?'🟢':'🟡',item.name,item.ready?item.evidence:(item.blocked_reason||'Runtime proof required.'),stateLabel(item.ready,true),item.ready?'green':'yellow')));
 connectors.forEach(item=>rows.push(monitorRow(item.ready?'📡':item.configured?'🟡':'⚪',item.name,item.readiness_reason||item.mode,stateLabel(item.ready,item.configured),item.ready?'green':item.configured?'yellow':'red')));
 if(war){const validation=Boolean(war.validation?.passed);const score=war.summary?.overall_evidence_score;rows.push(monitorRow('⚔','War Room',score!==undefined?`Evidence score ${score}; validation ${validation?'passed':'open'}.`:'Read-only evidence projection available.',validation?'PROVEN':'REVIEW',validation?'green':'yellow'))}
 errors.forEach(err=>rows.push(monitorRow('🚨',err.source,err.message,'UNAVAILABLE','red')));
 host.innerHTML=rows.join('');
 const refresh=document.getElementById('smi-last-refresh');if(refresh)refresh.textContent=`Updated ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`;
 const blockers=caps.filter(x=>!x.ready).map(x=>x.blocked_reason).filter(Boolean);const next=document.getElementById('smi-next-gate');if(next){if(errors.length)next.innerHTML=`<strong>Restore evidence feed:</strong> ${esc(errors[0].source)} is unavailable. Keep the affected capability fail-closed.`;else if(blockers.length)next.innerHTML=`<strong>Next before green:</strong> ${esc(blockers[0])}`;else next.innerHTML='<strong>Core runtime proof is green.</strong> Continue with the next governed product gate; Human Authority remains final.'}
}
async function refresh(){
 const button=document.getElementById('smi-refresh');if(button){button.disabled=true;button.textContent='↻ Reading…'};const errors=[];let workbench=null,health=null,war=null;
 const results=await Promise.allSettled([fetchJson(cfg.workbenchUrl),fetchJson(cfg.healthUrl),fetchJson(cfg.warRoomStatusUrl)]);
 if(results[0].status==='fulfilled')workbench=results[0].value;else errors.push({source:'Workbench',message:results[0].reason?.message||'Unavailable'});
 if(results[1].status==='fulfilled')health=results[1].value;else errors.push({source:'SMI health',message:results[1].reason?.message||'Unavailable'});
 if(results[2].status==='fulfilled')war=results[2].value;else errors.push({source:'War Room',message:results[2].reason?.message||'Unavailable'});
 renderSummary(workbench,health,war);renderCapabilities(workbench);renderConnectors(workbench);renderMonitor(workbench,health,war,errors);
 if(button){button.disabled=false;button.textContent='↻ Refresh evidence'}
}
function boot(){
 const main=document.querySelector('.smi-shell');if(!main||document.getElementById('smi-dashboard'))return;
 document.body.classList.add('smi-sovereign-ready','smi-dashboard-mode');
 main.insertBefore(shell(),main.querySelector('.workspace-grid'));
 const back=document.createElement('button');back.type='button';back.className='smi-button smi-chat-return';back.textContent='← Dashboard';back.addEventListener('click',goDashboard);document.body.append(back);
 document.querySelectorAll('[data-smi-chat]').forEach(el=>el.addEventListener('click',goChat));document.querySelectorAll('[data-smi-dashboard]').forEach(el=>el.addEventListener('click',goDashboard));document.querySelectorAll('[data-scroll]').forEach(el=>el.addEventListener('click',()=>scrollToPanel(el.dataset.scroll)));
 const refreshButton=document.getElementById('smi-refresh');if(refreshButton)refreshButton.addEventListener('click',refresh);
 const title=document.querySelector('.chat-title');if(title)title.textContent='Sovereign Megaverse Intelligence';const subtitle=document.querySelector('.chat-subtitle');if(subtitle)subtitle.textContent='Founder session · governed intelligence';
 refresh();window.setInterval(refresh,30000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
