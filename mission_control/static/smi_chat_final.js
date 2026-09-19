window.OAP_SMI_CONTROL_SURFACE_V2_PENDING=true;
(()=>{
const cfg=window.OAP_SMI_UI||{};
const q=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];
const input=q('#message'),messages=q('#messages'),history=q('.history'),historyList=q('#history-list'),head=q('.chat-head'),plus=q('#plus-button'),menu=q('#attach-menu'),thinking=q('#thinking');
if(q('.chat-title'))q('.chat-title').textContent='Personal SMI';if(q('.chat-head .chat-subtitle'))q('.chat-head .chat-subtitle').textContent='Private Founder intelligence · straight answers · guarded actions';if(q('#thinking-title'))q('#thinking-title').textContent='🧠 Thinking Process · safe work stages';document.title='Personal SMI · OAP';
if(input){input.rows=1;input.placeholder='Ask SMI…';const resize=()=>{input.style.height='31px';if(input.value.trim())input.style.height=Math.min(input.scrollHeight,96)+'px';};input.addEventListener('input',resize);resize()}
function inline(parent,text){const re=/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g;let last=0;for(const m of text.matchAll(re)){if(m.index>last)parent.append(document.createTextNode(text.slice(last,m.index)));const t=m[0];if(t.startsWith('**')){const e=document.createElement('strong');e.textContent=t.slice(2,-2);parent.append(e)}else if(t.startsWith('`')){const e=document.createElement('code');e.className='md-inline-code';e.textContent=t.slice(1,-1);parent.append(e)}else{const p=t.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);if(p){const a=document.createElement('a');a.className='md-link';a.textContent=p[1];a.href=p[2];a.target='_blank';a.rel='noopener noreferrer';parent.append(a)}}last=m.index+t.length}if(last<text.length)parent.append(document.createTextNode(text.slice(last)))}
function rich(body,text){body.textContent='';const blocks=String(text||'').split(/```/);blocks.forEach((block,index)=>{if(index%2){const first=block.indexOf('\n'),lang=first>=0?block.slice(0,first).trim():'code',code=first>=0?block.slice(first+1):block,wrap=document.createElement('div');wrap.className='code-block';const hd=document.createElement('div');hd.className='code-head';const label=document.createElement('span');label.textContent=lang||'code';const copy=document.createElement('button');copy.type='button';copy.className='copy';copy.textContent='Copy code';copy.onclick=async()=>{try{await navigator.clipboard.writeText(code);copy.textContent='Copied ✓'}catch{copy.textContent='Copy failed'}setTimeout(()=>copy.textContent='Copy code',1400)};hd.append(label,copy);const pre=document.createElement('pre'),c=document.createElement('code');c.textContent=code;pre.append(c);wrap.append(hd,pre);body.append(wrap);return}const lines=block.split('\n');let i=0;while(i<lines.length){const line=lines[i];if(!line.trim()){i++;continue}const h=line.match(/^(#{1,3})\s+(.+)$/);if(h){const e=document.createElement('div');e.className='md-h h'+h[1].length;inline(e,h[2]);body.append(e);i++;continue}if(/^>\s?/.test(line)){const e=document.createElement('div');e.className='md-quote';inline(e,line.replace(/^>\s?/,''));body.append(e);i++;continue}if(/^[-*]\s+/.test(line)){const ul=document.createElement('ul');ul.className='md-list';while(i<lines.length&&/^[-*]\s+/.test(lines[i])){const li=document.createElement('li');inline(li,lines[i].replace(/^[-*]\s+/,''));ul.append(li);i++}body.append(ul);continue}if(/^\d+\.\s+/.test(line)){const ol=document.createElement('ol');ol.className='md-list';while(i<lines.length&&/^\d+\.\s+/.test(lines[i])){const li=document.createElement('li');inline(li,lines[i].replace(/^\d+\.\s+/,''));ol.append(li);i++}body.append(ol);continue}const p=document.createElement('div');p.className='md-p';inline(p,line);body.append(p);i++}})}
try{window.renderMessage=rich}catch{}
function enhance(msg){if(msg.dataset.uiEnhanced)return;msg.dataset.uiEnhanced='1';const body=msg.querySelector('.msg-text');if(body&&body.innerText)rich(body,body.innerText);let actions=msg.querySelector('.msg-actions');if(!actions){actions=document.createElement('div');actions.className='msg-actions';msg.append(actions)}if(msg.classList.contains('user')){const b=document.createElement('button');b.type='button';b.className='msg-action-extra';b.textContent='Edit';b.onclick=()=>{input.value=body?.innerText||'';input.focus();input.dispatchEvent(new Event('input',{bubbles:true}))};actions.append(b)}if(msg.classList.contains('assistant')){const retry=document.createElement('button');retry.type='button';retry.className='msg-action-extra';retry.textContent='Retry';retry.onclick=()=>{let p=msg.previousElementSibling;while(p&&!p.classList.contains('user'))p=p.previousElementSibling;if(!p)return;input.value=p.querySelector('.msg-text')?.innerText||'';input.dispatchEvent(new Event('input',{bubbles:true}));q('#chat-form')?.requestSubmit()};const speak=document.createElement('button');speak.type='button';speak.className='msg-action-extra';speak.textContent='🔊';speak.title='Read aloud';speak.onclick=()=>{if(!('speechSynthesis'in window))return;window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(body?.innerText||'');u.lang='en-GB';window.speechSynthesis.speak(u)};const up=document.createElement('button');up.type='button';up.className='msg-action-extra feedback-btn';up.textContent='👍';up.title='Helpful';const down=document.createElement('button');down.type='button';down.className='msg-action-extra feedback-btn';down.textContent='👎';down.title='Not helpful';const feedback=async(signal,button)=>{const requestId=msg.dataset.requestId,conversationId=msg.dataset.conversationId;if(!requestId||!conversationId){q('#status').textContent='Feedback target is not ready yet';return}up.disabled=down.disabled=true;try{const r=await fetch(cfg.feedbackUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify({request_id:requestId,conversation_id:conversationId,signal})}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||'Feedback unavailable');button.classList.add('active');q('#status').textContent='Feedback recorded in the governed audit chain'}catch(e){q('#status').textContent=e.message||'Feedback unavailable';up.disabled=down.disabled=false}};up.onclick=()=>feedback('helpful',up);down.onclick=()=>feedback('not_helpful',down);actions.append(retry,speak,up,down)}}
qa('.msg').forEach(enhance);if(messages)new MutationObserver(ms=>ms.forEach(m=>m.addedNodes.forEach(n=>{if(n.nodeType===1){if(n.classList?.contains('msg'))enhance(n);n.querySelectorAll?.('.msg').forEach(enhance)}}))).observe(messages,{childList:true,subtree:true});
if(history&&!history.querySelector('.history-search')){const s=document.createElement('input');s.className='history-search';s.type='search';s.placeholder='Search conversations';history.querySelector('.history-head')?.insertAdjacentElement('afterend',s);s.oninput=()=>historyList?.querySelectorAll('.history-item').forEach(i=>i.style.display=!s.value||i.innerText.toLowerCase().includes(s.value.toLowerCase())?'':'none')}
if(history&&head){const toggle=document.createElement('button');toggle.type='button';toggle.className='mobile-chats-toggle';toggle.textContent='☰ Saved';const bg=document.createElement('div');bg.className='history-backdrop';document.body.append(bg);const close=()=>{history.classList.remove('mobile-open');bg.classList.remove('mobile-open')};toggle.onclick=()=>{const open=!history.classList.contains('mobile-open');history.classList.toggle('mobile-open',open);bg.classList.toggle('mobile-open',open)};bg.onclick=close;head.insertBefore(toggle,head.firstChild);const actions=document.createElement('div');actions.className='chat-head-actions';const truth=document.createElement('span');truth.className='truth-strip';truth.innerHTML='<span class="truth-dot"></span><span>Checking truth</span>';const n=document.createElement('button');n.type='button';n.className='corner-action';n.textContent='＋ New';n.onclick=()=>q('#new-chat')?.click();const w=document.createElement('a');w.className='corner-action';w.href=cfg.warRoomUrl;w.textContent='⚔ War';actions.append(truth,n,w);head.append(actions);truth.querySelector('.truth-dot').className='truth-dot';truth.lastElementChild.textContent='Chat unproven · send a real message'}
let workbenchCache=null;const addTool=(title,text,state='purple')=>{if(!messages)return;const c=document.createElement('div');c.className='msg tool-result';const h=document.createElement('strong');h.textContent=`${state==='green'?'🟢':state==='red'?'🔴':state==='yellow'?'🟡':'🟣'} ${title}`;const b=document.createElement('span');b.className='tool-meta';b.textContent=text;c.append(h,b);messages.append(c);messages.scrollTop=messages.scrollHeight};const loadWorkbench=async(force=false)=>{if(workbenchCache&&!force)return workbenchCache;const r=await fetch(cfg.workbenchUrl,{cache:'no-store',credentials:'same-origin'}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||'Tools unavailable');workbenchCache=d;return d};
async function inspect(id,button){button.disabled=true;const state=button.querySelector('.connector-state');if(state)state.textContent='Checking';try{const data=await loadWorkbench(true),item=data.connectors.find(x=>x.id===id);if(!item)throw new Error('Connector not registered');if(item.inspect_available===false)throw new Error(item.readiness_reason||'Inspection unavailable');const r=await fetch(item.inspect_url,{cache:'no-store',credentials:'same-origin'}),p=await r.json();if(!r.ok)throw new Error(p?.error?.message||'Inspection unavailable');const payload=p.data||p.database||p;const proven=p.proven===true;addTool(item.name,JSON.stringify(payload,null,2).slice(0,2200),proven?'green':'yellow');if(state){state.textContent=proven?'Proven':'Limited';state.classList.toggle('ready',proven);state.classList.toggle('attention',!proven)}}catch(e){addTool(id,e.message||'Inspection unavailable','yellow');if(state){state.textContent='Blocked';state.classList.remove('ready');state.classList.add('attention')}}finally{button.disabled=false;menu?.classList.remove('show')}}
function addFields(card,kind){const a=card.querySelector('[data-fields]');a.textContent='';const add=(label,name,ta=false,ph='')=>{const l=document.createElement('label');l.textContent=label;const x=document.createElement(ta?'textarea':'input');x.name=name;x.placeholder=ph;l.append(x);a.append(l)};if(kind==='branch'){add('Branch','branch',false,'oap-mind/feature');add('Base SHA','base_sha',false,'40-character SHA')}else if(kind==='file'){add('Branch','branch',false,'oap-mind/feature');add('Path','path');add('Commit message','message');add('Existing SHA (optional)','sha');add('Complete file content','content',true)}else{add('Head branch','head',false,'oap-mind/feature');add('Title','title');add('Body','body',true);add('Base','base',false,'main');a.querySelector('[name=base]').value='main'}}
function githubAction(){menu?.classList.remove('show');const c=document.createElement('div');c.className='msg action-card';c.innerHTML='<strong>⚫ Governed GitHub Action</strong><span class="tool-meta">Prepare → exact review → Human Authority receipt → Living Kernel. Nothing runs before approval.</span><label>Action<select data-kind><option value="branch">Create branch</option><option value="file">Write file</option><option value="pr">Create pull request</option></select></label><div data-fields></div><div class="action-row"><button class="action-btn primary" data-prepare type="button">Prepare exact plan</button></div><span class="tool-meta" data-state>Not prepared.</span>';messages.append(c);const kind=c.querySelector('[data-kind]');addFields(c,kind.value);kind.onchange=()=>addFields(c,kind.value);c.querySelector('[data-prepare]').onclick=async e=>{const state=c.querySelector('[data-state]'),button=e.currentTarget;button.disabled=true;try{const payload=Object.fromEntries([...c.querySelectorAll('[data-fields] input,[data-fields] textarea')].map(x=>[x.name,x.value]));const endpoint=(kind.value==='branch'?cfg.proposalBranchUrl:kind.value==='file'?cfg.proposalFileUrl:cfg.proposalPrUrl);const r=await fetch(endpoint,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify(payload)}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||'Proposal failed');const p=d.proposal;state.textContent=`${p.action_type}\nDigest ${p.action_digest}\nRequest ${p.request_id}`;button.remove();const row=document.createElement('div');row.className='action-row';const yes=document.createElement('button');yes.className='action-btn primary';yes.textContent='Approve';const no=document.createElement('button');no.className='action-btn danger';no.textContent='Reject';row.append(yes,no);c.append(row);const decide=async decision=>{yes.disabled=no.disabled=true;const ar=await fetch(cfg.approvalUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify({request_id:p.request_id,decision,action_type:p.action_type,action_digest:p.action_digest})}),ad=await ar.json();if(!ar.ok){state.textContent=ad?.error?.message||'Decision failed';yes.disabled=no.disabled=false;return}const receipt=ad.approval;state.textContent=`${receipt.decision} · signed ${receipt.receipt_id}\nExpires ${receipt.expires_at}`;if(receipt.decision==='APPROVED'){const run=document.createElement('button');run.className='action-btn primary';run.textContent='Execute through Living Kernel';row.append(run);run.onclick=async()=>{run.disabled=true;const er=await fetch(cfg.executeUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify({receipt_id:receipt.receipt_id,plan:p})}),ed=await er.json();if(!er.ok){state.textContent=ed?.error?.message||'Execution blocked';run.disabled=false;return}state.textContent=`${ed.executed?'EXECUTED':'BLOCKED'} · ${ed.state}\n${ed.reason}\nAudit ${ed.audit_event_id||'recorded'}`;run.textContent=ed.executed?'Executed ✓':'Blocked'}}};yes.onclick=()=>decide('APPROVED');no.onclick=()=>decide('REJECTED')}catch(err){state.textContent=err.message||'Proposal failed';button.disabled=false}};messages.scrollTop=messages.scrollHeight}
qa('[data-connector-id]').forEach(button=>{button.onclick=()=>inspect(button.dataset.connectorId,button)});
const safeInspect=async(title,url,button)=>{if(!url)return;button.disabled=true;try{const r=await fetch(url,{cache:'no-store',credentials:'same-origin'}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||title+' unavailable');const explicitFalse=d?.ready===false||d?.green===false||d?.schema_ready===false||d?.whole_smi_green===false;const explicitTrue=d?.ready===true||d?.green===true||d?.schema_ready===true||d?.whole_smi_green===true;addTool(title,JSON.stringify(d,null,2).slice(0,2200),explicitFalse&&!explicitTrue?'yellow':'green')}catch(e){addTool(title,e.message||'Unavailable','yellow')}finally{button.disabled=false;menu?.classList.remove('show')}};
const studioButton=q('#studio-button');if(studioButton)studioButton.onclick=async()=>{studioButton.disabled=true;try{const r=await fetch(cfg.studioStatusUrl,{cache:'no-store',credentials:'same-origin'}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||'Studio unavailable');studioMode=!studioMode;studioButton.classList.toggle('active',studioMode);const state=q('#studio-state'),backendProven=Boolean(d?.generation_backend_proven),fullLive=Boolean(d?.full_live_certificate);if(state)state.textContent=studioMode?(fullLive?'Live':backendProven?'Generate':'Plan'):'Off';if(studioMode){const tools=(d.generation_tools||[]).map(item=>item.name).join(' · ');addTool('OAP Studio Intelligence',[tools||'Studio tools available',backendProven?'Generation backend configured':'Generation backend unproven',fullLive?'Full live certificate proven':'Full live certificate pending artifact proof'].join('\n'),fullLive?'green':'yellow');q('#status').textContent=fullLive?'OAP Studio Intelligence live':'OAP Studio Intelligence active · SMI 21 governed generation';if(!input.value.trim()){input.placeholder='Create or analyse with OAP Studio Intelligence…';input.focus()}}else{q('#status').textContent='OAP Studio Intelligence off';input.placeholder='Ask SMI…'}}catch(e){q('#status').textContent=e.message||'Studio unavailable'}finally{studioButton.disabled=false;menu?.classList.remove('show')}};
const mapWorkspace=q('#smi-map-workspace'),mapFrame=q('#smi-map-frame'),mapClose=q('#smi-map-close'),mapFull=q('#smi-map-open-full');
function openMapWorkspace(path='/on-any-place'){
  if(!mapWorkspace||!mapFrame)return;
  mapWorkspace.hidden=false;document.body.classList.add('smi-map-open');
  mapFrame.src=path;if(mapFull)mapFull.href=path;
  qa('[data-map-view]').forEach(b=>b.classList.toggle('active',b.dataset.mapView===path));
  menu?.classList.remove('show');plus?.setAttribute('aria-expanded','false');
  q('#status').textContent='Map Intelligence open · OAP Spatial Core';
}
function closeMapWorkspace(){
  if(!mapWorkspace)return;
  mapWorkspace.hidden=true;document.body.classList.remove('smi-map-open');
  q('#status').textContent='Map Intelligence closed · SMI ready';
}
qa('[data-map-view]').forEach(button=>button.onclick=()=>openMapWorkspace(button.dataset.mapView||'/on-any-place'));
if(mapClose)mapClose.onclick=closeMapWorkspace;
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&mapWorkspace&&!mapWorkspace.hidden)closeMapWorkspace()});
if(!window.OAP_SMI_CONTROL_SURFACE_V2_PENDING)qa('[data-oap-action]').forEach(button=>{button.onclick=()=>{const id=button.dataset.oapAction;if(id==='map-intelligence'){openMapWorkspace('/on-any-place');return}if(id==='war-room'){location.href=cfg.warRoomUrl;return}if(id==='improvement'){location.href=cfg.improvementUrl;return}if(id==='swot'){input.value=input.value.trim()?('Run SWOT Intelligence on this:\n'+input.value.trim()):'Run SWOT Intelligence on: ';input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();q('#status').textContent='SWOT Intelligence ready · Strengths · Weaknesses · Opportunities · Threats · Practical Move';menu?.classList.remove('show');return}if(id==='behaviour'){input.value=input.value.trim()?('Run Behaviour Intelligence on this:\n'+input.value.trim()):'Run Behaviour Intelligence on: ';input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();q('#status').textContent='Behaviour Intelligence ready · 21 dimensions · evidence-backed percentages only';menu?.classList.remove('show');return}if(id==='github-governed'){githubAction();return}if(id==='function-health'){safeInspect('Function Health',cfg.functionHealthUrl,button);return}if(id==='green-gate'){safeInspect('Green Gate',cfg.greenGateUrl,button);return}if(id==='hrm'){safeInspect('HRM / Jog Memory',cfg.hrmUrl,button);return}if(id==='founder-library'){safeInspect('Founder Library',cfg.founderLibraryUrl,button);return}}});
if(plus&&menu&&!menu.querySelector('[data-oap-connectors]')){const d=document.createElement('div');d.className='attach-divider';d.dataset.oapConnectors='1';menu.append(d);const l=document.createElement('div');l.className='attach-section-label';l.textContent='Connected tools';menu.append(l);[['render','◇','Render'],['github','◇','GitHub'],['neon','◇','Neon']].forEach(([id,icon,name])=>{const b=document.createElement('button');b.type='button';b.className='attach-option connector';b.innerHTML=`<span class="connector-copy"><span>${icon}</span><span>${name}</span></span><span class="connector-state">Inspect</span>`;b.onclick=()=>inspect(id,b);menu.append(b)});const improve=document.createElement('button');improve.type='button';improve.className='attach-option connector';improve.innerHTML='<span class="connector-copy"><span>🟠</span><span>Improvement Loop</span></span><span class="connector-state attention">Review</span>';improve.onclick=()=>{location.href=cfg.improvementUrl};menu.append(improve);const a=document.createElement('button');a.type='button';a.className='attach-option connector';a.innerHTML='<span class="connector-copy"><span>⚙️</span><span>Governed GitHub action</span></span><span class="connector-state attention">Approval</span>';a.onclick=githubAction;menu.append(a);const note=document.createElement('div');note.className='attach-note';note.textContent='Credentials never appear here. Consequential actions require Human Authority and a signed receipt.';menu.append(note)}
const nativeFetch=window.fetch.bind(window);window.fetch=async function(req,init){const response=await nativeFetch(req,init);try{const url=typeof req==='string'?req:req?.url||'';if(url===cfg.streamUrl){response.clone().text().then(text=>{for(const block of text.split(/\n\n+/)){if(!block.includes('event: complete'))continue;const line=block.split('\n').find(x=>x.startsWith('data: '));if(line){try{window.dispatchEvent(new CustomEvent('oap-smi-complete',{detail:JSON.parse(line.slice(6)).result}))}catch{}}}})}}catch{}return response};
window.OAP_SMI_MASTER={version:'1.3',masterTools:true,savedWork:true,founderLibrary:true,search:true,studio21:true,mapIntelligenceWorkspace:true,governedActions:true};
window.addEventListener('oap-smi-complete',e=>{const r=e.detail||{};const assistant=[...document.querySelectorAll('.msg.assistant')].reverse().find(x=>!x.dataset.requestId);if(assistant&&r.request_id&&r.conversation_id){assistant.dataset.requestId=r.request_id;assistant.dataset.conversationId=r.conversation_id;}const c=document.createElement('div');c.className='msg receipt-card';c.innerHTML='<strong>🧾 JOOG / HRM receipt</strong><span class="receipt-meta">Shown only after the governed response completed and returned its recorded result.</span>';const g=document.createElement('div');g.className='receipt-grid';[['Request',r.request_id],['Guardian',r.guardian],['Provider',`${r.provider||'—'} · ${r.model||'—'}`],['Output',r.output_state],['Memory',r.adaptive?.active?`${r.adaptive.hrm_lessons||0} HRM lessons used`:'—'],['Judgement',r.judgement?`${r.judgement.completed_sections}/${r.judgement.total_sections}`:'—'],['Authority',r.human_authority_final?'Human final':'attention'],['Execute',r.can_execute===false?'Locked':'attention']].forEach(([k,v])=>{const p=document.createElement('div');p.className='receipt-pill';const b=document.createElement('b');b.textContent=k;const s=document.createElement('span');s.textContent=String(v||'—');p.append(b,s);g.append(p)});c.append(g);messages.append(c);messages.scrollTop=messages.scrollHeight});
const composer=q('#chat-form');if(composer){['dragenter','dragover'].forEach(n=>composer.addEventListener(n,e=>{e.preventDefault();composer.classList.add('drop-active')}));['dragleave','drop'].forEach(n=>composer.addEventListener(n,e=>{e.preventDefault();composer.classList.remove('drop-active')}));composer.addEventListener('drop',e=>{const f=e.dataTransfer?.files?.[0];if(!f)return;const target=f.type.startsWith('image/')?q('#image-input'):q('#media-input');if(!target)return;const dt=new DataTransfer();dt.items.add(f);target.files=dt.files;target.dispatchEvent(new Event('change',{bubbles:true}))})}
})();

;(()=>{
const cfg=window.OAP_SMI_UI||{};
const q=s=>document.querySelector(s);
const head=q('.chat-head');
const messages=q('#messages');
if(!head||!messages||!cfg.warRoomActionsUrl)return;

const truth=q('.truth-strip');
const ops=document.createElement('div');
ops.className='smi-chat-ops';
ops.innerHTML=
  '<div class="smi-chat-op" data-op="chat"><span class="smi-dot purple"></span><strong>Chat</strong><small>UNPROVEN</small></div>'+
  '<div class="smi-chat-op" data-op="infrastructure"><span class="smi-dot purple"></span><strong>Infrastructure</strong><small>CHECKING</small></div>'+
  '<div class="smi-chat-op" data-op="intelligence"><span class="smi-dot purple"></span><strong>Intelligence</strong><small>CHECKING</small></div>'+
  '<div class="smi-chat-op" data-op="war-room"><span class="smi-dot purple"></span><strong>War Room</strong><small>CHECKING</small></div>'+
  '<div class="smi-chat-op" data-op="green-gate"><span class="smi-dot purple"></span><strong>Green Gate</strong><small>CHECKING</small></div>';
(q('#thinking')||head).insertAdjacentElement('afterend',ops);

const actionHost=q('.chat-head-actions');
const auto=document.createElement('button');
auto.type='button';
auto.className='corner-action smi-auto-fix';
auto.textContent='🟣 AUTO FIX';
auto.title='Run bounded SMI recovery checks. Consequential changes still require Founder approval.';
actionHost?.insertBefore(auto,actionHost.firstChild);

function setOp(id,state,label){
  const el=ops.querySelector('[data-op="'+id+'"]');
  if(!el)return;
  const dot=el.querySelector('.smi-dot'),small=el.querySelector('small');
  dot.className='smi-dot '+(state==='green'?'green':state==='red'?'red':state==='yellow'?'': 'purple');
  small.textContent=label;
}
function appendResult(title,lines,state='purple'){
  const c=document.createElement('div');
  c.className='msg tool-result smi-auto-fix-result';
  const h=document.createElement('strong');
  h.textContent=(state==='green'?'🟢 ':state==='red'?'🔴 ':state==='yellow'?'🟡 ':'🟣 ')+title;
  const b=document.createElement('span');
  b.className='tool-meta';
  b.textContent=lines.join('\n');
  c.append(h,b);
  messages.append(c);
  messages.scrollTop=messages.scrollHeight;
}
async function getJson(url){
  const r=await fetch(url,{cache:'no-store',credentials:'same-origin'});
  let d={};try{d=await r.json()}catch{}
  if(!r.ok)throw new Error(d?.error?.message||('HTTP '+r.status));
  return d;
}
async function refreshOps(){
  const tasks=[
    getJson(cfg.workbenchUrl).then(d=>{
      const connectors=Array.isArray(d?.connectors)?d.connectors:[];
      const proven=connectors.filter(x=>x?.proven===true||x?.ready===true||x?.state==='ready').length;
      setOp('infrastructure',connectors.length&&proven===connectors.length?'green':'purple',connectors.length?(proven+'/'+connectors.length+' PROVEN'):'CHECKED');
    }).catch(()=>setOp('infrastructure','yellow','ATTENTION')),
    getJson(cfg.signalsUrl).then(d=>{
      const ready=Boolean(d?.ready&&d?.signals_valid&&Number(d?.signal_count)===21);
      setOp('intelligence',ready?'green':'yellow',ready?'21/21 PROVEN':'PROOF REQUIRED');
    }).catch(()=>setOp('intelligence','yellow','ATTENTION')),
    getJson(cfg.warRoomStatusUrl).then(()=>setOp('war-room','purple','STATUS CHECKED')).catch(()=>setOp('war-room','yellow','ATTENTION')),
    getJson(cfg.functionHealthUrl).then(d=>{
      const gate=d?.green_gate||{};
      const green=Boolean(d?.whole_smi_green===true&&gate?.green===true);
      setOp('green-gate',green?'green':'yellow',green?'PROVEN':'NOT GREEN');
    }).catch(()=>setOp('green-gate','yellow','ATTENTION'))
  ];
  await Promise.allSettled(tasks);
}
window.addEventListener('oap-smi-complete',event=>{
  const d=event?.detail||{};
  const durable=Boolean(
    d?.behaviour_receipt?.durable===true||
    d?.behaviour_score_receipt?.durable===true||
    d?.behaviour_learning_receipt?.durable===true||
    d?.behaviour_step4_receipt?.durable===true
  );
  const proven=Boolean(d?.response&&d?.conversation_id&&durable);
  setOp('chat',proven?'green':'yellow',proven?'PROVEN THIS SESSION':'RECEIPT UNPROVEN');
  if(truth){
    truth.querySelector('.truth-dot').className='truth-dot'+(proven?' green':'');
    truth.lastElementChild.textContent=proven?'Chat proven · response + durable receipt':'Chat response received · durable receipt unproven';
  }
  refreshOps();
});

auto.addEventListener('click',async()=>{
  if(auto.disabled)return;
  auto.disabled=true;
  auto.textContent='🟣 AUTO FIX RUNNING';
  const ids=['alignment-check','aegis-check','function-health','green-gate','hrm-receipt'];
  const results=[];
  for(const id of ids){
    try{
      const r=await fetch(cfg.warRoomActionsUrl+'/'+encodeURIComponent(id),{
        method:'POST',
        credentials:'same-origin',
        headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||cfg.csrfToken||''},
        body:'{}'
      });
      let d={};try{d=await r.json()}catch{}
      results.push({id,ok:r.ok,signal:d?.signal||d?.result?.signal||'',state:d?.state||d?.result?.state||'',message:d?.message||d?.result?.message||d?.error?.message||('HTTP '+r.status)});
    }catch(e){results.push({id,ok:false,message:e?.message||'unavailable'});}
  }
  let health={},gate={};
  try{health=await getJson(cfg.functionHealthUrl);}catch{}
  try{gate=await getJson(cfg.greenGateUrl);}catch{}
  const missing=Array.isArray(gate?.missing)?gate.missing:(Array.isArray(health?.green_gate?.missing)?health.green_gate.missing:[]);
  const allSafe=results.every(x=>x.ok);
  const fullGreen=Boolean(health?.whole_smi_green===true&&gate?.green===true);
  const lines=[
    'Safe checks: '+results.filter(x=>x.ok).length+'/'+results.length,
    'Runtime-ready: '+String(health?.runtime_ready_count??'?')+'/'+String(health?.expected_count??'?'),
    'Green Gate: '+(gate?.green===true?'PASS':'NOT PASSED'),
    missing.length?'Missing: '+missing.join(', '):'Missing: not exposed by current safe status',
    fullGreen?'No repair required.':'AUTO FIX stopped at the truth boundary. Code/deploy repair requires governed proposal + Founder approval.',
    'Consequential execution: NOT PERFORMED'
  ];
  appendResult('SMI AUTO FIX',lines,fullGreen?'green':allSafe?'purple':'yellow');
  await refreshOps();
  auto.disabled=false;
  auto.textContent='🟣 AUTO FIX';
});
setOp('chat','purple','UNPROVEN');
refreshOps();
})();

;(()=> {
  "use strict";
  const cfg=window.OAP_SMI_UI||{};
  const q=(selector,root=document)=>root.querySelector(selector);
  const qa=(selector,root=document)=>[...root.querySelectorAll(selector)];

  function bootControlSurfaceV2(){
    const menu=q("#attach-menu");
    const plus=q("#plus-button");
    const input=q("#message");
    const messages=q("#messages");
    const status=q("#status");
    if(!menu||!plus||!input||!messages)return;

    const setStatus=(text)=>{if(status)status.textContent=String(text||"");};
    const addCard=(title,text,state="purple")=>{
      const card=document.createElement("div");
      card.className="msg tool-result smi-v2-result";
      const heading=document.createElement("strong");
      heading.textContent=(state==="green"?"🟢":state==="red"?"🔴":state==="yellow"?"🟡":"🟣")+" "+title;
      const body=document.createElement("span");
      body.className="tool-meta";
      body.textContent=String(text||"");
      card.append(heading,body);
      messages.append(card);
      messages.scrollTop=messages.scrollHeight;
      return card;
    };
    const receiptId=(value)=>{
      const receipt=value&&value.chronicle_receipt;
      return receipt&&typeof receipt==="object"
        ? String(receipt.receipt_id||receipt.id||"")
        : "";
    };
    const endpoint=(template,id)=>String(template||"").replace("__VIDEO_ID__",encodeURIComponent(String(id||"")));

    async function recordButtonProof(actionId,target,statusCode){
      if(!cfg.buttonProofUrl)return null;
      try{
        const response=await fetch(cfg.buttonProofUrl,{
          method:"POST",
          credentials:"same-origin",
          headers:{
            "Content-Type":"application/json",
            "X-OAP-CSRF":window.csrfToken||cfg.csrfToken||""
          },
          body:JSON.stringify({
            action_id:actionId,
            target,
            status_code:Number(statusCode||0)
          })
        });
        const payload=await response.json().catch(()=>({}));
        if(!response.ok||payload.proven!==true)return null;
        const receipt=payload.chronicle_receipt||null;
        if(receipt?.receipt_id){
          try{sessionStorage.setItem("oap_smi_button_proof:"+actionId,String(receipt.receipt_id));}catch{}
        }
        return receipt;
      }catch{return null;}
    }

    async function fetchAck(actionId,target,{json=true}={}){
      let response;
      try{
        response=await fetch(target,{
          method:"HEAD",
          credentials:"same-origin",
          cache:"no-store",
          redirect:"follow"
        });
        if(response.status===405||response.status===501){
          response=await fetch(target,{credentials:"same-origin",cache:"no-store"});
        }
      }catch(error){
        throw new Error("Runtime route unavailable");
      }
      if(!response.ok)throw new Error("Runtime route returned "+response.status);
      const proof=await recordButtonProof(actionId,target,response.status);
      if(!json)return {response,proof,payload:null};
      let payload=null;
      try{
        const full=await fetch(target,{credentials:"same-origin",cache:"no-store"});
        if(!full.ok)throw new Error("Runtime route returned "+full.status);
        payload=await full.json();
      }catch{
        payload=null;
      }
      return {response,proof,payload};
    }

    function openMap(path="/on-any-place"){
      const workspace=q("#smi-map-workspace");
      const frame=q("#smi-map-frame");
      const full=q("#smi-map-open-full");
      if(!workspace||!frame)return;
      workspace.hidden=false;
      document.body.classList.add("smi-map-open");
      frame.src=path;
      if(full)full.href=path;
      qa("[data-map-view]").forEach(button=>button.classList.toggle("active",button.dataset.mapView===path));
      menu.classList.remove("show");
      plus.setAttribute("aria-expanded","false");
      setStatus("Map Intelligence open · OAP Spatial Core");
    }

    function makeOption({id,label,icon,state="Open",studioTool=""}){
      let button=q('[data-oap-action="'+id+'"]',menu);
      if(button)return button;
      button=document.createElement("button");
      button.type="button";
      button.className="attach-option connector smi-v2-option";
      if(studioTool){
        button.dataset.studioTool=studioTool;
      }else{
        button.dataset.oapAction=id;
      }
      button.innerHTML='<span class="connector-copy"><span>'+icon+'</span><span>'+label+'</span></span><span class="connector-state">'+state+'</span>';
      return button;
    }

    if(!q(".smi-tool-search",menu)){
      const search=document.createElement("input");
      search.type="search";
      search.className="smi-tool-search";
      search.placeholder="Search SMI tools…";
      search.setAttribute("aria-label","Search SMI tools");
      search.addEventListener("input",()=>{
        const term=search.value.trim().toLowerCase();
        qa(".attach-option",menu).forEach(button=>{
          if(button.id==="image-button"||button.id==="file-button")return;
          button.hidden=Boolean(term&&!button.innerText.toLowerCase().includes(term));
        });
      });
      menu.prepend(search);
    }

    const note=q(".attach-note",menu);
    const intelligenceLabel=document.createElement("div");
    intelligenceLabel.className="attach-section-label smi-v2-label";
    intelligenceLabel.textContent="SMI Intelligence";
    const intelligenceButtons=[
      {id:"signals-21",label:"21 Signals",icon:"📡",state:"Check"},
      {id:"guardian",label:"Guardian",icon:"🛡️",state:"Check"},
      {id:"routes",label:"Routes",icon:"🧭",state:"Check"},
      {id:"brain",label:"SMI Brain",icon:"🧬"},
      {id:"agents",label:"Agents",icon:"🧩"},
      {id:"infrastructure",label:"Infrastructure",icon:"🏗️"},
      {id:"judgement",label:"Judgement",icon:"⚖️"}
    ].map(makeOption);
    if(note&&!q(".smi-v2-label",menu)){
      note.before(intelligenceLabel,...intelligenceButtons);
    }

    const studioButton=q("#studio-button",menu);
    if(studioButton&&!q('[data-studio-tool="imagine"]',menu)){
      const studioLabel=document.createElement("div");
      studioLabel.className="attach-section-label smi-studio-tools-label";
      studioLabel.textContent="Create with Studio";
      const imagine=makeOption({id:"studio-imagine",studioTool:"imagine",label:"Imagine · Text → Image",icon:"✨",state:"Run"});
      imagine.dataset.proofAction="studio-imagine";
      const alive=makeOption({id:"studio-bring-alive",studioTool:"bring_alive",label:"Bring Alive · Image → Video",icon:"🎞️",state:"Run"});
      alive.dataset.proofAction="studio-bring-alive";
      const scene=makeOption({id:"studio-scene-builder",studioTool:"scene_builder",label:"Scene Builder · Text → Video",icon:"🎬",state:"Run"});
      scene.dataset.proofAction="studio-scene-builder";
      studioButton.after(studioLabel,imagine,alive,scene);
    }

    async function syncFunctionHealth(){
      if(!cfg.functionHealthUrl)return;
      try{
        const response=await fetch(cfg.functionHealthUrl,{credentials:"same-origin",cache:"no-store"});
        const data=await response.json();
        if(!response.ok||!Array.isArray(data.functions))return;
        const byId=new Map(data.functions.map(item=>[item.id,item]));
        qa("[data-oap-action]",menu).forEach(button=>{
          const item=byId.get(button.dataset.oapAction);
          if(!item)return;
          const chip=q(".connector-state",button);
          if(!chip)return;
          let receipt="";
          try{receipt=sessionStorage.getItem("oap_smi_button_proof:"+button.dataset.oapAction)||"";}catch{}
          const proven=Boolean(receipt);
          chip.textContent=proven?"Proven":item.state==="red"?"Blocked":item.state==="green"?"Ready":"Check";
          chip.classList.toggle("ready",proven);
          chip.classList.toggle("attention",item.state==="red");
          button.dataset.runtimeState=proven?"proven_this_session":(item.state||"unknown");
          button.dataset.proofReceipt=receipt;
          button.title=item.evidence||item.label||"";
        });
      }catch{}
    }

    plus.addEventListener("click",()=>setTimeout(()=>{
      if(menu.classList.contains("show"))syncFunctionHealth();
    },0));

    async function inspectJson(actionId,title,target,button){
      button.disabled=true;
      const chip=q(".connector-state",button);
      if(chip)chip.textContent="Checking";
      try{
        const response=await fetch(target,{credentials:"same-origin",cache:"no-store"});
        const payload=await response.json().catch(()=>({}));
        if(!response.ok)throw new Error(payload?.error?.message||title+" unavailable");
        const proof=await recordButtonProof(actionId,target,response.status);
        const proofText=proof?.receipt_id?"\nButton Proof "+proof.receipt_id:"\nButton Proof pending";
        addCard(title,JSON.stringify(payload,null,2).slice(0,2600)+proofText,proof?.receipt_id?"green":"purple");
        if(chip){
          chip.textContent=proof?.receipt_id?"Proven":"Reached";
          chip.classList.toggle("ready",Boolean(proof?.receipt_id));
          chip.classList.toggle("attention",!proof?.receipt_id);
        }
      }catch(error){
        addCard(title,error?.message||"Unavailable","red");
        if(chip){chip.textContent="Blocked";chip.classList.add("attention");}
      }finally{
        button.disabled=false;
        menu.classList.remove("show");
        plus.setAttribute("aria-expanded","false");
      }
    }

    async function navigateProven(actionId,target,button){
      button.disabled=true;
      const chip=q(".connector-state",button);
      if(chip)chip.textContent="Checking";
      try{
        const ack=await fetchAck(actionId,target,{json:false});
        if(chip)chip.textContent=ack.proof?.receipt_id?"Proven":"Reached";
        window.location.assign(target);
      }catch(error){
        addCard(button.innerText.trim(),error?.message||"Route unavailable","red");
        if(chip){chip.textContent="Blocked";chip.classList.add("attention");}
        button.disabled=false;
      }
    }

    function appendVideoCard(result,toolName){
      const artifact=result?.artifact||{};
      const card=document.createElement("div");
      card.className="msg tool-result smi-studio-artifact";
      const title=document.createElement("strong");
      title.textContent="🟣 "+toolName;
      const meta=document.createElement("span");
      meta.className="tool-meta";
      const receipt=receiptId(result);
      meta.textContent=[
        artifact.id?"Job "+artifact.id:"",
        artifact.status?"Status "+artifact.status:"",
        Number.isFinite(Number(artifact.progress))?"Progress "+Number(artifact.progress)+"%":"",
        receipt?"Chronicle "+receipt:"Chronicle receipt pending"
      ].filter(Boolean).join(" · ");
      const controls=document.createElement("div");
      controls.className="smi-studio-controls";
      const check=document.createElement("button");
      check.type="button";
      check.className="action-btn primary";
      check.textContent="Check progress";
      controls.append(check);
      card.append(title,meta,controls);
      messages.append(card);
      messages.scrollTop=messages.scrollHeight;
      const refresh=async()=>{
        check.disabled=true;
        try{
          const response=await fetch(endpoint(cfg.studioVideoStatusUrl,artifact.id),{credentials:"same-origin",cache:"no-store"});
          const payload=await response.json();
          if(!response.ok)throw new Error(payload?.error?.message||"Video status unavailable");
          const current=payload.artifact||{};
          const currentReceipt=receiptId(payload);
          meta.textContent=[
            current.id?"Job "+current.id:"",
            current.status?"Status "+current.status:"",
            Number.isFinite(Number(current.progress))?"Progress "+Number(current.progress)+"%":"",
            currentReceipt?"Chronicle "+currentReceipt:""
          ].filter(Boolean).join(" · ");
          if(current.artifact_proven){
            title.textContent="🟢 "+toolName+" · artifact proven";
            if(!q("video",card)){
              const video=document.createElement("video");
              video.controls=true;
              video.playsInline=true;
              video.preload="metadata";
              video.className="smi-studio-video";
              video.src=endpoint(cfg.studioVideoContentUrl,current.id);
              card.insertBefore(video,controls);
            }
            check.textContent="Completed ✓";
            check.disabled=true;
          }else{
            check.disabled=false;
            check.textContent="Check progress";
          }
        }catch(error){
          meta.textContent=error?.message||"Video status unavailable";
          check.disabled=false;
        }
      };
      check.addEventListener("click",refresh);
    }

    async function runStudioTool(toolId,button){
      const prompt=input.value.trim();
      const sourceImage=(typeof selectedImage!=="undefined"&&selectedImage)?selectedImage:"";
      if((toolId==="imagine"||toolId==="scene_builder")&&!prompt){
        setStatus("Add a written brief first.");
        input.focus();
        return;
      }
      if(toolId==="bring_alive"&&!sourceImage){
        setStatus("Bring Alive needs an image first · attach or capture one.");
        return;
      }
      button.disabled=true;
      const chip=q(".connector-state",button);
      if(chip)chip.textContent="Running";
      try{
        const response=await fetch(cfg.studioGenerateUrl,{
          method:"POST",
          credentials:"same-origin",
          headers:{
            "Content-Type":"application/json",
            "X-OAP-CSRF":window.csrfToken||cfg.csrfToken||""
          },
          body:JSON.stringify({
            tool_id:toolId,
            prompt:prompt||"Bring this image alive with natural cinematic motion.",
            source_image_data:sourceImage
          })
        });
        const result=await response.json();
        if(!response.ok)throw new Error(result?.error?.message||"Studio generation unavailable");
        const proofAction=button.dataset.proofAction;
        const proof=await recordButtonProof(proofAction,"/mission/studio/generate",response.status);
        const artifact=result.artifact||{};
        const toolName=result?.tool?.name||toolId;
        const receipt=receiptId(result);
        if(artifact.kind==="image"&&artifact.b64_json){
          const card=document.createElement("div");
          card.className="msg tool-result smi-studio-artifact";
          const heading=document.createElement("strong");
          heading.textContent="🟢 "+toolName+" · artifact proven";
          const image=document.createElement("img");
          image.className="smi-studio-image";
          image.alt="OAP Studio generated image";
          image.src="data:"+(artifact.mime_type||"image/png")+";base64,"+artifact.b64_json;
          const meta=document.createElement("span");
          meta.className="tool-meta";
          meta.textContent=(receipt?"Chronicle "+receipt:"Chronicle receipt pending")+(proof?.receipt_id?" · Button Proof "+proof.receipt_id:"");
          card.append(heading,image,meta);
          messages.append(card);
          messages.scrollTop=messages.scrollHeight;
        }else if(artifact.kind==="video_job"&&artifact.id){
          appendVideoCard(result,toolName);
        }else{
          addCard(toolName,JSON.stringify(result,null,2).slice(0,2600),result.output_generated?"green":"purple");
        }
        if(chip){
          chip.textContent=proof?.receipt_id?"Proven":result.output_generated?"Generated":"Started";
          chip.classList.toggle("ready",Boolean(proof?.receipt_id));
        }
        menu.classList.remove("show");
        plus.setAttribute("aria-expanded","false");
        setStatus(toolName+" complete/current state recorded · Human Authority final");
      }catch(error){
        addCard("OAP Studio",error?.message||"Studio generation unavailable","red");
        if(chip){chip.textContent="Blocked";chip.classList.add("attention");}
        setStatus(error?.message||"Studio generation unavailable");
      }finally{
        button.disabled=false;
      }
    }

    const inspectTargets={
      "function-health":["Function Health",cfg.functionHealthUrl],
      "green-gate":["Green Gate",cfg.greenGateUrl],
      "hrm":["HRM / Jog Memory",cfg.hrmUrl],
      "founder-library":["Founder Library",cfg.founderLibraryUrl],
      "signals-21":["21 Signals",cfg.signalsUrl],
      "guardian":["Guardian",cfg.guardianUrl],
      "routes":["Routes",cfg.routesUrl]
    };
    const navTargets={
      "war-room":cfg.warRoomUrl,
      "improvement":cfg.improvementUrl,
      "brain":cfg.brainUrl,
      "agents":cfg.agentsUrl,
      "infrastructure":cfg.infrastructureUrl,
      "judgement":cfg.judgementUrl
    };

    menu.addEventListener("click",async event=>{
      const studio=event.target.closest("[data-studio-tool]");
      if(studio){
        event.preventDefault();
        event.stopImmediatePropagation();
        await runStudioTool(studio.dataset.studioTool,studio);
        return;
      }
      const button=event.target.closest("[data-oap-action]");
      if(!button)return;
      const id=button.dataset.oapAction;
      if(id==="github-governed")return;
      event.preventDefault();
      event.stopImmediatePropagation();
      if(id==="map-intelligence"){
        button.disabled=true;
        try{
          const ack=await fetchAck(id,"/on-any-place",{json:false});
          const chip=q(".connector-state",button);
          if(chip)chip.textContent=ack.proof?.receipt_id?"Proven":"Reached";
          openMap("/on-any-place");
        }catch(error){
          addCard("Map Intelligence",error?.message||"Map unavailable","red");
        }finally{button.disabled=false;}
        return;
      }
      if(id==="swot"||id==="behaviour"){
        const prefix=id==="swot"?"Run SWOT Intelligence on this:\n":"Run Behaviour Intelligence on this:\n";
        input.value=input.value.trim()?prefix+input.value.trim():prefix;
        input.dispatchEvent(new Event("input",{bubbles:true}));
        input.focus();
        menu.classList.remove("show");
        plus.setAttribute("aria-expanded","false");
        setStatus(id==="swot"?"SWOT Intelligence ready":"Behaviour Intelligence ready · evidence-backed percentages only");
        return;
      }
      if(inspectTargets[id]){
        const [title,target]=inspectTargets[id];
        await inspectJson(id,title,target,button);
        return;
      }
      if(navTargets[id]){
        await navigateProven(id,navTargets[id],button);
      }
    },true);

    window.addEventListener("oap-smi-complete",event=>{
      const result=event.detail||{};
      const provider=q("#provider-state");
      const resolved=Number(result.resolved_depth||0);
      const auto=Boolean(result.auto_selected);
      if(provider&&resolved){
        provider.textContent=(auto?"AUTO → ":"Depth ")+resolved+" · Ready";
      }
      if(auto&&resolved){
        const system=document.createElement("div");
        system.className="msg system smi-depth-proof";
        system.textContent="🧠 AUTO resolved to "+resolved+" · governed completion metadata";
        messages.append(system);
        messages.scrollTop=messages.scrollHeight;
      }
    });

    syncFunctionHealth();
    window.OAP_SMI_CONTROL_SURFACE={
      version:"2.0",
      liveButtonProof:true,
      directStudioTools:true,
      autoDepthVisible:true,
      completedVideoPlayback:true,
      functionHealthSync:true,
      clickOnlyProof:false,
      functionHealthIsNotButtonProof:true,
      greenRequiresCurrentSessionReceipt:true
    };
    window.OAP_SMI_CONTROL_SURFACE_V2_PENDING=false;
  }

  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",bootControlSurfaceV2,{once:true});
  }else{
    bootControlSurfaceV2();
  }
})();

