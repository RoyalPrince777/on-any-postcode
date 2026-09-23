/* OAP first-party reply WAV playback: uses the clock of actual decoded audio.
 * Never derives mouth shape from text/browser speech boundaries. No telemetry.
 */
(function(root,factory){
 "use strict";
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 if(root)root.OAP_SMI_LOCAL_REPLY_PLAYER=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 "use strict";
 const VISEMES=new Set(["silence","closed","wide","round","teeth","tongue"]);
 const MAX_BYTES=8*1024*1024;
 function validate(alignment,actualSha,durationMs){
  if(!alignment||alignment.source!=="decoded_audio_phoneme_timeline"||
    alignment.audioSha256!==actualSha||alignment.audioDecoded!==true||
    alignment.predictedFromText!==false||alignment.storesAudio!==false||
    alignment.storesReplyText!==false||
    !Number.isFinite(alignment.audioDurationMs)||
    Math.abs(alignment.audioDurationMs-durationMs)>1||
    !Array.isArray(alignment.cues)||alignment.cues.length<3||
    alignment.cues.length>10000)return false;
  let at=-1;
  for(const cue of alignment.cues){
   if(!Number.isFinite(cue.atMs)||cue.atMs<=at||
      cue.atMs>alignment.audioDurationMs||!VISEMES.has(cue.viseme)||
      cue.confidence<.8||cue.confidence>1||
      Object.keys(cue).some(key=>!["atMs","viseme","confidence"].includes(key)))return false;
   at=cue.atMs;
  }
  return alignment.cues[0].atMs===0&&
   alignment.cues[0].viseme==="silence"&&
   alignment.cues[alignment.cues.length-1].viseme==="silence"&&
   Math.abs(at-alignment.audioDurationMs)<=1;
 }
 function create(win=typeof window!=="undefined"?window:null){
  let token=0,abort=null,context=null,source=null,frame=null,active=false;
  function stop(){
   token+=1;active=false;
   try{abort?.abort()}catch{}
   abort=null;
   try{source?.stop()}catch{}
   source=null;
   if(frame!==null){try{win?.cancelAnimationFrame?.(frame)}catch{}frame=null;}
   const previous=context;context=null;
   if(previous){try{previous.close()}catch{}}
  }
  async function play({url,csrf,conversationId,requestId,isCurrent,onStart,onCue,onEnd,onError}={}){
   stop();
   const current=token;
   const allowed=()=>current===token&&(!isCurrent||isCurrent());
   if(!win?.fetch||!win?.crypto?.subtle||!win?.AudioContext||
      !/^[a-f0-9-]{36}$/i.test(String(conversationId||""))||
      !/^[a-f0-9-]{36}$/i.test(String(requestId||"")))return false;
   abort=new win.AbortController();
   try{
    const response=await win.fetch(url,{method:"POST",credentials:"same-origin",
     headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},
     body:JSON.stringify({conversation_id:conversationId,request_id:requestId}),
     signal:abort.signal});
    if(!allowed()||!response.ok)return false;
    const payload=await response.json();
    if(!allowed()||payload?.mime!=="audio/wav"||
      payload?.engine!=="self_hosted_espeak"||
      typeof payload.audioBase64!=="string"||
      payload.audioBase64.length>MAX_BYTES*1.34||
      !/^[A-Za-z0-9+/]*={0,2}$/.test(payload.audioBase64))return false;
    const binary=win.atob(payload.audioBase64),bytes=new Uint8Array(binary.length);
    if(binary.length<44||binary.length>MAX_BYTES)return false;
    for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
    const digest=await win.crypto.subtle.digest("SHA-256",bytes);
    const sha=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,"0")).join("");
    if(!allowed())return false;
    const audio=bytes.buffer.slice(0);
    context=new win.AudioContext();
    const buffer=await context.decodeAudioData(audio);
    if(!allowed()||!validate(payload.alignment,sha,buffer.duration*1000))return false;
    await context.resume();
    if(!allowed()||context.state!=="running")return false;
    source=context.createBufferSource();source.buffer=buffer;source.connect(context.destination);
    const startAt=context.currentTime+.025;
    let cueIndex=-1;
    function tick(){
     if(!allowed()||!active||!context)return;
     if(context.state!=="running"){frame=win.requestAnimationFrame(tick);return;}
     const ms=Math.max(0,(context.currentTime-startAt)*1000);
     const cues=payload.alignment.cues;
     let index=cueIndex;
     while(index+1<cues.length&&cues[index+1].atMs<=ms)index++;
     if(index!==cueIndex&&index>=0){
      cueIndex=index;
      onCue?.({viseme:cues[index].viseme,atMs:cues[index].atMs,
        audioClockMs:ms,decodedAudio:true,source:"oap-first-party-pcm",
        synthesisPhonemeTiming:true,accurateLipSyncProven:false});
     }
     frame=win.requestAnimationFrame(tick);
    }
    source.onended=()=>{
     if(!allowed())return;
     onCue?.({viseme:"silence",atMs:payload.alignment.audioDurationMs,
       audioClockMs:payload.alignment.audioDurationMs,decodedAudio:true,
       source:"oap-first-party-pcm",synthesisPhonemeTiming:true,
       accurateLipSyncProven:false});
     stop();onEnd?.();
    };
    source.start(startAt);
    active=true;
    onStart?.();
    frame=win.requestAnimationFrame(tick);
    return true;
   }catch(_error){
    if(allowed())onError?.();
    return false;
   }finally{
    if(!active&&allowed())stop();
   }
  }
  function pause(){if(context&&active){try{context.suspend()}catch{}}}
  function resume(){if(context&&active){try{context.resume()}catch{}}}
  return Object.freeze({play,stop,pause,resume,snapshot:()=>Object.freeze({
   active,hasDecodedAudio:Boolean(active&&context),retainsAudio:false,
   externalTelemetry:false,accurateHumanLipSyncProven:false
  })});
 }
 return Object.freeze({create,validate});
});
