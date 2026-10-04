(()=>{
'use strict';
const cfg=window.OAP_SMI_UI||{};
const CORE_SIGNALS=[
['healthy','🟢','Healthy','health'],['starting','🔵','Starting','activity'],['warning','🟡','Warning','health'],['critical','🔴','Critical','health'],['offline','⚪','Offline','system'],['learning','🟣','Learning','cognition'],['maintenance','🟤','Maintenance','state'],['high_performance','⚡','High Performance','system'],['connected','📡','Connected','system'],['synchronising','🔄','Synchronising','cognition'],['memory_active','💾','Memory Active','system'],['thinking','🧠','Thinking','cognition'],['mind_healthy','❤️','Mind Healthy','health'],['body_healthy','💪','Body Healthy','health'],['soul_healthy','✨','Soul Healthy','health'],['protected','🛡','Protected','state'],['improving','📈','Improving','state'],['alert','🚨','Alert','state'],['complete','✅','Complete','state'],['working','⏳','Active / Working','activity'],['idle','💤','Idle','activity']
];
const esc=(value)=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const stateClass=(value)=>{const v=String(value||'').toLowerCase();if(['green','ready','healthy','live','complete','connected','proven','available'].some(x=>v.includes(x)))return'green';if(['critical','red','failed','error','offline','blocked','missing'].some(x=>v.includes(x)))return'red';if(['learning','purple'].some(x=>v.includes(x)))return'purple';return'yellow'};
const fetchJson=async(url,timeoutMs=4500)=>{if(!url)throw new Error('route_not_configured');const controller=new AbortController();const timer=setTimeout(()=>controller.abort('dashboard_timeout'),timeoutMs);try{const response=await fetch(url,{credentials:'same-origin',headers:{Accept:'application/json'},cache:'no-store',signal:controller.signal});if(!response.ok)throw new Error(`HTTP ${response.status}`);return await response.json()}catch(error){if(error?.name==='AbortError'||controller.signal.aborted)throw new Error('timeout');throw error}finally{clearTimeout(timer)}};
const updateStatusToggle=()=>{const button=document.querySelector('.smi-chat-return');if(button)button.textContent=document.body.classList.contains('smi-home-open')?'✦ Chat':'⌂ Home'};
const goChat=()=>{document.body.classList.remove('smi-home-open');updateStatusToggle();document.getElementById('message')?.focus()};
const goDashboard=()=>{document.body.classList.add('smi-home-open');updateStatusToggle();refresh()};
const scrollToPanel=(id)=>{const panel=document.getElementById(id);if(!panel)return;if(panel.tagName==='DETAILS')panel.open=true;panel.scrollIntoView({behavior:'auto',block:'start'});};
function command(icon,label,detail,href,chat=false){if(chat)return `<button class="smi-command" type="button" data-smi-chat><span class="smi-command-icon">${icon}</span><span><strong>${esc(label)}</strong><small>${esc(detail)}</small></span></button>`;return `<a class="smi-command" href="${esc(href)}"><span class="smi-command-icon">${icon}</span><span><strong>${esc(label)}</strong><small>${esc(detail)}</small></span></a>`}
function shell(){
 const layer=document.createElement('section');layer.className='smi-dashboard-layer';layer.id='smi-dashboard';layer.setAttribute('aria-label','SMI Home dashboard');
 layer.style.setProperty('--smi-home-art',cfg.approvedWallpaperUrl?\`url("\${cfg.approvedWallpaperUrl}")\`:'none');
 const homeActions=[
  ['💬','Chat','Talk with SMI · Ideas · Analysis · Creation','#','chat'],
  ['🎯','Missions','Plan · Execute · Track',cfg.missionsUrl,'link'],
  ['🌐','War Room','Global intelligence · Challenge · Evidence',cfg.warRoomUrl,'link'],
  ['👥','Agents','Specialists · Coordination · Collaboration',cfg.agentsUrl,'link'],
  ['🗄️','Archive','Knowledge · Memory · History',cfg.archiveUrl,'link'],
  ['🛠️','Tools','Create · Build · Solve','#','tools'],
  ['⚙️','Control Center','Systems · Security · Settings',cfg.controlCenterUrl,'link']
 ];
 const actionMarkup=homeActions.map(([icon,label,detail,href,kind])=>{
  const body=\`<span class="smi-home-action-icon">\${icon}</span><span class="smi-home-action-copy"><strong>\${esc(label)}</strong><small>\${esc(detail)}</small></span><span class="smi-home-action-arrow">›</span>\`;
  if(kind==='chat')return \`<button class="smi-home-action" type="button" data-smi-chat>\${body}</button>\`;
  if(kind==='tools')return \`<button class="smi-home-action" type="button" data-smi-tools>\${body}</button>\`;
  return \`<a class="smi-home-action" href="\${esc(href||'#')}">\${body}</a>\`;
 }).join('');
 layer.innerHTML=\`<div class="smi-dashboard-shell">
  <section class="smi-dashboard-main smi-home-main">
   <header class="smi-dashboard-top smi-home-top">
    <div><p class="smi-kicker">OAP · SMI · HUMAN AUTHORITY ALWAYS FINAL</p><h1>SMI</h1><p>One brain. One home screen. Seven top-level rooms.</p></div>
    <div class="smi-top-actions"><button class="smi-button" id="smi-refresh" type="button">↻ Refresh signals</button><button class="smi-button primary" type="button" data-smi-chat>Open Chat</button></div>
   </header>
   <section class="smi-home-stage" aria-label="SMI primary navigation">
    <div class="smi-home-character" aria-hidden="true"></div>
    <div class="smi-home-actions">\${actionMarkup}</div>
   </section>
   <section class="smi-summary-strip smi-home-summary" id="smi-summary-strip" aria-label="SMI essential status">
    <article class="smi-summary-card"><small>SMI</small><strong><i class="smi-dot"></i>Reading</strong><span>Runtime</span></article>
    <article class="smi-summary-card"><small>Founder</small><strong><i class="smi-dot"></i>Checking</strong><span>Authority</span></article>
    <article class="smi-summary-card"><small>HRM</small><strong><i class="smi-dot"></i>Checking</strong><span>Memory</span></article>
    <article class="smi-summary-card"><small>Green Gate</small><strong><i class="smi-dot"></i>Checking</strong><span>Proof</span></article>
    <article class="smi-summary-card"><small>21 Signals</small><strong><i class="smi-dot"></i>Checking</strong><span>Canonical</span></article>
   </section>
   <div class="smi-home-lower">
    <section class="smi-panel smi-scroll-target" id="smi-live-monitor"><div class="smi-panel-head"><h2>System Status</h2><span id="smi-last-refresh">Starting bounded read</span></div><div class="smi-monitor-list" id="smi-monitor-list"><div class="smi-monitor-item"><span>🔄</span><span><strong>Reading evidence</strong><small>Bounded to 4.5 seconds per endpoint; unavailable never means Green.</small></span><span class="smi-state yellow">CHECKING</span></div></div><div class="smi-secondary-proof" aria-label="Core Functions"><strong>Core Functions</strong><div class="smi-secondary-proof-actions"><a href="${esc(cfg.functionHealthUrl)}">Function Health</a><a href="${esc(cfg.greenGateUrl)}">Green Gate</a><button type="button" data-scroll="smi-signal-intelligence">21 Signals</button><a href="${esc(cfg.guardianUrl)}">Guardian</a><a href="${esc(cfg.hrmUrl)}">HRM</a></div><small>No duplicate controls · proof routes only.</small></div></section>
    <details class="smi-panel smi-signal-details smi-scroll-target" id="smi-signal-intelligence"><summary><span><strong>21 Signals</strong><small>Canonical OAP signal contract · open only when needed</small></span><span>Open</span></summary><div class="smi-signal-runtime" id="smi-signal-runtime" role="status" aria-live="polite">Awaiting bounded signed-in response · no green assumed.</div><div class="smi-signal-grid">\${CORE_SIGNALS.map(([id,emoji,label,group])=>\`<article class="smi-signal" data-signal-id="\${id}"><span class="emoji">\${emoji}</span><strong>\${esc(label)}</strong><small>\${esc(group)}</small></article>\`).join('')}</div></details>
   </div>
   <section class="smi-truth smi-first-party-note"><strong>Truth Mode.</strong> Dashboard buttons route to existing first-party rooms. A home-screen click does not silently deploy, spend, dispatch, migrate or approve consequential actions.</section>
  </section>
 </div>\`;
 return layer;
}
function renderSummary(workbench,health,functionHealth,greenGate,signals){const cards=document.querySelectorAll('#smi-summary-strip .smi-summary-card');const caps=Array.isArray(workbench?.capabilities)?workbench.capabilities:[];const memory=caps.find(x=>x.id==='memory');const runtimeReady=String(workbench?.status||'').toLowerCase()==='ready'&&['green','ready','healthy','ok'].includes(String(health?.status||'').toLowerCase());const founderReady=Boolean(workbench?.runtime_gate&&!workbench.runtime_gate.fail_closed);const gateReady=Boolean(greenGate?.green);const signalsReady=Boolean(signals?.ready&&signals?.signals_valid&&Number(signals?.signal_count)===21);const functions=`${Number(functionHealth?.available_count||0)}/${Number(functionHealth?.expected_count||0)}`;const values=[['SMI',runtimeReady?'Healthy':'Attention',runtimeReady?'green':'yellow',`${functions} functions routed`],['Founder',founderReady?'Protected':'Fail closed',founderReady?'green':'yellow','Authority'],['HRM',memory?.ready?'Active':'Attention',memory?.ready?'green':'yellow','Memory'],['Green Gate',gateReady?'Green':'Proof required',gateReady?'green':'yellow','Proof'],['21 Signals',signalsReady?'Validated':'Review',signalsReady?'green':'yellow','Canonical']];cards.forEach((card,i)=>{const [name,value,color,detail]=values[i];card.innerHTML=`<small>${name}</small><strong><i class="smi-dot ${color}"></i>${esc(value)}</strong><span>${esc(detail)}</span>`})}
function row(icon,name,detail,state,color){return `<div class="smi-monitor-item"><span>${icon}</span><span><strong>${esc(name)}</strong><small>${esc(detail)}</small></span><span class="smi-state ${color}">${esc(state)}</span></div>`}
function renderMonitor(workbench,health,war,functionHealth,greenGate,signals,errors){const host=document.getElementById('smi-monitor-list');if(!host)return;const rows=[];const runtimeState=workbench?.status||health?.status||'unknown';rows.push(row('🧠','SMI Runtime',workbench?.runtime_gate?.summary||'Governed runtime status.',String(runtimeState).toUpperCase(),stateClass(runtimeState)));const functions=Array.isArray(functionHealth?.functions)?functionHealth.functions:[];const available=Number(functionHealth?.available_count||0);const expected=Number(functionHealth?.expected_count||0);const checked=Number(functionHealth?.proof_checked_count||0);const proofRequired=Number(functionHealth?.proof_required_count||0);const functionReady=expected>0&&available===expected&&checked===expected&&proofRequired===0;rows.push(row('✓','Function Health',`${available}/${expected||'?'} routes · ${checked}/${expected||'?'} proof checks`,functionReady?'PROVEN':proofRequired?'PROOF REQUIRED':'REVIEW',functionReady?'green':'yellow'));if(signals)rows.push(row('◌','21 Signals',`${Number(signals.signal_count||0)} canonical states.`,signals.ready&&signals.signals_valid?'PROVEN':'REVIEW',signals.ready&&signals.signals_valid?'green':'yellow'));if(greenGate)rows.push(row('🟢','Green Gate',greenGate.green?'Current bounded proof checks satisfied.':`Missing: ${(greenGate.missing||[]).join(', ')||'proof required'}.`,greenGate.green?'GREEN':'PROOF REQUIRED',greenGate.green?'green':'yellow'));if(war){const validation=Boolean(war.validation?.passed);rows.push(row('⚔','War Room',war.summary?.overall_evidence_score!==undefined?`Evidence score ${war.summary.overall_evidence_score}.`:'Evidence projection available.',validation?'PROVEN':'REVIEW',validation?'green':'yellow'))}errors.forEach(err=>rows.push(row('🚨',err.source,err.message,'UNAVAILABLE','red')));host.innerHTML=rows.join('');document.getElementById('smi-last-refresh').textContent=`Updated ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`;const next=document.getElementById('smi-next-gate');const missing=(greenGate?.missing||[])[0];const routeGap=functions.find(x=>!x.available);const proofGap=functions.find(x=>x.runtime_proven===false);if(errors.length)next.innerHTML=`<strong>Restore evidence:</strong> ${esc(errors[0].source)}`;else if(routeGap)next.innerHTML=`<strong>Fix route:</strong> ${esc(routeGap.name)}`;else if(missing)next.innerHTML=`<strong>Next before green:</strong> ${esc(missing)}`;else if(proofGap)next.innerHTML=`<strong>Prove:</strong> ${esc(proofGap.name)}`;else next.innerHTML='<strong>Core bounded proof is green.</strong> Human Authority remains final.'}
let dashboardRefreshing=false;async function refresh(){if(dashboardRefreshing)return;dashboardRefreshing=true;const button=document.getElementById('smi-refresh');if(button){button.disabled=true;button.textContent='↻ Reading…'}const urls=[cfg.workbenchUrl,cfg.healthUrl,cfg.warRoomStatusUrl,cfg.functionHealthUrl,cfg.greenGateUrl,cfg.signalsUrl];const names=['Workbench','SMI health','War Room','Function Health','Green Gate','21 Signals'];const results=await Promise.allSettled(urls.map(fetchJson));const errors=[];results.forEach((r,i)=>{if(r.status==='rejected')errors.push({source:names[i],message:r.reason?.message||'Unavailable'})});const value=i=>results[i].status==='fulfilled'?results[i].value:null;const workbench=value(0),health=value(1),war=value(2),functionHealth=value(3),greenGate=value(4),signals=value(5);renderSummary(workbench,health,functionHealth,greenGate,signals);
 const signalRuntime=document.getElementById('smi-signal-runtime');
 if(signalRuntime){
  const valid=signals?.ready===true&&signals?.signals_valid===true&&Number(signals?.signal_count)===21;
  signalRuntime.textContent=signals?
   (valid?'21/21 signal contract validated · source status received':String(Number(signals?.signal_count||0))+'/21 signals · NOT PROVEN · check endpoint evidence'):
   '21 Signals endpoint unavailable · NOT PROVEN';
  signalRuntime.dataset.proven=String(valid);
 }
 renderMonitor(workbench,health,war,functionHealth,greenGate,signals,errors);if(button){button.disabled=false;button.textContent='↻ Refresh signals'}dashboardRefreshing=false}
function boot(){
 const main=document.querySelector('.smi-shell');if(!main||document.getElementById('smi-dashboard'))return;
 document.body.classList.add('smi-sovereign-ready','smi-home-open');
 main.insertBefore(shell(),main.querySelector('.workspace-grid'));
 const back=document.createElement('button');back.type='button';back.className='corner-action smi-chat-return';back.textContent='✦ Chat';
 back.addEventListener('click',()=>document.body.classList.contains('smi-home-open')?goChat():goDashboard());
 (document.querySelector('.chat-head-actions')||document.querySelector('.chat-head'))?.append(back);
 document.querySelectorAll('[data-smi-chat]').forEach(el=>el.addEventListener('click',goChat));
 document.querySelectorAll('[data-smi-dashboard]').forEach(el=>el.addEventListener('click',goDashboard));
 document.querySelectorAll('[data-scroll]').forEach(el=>el.addEventListener('click',()=>scrollToPanel(el.dataset.scroll)));
 document.querySelectorAll('[data-smi-tools]').forEach(el=>el.addEventListener('click',()=>{goChat();setTimeout(()=>document.getElementById('plus-button')?.click(),0)}));
 document.getElementById('smi-refresh')?.addEventListener('click',refresh);
 const title=document.querySelector('.chat-title');if(title)title.textContent='SMI';
 const subtitle=document.querySelector('.chat-subtitle');if(subtitle)subtitle.textContent='Founder session · OAP first-party intelligence';
 refresh();window.setInterval(()=>{if(document.body.classList.contains('smi-home-open'))refresh()},30000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
