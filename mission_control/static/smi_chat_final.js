(()=>{
const cfg=window.OAP_SMI_UI||{};
const q=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];
const input=q('#message'),messages=q('#messages'),history=q('.history'),historyList=q('#history-list'),head=q('.chat-head'),plus=q('#plus-button'),menu=q('#attach-menu'),thinking=q('#thinking');
if(q('.chat-title'))q('.chat-title').textContent='Personal SMI';if(q('.chat-head .chat-subtitle'))q('.chat-head .chat-subtitle').textContent='Private Founder intelligence · straight answers · guarded actions';if(q('#thinking-title'))q('#thinking-title').textContent='🧠 Thinking Process · safe work stages';document.title='Personal SMI · OAP';
if(input){input.rows=1;input.placeholder='Ask SMI…';const resize=()=>{input.style.height='31px';if(input.value.trim())input.style.height=Math.min(input.scrollHeight,96)+'px';};input.addEventListener('input',resize);input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();q('#chat-form')?.requestSubmit()}});resize()}
function inline(parent,text){const re=/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g;let last=0;for(const m of text.matchAll(re)){if(m.index>last)parent.append(document.createTextNode(text.slice(last,m.index)));const t=m[0];if(t.startsWith('**')){const e=document.createElement('strong');e.textContent=t.slice(2,-2);parent.append(e)}else if(t.startsWith('`')){const e=document.createElement('code');e.className='md-inline-code';e.textContent=t.slice(1,-1);parent.append(e)}else{const p=t.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);if(p){const a=document.createElement('a');a.className='md-link';a.textContent=p[1];a.href=p[2];a.target='_blank';a.rel='noopener noreferrer';parent.append(a)}}last=m.index+t.length}if(last<text.length)parent.append(document.createTextNode(text.slice(last)))}
function rich(body,text){body.textContent='';const blocks=String(text||'').split(/```/);blocks.forEach((block,index)=>{if(index%2){const first=block.indexOf('\n'),lang=first>=0?block.slice(0,first).trim():'code',code=first>=0?block.slice(first+1):block,wrap=document.createElement('div');wrap.className='code-block';const hd=document.createElement('div');hd.className='code-head';const label=document.createElement('span');label.textContent=lang||'code';const copy=document.createElement('button');copy.type='button';copy.className='copy';copy.textContent='Copy code';copy.onclick=async()=>{try{await navigator.clipboard.writeText(code);copy.textContent='Copied ✓'}catch{copy.textContent='Copy failed'}setTimeout(()=>copy.textContent='Copy code',1400)};hd.append(label,copy);const pre=document.createElement('pre'),c=document.createElement('code');c.textContent=code;pre.append(c);wrap.append(hd,pre);body.append(wrap);return}const lines=block.split('\n');let i=0;while(i<lines.length){const line=lines[i];if(!line.trim()){i++;continue}const h=line.match(/^(#{1,3})\s+(.+)$/);if(h){const e=document.createElement('div');e.className='md-h h'+h[1].length;inline(e,h[2]);body.append(e);i++;continue}if(/^>\s?/.test(line)){const e=document.createElement('div');e.className='md-quote';inline(e,line.replace(/^>\s?/,''));body.append(e);i++;continue}if(/^[-*]\s+/.test(line)){const ul=document.createElement('ul');ul.className='md-list';while(i<lines.length&&/^[-*]\s+/.test(lines[i])){const li=document.createElement('li');inline(li,lines[i].replace(/^[-*]\s+/,''));ul.append(li);i++}body.append(ul);continue}if(/^\d+\.\s+/.test(line)){const ol=document.createElement('ol');ol.className='md-list';while(i<lines.length&&/^\d+\.\s+/.test(lines[i])){const li=document.createElement('li');inline(li,lines[i].replace(/^\d+\.\s+/,''));ol.append(li);i++}body.append(ol);continue}const p=document.createElement('div');p.className='md-p';inline(p,line);body.append(p);i++}})}
try{window.renderMessage=rich}catch{}
function enhance(msg){if(msg.dataset.uiEnhanced)return;msg.dataset.uiEnhanced='1';const body=msg.querySelector('.msg-text');if(body&&body.innerText)rich(body,body.innerText);let actions=msg.querySelector('.msg-actions');if(!actions){actions=document.createElement('div');actions.className='msg-actions';msg.append(actions)}if(msg.classList.contains('user')){const b=document.createElement('button');b.type='button';b.className='msg-action-extra';b.textContent='Edit';b.onclick=()=>{input.value=body?.innerText||'';input.focus();input.dispatchEvent(new Event('input',{bubbles:true}))};actions.append(b)}if(msg.classList.contains('assistant')){const retry=document.createElement('button');retry.type='button';retry.className='msg-action-extra';retry.textContent='Retry';retry.onclick=()=>{let p=msg.previousElementSibling;while(p&&!p.classList.contains('user'))p=p.previousElementSibling;if(!p)return;input.value=p.querySelector('.msg-text')?.innerText||'';input.dispatchEvent(new Event('input',{bubbles:true}));q('#chat-form')?.requestSubmit()};const speak=document.createElement('button');speak.type='button';speak.className='msg-action-extra';speak.textContent='🔊';speak.title='Read aloud';speak.onclick=()=>{if(!('speechSynthesis'in window))return;window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(body?.innerText||'');u.lang='en-GB';window.speechSynthesis.speak(u)};const up=document.createElement('button');up.type='button';up.className='msg-action-extra feedback-btn';up.textContent='👍';up.title='Helpful';const down=document.createElement('button');down.type='button';down.className='msg-action-extra feedback-btn';down.textContent='👎';down.title='Not helpful';const feedback=async(signal,button)=>{const requestId=msg.dataset.requestId,conversationId=msg.dataset.conversationId;if(!requestId||!conversationId){q('#status').textContent='Feedback target is not ready yet';return}up.disabled=down.disabled=true;try{const r=await fetch(cfg.feedbackUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify({request_id:requestId,conversation_id:conversationId,signal})}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||'Feedback unavailable');button.classList.add('active');q('#status').textContent='Feedback recorded in the governed audit chain'}catch(e){q('#status').textContent=e.message||'Feedback unavailable';up.disabled=down.disabled=false}};up.onclick=()=>feedback('helpful',up);down.onclick=()=>feedback('not_helpful',down);actions.append(retry,speak,up,down)}}
qa('.msg').forEach(enhance);if(messages)new MutationObserver(ms=>ms.forEach(m=>m.addedNodes.forEach(n=>{if(n.nodeType===1){if(n.classList?.contains('msg'))enhance(n);n.querySelectorAll?.('.msg').forEach(enhance)}}))).observe(messages,{childList:true,subtree:true});
if(history&&!history.querySelector('.history-search')){const s=document.createElement('input');s.className='history-search';s.type='search';s.placeholder='Search conversations';history.querySelector('.history-head')?.insertAdjacentElement('afterend',s);s.oninput=()=>historyList?.querySelectorAll('.history-item').forEach(i=>i.style.display=!s.value||i.innerText.toLowerCase().includes(s.value.toLowerCase())?'':'none')}
if(history&&head){const toggle=document.createElement('button');toggle.type='button';toggle.className='mobile-chats-toggle';toggle.textContent='☰ Saved';const bg=document.createElement('div');bg.className='history-backdrop';document.body.append(bg);const close=()=>{history.classList.remove('mobile-open');bg.classList.remove('mobile-open')};toggle.onclick=()=>{const open=!history.classList.contains('mobile-open');history.classList.toggle('mobile-open',open);bg.classList.toggle('mobile-open',open)};bg.onclick=close;head.insertBefore(toggle,head.firstChild);const actions=document.createElement('div');actions.className='chat-head-actions';const truth=document.createElement('span');truth.className='truth-strip';truth.innerHTML='<span class="truth-dot"></span><span>Checking truth</span>';const n=document.createElement('button');n.type='button';n.className='corner-action';n.textContent='＋ New';n.onclick=()=>q('#new-chat')?.click();const w=document.createElement('a');w.className='corner-action';w.href=cfg.warRoomUrl;w.textContent='⚔ War';actions.append(truth,n,w);head.append(actions);truth.querySelector('.truth-dot').className='truth-dot';truth.lastElementChild.textContent='Chat unproven · send a real message'}
let workbenchCache=null;const addTool=(title,text,state='green')=>{if(!messages)return;const c=document.createElement('div');c.className='msg tool-result';const h=document.createElement('strong');h.textContent=`${state==='green'?'🟢':'🟡'} ${title}`;const b=document.createElement('span');b.className='tool-meta';b.textContent=text;c.append(h,b);messages.append(c);messages.scrollTop=messages.scrollHeight};const loadWorkbench=async(force=false)=>{if(workbenchCache&&!force)return workbenchCache;const r=await fetch(cfg.workbenchUrl,{cache:'no-store',credentials:'same-origin'}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||'Tools unavailable');workbenchCache=d;return d};
async function inspect(id,button){button.disabled=true;const state=button.querySelector('.connector-state');if(state)state.textContent='Checking';try{const data=await loadWorkbench(true),item=data.connectors.find(x=>x.id===id);if(!item)throw new Error('Connector not registered');if(item.inspect_available===false)throw new Error(item.readiness_reason||'Inspection unavailable');const r=await fetch(item.inspect_url,{cache:'no-store',credentials:'same-origin'}),p=await r.json();if(!r.ok)throw new Error(p?.error?.message||'Inspection unavailable');const payload=p.data||p.database||p;const proven=p.proven===true;addTool(item.name,JSON.stringify(payload,null,2).slice(0,2200),proven?'green':'yellow');if(state){state.textContent=proven?'Proven':'Limited';state.classList.toggle('ready',proven);state.classList.toggle('attention',!proven)}}catch(e){addTool(id,e.message||'Inspection unavailable','yellow');if(state){state.textContent='Blocked';state.classList.remove('ready');state.classList.add('attention')}}finally{button.disabled=false;menu?.classList.remove('show')}}
function addFields(card,kind){const a=card.querySelector('[data-fields]');a.textContent='';const add=(label,name,ta=false,ph='')=>{const l=document.createElement('label');l.textContent=label;const x=document.createElement(ta?'textarea':'input');x.name=name;x.placeholder=ph;l.append(x);a.append(l)};if(kind==='branch'){add('Branch','branch',false,'oap-mind/feature');add('Base SHA','base_sha',false,'40-character SHA')}else if(kind==='file'){add('Branch','branch',false,'oap-mind/feature');add('Path','path');add('Commit message','message');add('Existing SHA (optional)','sha');add('Complete file content','content',true)}else{add('Head branch','head',false,'oap-mind/feature');add('Title','title');add('Body','body',true);add('Base','base',false,'main');a.querySelector('[name=base]').value='main'}}
function githubAction(){menu?.classList.remove('show');const c=document.createElement('div');c.className='msg action-card';c.innerHTML='<strong>⚫ Governed GitHub Action</strong><span class="tool-meta">Prepare → exact review → Human Authority receipt → Living Kernel. Nothing runs before approval.</span><label>Action<select data-kind><option value="branch">Create branch</option><option value="file">Write file</option><option value="pr">Create pull request</option></select></label><div data-fields></div><div class="action-row"><button class="action-btn primary" data-prepare type="button">Prepare exact plan</button></div><span class="tool-meta" data-state>Not prepared.</span>';messages.append(c);const kind=c.querySelector('[data-kind]');addFields(c,kind.value);kind.onchange=()=>addFields(c,kind.value);c.querySelector('[data-prepare]').onclick=async e=>{const state=c.querySelector('[data-state]'),button=e.currentTarget;button.disabled=true;try{const payload=Object.fromEntries([...c.querySelectorAll('[data-fields] input,[data-fields] textarea')].map(x=>[x.name,x.value]));const endpoint=(kind.value==='branch'?cfg.proposalBranchUrl:kind.value==='file'?cfg.proposalFileUrl:cfg.proposalPrUrl);const r=await fetch(endpoint,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify(payload)}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||'Proposal failed');const p=d.proposal;state.textContent=`${p.action_type}\nDigest ${p.action_digest}\nRequest ${p.request_id}`;button.remove();const row=document.createElement('div');row.className='action-row';const yes=document.createElement('button');yes.className='action-btn primary';yes.textContent='Approve';const no=document.createElement('button');no.className='action-btn danger';no.textContent='Reject';row.append(yes,no);c.append(row);const decide=async decision=>{yes.disabled=no.disabled=true;const ar=await fetch(cfg.approvalUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify({request_id:p.request_id,decision,action_type:p.action_type,action_digest:p.action_digest})}),ad=await ar.json();if(!ar.ok){state.textContent=ad?.error?.message||'Decision failed';yes.disabled=no.disabled=false;return}const receipt=ad.approval;state.textContent=`${receipt.decision} · signed ${receipt.receipt_id}\nExpires ${receipt.expires_at}`;if(receipt.decision==='APPROVED'){const run=document.createElement('button');run.className='action-btn primary';run.textContent='Execute through Living Kernel';row.append(run);run.onclick=async()=>{run.disabled=true;const er=await fetch(cfg.executeUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify({receipt_id:receipt.receipt_id,plan:p})}),ed=await er.json();if(!er.ok){state.textContent=ed?.error?.message||'Execution blocked';run.disabled=false;return}state.textContent=`${ed.executed?'EXECUTED':'BLOCKED'} · ${ed.state}\n${ed.reason}\nAudit ${ed.audit_event_id||'recorded'}`;run.textContent=ed.executed?'Executed ✓':'Blocked'}}};yes.onclick=()=>decide('APPROVED');no.onclick=()=>decide('REJECTED')}catch(err){state.textContent=err.message||'Proposal failed';button.disabled=false}};messages.scrollTop=messages.scrollHeight}
qa('[data-connector-id]').forEach(button=>{button.onclick=()=>inspect(button.dataset.connectorId,button)});
const safeInspect=async(title,url,button)=>{if(!url)return;button.disabled=true;try{const r=await fetch(url,{cache:'no-store',credentials:'same-origin'}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||title+' unavailable');addTool(title,JSON.stringify(d,null,2).slice(0,2200),'green')}catch(e){addTool(title,e.message||'Unavailable','yellow')}finally{button.disabled=false;menu?.classList.remove('show')}};
const studioButton=q('#studio-button');if(studioButton)studioButton.onclick=async()=>{studioButton.disabled=true;try{const r=await fetch(cfg.studioStatusUrl,{cache:'no-store',credentials:'same-origin'}),d=await r.json();if(!r.ok)throw new Error(d?.error?.message||'Studio unavailable');studioMode=!studioMode;studioButton.classList.toggle('active',studioMode);const state=q('#studio-state'),backendProven=Boolean(d?.generation_backend_configured),fullLive=Boolean(d?.full_live_certificate);if(state)state.textContent=studioMode?(fullLive?'Live':backendProven?'Generate':'Plan'):'Off';if(studioMode){const tools=(d.generation_tools||[]).map(item=>item.name).join(' · ');addTool('OAP Studio Intelligence',[tools||'Studio tools available',backendProven?'Generation backend configured':'Generation backend unconfigured',fullLive?'Full live certificate proven':'Full live certificate pending artifact proof'].join('\n'),fullLive?'green':'yellow');q('#status').textContent=fullLive?'OAP Studio Intelligence live':'OAP Studio Intelligence active · SMI 21 governed generation';if(!input.value.trim()){input.placeholder='Create or analyse with OAP Studio Intelligence…';input.focus()}}else{q('#status').textContent='OAP Studio Intelligence off';input.placeholder='Ask SMI…'}}catch(e){q('#status').textContent=e.message||'Studio unavailable'}finally{studioButton.disabled=false;menu?.classList.remove('show')}};

function studioArtifactCard(title){
  const card=document.createElement('div');card.className='msg tool-result studio-artifact';
  const head=document.createElement('strong');head.textContent=title;
  const meta=document.createElement('span');meta.className='tool-meta';card.append(head,meta);
  messages?.append(card);messages.scrollTop=messages.scrollHeight;return {card,meta};
}
function studioUrl(template,id){return String(template||'').replace('__VIDEO_ID__',encodeURIComponent(id))}
async function pollStudioVideo(videoId,card,meta){
  for(let attempt=0;attempt<30;attempt++){
    await new Promise(resolve=>setTimeout(resolve,4000));
    const r=await fetch(studioUrl(cfg.studioVideoStatusUrlTemplate,videoId),{cache:'no-store',credentials:'same-origin'}),d=await r.json();
    if(!r.ok)throw new Error(d?.error?.message||'Video status unavailable');
    const a=d.artifact||{};meta.textContent='🟣 '+String(a.status||'processing')+' · '+Number(a.progress||0)+'% · Chronicle '+(d.chronicle_receipt?.receipt_id||'recorded');
    if(a.artifact_proven===true&&String(a.status)==='completed'){
      meta.textContent='🟢 Video artifact proven · Chronicle '+(d.chronicle_receipt?.receipt_id||'recorded');
      const video=document.createElement('video');video.controls=true;video.playsInline=true;video.preload='metadata';video.src=studioUrl(cfg.studioVideoContentUrlTemplate,videoId);video.style.maxWidth='100%';video.style.borderRadius='12px';card.append(video);return;
    }
    if(['failed','cancelled'].includes(String(a.status||'').toLowerCase()))throw new Error('Video generation '+a.status);
  }
  throw new Error('Video is still processing after the bounded status window');
}
async function runStudioTool(toolId,button){
  const prompt=(input?.value||'').trim();
  if(!prompt){q('#status').textContent='Add a creation brief first';input?.focus();return}
  if(toolId==='bring_alive'&&!selectedImage){q('#status').textContent='Bring Alive needs an attached image';q('#image-button')?.click();return}
  button.disabled=true;menu?.classList.remove('show');
  const title={imagine:'🖼️ Imagine',bring_alive:'🎞️ Bring Alive',scene_builder:'🎬 Scene Builder'}[toolId]||'🎬 Studio';
  const {card,meta}=studioArtifactCard(title);meta.textContent='🟣 SMI 21 · Guardian · generating…';
  try{
    const r=await fetch(cfg.studioGenerateUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-OAP-CSRF':window.csrfToken||''},body:JSON.stringify({tool_id:toolId,prompt,source_image_data:toolId==='bring_alive'?selectedImage:''})}),d=await r.json();
    if(!r.ok)throw new Error(d?.error?.message||'Studio generation unavailable');
    const a=d.artifact||{};
    if(toolId==='imagine'&&a.artifact_proven===true&&a.b64_json){
      const img=document.createElement('img');img.alt='OAP Studio generated image';img.src='data:'+(a.mime_type||'image/png')+';base64,'+a.b64_json;img.style.maxWidth='100%';img.style.borderRadius='12px';card.append(img);
      meta.textContent='🟢 Image artifact proven · Chronicle '+(d.chronicle_receipt?.receipt_id||'recorded');q('#status').textContent='Imagine complete · artifact proven';return;
    }
    if(a.id){meta.textContent='🟣 Video job started · '+String(a.status||'queued');await pollStudioVideo(a.id,card,meta);q('#status').textContent='Studio video complete · artifact proven';return}
    throw new Error('Studio returned no proven artifact or video job');
  }catch(e){meta.textContent='🟣 '+(e.message||'Studio generation unavailable');q('#status').textContent=e.message||'Studio generation unavailable'}finally{button.disabled=false}
}
qa('[data-studio-tool]').forEach(button=>{button.onclick=()=>runStudioTool(button.dataset.studioTool,button)});
qa('[data-oap-action]').forEach(button=>{button.onclick=()=>{const id=button.dataset.oapAction;if(id==='war-room'){location.href=cfg.warRoomUrl;return}if(id==='button-proof'){safeInspect('Button Proof',cfg.buttonProofUrl,button);return}if(id==='improvement'){location.href=cfg.improvementUrl;return}if(id==='swot'){input.value=input.value.trim()?('Run SWOT Intelligence on this:\n'+input.value.trim()):'Run SWOT Intelligence on: ';input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();q('#status').textContent='SWOT Intelligence ready · Strengths · Weaknesses · Opportunities · Threats · Practical Move';menu?.classList.remove('show');return}if(id==='behaviour'){input.value=input.value.trim()?('Run Behaviour Intelligence on this:\n'+input.value.trim()):'Run Behaviour Intelligence on: ';input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();q('#status').textContent='Behaviour Intelligence ready · 21 dimensions · evidence-backed percentages only';menu?.classList.remove('show');return}if(id==='github-governed'){githubAction();return}if(id==='function-health'){safeInspect('Function Health',cfg.functionHealthUrl,button);return}if(id==='green-gate'){safeInspect('Green Gate',cfg.greenGateUrl,button);return}if(id==='hrm'){safeInspect('HRM / Jog Memory',cfg.hrmUrl,button);return}}});
if(plus&&menu&&!menu.querySelector('[data-oap-connectors]')){const d=document.createElement('div');d.className='attach-divider';d.dataset.oapConnectors='1';menu.append(d);const l=document.createElement('div');l.className='attach-section-label';l.textContent='Connected tools';menu.append(l);[['render','🟣','Render'],['github','⚫','GitHub'],['neon','🟢','Neon']].forEach(([id,icon,name])=>{const b=document.createElement('button');b.type='button';b.className='attach-option connector';b.innerHTML=`<span class="connector-copy"><span>${icon}</span><span>${name}</span></span><span class="connector-state">Inspect</span>`;b.onclick=()=>inspect(id,b);menu.append(b)});const improve=document.createElement('button');improve.type='button';improve.className='attach-option connector';improve.innerHTML='<span class="connector-copy"><span>🟠</span><span>Improvement Loop</span></span><span class="connector-state attention">Review</span>';improve.onclick=()=>{location.href=cfg.improvementUrl};menu.append(improve);const a=document.createElement('button');a.type='button';a.className='attach-option connector';a.innerHTML='<span class="connector-copy"><span>⚙️</span><span>Governed GitHub action</span></span><span class="connector-state attention">Approval</span>';a.onclick=githubAction;menu.append(a);const note=document.createElement('div');note.className='attach-note';note.textContent='Credentials never appear here. Consequential actions require Human Authority and a signed receipt.';menu.append(note)}
const nativeFetch=window.fetch.bind(window);window.fetch=async function(req,init){const response=await nativeFetch(req,init);try{const url=typeof req==='string'?req:req?.url||'';if(url===cfg.streamUrl){response.clone().text().then(text=>{for(const block of text.split(/\n\n+/)){if(!block.includes('event: complete'))continue;const line=block.split('\n').find(x=>x.startsWith('data: '));if(line){try{window.dispatchEvent(new CustomEvent('oap-smi-complete',{detail:JSON.parse(line.slice(6)).result}))}catch{}}}})}}catch{}return response};
window.OAP_SMI_MASTER={version:'1.2',masterTools:true,savedWork:true,search:true,studio21:true,studioExecution:true,buttonProof:true,autoDepthVisible:true,governedActions:true};
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
head.insertAdjacentElement('afterend',ops);

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
