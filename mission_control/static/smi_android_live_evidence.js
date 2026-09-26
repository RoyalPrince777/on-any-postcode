/* Physical Android live SMI evidence collector.
 * Captures only bounded runtime booleans, timings and integrity hashes.
 * Never stores transcript/audio, never fabricates missing events and never
 * grants production approval or Human Final.
 */
(()=>{
"use strict";
const SOURCE_SHA="f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b";
const LAYERS=["eyes","head","breathing","mouth_visemes","face","hands","upper_body"];
const state={
 microphoneStartObserved:false,sendObserved:false,persistedReplyObserved:false,
 playedAudioObserved:false,motionObserved:false,pauseObserved:false,resumeObserved:false,
 maxAudioClockDeltaMs:0,motionStopped:false,audioStopped:false,stopAcknowledgementMs:null,
 backgroundStopPassed:false,backgroundArmed:false,conversationId:null,requestId:null,
 lastCharacterState:"ready",pcmActive:false,submitted:false
};
const isAndroid=()=>/Android/i.test(navigator.userAgent||"");
function uuidish(value){return /^[a-f0-9-]{16,64}$/i.test(String(value||""));}
function proofSnapshot(){
 const proof=window.OAP_SMI_LIVE_PROOF?.snapshot?.()||{};
 const counters=proof.counters||{};
 return {proof,counters};
}
function motionSnapshot(){return window.OAP_SMI_SOURCE_PIXEL_MOTION_SESSION?.snapshot?.()||null;}
async function waitForMotion(){
 try{return await (window.OAP_SMI_SOURCE_PIXEL_MOTION_READY||Promise.resolve(null));}
 catch{return null;}
}
async function deviceInfo(){
 let model="",version="";
 try{
  if(navigator.userAgentData?.getHighEntropyValues){
   const high=await navigator.userAgentData.getHighEntropyValues(["model","platformVersion"]);
   model=String(high?.model||"").trim();
   version=String(high?.platformVersion||"").trim();
  }
 }catch{}
 const ua=String(navigator.userAgent||"");
 if(!version){const m=ua.match(/Android\s+([0-9.]+)/i);if(m)version=m[1];}
 if(!model){
  const m=ua.match(/;\s*([^;()]+?)\s+Build\//i);
  if(m)model=m[1].trim();
 }
 return {model,version};
}
function automatedStatus(){
 const {counters}=proofSnapshot(),motion=motionSnapshot();
 const layers=motion?.evidenceLayerSha256;
 const validLayers=Boolean(layers&&LAYERS.every(name=>/^[a-f0-9]{64}$/.test(String(layers[name]||""))));
 const paused=state.pauseObserved||Number(counters.pause||0)>0;
 const resumed=state.resumeObserved||Number(counters.resume||0)>0;
 const mic=state.microphoneStartObserved||Number(counters.listenStart||0)>0;
 const motionObserved=state.motionObserved||Boolean(motion?.frames>0&&motion?.audioCues>0);
 const exact=Boolean(motion?.sourceSha256===SOURCE_SHA&&validLayers&&motion?.fullSceneSourcePixelMotion);
 return {
  exactCharacterIntact:exact,
  microphoneStartObserved:mic,
  sendObserved:state.sendObserved,
  persistedReplyObserved:state.persistedReplyObserved&&uuidish(state.conversationId)&&uuidish(state.requestId),
  playedAudioObserved:state.playedAudioObserved,
  motionObserved,
  pauseObserved:paused,
  resumeObserved:resumed,
  maxAudioClockDeltaMs:state.maxAudioClockDeltaMs,
  motionStopped:state.motionStopped,
  audioStopped:state.audioStopped,
  stopAcknowledgementMs:state.stopAcknowledgementMs,
  backgroundStopPassed:state.backgroundStopPassed,
  source:motion,
 };
}
function missingChecks(status){
 const missing=[];
 for(const [field,label] of [
  ["exactCharacterIntact","exact character/source integrity"],
  ["microphoneStartObserved","microphone start"],
  ["sendObserved","Send"],
  ["persistedReplyObserved","persisted reply"],
  ["playedAudioObserved","first-party PCM playback"],
  ["motionObserved","character motion from actual audio"],
  ["pauseObserved","Pause"],
  ["resumeObserved","Resume"],
  ["motionStopped","motion STOP"],
  ["audioStopped","audio STOP"],
  ["backgroundStopPassed","background STOP"]
 ])if(status[field]!==true)missing.push(label);
 if(!Number.isFinite(status.stopAcknowledgementMs)||status.stopAcknowledgementMs>50)missing.push("STOP acknowledgement ≤50ms");
 if(!Number.isFinite(status.maxAudioClockDeltaMs)||status.maxAudioClockDeltaMs>80)missing.push("played-audio timing ≤80ms");
 return missing;
}
window.addEventListener("oap-smi-character-state",event=>{
 const next=String(event?.detail?.state||"ready");
 if(next==="listening")state.microphoneStartObserved=true;
 if(next==="paused")state.pauseObserved=true;
 if(state.lastCharacterState==="paused"&&next!=="paused"&&next!=="stopped")state.resumeObserved=true;
 state.lastCharacterState=next;
});
window.addEventListener("oap-smi-submit-start",()=>{state.sendObserved=true;});
window.addEventListener("oap-smi-complete",event=>{
 const d=event?.detail||{};
 if(uuidish(d.conversation_id)&&uuidish(d.request_id)){
  state.persistedReplyObserved=true;state.conversationId=d.conversation_id;state.requestId=d.request_id;
 }
});
window.addEventListener("oap-smi-playback-state",event=>{
 const d=event?.detail||{};
 const pcm=d.source==="oap-first-party-pcm"&&d.decodedAudio===true;
 if(pcm&&d.phase==="playing"){
  state.playedAudioObserved=true;state.pcmActive=true;state.backgroundArmed=true;
 }
 if(pcm&&["ended","stopped","cancelled","error"].includes(String(d.phase)))state.pcmActive=false;
});
window.addEventListener("oap-smi-audio-cue",event=>{
 const d=event?.detail||{};
 if(d.source!=="oap-first-party-pcm"||d.decodedAudio!==true||d.synthesisPhonemeTiming!==true)return;
 if(!Number.isFinite(d.audioClockMs)||!Number.isFinite(d.atMs))return;
 state.playedAudioObserved=true;
 state.maxAudioClockDeltaMs=Math.max(state.maxAudioClockDeltaMs,Math.abs(d.audioClockMs-d.atMs));
 requestAnimationFrame(()=>{
  const m=motionSnapshot();
  if(m?.frames>0&&m?.audioCues>0)state.motionObserved=true;
 });
});
window.addEventListener("oap-smi-human-stop",event=>{
 const d=event?.detail||{};
 if(Number.isFinite(d.stopAcknowledgementMs))state.stopAcknowledgementMs=d.stopAcknowledgementMs;
 state.motionStopped=d.motionStopped===true;
 state.audioStopped=d.audioStopped===true;
});
window.addEventListener("oap-smi-background-stop",event=>{
 const d=event?.detail||{};
 if(state.backgroundArmed&&d.audioStopped===true&&d.motionStopped===true){
  state.backgroundStopPassed=true;state.backgroundArmed=false;
 }
});
async function buildReceipt({humanVisualApproved=false,humanNote="",deviceModelOverride=""}={}){
 await waitForMotion();
 const status=automatedStatus(),info=await deviceInfo(),motion=status.source||{};
 return {
  evidenceType:"physical_android_live_smi",
  platform:isAndroid()?"Android":"",
  deviceModel:String(deviceModelOverride||info.model||"").trim(),
  androidVersion:String(info.version||"").trim(),
  approvedSourceSha256:motion.sourceSha256||"",
  layerSha256:motion.evidenceLayerSha256||{},
  exactCharacterIntact:status.exactCharacterIntact,
  microphoneStartObserved:status.microphoneStartObserved,
  sendObserved:status.sendObserved,
  persistedReplyObserved:status.persistedReplyObserved,
  conversationId:state.conversationId,
  requestId:state.requestId,
  playedAudioObserved:status.playedAudioObserved,
  motionObserved:status.motionObserved,
  pauseObserved:status.pauseObserved,
  resumeObserved:status.resumeObserved,
  maxAudioClockDeltaMs:status.maxAudioClockDeltaMs,
  motionStopped:status.motionStopped,
  audioStopped:status.audioStopped,
  stopAcknowledgementMs:status.stopAcknowledgementMs,
  backgroundStopPassed:status.backgroundStopPassed,
  storesAudio:false,
  storesTranscript:false,
  humanVisualApproved:humanVisualApproved===true,
  productionApproved:false,
  humanFinalApproved:false,
  testedAt:new Date().toISOString(),
  humanNote:String(humanNote||"").trim()
 };
}
async function submitHumanApproved(){
 if(!isAndroid())return {accepted:false,reasons:["platform_not_android"]};
 const status=automatedStatus(),missing=missingChecks(status);
 if(missing.length){
  window.alert("Physical Android proof is not complete yet. Real evidence still needed: "+missing.join(", ")+".");
  return {accepted:false,reasons:missing};
 }
 const observed=window.confirm("Did you personally observe the exact original SMI character moving correctly with the actual first-party reply audio on this Android device?");
 if(!observed)return {accepted:false,reasons:["human_visual_approval_missing"]};
 let note=window.prompt("Add a short visual acceptance note (no private transcript):","Exact original SMI character and actual reply audio observed.")||"";
 note=note.trim();
 if(note.length<3)return {accepted:false,reasons:["human_note_missing"]};
 const info=await deviceInfo();
 let model=info.model;
 if(!model)model=(window.prompt("Android device model for this physical proof:","")||"").trim();
 const receipt=await buildReceipt({humanVisualApproved:true,humanNote:note,deviceModelOverride:model});
 const response=await fetch(window.OAP_SMI_UI?.androidEvidenceUrl||"",{
  method:"POST",credentials:"same-origin",
  headers:{"Content-Type":"application/json","X-OAP-CSRF":window.csrfToken||""},
  body:JSON.stringify(receipt)
 });
 let payload={};try{payload=await response.json()}catch{}
 state.submitted=Boolean(response.ok&&payload?.accepted);
 if(!state.submitted){
  window.alert("Android proof was not recorded. "+String(payload?.reasons?.join(", ")||payload?.error?.message||"Evidence remains locked."));
  return payload;
 }
 const tool=document.getElementById("android-proof-button");
 if(tool){const s=tool.querySelector(".connector-state");if(s)s.textContent="Recorded";tool.dataset.proven="true";}
 window.alert("Physical Android SMI evidence was recorded durably. Production/Human Final remain separate.");
 return payload;
}
function addTool(){
 if(!isAndroid())return;
 const menu=document.getElementById("attach-menu");if(!menu||document.getElementById("android-proof-button"))return;
 const button=document.createElement("button");button.type="button";button.id="android-proof-button";button.className="attach-option connector";
 button.innerHTML='<span class="connector-copy"><span>📱</span><span>Android Proof</span></span><span class="connector-state">Check</span>';
 button.addEventListener("click",event=>{event.preventDefault();event.stopImmediatePropagation();menu.classList.remove("show");submitHumanApproved().catch(()=>window.alert("Android proof remains locked because the durable evidence write did not complete."));},true);
 const green=menu.querySelector('[data-oap-action="green-gate"]');if(green)green.after(button);else menu.append(button);
}
window.OAP_SMI_ANDROID_EVIDENCE=Object.freeze({
 snapshot:()=>JSON.parse(JSON.stringify({...state,automated:automatedStatus()})),
 buildReceipt,
 submitHumanApproved,
 privacy:Object.freeze({storesAudio:false,storesTranscript:false,storesUserAgent:false})
});
addTool();
})();