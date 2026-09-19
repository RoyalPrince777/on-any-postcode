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
  if(tab.dataset.view==="evidence")refreshEvidence();
 });
 const stage=panel.querySelector(".smi-command-stage");
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
 let active=false,request=null;
 function setOpen(open){
  if(open===active)return;
  active=open;
  if(open){
   stage.append(character);
   document.body.classList.add("smi-command-open");
   toggle.textContent="◈ Back to Chat";toggle.setAttribute("aria-label","Close SMI Command Centre");
   toggle.setAttribute("aria-pressed","true");
   refreshEvidence();
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
 refresh.addEventListener("click",refreshEvidence);
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
  if(event.detail&&event.detail.live&&active)setOpen(false);
 });
 window.addEventListener("pagehide",()=>{if(active)setOpen(false);});
 // Command Centre is the approved visual front door; Chat remains immediately reachable.
 // Never override a voice-first/fullscreen session already active.
 if(!document.body.classList.contains("smi-live-fullscreen"))setOpen(true);
})();
