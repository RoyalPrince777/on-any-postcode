"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const {webcrypto}=require("node:crypto");
const {create,validate}=require("../mission_control/static/smi_reply_audio_player.js");

const conversationId="12345678-1234-4234-8234-123456789abc";
const requestId="87654321-4321-4321-8321-abcdefabcdef";

async function sha256(bytes){
 const digest=await webcrypto.subtle.digest("SHA-256",bytes);
 return Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,"0")).join("");
}

(async()=>{
 const wav=new Uint8Array(44);
 const audioSha=await sha256(wav);
 const alignment={
  source:"decoded_audio_phoneme_timeline",audioSha256:audioSha,
  audioDecoded:true,predictedFromText:false,storesAudio:false,
  storesReplyText:false,audioDurationMs:1000,
  cues:[
   {atMs:0,viseme:"silence",confidence:1},
   {atMs:100,viseme:"wide",confidence:1},
   {atMs:1000,viseme:"silence",confidence:1}
  ]
 };
 alignment.timelineSha256=await sha256(new TextEncoder().encode(JSON.stringify({
  audioSha256:audioSha,audioDurationMs:1000,cues:alignment.cues
 })));
 assert.equal(validate(alignment,audioSha,1000),true);
 for(const invalid of [
  {...alignment,audioSha256:"b".repeat(64)},
  {...alignment,predictedFromText:true},
  {...alignment,cues:[alignment.cues[0],{atMs:100,viseme:"invented",confidence:1},alignment.cues[2]]},
  {...alignment,cues:[alignment.cues[0],{atMs:0,viseme:"wide",confidence:1},alignment.cues[2]]},
  {...alignment,audioDurationMs:300001},
  {...alignment,audioDurationMs:99},
  {...alignment,alignmentErrorMeasured:true},
  {...alignment,maxAlignmentErrorMs:40},
  {...alignment,cues:[alignment.cues[0],{atMs:100,viseme:"wide"},alignment.cues[2]]},
  {...alignment,cues:[alignment.cues[0],{atMs:100,viseme:"wide",confidence:"1"},alignment.cues[2]]},
  {...alignment,cues:[alignment.cues[0],{atMs:100,viseme:"wide",confidence:null},alignment.cues[2]]}
 ])assert.equal(validate(invalid,audioSha,1000),false);

 let raf=null,contextInstance=null;
 const sources=[];
 class FakeAudioContext{
  constructor(){this.state="suspended";this.currentTime=0;this.destination={};this.closed=false;contextInstance=this;}
  async resume(){this.state="running";}
  async suspend(){this.state="suspended";}
  async close(){this.state="closed";this.closed=true;}
  async decodeAudioData(){return {duration:1};}
  createBufferSource(){
   const source={buffer:null,onended:null,started:false,stopped:false,disconnected:false,
    connect(){},start(){this.started=true;},stop(){this.stopped=true;},
    disconnect(){this.disconnected=true;}};
   sources.push(source);return source;
  }
 }
 const payload={
  mime:"audio/wav",engine:"self_hosted_espeak",
  engineBuild:"espeak-ng-1.51-bundled",voiceLocale:"en",
  phonemeIssuedBySynth:true,audioBase64:Buffer.from(wav).toString("base64"),
  alignment
 };
 const win={
  fetch:async()=>({ok:true,json:async()=>payload}),crypto:webcrypto,
  AudioContext:FakeAudioContext,AbortController,
  atob:value=>Buffer.from(value,"base64").toString("binary"),TextEncoder,
  requestAnimationFrame:fn=>{raf=fn;return 1;},cancelAnimationFrame:()=>{raf=null;}
 };
 const player=create(win);
 let externalFetches=0;
 const originalFetch=win.fetch;
 win.fetch=async(...args)=>{externalFetches++;return originalFetch(...args);};
 for(const unsafeUrl of [
  "https://attacker.example/collect","//attacker.example/collect",
  "http://attacker.example/collect","/\\\\attacker.example/collect",
  "/mission/chat/reply-audio\nmalformed"
 ]){
  assert.equal(await player.play({
   url:unsafeUrl,csrf:"csrf",conversationId,requestId
  }),false,"off-origin or malformed reply route must fail closed");
 }
 assert.equal(externalFetches,0,"do not send CSRF or reply IDs to an untrusted URL");
 // Android audio focus denial and missing Web Audio must not start or export a reply.
 const denied=create({
  AudioContext:class{constructor(){throw new Error("audio focus denied");}},
  fetch:async()=>{throw new Error("permission denial must not fetch audio");},
  crypto:webcrypto
 });
 assert.equal(await denied.prepare(),false);
 assert.equal(denied.snapshot().prepared,false);
 denied.stop();denied.destroy();
 const unsupported=create({fetch:win.fetch,crypto:webcrypto});
 assert.equal(await unsupported.prepare(),false);
 assert.equal(unsupported.snapshot().active,false);
 assert.equal(await unsupported.play({
  url:"/mission/chat/reply-audio",csrf:"csrf",conversationId,requestId
 }),false);
 // If Android audio focus is lost after the authenticated fetch, no source may start.
 let focusErrors=0,focusFetches=0;
 const deniedDuringPlay=create({
  ...win,
  AudioContext:class{constructor(){throw new Error("audio focus denied after fetch");}},
  fetch:async()=>{focusFetches++;return {ok:true,json:async()=>payload};}
 });
 assert.equal(await deniedDuringPlay.play({
  url:"/mission/chat/reply-audio",csrf:"csrf",conversationId,requestId,
  onError:()=>focusErrors++
 }),false);
 assert.equal(focusFetches,1);
 assert.equal(focusErrors,1);
 assert.equal(deniedDuringPlay.snapshot().active,false);
 deniedDuringPlay.destroy();
 assert.equal(await player.prepare(),true);
 assert.equal(player.snapshot().prepared,true);
 let starts=0,cues=0,playbackErrors=0;
 assert.equal(await player.play({
  url:"/mission/chat/reply-audio",csrf:"csrf",conversationId,requestId,
  onStart:()=>starts++,onCue:()=>cues++,onError:()=>playbackErrors++
 }),true);
 assert.equal(starts,1);
 assert.equal(sources[0].started,true);
 assert.equal(player.snapshot().active,true);
 contextInstance.currentTime=.2;raf?.(.2);
 assert.equal(cues,1);
 assert.equal(player.pause(),true);assert.equal(contextInstance.state,"suspended");
 assert.equal(player.resume(),true);assert.equal(contextInstance.state,"running");
 // Android/browser interruptions can reject suspend/resume asynchronously.
 // Both must be handled without an unhandled rejection or false STOP Green.
 contextInstance.suspend=()=>Promise.reject(new Error("audio interruption"));
 contextInstance.resume=()=>Promise.reject(new Error("audio focus denied"));
 assert.equal(player.pause(),true);
 assert.equal(player.resume(),true);
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(player.snapshot().active,false,"rejected audio focus must cancel playback");
 assert.equal(playbackErrors,1,"audio-focus failure must notify canonical character controller exactly once");
 assert.equal(sources[0].stopped,true);
 assert.equal(sources[0].disconnected,true);
 assert.equal(player.pause(),false);
 assert.equal(player.resume(),false);
 player.stop();
 assert.equal(player.snapshot().active,false);
 assert.equal(player.snapshot().prepared,true);
 assert.equal(contextInstance.closed,false,"STOP must preserve the gesture-unlocked context");
 assert.equal(sources[0].stopped,true);
 assert.equal(sources[0].disconnected,true);
 player.destroy();
 assert.equal(contextInstance.closed,true);
 assert.equal(player.snapshot().prepared,false);

 let resolveFetch;
 win.fetch=()=>new Promise(resolve=>{resolveFetch=resolve;});
 const stalePlayer=create(win);
 let staleStarts=0;
 const pending=stalePlayer.play({
  url:"/mission/chat/reply-audio",csrf:"csrf",conversationId,requestId,
  onStart:()=>staleStarts++
 });
 stalePlayer.stop();
 resolveFetch({ok:true,json:async()=>payload});
 assert.equal(await pending,false);
 assert.equal(staleStarts,0);

 const html=fs.readFileSync("mission_control/templates/ollama_chat.html","utf8");
 const controller=fs.readFileSync("mission_control/static/smi_canonical_controller.js","utf8");
 const renderer=fs.readFileSync("mission_control/static/smi_source_pixel_motion.js","utf8");
 assert.ok(html.indexOf("smi_reply_audio_player.js")<html.indexOf("smi_canonical_controller.js"));
 assert.ok(controller.includes("oapSpeak(completeResult.response,completeResult)"));
 assert.ok(controller.includes("oapLocalPlayer?.prepare?.()"));
 const liveClick=controller.slice(controller.indexOf("if(oapLiveToggle)oapLiveToggle.addEventListener"),controller.indexOf("window.addEventListener('pagehide'"));
 assert.ok(liveClick.includes("if(!oapRuntime?.live&&oapRecognition)oapLocalPlayer?.prepare?.();"),"first Live tap must unlock local audio before recognition/auto-send");
 assert.ok(liveClick.indexOf("oapLocalPlayer?.prepare?.()")<liveClick.indexOf("oapSetLive(!Boolean(oapRuntime?.live))"));
 assert.ok(!liveClick.includes("if(oapVoiceEnabled)oapLocalPlayer?.prepare?.()"),"first voice-first entry starts with voice disabled");
 assert.ok(controller.includes("oapLocalPlayer?.destroy?.()"));
 assert.ok(controller.includes("if(!document.hidden)return;"));
 assert.ok(controller.includes("if(oapRuntime?.live){oapSetLive(false);"));
 const hiddenHandler=controller.slice(controller.indexOf("document.addEventListener('visibilitychange'"));
 assert.ok(hiddenHandler.includes("oapSpeechSeq+=1;oapLocalPlayer?.stop()"),"background ordinary audio must STOP");
 assert.ok(hiddenHandler.includes("oapPlaybackState('cancelled',oapRuntime?.epoch)"),"background must clear character playback");
 assert.ok(controller.includes("oap-smi-audio-cue"));
 assert.ok(renderer.includes('cue?.source!=="oap-first-party-pcm"'));
 const audioCode=fs.readFileSync("mission_control/static/smi_reply_audio_player.js","utf8");
 assert.ok(audioCode.includes('if(playbackContext.state!=="running"){frame=win.requestAnimationFrame(tick);return;}'));
 assert.ok(controller.includes("oapLocalPlayer?.pause()"));
 assert.ok(controller.includes("oapLocalPlayer?.resume()"));
 assert.ok(controller.includes("oapLocalPlayer?.stop()"));
 assert.ok(audioCode.includes("timelineSha!==payload.alignment.timelineSha256"));
 assert.ok(audioCode.includes('payload?.engineBuild!=="espeak-ng-1.51-bundled"'));
 assert.ok(audioCode.includes("if(!allowed()||!active)return false"));
 assert.ok(audioCode.includes("MAX_BYTES=32*1024*1024"));
 assert.ok(!audioCode.includes("localStorage"));
 assert.ok(!audioCode.includes("sendBeacon"));
 assert.ok(!audioCode.includes("WebSocket"));
 console.log("SMI_LOCAL_AUDIO_CLOCK_STOP_AND_WIRING_PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});
