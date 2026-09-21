/* Private SMI real-reply motion bridge candidate.
 * Not loaded by the live page. Accepts browser SpeechSynthesis playback events,
 * emits bounded viseme/body cues, and stores neither reply text nor audio.
 */
"use strict";
const SOURCE="smi_response_stream";
const VISEMES=Object.freeze(["silence","closed","wide","round","teeth","tongue"]);
function visemeFor(fragment){
  const s=String(fragment||"").toLowerCase();
  if(!s.trim())return "silence";
  if(/[bmp]/.test(s[0]))return "closed";
  if(/[aehiy]/.test(s[0]))return "wide";
  if(/[ouqw]/.test(s[0]))return "round";
  if(/[fvsxz]/.test(s[0]))return "teeth";
  if(/[ltdnr]/.test(s[0]))return "tongue";
  return "wide";
}
function createRealReplyBridge({source,replyId,humanStart}={}){
  const admitted=source===SOURCE&&typeof replyId==="string"&&replyId.length>=8&&humanStart===true;
  let epoch=0,started=false,stopped=false,lastElapsedMs=-1,lastBoundaryAtMs=-1,events=0;
  const snapshot=()=>Object.freeze({version:"0.1-private",admitted,epoch,started,stopped,lastElapsedMs,
    lastBoundaryAtMs,events,storesText:false,storesAudio:false,attachedToLivePage:false,
    productionApproved:false,humanFinalApproved:false});
  function playbackStart({elapsedMs=0}={}){
    if(!admitted||stopped||!Number.isFinite(elapsedMs)||elapsedMs<0)return null;
    started=true;lastElapsedMs=elapsedMs;events+=1;
    return Object.freeze({type:"playback-start",epoch,elapsedMs,productionApproved:false});
  }
  function playbackBoundary({elapsedMs,fragment,boundaryObservedAtMs}={}){
    if(!admitted||!started||stopped||!Number.isFinite(elapsedMs)||elapsedMs<lastElapsedMs||
      !Number.isFinite(boundaryObservedAtMs)||boundaryObservedAtMs<lastBoundaryAtMs)return null;
    lastElapsedMs=elapsedMs;lastBoundaryAtMs=boundaryObservedAtMs;events+=1;
    const viseme=visemeFor(fragment);
    return Object.freeze({type:"played-audio-boundary",epoch,elapsedMs,viseme,
      mouthScaleY:viseme==="silence"?1:1.08,headRotateDeg:Math.sin(elapsedMs/900)*0.3,
      handOffsetY:Math.sin(elapsedMs/650)*0.6,productionApproved:false,humanFinalApproved:false});
  }
  function playbackEnd({elapsedMs}={}){
    if(!admitted||!started||stopped||!Number.isFinite(elapsedMs)||elapsedMs<lastElapsedMs)return null;
    lastElapsedMs=elapsedMs;started=false;events+=1;
    return Object.freeze({type:"playback-end",epoch,elapsedMs,viseme:"silence",mouthScaleY:1,productionApproved:false});
  }
  function humanStop(){epoch+=1;started=false;stopped=true;events+=1;return snapshot();}
  function resetAfterHumanAction(approved){if(approved!==true||!stopped)return snapshot();epoch+=1;stopped=false;lastElapsedMs=-1;lastBoundaryAtMs=-1;events+=1;return snapshot();}
  return Object.freeze({snapshot,playbackStart,playbackBoundary,playbackEnd,humanStop,resetAfterHumanAction});
}
module.exports=Object.freeze({SOURCE,VISEMES,visemeFor,createRealReplyBridge});
