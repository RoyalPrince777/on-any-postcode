/* Additive Command Centre. Existing Chat, Live SMI, Guardian and Founder actions stay canonical. */
(() => {
 "use strict";
 const cfg=window.OAP_SMI_UI||{};
 const chatbox=document.querySelector(".chatbox");
 const head=document.querySelector(".chat-head");
 const character=document.getElementById("smi-character");
 const messages=document.getElementById("messages");
 if(!chatbox||!head||!character||!messages||document.getElementById("smi-command-centre"))return;
 const marker=document.createComment("original SMI character position");
 character.parentNode.insertBefore(marker,character);
 const presenceActions=document.createElement("nav");
 presenceActions.className="smi-presence-actions";
 presenceActions.setAttribute("aria-label","SMI character controls");
 for(const [label,target] of [["💬 Chat","messages"],["＋ Tools","plus-button"],["⚔️ War Room","war-room"]]){
  const button=document.createElement("button");button.type="button";button.textContent=label;
  button.addEventListener("click",()=>{
   if(target==="messages"){
    if(document.body.classList.contains("smi-command-open"))document.querySelector(".smi-command-close")?.click();
    document.getElementById("message")?.focus();return;
   }
   if(document.body.classList.contains("smi-command-open"))document.querySelector(".smi-command-close")?.click();
   if(target==="war-room")document.querySelector('#attach-menu [data-oap-action="war-room"]')?.click();
   else document.getElementById(target)?.click();
  });
  presenceActions.append(button);
 }
 character.append(presenceActions);
 const actionHost=head.querySelector(".chat-head-actions")||head;
 const toggle=document.createElement("button");
 toggle.type="button";toggle.className="smi-command-toggle";
 toggle.textContent="◈ Command Centre";toggle.setAttribute("aria-pressed","false");
 toggle.setAttribute("aria-controls","smi-command-centre");
 toggle.setAttribute("aria-label","Open SMI Command Centre");
 actionHost.append(toggle);
 const panel=document.createElement("section");
 panel.className="smi-command-centre";panel.id="smi-command-centre";
 panel.setAttribute("aria-label","OAP SMI Digital Organism Command Centre");
 panel.innerHTML='<header class="smi-command-top"><div><strong>♛ OAP · SMI THE DIGITAL ORGANISM</strong><br><small>ONE BRAIN · A LIVING SYSTEM · A BRIGHTER TOMORROW</small></div><button type="button" class="smi-command-close">✕ Close</button></header><div class="smi-command-layout"><nav class="smi-command-side smi-command-anatomy" aria-label="SMI organism systems"><h3>OAP SYSTEMS · ANATOMY</h3></nav><div class="smi-command-scene"><div class="smi-command-stage"></div><div class="smi-command-foot"><span>🧠 <b>SMI</b> · one brain</span><span>👑 Human Authority final</span></div></div><aside class="smi-command-side smi-command-evidence" aria-label="Live evidence and universe links"><h3>LIVE EVIDENCE · NOT ASSUMED</h3></aside></div><p class="smi-command-note">System labels are navigation, not proof. Status stays unverified unless a signed-in backend check returns exact true.</p>';
 messages.before(panel);
 // The full-room overlay must expose Status itself: its old header control sits underneath it.
 const statusActions=document.createElement("div");
 statusActions.className="smi-command-status-actions";
 const statusButton=document.createElement("button");statusButton.type="button";
 statusButton.textContent="📊 SMI Status";statusButton.setAttribute("aria-label","Open live SMI status and percentages");
 const signalsButton=document.createElement("button");signalsButton.type="button";
 signalsButton.textContent="◌ 21 Signals";signalsButton.setAttribute("aria-label","Open canonical 21 Signals status");
 statusActions.append(statusButton,signalsButton);
 panel.querySelector(".smi-command-top").append(statusActions);
 const openStatus=(signals=false)=>{
  const statusToggle=document.querySelector(".smi-chat-return");
  if(!statusToggle){const feedback=document.getElementById("status");if(feedback)feedback.textContent="SMI Status unavailable";return;}
  if(!document.body.classList.contains("smi-status-open"))statusToggle.click();
  if(signals){
   const details=document.getElementById("smi-signal-intelligence");
   if(details){details.open=true;details.scrollIntoView({block:"start",behavior:"auto"});}
  }
 };
 statusButton.addEventListener("click",()=>openStatus(false));
 signalsButton.addEventListener("click",()=>openStatus(true));
 // Quick access reuses the existing, governed Master Tools handlers.
 const universe=document.createElement("nav");
 universe.className="smi-command-universe";
 universe.setAttribute("aria-label","SMI universe tools");
 const quickActions=[
  ["⚔️ War Room","war-room"],
  ["🕶 Matrix","agents"],
  ["🧠 HRM","hrm"],
  ["🛡 Guardian","guardian"],
  ["🟣 Green Gate","green-gate"]
 ];
 for(const [label,action] of quickActions){
  const button=document.createElement("button");button.type="button";button.textContent=label;
  button.dataset.action=action;
  universe.append(button);
 }
 panel.querySelector(".smi-command-layout").after(universe);
 // Mobile remains one command room: expose anatomy and live evidence as real tabs.
 const mobileViews=document.createElement("nav");
 mobileViews.className="smi-command-mobile-views";
 mobileViews.setAttribute("aria-label","Mobile SMI room views");
 for(const [name,label] of [["scene","👁 Presence"],["anatomy","🧬 Anatomy"],["evidence","📊 Evidence"]]){
  const tab=document.createElement("button");tab.type="button";tab.textContent=label;tab.dataset.view=name;
  tab.setAttribute("aria-pressed",String(name==="scene"));
  mobileViews.append(tab);
 }
 panel.querySelector(".smi-command-layout").before(mobileViews);
 panel.dataset.mobileView="scene";
 mobileViews.addEventListener("click",event=>{
  const tab=event.target.closest("button[data-view]");
  if(!tab)return;
  panel.dataset.mobileView=tab.dataset.view;
  mobileViews.querySelectorAll("button[data-view]").forEach(button=>button.setAttribute("aria-pressed",String(button===tab)));
  if(tab.dataset.view==="evidence"){refreshEvidence();refreshRoomStatus();}
 });
 const stage=panel.querySelector(".smi-command-stage");
 // First-party state-linked ambient motion; never replace or deform the approved still.
 const presence=document.createElement("div");
 presence.className="smi-scene-presence";
 presence.setAttribute("aria-hidden","true");
 stage.append(presence);
 const presenceStates=new Set(["ready","listening","thinking","speaking","paused","stopped"]);
 const setPresenceState=(value)=>{
  panel.dataset.presenceState=presenceStates.has(value)?value:"ready";
 };
 setPresenceState(character.dataset.state||"ready");
 // Load the exact approved picture from the first-party app asset.
 // No visual green until the bytes resolve; the existing CSS character remains fallback.
 const scene=panel.querySelector(".smi-command-scene");
 if(cfg.approvedWallpaperUrl){
  const wallpaper=new Image();
  wallpaper.onload=()=>{
   if(!wallpaper.naturalWidth||!wallpaper.naturalHeight)return;
   scene.style.setProperty("--oap-smi-wallpaper",'url("'+cfg.approvedWallpaperUrl+'")');
   panel.classList.add("smi-room-art-loaded");
   scene.dataset.wallpaperReady="true";
  };
  wallpaper.onerror=()=>{
   scene.dataset.wallpaperReady="false";
   const status=document.getElementById("status");
   if(status)status.textContent="Approved SMI artwork unavailable · existing organism preserved";
  };
  wallpaper.src=cfg.approvedWallpaperUrl;
 }
 const anatomy=panel.querySelector(".smi-command-anatomy");
 const evidence=panel.querySelector(".smi-command-evidence");
 const anatomyLinks=[
  ["🧠","Brain · SMI","Intelligence · memory · reasoning",cfg.brainUrl],
  ["👁️","Eyes · Vision","Screens · maps · insight","/on-any-place"],
  ["🎙️","Ears · Language","Listening · communication",null],
  ["💬","Mouth · Communication","SMI Chat · messages",null],
  ["❤️","Heart · Living Kernel","Governed work","/mission"],
  ["🌐","Lungs · Connectivity","OAP infrastructure",cfg.infrastructureUrl],
  ["🛡️","Immune · Guardian","Safety · permissions",cfg.warRoomUrl],
  ["🧬","HRM · Memory","Receipts · recall",cfg.hrmUrl],
  ["⚔️","War Room · Judges","3 / 7 / 21 depth",cfg.warRoomUrl],
  ["🗺️","Movement · Routes","Spatial intelligence","/movement"],
  ["🧬","DNA · OAP Constitution","21 laws · approved authority",null],
  ["🔗","Nervous System · NEXUS","Signals · governed routing",null],
  ["🌐","Matrix · World State","Routes · events · dependencies",null],
  ["💪","Muscles · Execution","Actions only when permitted",null],
  ["🩸","Blood · Signals","Pulse · governed events",null],
  ["🦴","Skeleton · Infrastructure","Render · storage · routing",null],
  ["🧪","Sanitisation","Filter · validate · minimise",null],
  ["🛡️","Skin · Security Boundary","Authentication · privacy",null],
  ["⚡","Energy · Metabolism","Compute · bandwidth · cost",null],
  ["🌱","Growth · Improvement","Evidence → proposal → approval",null]
 ];
 function addLink(parent,icon,name,detail,url){
  const link=document.createElement(url?"a":"div");link.className="smi-command-link";
  if(url){link.href=url;link.title=detail;}
  else{link.classList.add("smi-command-descriptive");link.title="Anatomy description · no live action implied";}
  const mark=document.createElement("span");mark.textContent=icon;
  const copy=document.createElement("div");const nameEl=document.createElement("strong");nameEl.textContent=name;
  const detailEl=document.createElement("small");detailEl.textContent=detail;
  copy.append(nameEl,document.createElement("br"),detailEl);link.append(mark,copy);
  parent.append(link);
 }
 anatomyLinks.forEach(([icon,name,detail,url])=>addLink(anatomy,icon,name,detail,url));
 // The approved command-room picture keeps intelligence, signals and gate evidence
 // in the scene itself; Status drawer remains a secondary detailed view.
 const dashboard=document.createElement("section");dashboard.className="smi-room-status";dashboard.setAttribute("aria-label","Live SMI intelligence and alignment");
 dashboard.innerHTML='<h3>◈ SYSTEM STATUS · LIVE PROOF</h3><div class="smi-room-status-grid"><article data-room-stat="runtime"><strong>SMI runtime</strong><small>Not checked</small></article><article data-room-stat="functions"><strong>Function health</strong><small>Not checked</small></article><article data-room-stat="signals"><strong>21 Signals</strong><small>Not checked</small></article><article data-room-stat="alignment"><strong>Alignment</strong><small>Not checked</small></article></div><h3>FOUR CHECKPOINTS · NO FAKE GREEN</h3><div class="smi-room-gates"><article data-room-gate="rollback"><strong>25% · Recovery</strong><small>Proof pending</small></article><article data-room-gate="runtime_guard"><strong>50% · Runtime Guard</strong><small>Proof pending</small></article><article data-room-gate="isolation"><strong>75% · Aegis</strong><small>Proof pending</small></article><article data-room-gate="founder"><strong>100% · Founder Final</strong><small>Founder decision required</small></article></div><p class="smi-room-status-note">Live evidence, not sample population figures. Contract validity does not prove all systems operational.</p>';
 evidence.append(dashboard);
 const roomStats=new Map([...dashboard.querySelectorAll("[data-room-stat]")].map(el=>[el.dataset.roomStat,el]));
 const roomGates=new Map([...dashboard.querySelectorAll("[data-room-gate]")].map(el=>[el.dataset.roomGate,el]));
 const proofList=document.createElement("div");proofList.className="smi-command-side";
 const monitored=[["biological_brain","Brain"],["nexus","NEXUS"],["hrm","HRM"],["guardian","Guardian"],["aegis","AEGIS"],["war_room","War Room"],["audit","Audit"],["human_authority","Human Authority"]];
 const proofNodes=new Map();
 monitored.forEach(([key,label])=>{
  const card=document.createElement("div");card.className="smi-command-proof";card.dataset.proven="false";
  const labelEl=document.createElement("strong");labelEl.textContent=label;
  const state=document.createElement("small");state.dataset.proofState="";state.textContent="Not checked";
  card.append(labelEl,state);proofList.append(card);proofNodes.set(key,{card,state});
 });
 evidence.append(proofList);
 const refresh=document.createElement("button");refresh.className="smi-command-toggle";refresh.type="button";refresh.textContent="↻ Refresh evidence";
 refresh.setAttribute("aria-label","Check signed-in SMI health evidence");
 evidence.append(refresh);
 addLink(evidence,"🌍","OAP World","Explore · connect","/on-any-place");
 addLink(evidence,"📚","Founder Library","Governed records",cfg.founderLibraryUrl);
 let active=false,request=null,roomRequest=null;
 const setRoom=(node,proven,message)=>{
  if(!node)return;
  node.dataset.proven=String(proven===true);
  node.querySelector("small").textContent=message;
 };
 async function refreshRoomStatus(){
  if(roomRequest)roomRequest.abort();
  roomRequest=new AbortController();
  const signal=roomRequest.signal;
  roomStats.forEach(node=>setRoom(node,false,"Checking live evidence…"));
  roomGates.forEach((node,key)=>setRoom(node,false,key==="founder"?"Founder decision required":"Checking proof…"));
  const targets=[
   ["runtime",cfg.healthUrl],
   ["functions",cfg.functionHealthUrl],
   ["signals",cfg.signalsUrl],
   ["alignment",cfg.greenGateUrl]
  ];
  const result=await Promise.allSettled(targets.map(async ([,url])=>{
   if(!url)throw new Error("Route unavailable");
   const response=await fetch(url,{cache:"no-store",credentials:"same-origin",signal});
   if(!response.ok)throw new Error("HTTP "+response.status);
   const value=await response.json();
   if(!value||typeof value!=="object"||Array.isArray(value))throw new Error("Evidence unavailable");
   return value;
  }));
  if(signal.aborted)return;
  const value=index=>result[index].status==="fulfilled"?result[index].value:null;
  const health=value(0),functions=value(1),signals=value(2),gate=value(3);
  const count=Number(functions?.available_count||0),expected=Number(functions?.expected_count||0);
  const functionsProven=expected>0&&count===expected&&Number(functions?.proof_checked_count||0)===expected&&Number(functions?.proof_required_count||0)===0;
  const signalProven=signals?.ready===true&&signals?.signals_valid===true&&Number(signals?.signal_count)===21;
  setRoom(roomStats.get("runtime"),health?.ready===true,
   health?String(health.status||"Response received · proof not green"):"Unavailable · NOT PROVEN");
  setRoom(roomStats.get("functions"),functionsProven,
   functions?count+"/"+(expected||"?")+" routes · "+Number(functions?.proof_checked_count||0)+" checks":"Unavailable · NOT PROVEN");
  setRoom(roomStats.get("signals"),signalProven,
   signals?(signalProven?"21/21 contract validated":"NOT PROVEN · "+Number(signals.signal_count||0)+"/21"):"Unavailable · NOT PROVEN");
  setRoom(roomStats.get("alignment"),gate?.green===true,
   gate?(gate.green===true?"Backend checks satisfied · Founder final":"Proof required · "+(Array.isArray(gate.missing)?gate.missing.length:"?")+" gaps"):"Unavailable · NOT PROVEN");
  const checks=gate?.checks||{};
  setRoom(roomGates.get("rollback"),checks.rollback_recovery===true,checks.rollback_recovery===true?"Backend proof recorded":"Not proven");
  setRoom(roomGates.get("runtime_guard"),checks.runtime_guard===true,checks.runtime_guard===true?"Backend proof recorded":"Not proven");
  setRoom(roomGates.get("isolation"),checks.isolation_recovery===true,checks.isolation_recovery===true?"Backend proof recorded":"Not proven");
  setRoom(roomGates.get("founder"),false,gate?.green===true?"Founder final decision pending":"Locked · all prior proof required");
 }
 function setOpen(open){
  if(open===active)return;
  active=open;
  if(open){
   stage.append(character);
   document.body.classList.add("smi-command-open");
   toggle.textContent="◈ Back to Chat";toggle.setAttribute("aria-label","Close SMI Command Centre");
   toggle.setAttribute("aria-pressed","true");
   refreshEvidence();
   refreshRoomStatus();
  }else{
   if(marker.parentNode)marker.parentNode.insertBefore(character,marker);
   document.body.classList.remove("smi-command-open");
   toggle.textContent="◈ Command Centre";toggle.setAttribute("aria-label","Open SMI Command Centre");
   toggle.setAttribute("aria-pressed","false");
  }
 }
 async function refreshEvidence(){
  if(!cfg.healthUrl)return;
  if(request)request.abort();
  request=new AbortController();
  refresh.disabled=true;refresh.textContent="Checking…";
  proofNodes.forEach(({card,state})=>{card.dataset.proven="false";state.textContent="Checking";});
  try{
   const response=await fetch(cfg.healthUrl,{cache:"no-store",credentials:"same-origin",signal:request.signal});
   if(!response.ok)throw new Error("Health endpoint unavailable");
   const data=await response.json();
   if(!data||!data.checks||typeof data.checks!=="object"||Array.isArray(data.checks))throw new Error("No check evidence");
   proofNodes.forEach(({card,state},key)=>{
    const proven=data.checks[key]===true;
    card.dataset.proven=String(proven);
    state.textContent=proven?"Proven by check":"Not proven";
   });
  }catch(error){
   if(error.name!=="AbortError")proofNodes.forEach(({card,state})=>{card.dataset.proven="false";state.textContent="Unavailable";});
  }finally{refresh.disabled=false;refresh.textContent="↻ Refresh evidence";}
 }
 toggle.addEventListener("click",()=>setOpen(!active));
 panel.querySelector(".smi-command-close").addEventListener("click",()=>{setOpen(false);toggle.focus();});
 refresh.addEventListener("click",()=>{refreshEvidence();refreshRoomStatus();});
 universe.addEventListener("click",event=>{
  const trigger=event.target.closest("[data-action]");
  if(!trigger)return;
  const action=trigger.dataset.action;
  const canonical=document.querySelector('#attach-menu [data-oap-action="'+action+'"]');
  if(!canonical||canonical.disabled){
   const feedback=document.getElementById("status");
   if(feedback)feedback.textContent="This SMI tool is not available for execution.";
   return;
  }
  setOpen(false);
  canonical.click();
 });
 // A real message should show the actual Chat response, not hide it behind the stage.
 document.addEventListener("submit",event=>{
  if(event.target?.id==="chat-form"&&active)setOpen(false);
 },true);
 document.addEventListener("keydown",event=>{
  if(active&&event.target?.id==="message"&&event.key==="Enter"&&!event.shiftKey&&!event.isComposing)setOpen(false);
 },true);
 document.addEventListener("keydown",event=>{
  if(event.key==="Escape"&&active&&!document.body.classList.contains("smi-live-fullscreen")){
   setOpen(false);toggle.focus();
  }
 });
 window.addEventListener("oap-smi-character-state",event=>{
  const detail=event.detail;
  if(!detail||typeof detail.state!=="string"){setPresenceState("ready");return;}
  setPresenceState(detail.state);
  if(detail.live&&active)setOpen(false);
 });
 window.addEventListener("pagehide",()=>{if(active)setOpen(false);});
 // Command Centre is the approved visual front door; Chat remains immediately reachable.
 // Never override a voice-first/fullscreen session already active.
 if(!cfg.singleLiveChatSurface&&!document.body.classList.contains("smi-live-fullscreen"))setOpen(true);
})();
