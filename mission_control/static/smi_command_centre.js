/* Additive Command Centre. Existing Chat, Live SMI, Guardian and Founder actions stay canonical. */
(() => {
 "use strict";
 const cfg=window.OAP_SMI_UI||{};
 const chatbox=document.querySelector(".chatbox");
 const head=document.querySelector(".chat-head");
 const character=document.getElementById("smi-character");
 const messages=document.getElementById("messages");
 const openWarRoom=()=>{
  const target=String(cfg.warRoomUrl||"").trim();
  if(!target){
   const feedback=document.getElementById("status");
   if(feedback)feedback.textContent="War Room route unavailable.";
   return false;
  }
  window.location.assign(target);
  return true;
 };
 if(!chatbox||!head||!character||!messages||document.getElementById("smi-command-centre"))return;
 const marker=document.createComment("original SMI character position");
 character.parentNode.insertBefore(marker,character);
 const presenceActions=document.createElement("nav");
 presenceActions.className="smi-presence-actions";
 presenceActions.setAttribute("aria-label","SMI character controls");
 for(const [label,target] of [["💬 Chat","messages"],["＋ Tools","plus-button"],["⚔️ War Room","war-room"]]){
  const button=document.createElement("button");button.type="button";button.textContent=label;
  button.addEventListener("click",event=>{
   event.stopPropagation(); // Prevent the canonical outside-click guard closing Master Tools.
   if(target==="messages"){
    if(document.body.classList.contains("smi-command-open"))document.querySelector(".smi-command-close")?.click();
    document.getElementById("message")?.focus();return;
   }
   if(document.body.classList.contains("smi-command-open"))document.querySelector(".smi-command-close")?.click();
   if(target==="war-room"){openWarRoom();return;}
   document.getElementById(target)?.click();
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
 statusButton.textContent="📊 SMI Status";statusButton.setAttribute("aria-label","Open live SMI evidence status");
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

 // Canonical private SMI home rail: one front door into the existing owners.
 // This is navigation/control composition only; it creates no duplicate runtime.
 const homeRail=document.createElement("nav");
 homeRail.className="smi-home-intelligence";
 homeRail.setAttribute("aria-label","SMI master home menu");

 const closeTransientPanels=()=>{
  document.querySelectorAll(".smi-world-controls").forEach(item=>{item.hidden=true;});
  document.querySelectorAll('[aria-controls="smi-world-controls"],[aria-controls="smi-jungle-controls"]').forEach(item=>item.setAttribute("aria-expanded","false"));
 };

 const triggerMasterTool=(action)=>{
  const button=document.querySelector('#attach-menu [data-oap-action="'+action+'"]');
  if(button&&!button.disabled){
   if(document.body.classList.contains("smi-command-open"))document.querySelector(".smi-command-close")?.click();
   button.click();
   return true;
  }
  const feedback=document.getElementById("status");
  if(feedback)feedback.textContent=action+" control unavailable";
  return false;
 };

 const homeButton=document.createElement("button");
 homeButton.type="button";homeButton.textContent="🏠 Home";
 homeButton.setAttribute("aria-label","Return to SMI Home");
 homeButton.addEventListener("click",()=>{
  closeTransientPanels();
  if(document.body.classList.contains("smi-command-open"))document.querySelector(".smi-command-close")?.click();
  if(document.body.classList.contains("smi-status-open"))document.querySelector(".smi-chat-return")?.click();
  document.getElementById("message")?.focus();
 });

 const smiButton=document.createElement("button");
 smiButton.type="button";smiButton.textContent="🧠 SMI";
 smiButton.setAttribute("aria-label","Open SMI system command centre");
 smiButton.addEventListener("click",()=>setOpen(true));

 const signalsHomeButton=document.createElement("button");
 signalsHomeButton.type="button";signalsHomeButton.textContent="📡 Signals";
 signalsHomeButton.setAttribute("aria-label","Open SMI signals");
 signalsHomeButton.addEventListener("click",()=>openStatus(true));

 const guardianHomeButton=document.createElement("button");
 guardianHomeButton.type="button";guardianHomeButton.textContent="🛡️ Guardian";
 guardianHomeButton.setAttribute("aria-label","Run Guardian evidence review");
 guardianHomeButton.addEventListener("click",()=>triggerMasterTool("guardian"));

 const warHomeButton=document.createElement("button");
 warHomeButton.type="button";warHomeButton.textContent="⚔️ War Room";
 warHomeButton.setAttribute("aria-label","Open War Room");
 warHomeButton.addEventListener("click",()=>openWarRoom());

 const intelligenceHomeButton=document.createElement("button");
 intelligenceHomeButton.type="button";intelligenceHomeButton.textContent="🧩 Intelligence";
 intelligenceHomeButton.setAttribute("aria-label","Open Intelligence systems");
 intelligenceHomeButton.addEventListener("click",()=>{
  const target=String(cfg.agentsUrl||"").trim();
  if(target.startsWith("/")&&!target.startsWith("//"))window.location.assign(target);
  else setOpen(true);
 });

 const hrmHomeButton=document.createElement("button");
 hrmHomeButton.type="button";hrmHomeButton.textContent="🧾 HRM / JOOG";
 hrmHomeButton.setAttribute("aria-label","Open HRM and Jog Memory");
 hrmHomeButton.addEventListener("click",()=>triggerMasterTool("hrm"));

 const controlHomeButton=document.createElement("button");
 controlHomeButton.type="button";controlHomeButton.textContent="⚙️ Control";
 controlHomeButton.setAttribute("aria-label","Open SMI Control and infrastructure");
 controlHomeButton.addEventListener("click",()=>{
  setOpen(true);
  panel.dataset.mobileView="evidence";
  mobileViews.querySelectorAll("button[data-view]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.view==="evidence")));
 });

 const settingsHomeButton=document.createElement("button");
 settingsHomeButton.type="button";settingsHomeButton.textContent="⚙ Settings";
 settingsHomeButton.setAttribute("aria-label","Open SMI Settings");
 settingsHomeButton.addEventListener("click",()=>{
  if(document.body.classList.contains("smi-command-open"))document.querySelector(".smi-command-close")?.click();
  document.getElementById("plus-button")?.click();
  const settings=document.getElementById("voice-settings-button");
  if(settings){
   const panelOpen=settings.getAttribute("aria-expanded")==="true";
   if(!panelOpen)settings.click();
   settings.scrollIntoView({block:"nearest",behavior:"auto"});
  }
 });

 homeRail.append(
  homeButton,smiButton,signalsHomeButton,guardianHomeButton,warHomeButton,
  intelligenceHomeButton,hrmHomeButton,controlHomeButton,settingsHomeButton
 );
 document.body.append(homeRail);

 // OAP World and Jungle remain available as deeper, existing command-centre systems.
 const worldPanel=document.createElement("nav");
 worldPanel.id="smi-world-controls";
 worldPanel.className="smi-world-controls";
 worldPanel.setAttribute("aria-label","OAP World public navigation");
 worldPanel.hidden=true;
 const publicRoot=String(cfg.publicWorldOrigin||"").trim();
 let publicOrigin=null;
 try{
  const candidate=new URL(publicRoot);
  if(candidate.protocol==="https:")publicOrigin=candidate.origin;
 }catch(_){}
 const publicRoutes=[
  ["🌍 Enter OAP World","/"],
  ["📍 The Spot","/the-spot"],
  ["🔗 Link Up","/linkup"],
  ["🗺️ OAP World / Place","/on-any-place"]
 ];
 const publicHeading=document.createElement("strong");
 publicHeading.className="smi-world-menu-heading";
 publicHeading.textContent="PUBLIC OAP · PREVIEW";
 worldPanel.append(publicHeading);
 const worldNotice=document.createElement("small");
 worldNotice.textContent="Public OAP · first-party front door · Founder controls stay private.";
 if(publicOrigin){
  publicRoutes.forEach(([label,path])=>{
   const link=document.createElement("a");
   link.textContent=label;link.href=publicOrigin+path;
   link.rel="noopener noreferrer";
   link.referrerPolicy="no-referrer";
   worldPanel.append(link);
  });
 }else{
  worldNotice.textContent="Public OAP origin unavailable · no unverified navigation.";
 }
 worldPanel.append(worldNotice);
 const controlHeading=document.createElement("strong");
 controlHeading.className="smi-world-menu-heading";
 controlHeading.textContent="PRIVATE SMI · WORLD GOVERNANCE";
 worldPanel.append(controlHeading);
 const worldFounderRoutes=[
  ["🌍 Civilization registry",cfg.civilizationStatusUrl],
  ["🌱 Ecosystem Intelligence",cfg.ecosystemDashboardUrl],
  ["🔗 Civilization × Ecosystem Evidence",cfg.civilizationBridgeUrl],
  ["🩺 World Function Health",cfg.functionHealthUrl],
  ["🟢 Green Gate evidence",cfg.greenGateUrl]
 ];
 worldFounderRoutes.forEach(([label,path])=>{
  const target=String(path||"").trim();
  if(!target.startsWith("/")||target.startsWith("//"))return;
  const link=document.createElement("a");
  link.textContent=label;link.href=target;
  link.className="smi-world-founder-link";
  worldPanel.append(link);
 });
 const governanceNotice=document.createElement("small");
 governanceNotice.textContent="Review only · no publication, payment, permission change or automatic Green. Founder Final remains separate.";
 worldPanel.append(governanceNotice);
 document.body.append(worldPanel);

 const junglePanel=document.createElement("nav");
 junglePanel.id="smi-jungle-controls";
 junglePanel.className="smi-world-controls smi-jungle-controls";
 junglePanel.setAttribute("aria-label","First-party Jungle intelligence families");
 junglePanel.hidden=true;
 const jungleRoutes=[
  ["🐆 Jungle Book","/mission/agents?family=jungle_book"],
  ["🦉 Animal Council","/mission/agents?family=animal"],
  ["🌍 Akan Animal","/mission/agents?family=akan_animal"],
  ["⚔️ War Room Council",String(cfg.warRoomUrl||"")]
 ];
 jungleRoutes.forEach(([label,path])=>{
  if(!path||!path.startsWith("/"))return;
  const link=document.createElement("a");
  link.textContent=label;link.href=path;
  junglePanel.append(link);
 });
 const jungleNotice=document.createElement("small");
 jungleNotice.textContent="Registered first-party roles only · review lenses are not independent agents.";
 junglePanel.append(jungleNotice);
 document.body.append(junglePanel);

 // Quick access reuses the existing, governed Master Tools handlers.
 const universe=document.createElement("nav");
 universe.className="smi-command-universe";
 universe.setAttribute("aria-label","SMI universe tools");
 const quickActions=[
  ["＋ Master Tools","master-tools"],
  ["🌍 OAP World","world-controls"],
  ["🐆 Jungle","jungle-controls"],
  ["⚔️ War Room","war-room"],
  ["🕶 Matrix Routes","matrix-routes"],
  ["🧠 HRM","hrm"],
  ["🗺️ Maps Controls","oap-maps-controls"],
  ["🖥️ Screen Intelligence","screen-intelligence"],
  ["🩺 Function Health","function-health"],
  ["🟣 Green Gate","green-gate"],
  ["🏦 Bank Controls","oap-bank-controls"]
 ];
 for(const [label,action] of quickActions){
  const button=document.createElement("button");button.type="button";button.textContent=label;
  button.dataset.action=action;
  universe.append(button);
 }
 panel.querySelector(".smi-command-layout").after(universe);
 // Founder Command Centre: non-operational banking controls. Do not create a
 // second banking engine, manufacture proof, or expose a transactional action.
 const bankControls=document.createElement("section");
 bankControls.className="smi-command-bank-controls";
 bankControls.hidden=true;
 bankControls.setAttribute("aria-label","USA Royalty Bank Founder controls · review only");
 const bankHeading=document.createElement("h3");
 bankHeading.textContent="🏦 USA ROYALTY BANK · FOUNDER REVIEW";
 const bankHeritage=document.createElement("p");
 bankHeritage.textContent="Prince Sovereign Bank · heritage | SIKA · separate value classes";
 const bankNotice=document.createElement("p");
 bankNotice.textContent="READ ONLY · no bank licence, balance, account, cash service, signed package or release is asserted.";
 const bankTabs=document.createElement("nav");
 bankTabs.setAttribute("aria-label","Bank review controls");
 const bankDetail=document.createElement("div");
 bankDetail.setAttribute("aria-live","polite");
 const bankReviews=[
  ["🧠 Mind","Primary: United States of Africa Royalty Bank. Prince Sovereign Bank is the heritage identity. SIKA Recognition is not GBP or issued SIKA; 1 proposed SIKA = 100 SEEDS."],
  ["⚙️ Body","OAP Bank is a planning rail. Accounts, ledger posting, payments and SIKA issuance are disabled. Post Core logistics and OAP Post Office financial access are separate."],
  ["💛 Soul","Customer consent and bank-specific permissions are separate from Founder approval. Financial records, bank signing keys and public Store data remain isolated."],
  ["📮 Post Office","Cash-in, cash-out and physical service locations are not verified or activated. Existing Post Core remains preserved."],
  ["📦 OAP Store","Bank package signing, installation and publication are not enabled. Supplied package checklist fields do not constitute independently verified artifact proof."],
  ["👑 Founder Final","Review-only control. No action here authorises transfers, cash, currency issuance, package publication, merge or deployment."]
 ];
 bankReviews.forEach(([label,detail],index)=>{
  const button=document.createElement("button");
  button.type="button";button.textContent=label;
  button.setAttribute("aria-pressed",String(index===0));
  button.addEventListener("click",()=>{
   bankTabs.querySelectorAll("button").forEach(item=>item.setAttribute("aria-pressed",String(item===button)));
   bankDetail.textContent=detail;
  });
  bankTabs.append(button);
 });
 bankDetail.textContent=bankReviews[0][1];
 bankControls.append(bankHeading,bankHeritage,bankNotice,bankTabs,bankDetail);
 universe.after(bankControls);

 // Maps MIND × BODY × SOUL controls reuse the existing first-party map owners.
 // These controls review or open canonical surfaces; they never create a second
 // map engine, request location, dispatch, book, pay, merge or deploy.
 const mapsControls=document.createElement("section");
 mapsControls.className="smi-command-bank-controls smi-command-maps-controls";
 mapsControls.hidden=true;
 mapsControls.setAttribute("aria-label","Maps Mind Body Soul controls");
 const mapsHeading=document.createElement("h3");
 mapsHeading.textContent="🗺️ MAPS · MIND × BODY × SOUL";
 const mapsNotice=document.createElement("p");
 mapsNotice.textContent="FIRST-PARTY · source proof before live claims · location by consent only · STOP unloads hidden map runtime.";
 const mapsTabs=document.createElement("nav");
 mapsTabs.setAttribute("aria-label","Maps review controls");
 const mapsDetail=document.createElement("div");
 mapsDetail.setAttribute("aria-live","polite");
 const mapsReviews=[
  ["🧠 Mind","Map Intelligence owns hierarchy, source health, stale-data boundaries and route evidence. Production navigation stays locked until runtime proof passes."],
  ["⚙️ Body","Open the existing SMI Map Intelligence workspace. This reuses /on-any-place and the existing road/routing renderer; no duplicate map runtime is created."],
  ["💛 Soul","Privacy and STOP boundary: precise location is consent-gated and not persisted by the map route; closing Maps unloads the hidden iframe."],
  ["📊 Status","Read-only evidence remains available through the existing Map Intelligence status surfaces. A button or configured source is never treated as Green by itself."],
  ["📈 Public %","Loading evidence-backed public Maps percentages…"],
  ["👑 Founder Final","No Maps control here authorises hidden tracking, dispatch, booking, payment, merge or deployment."]
 ];
 mapsReviews.forEach(([label,detail],index)=>{
  const button=document.createElement("button");
  button.type="button";button.textContent=label;
  button.dataset.mapsReview=label.includes("Mind")?"mind":label.includes("Body")?"body":label.includes("Soul")?"soul":label.includes("Status")?"status":label.includes("Public")?"public-percent":"founder";
  button.setAttribute("aria-pressed",String(index===0));
  button.addEventListener("click",()=>{
   mapsTabs.querySelectorAll("button").forEach(item=>item.setAttribute("aria-pressed",String(item===button)));
   mapsDetail.textContent=detail;
   if(button.dataset.mapsReview==="public-percent"){
    mapsDetail.textContent="Checking public Maps proof percentages…";
    fetch("/mission/map-intelligence",{cache:"no-store",credentials:"same-origin"})
     .then(response=>{if(!response.ok)throw new Error("Map Intelligence evidence unavailable");return response.json();})
     .then(data=>{
      const summary=data&&data.summary?data.summary:{};
      const counts=summary.counts||{};
      const total=Number(summary.total_checks||0);
      const percent=value=>total?Math.round((Number(value||0)/total)*100):0;
      const proven=Number(summary.green_or_guarded||0);
      mapsDetail.textContent=[
       "Public Maps proof · "+percent(proven)+"% proven/guarded",
       percent(summary.building)+"% building",
       percent(summary.locked)+"% locked",
       percent(summary.attention)+"% attention",
       "Checks: "+total+" · no missing proof hidden"
      ].join(" · ");
     })
     .catch(()=>{mapsDetail.textContent="Public Maps percentages unavailable · evidence remains unproven.";});
    return;
   }
   if(button.dataset.mapsReview==="body"){
    const canonical=document.querySelector('#attach-menu [data-oap-action="map-intelligence"]');
    if(canonical&&!canonical.disabled){
     mapsControls.hidden=true;
     setOpen(false);
     canonical.click();
    }
   }
  });
  mapsTabs.append(button);
 });
 mapsDetail.textContent=mapsReviews[0][1];
 mapsControls.append(mapsHeading,mapsNotice,mapsTabs,mapsDetail);
 bankControls.after(mapsControls);

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
  ["🔗","Link Up · Messenger","Open first-party Link Up · existing permissions","/linkup"],
  ["❤️","Heart · Living Kernel","Governed work","/mission"],
  ["🌐","Lungs · Connectivity","OAP infrastructure",cfg.infrastructureUrl],
  ["🛡️","Immune · Guardian","Safety · permissions",cfg.warRoomUrl],
  ["🧬","HRM · Memory","Receipts · recall",cfg.hrmUrl],
  ["⚔️","War Room · Judges","3 / 7 / 21 depth",cfg.warRoomUrl],
  ["🗺️","Movement · Routes","Spatial intelligence","/movement"],
  ["🧬","DNA · OAP Constitution","21 laws · approved authority",null],
  ["🔗","Nervous System · NEXUS","Signals · governed routing",null],
  ["🌐","Matrix · World State","Routes · events · dependencies","/mission/war-room/routes"],
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
 dashboard.innerHTML='<h3>◈ SYSTEM STATUS · LIVE PROOF</h3><div class="smi-room-status-grid"><article data-room-stat="runtime"><strong>SMI runtime</strong><small>Not checked</small></article><article data-room-stat="functions"><strong>Function health</strong><small>Not checked</small></article><article data-room-stat="signals"><strong>21 Signals</strong><small>Not checked</small></article><article data-room-stat="alignment"><strong>Alignment</strong><small>Not checked</small></article></div><h3>MIND × BODY × SOUL · DIRECT EVIDENCE</h3><div class="smi-room-gates"><article data-room-gate="mind"><strong>🧠 MIND</strong><small>Reasoning · alignment · evidence coherence</small></article><article data-room-gate="body"><strong>⚙️ BODY</strong><small>Runtime · functions · routes · execution health</small></article><article data-room-gate="soul"><strong>💛 SOUL</strong><small>Guardian · Aegis · recovery · trust boundaries</small></article></div><p class="smi-room-status-note">MBS is the operating model, not a percentage ladder. 3 / 7 / 21 controls review depth only. Founder Final remains separate Human Authority after evidence gates.</p>';
 evidence.append(dashboard);
 // One System Intelligence reading surface. Each tile reports backend evidence,
 // not inferred readiness from a reachable URL or an illustrated organism.
 const unified=document.createElement("section");
 unified.className="smi-unified-intelligence";
 unified.setAttribute("aria-label","SMI unified system intelligence");
 const unifiedTitle=document.createElement("h3");
 unifiedTitle.textContent="🧠 SMI SYSTEM INTELLIGENCE · EVIDENCE";
 const unifiedGrid=document.createElement("div");
 unifiedGrid.className="smi-unified-grid";
 const unifiedSources=[
  ["mission","🎯 Mission","No verified active mission feed","/mission/all-in-ai/app"],
  ["civilization","🌍 Civilization","Architecture not checked",cfg.civilizationStatusUrl],
  ["ecosystem","🌱 Ecosystem","Runtime/source evidence not checked",cfg.ecosystemDashboardUrl],
  ["matrix","🌐 Matrix","Routes not checked","/mission/war-room/routes"],
  ["guardian","🛡️ Guardian","Safety evidence not checked",cfg.greenGateUrl],
  ["hrm","🧬 HRM","Receipts not checked",cfg.hrmUrl],
  ["signals","📡 21 Signals","Contract not checked",cfg.signalsUrl],
  ["gate","🟢 Green Gate","Decision evidence not checked",cfg.greenGateUrl]
 ];
 const unifiedNodes=new Map();
 unifiedSources.forEach(([key,label,initial,url])=>{
  const tile=document.createElement("article");
  tile.dataset.unified=key;tile.dataset.proven="false";
  const heading=document.createElement("strong");
  heading.textContent=label;
  const state=document.createElement("small");
  state.textContent=initial;
  tile.append(heading,state);
  if(url){
   const link=document.createElement("a");
   link.href=url;link.textContent="Open";
   link.setAttribute("aria-label","Open "+label+" canonical surface");
   tile.append(link);
  }
  unifiedGrid.append(tile);
  unifiedNodes.set(key,tile);
 });
 unified.append(unifiedTitle,unifiedGrid);
 dashboard.before(unified);
 // Preserve the original deep proof grid without making the home system a second wall.
 const evidenceDetail=document.createElement("details");
 evidenceDetail.className="smi-system-detail";
 const evidenceSummary=document.createElement("summary");
 evidenceSummary.textContent="Detailed MIND × BODY × SOUL evidence";
 dashboard.before(evidenceDetail);
 evidenceDetail.append(evidenceSummary,dashboard);
 const setUnified=(key,proven,message)=>{
  const node=unifiedNodes.get(key);
  if(!node)return;
  node.dataset.proven=String(proven===true);
  node.querySelector("small").textContent=message;
 };
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
  for(const key of ["matrix","guardian","hrm","signals","gate","civilization","ecosystem"])setUnified(key,false,"Checking backend evidence…");
  setUnified("mission",false,"No verified active mission feed · do not infer one");
  const targets=[
   ["runtime",cfg.healthUrl],
   ["functions",cfg.functionHealthUrl],
   ["signals",cfg.signalsUrl],
   ["alignment",cfg.greenGateUrl],
   ["matrix",cfg.routesUrl],
   ["hrm",cfg.hrmUrl],
   ["civilization",cfg.civilizationStatusUrl],
   ["ecosystem",cfg.ecosystemStatusUrl],
   ["mission","/mission/all-in-ai/mission/latest"]
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
  const health=value(0),functions=value(1),signals=value(2),gate=value(3),matrix=value(4),hrm=value(5),civilization=value(6),ecosystem=value(7),mission=value(8);
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
  const mindProven=signalProven&&gate?.green===true;
  const bodyProven=health?.ready===true&&functionsProven&&checks.runtime_guard===true;
  const soulProven=checks.rollback_recovery===true&&checks.isolation_recovery===true;
  setRoom(roomGates.get("mind"),mindProven,mindProven?"Evidence coherent":"Reasoning/alignment proof incomplete");
  setRoom(roomGates.get("body"),bodyProven,bodyProven?"Runtime and function proof recorded":"Runtime/function proof incomplete");
  setRoom(roomGates.get("soul"),soulProven,soulProven?"Guardian/Aegis recovery proof recorded":"Safety/recovery proof incomplete");
  // A plan is not an active mission: require the canonical owner-scoped HRM and
  // audit read-back contract, never infer execution from HTTP 200 or a route.
  const missionVerified=mission?.found===true&&mission?.read_back_verified===true&&
   mission?.audit_verified===true&&mission?.hrm_verified===true&&
   mission?.execution_granted===false&&mission?.human_authority_final===true&&
   ["planned","stopped","recovered"].includes(mission?.state);
  setUnified("mission",missionVerified,
   missionVerified?"Verified "+mission.state+" checkpoint · no execution":
   mission?.found===false?"No recorded mission · NOT PROVEN":
   "Mission receipt unavailable/unverified · NOT PROVEN");
  // A valid response is not a Green receipt. Claim only explicit boolean contracts.
  setUnified("matrix",false,matrix?"Route evidence reachable · Matrix world-state not certified":"Routes unavailable · NOT PROVEN");
  setUnified("hrm",false,hrm?"HRM source reached · durable receipt not certified":"HRM unavailable · NOT PROVEN");
  setUnified("guardian",soulProven,soulProven?"Recovery checks explicitly passed":"Guardian/Aegis proof incomplete");
  setUnified("signals",signalProven,signalProven?"21/21 signal contract validated":signals?"21 Signals proof incomplete":"Signals unavailable · NOT PROVEN");
  setUnified("gate",gate?.green===true,gate?.green===true?"Backend gate satisfied · Founder Final separate":gate?"Missing proof · NOT GREEN":"Gate unavailable · NOT GREEN");
  // Architecture and internal ingestion are distinct from verified, externally current world-state.
  const civilizationDefined=civilization?.validation?.passed===true&&civilization?.status==="architecture_protocol_defined";
  setUnified("civilization",false,civilizationDefined?
   "Architecture validated · 9 domains · operational Green not claimed":
   civilization?"Architecture or protocol not validated · NOT PROVEN":"Civilization source unavailable · NOT PROVEN");
  const ecosystemInternal=ecosystem?.runtime?.automatic_internal_ingestion_ready===true;
  const provenGates=Number(ecosystem?.live_sources?.proven_gate_count||0);
  const requiredGates=Number(ecosystem?.live_sources?.required_gate_count||0);
  const ecosystemComplete=ecosystemInternal&&requiredGates>0&&provenGates===requiredGates&&
   ecosystem?.live_sources?.all_required_live_sources_proven===true&&
   ecosystem?.runtime?.external_live_complete===true&&ecosystem?.architecture?.full_green===true;
  setUnified("ecosystem",ecosystemComplete,
   ecosystemInternal?"Internal signals ready · "+provenGates+"/"+(requiredGates||"?")+" external gates · "+(ecosystemComplete?"source coverage proven; Founder Final separate":"NOT FULL GREEN"):
   ecosystem?"Internal ingestion not proven · NOT GREEN":"Ecosystem source unavailable · NOT PROVEN");
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
  if(action==="world-controls"){
   worldPanel.hidden=!worldPanel.hidden;
   junglePanel.hidden=true;
   return;
  }
  if(action==="jungle-controls"){
   junglePanel.hidden=!junglePanel.hidden;
   worldPanel.hidden=true;
   return;
  }
  if(action==="master-tools"){
   // Only the original composer owns the drawer. The originating click must not
   // bubble to its outside-click guard after the canonical button opens it.
   event.stopPropagation();
   const plus=document.getElementById("plus-button");
   if(!plus||plus.disabled){
    const feedback=document.getElementById("status");
    if(feedback)feedback.textContent="Master Tools unavailable.";
    return;
   }
   setOpen(false);
   plus.click();
   return;
  }
  if(action==="oap-bank-controls"){
   bankControls.hidden=!bankControls.hidden;
   trigger.setAttribute("aria-expanded",String(!bankControls.hidden));
   return;
  }
  if(action==="oap-maps-controls"){
   mapsControls.hidden=!mapsControls.hidden;
   trigger.setAttribute("aria-expanded",String(!mapsControls.hidden));
   return;
  }
  if(action==="war-room"){
   setOpen(false);
   openWarRoom();
   return;
  }
  if(action==="matrix-routes"){
   setOpen(false);
   window.location.assign("/mission/war-room/routes");
   return;
  }
  if(action==="screen-intelligence"){
   const screen=document.getElementById("screen-menu-button");
   if(!screen||screen.disabled){
    const feedback=document.getElementById("status");
    if(feedback)feedback.textContent="Screen Intelligence unavailable.";
    return;
   }
   setOpen(false);
   screen.click();
   return;
  }
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
