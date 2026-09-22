/* Private SMI real-reply motion bridge candidate.
 * Not loaded by the live page. It consumes an integrity-bound viseme timeline
 * derived from decoded reply audio and never guesses mouth shapes from text.
 */
"use strict";

const crypto=require("node:crypto");
const SOURCE="smi_response_audio";
const ALIGNMENT_SOURCE="decoded_audio_phoneme_timeline";
const CLOCK_SOURCES=Object.freeze(["audio-context","media-element"]);
const VISEMES=Object.freeze(["silence","closed","wide","round","teeth","tongue"]);
const MAX_AUDIO_CLOCK_DELTA_MS=80;
const MIN_ALIGNMENT_CONFIDENCE=0.8;
const MAX_AUDIO_DURATION_MS=300000;
const HASH=/^[a-f0-9]{64}$/;

function finite(value){return Number.isFinite(value)&&typeof value==="number";}
function timelineSha256({audioSha256,audioDurationMs,cues}={}){
  const canonical={audioSha256,audioDurationMs,cues:Array.isArray(cues)?cues.map(cue=>({
    atMs:cue?.atMs,viseme:cue?.viseme,confidence:cue?.confidence,
  })):cues};
  return crypto.createHash("sha256").update(JSON.stringify(canonical)).digest("hex");
}
function inspectAlignment(alignment,expectedAudioSha256){
  const reasons=[];
  if(!alignment||typeof alignment!=="object"||Array.isArray(alignment)){
    return Object.freeze({accepted:false,reasons:Object.freeze(["alignment_missing"])});
  }
  if(alignment.source!==ALIGNMENT_SOURCE)reasons.push("decoded_audio_alignment_missing");
  if(!HASH.test(alignment.audioSha256||"")||alignment.audioSha256!==expectedAudioSha256)reasons.push("audio_hash_mismatch");
  if(!finite(alignment.audioDurationMs)||alignment.audioDurationMs<=0||alignment.audioDurationMs>MAX_AUDIO_DURATION_MS)reasons.push("audio_duration_invalid");
  if(!CLOCK_SOURCES.includes(alignment.clockSource))reasons.push("played_audio_clock_missing");
  if(alignment.audioDecoded!==true)reasons.push("decoded_audio_unproven");
  if(alignment.predictedFromText!==false)reasons.push("text_prediction_forbidden");
  if(alignment.storesAudio!==false||alignment.storesReplyText!==false)reasons.push("retention_boundary_invalid");
  if(alignment.productionApproved!==false||alignment.humanFinalApproved!==false)reasons.push("forbidden_approval_claim");
  if(!finite(alignment.maxAlignmentErrorMs)||alignment.maxAlignmentErrorMs<0||alignment.maxAlignmentErrorMs>MAX_AUDIO_CLOCK_DELTA_MS)reasons.push("alignment_error_unbounded");
  const cues=alignment.cues;
  if(!Array.isArray(cues)||cues.length<3||cues.length>10000)reasons.push("viseme_timeline_invalid");
  else{
    let previous=-1;
    for(const cue of cues){
      const keys=cue&&typeof cue==="object"&&!Array.isArray(cue)?Object.keys(cue):[];
      if(keys.some(key=>!["atMs","viseme","confidence"].includes(key)))reasons.push("timeline_contains_unapproved_data");
      if(!finite(cue?.atMs)||cue.atMs<0||cue.atMs<=previous||cue.atMs>alignment.audioDurationMs)reasons.push("viseme_time_invalid");
      if(!VISEMES.includes(cue?.viseme))reasons.push("viseme_invalid");
      if(!finite(cue?.confidence)||cue.confidence<MIN_ALIGNMENT_CONFIDENCE||cue.confidence>1)reasons.push("viseme_confidence_invalid");
      previous=cue?.atMs;
    }
    const first=cues[0],last=cues[cues.length-1];
    if(first?.atMs!==0||first?.viseme!=="silence")reasons.push("opening_silence_missing");
    if(last?.viseme!=="silence"||!finite(last?.atMs)||Math.abs(last.atMs-alignment.audioDurationMs)>1)reasons.push("closing_silence_missing");
    if(!HASH.test(alignment.timelineSha256||"")||alignment.timelineSha256!==timelineSha256(alignment))reasons.push("timeline_hash_mismatch");
  }
  return Object.freeze({accepted:reasons.length===0,reasons:Object.freeze([...new Set(reasons)])});
}
function createRealReplyBridge({source,replyId,humanStart,audioSha256,alignment}={}){
  const identityAccepted=source===SOURCE&&typeof replyId==="string"&&/^[A-Za-z0-9._:-]{8,128}$/.test(replyId)&&
    humanStart===true&&HASH.test(audioSha256||"");
  const inspection=inspectAlignment(alignment,audioSha256);
  const admitted=identityAccepted&&inspection.accepted;
  const cues=inspection.accepted?alignment.cues.map(cue=>Object.freeze({...cue})):[];
  const durationMs=inspection.accepted?alignment.audioDurationMs:0;
  const expectedClock=inspection.accepted?alignment.clockSource:null;
  const alignmentToleranceMs=inspection.accepted?alignment.maxAlignmentErrorMs:0;
  let epoch=0,started=false,stopped=false,failedClosed=false,failReason=null,events=0;
  let startAudioClockMs=-1,startObservedAtMs=-1,lastAudioClockMs=-1,lastObservedAtMs=-1,lastStopAcknowledgementMs=null;
  const snapshot=()=>Object.freeze({version:"0.2-private-no-guess",admitted,
    alignmentContractAccepted:inspection.accepted,alignmentReasons:inspection.reasons,
    epoch,started,stopped,failedClosed,failReason,events,lastAudioClockMs,lastObservedAtMs,
    lastStopAcknowledgementMs,storesText:false,storesAudio:false,attachedToLivePage:false,
    accurateLipSyncProven:false,physicalAndroidStopProven:false,
    productionApproved:false,humanFinalApproved:false});
  function failClosed(reason){
    epoch+=1;started=false;stopped=true;failedClosed=true;failReason=reason;events+=1;
    return null;
  }
  function playbackStart({audioClockMs=0,observedAtMs,eventType,clockSource}={}){
    if(!admitted||stopped||started||eventType!=="playing"||clockSource!==expectedClock||
      !finite(audioClockMs)||audioClockMs<0||audioClockMs>MAX_AUDIO_CLOCK_DELTA_MS||!finite(observedAtMs))return null;
    started=true;startAudioClockMs=audioClockMs;startObservedAtMs=observedAtMs;
    lastAudioClockMs=audioClockMs;lastObservedAtMs=observedAtMs;events+=1;
    return Object.freeze({type:"playback-start",epoch,audioClockMs,productionApproved:false,humanFinalApproved:false});
  }
  function activeCue(audioClockMs){
    let active=cues[0],index=0;
    for(let i=1;i<cues.length&&cues[i].atMs<=audioClockMs;i+=1){active=cues[i];index=i;}
    return {active,index};
  }
  function playbackSample({audioClockMs,observedAtMs}={}){
    if(!admitted||!started||stopped)return null;
    if(!finite(audioClockMs)||!finite(observedAtMs)||audioClockMs<lastAudioClockMs||observedAtMs<lastObservedAtMs||audioClockMs>durationMs+MAX_AUDIO_CLOCK_DELTA_MS)return failClosed("played_audio_clock_invalid");
    const audioElapsed=audioClockMs-startAudioClockMs,observedElapsed=observedAtMs-startObservedAtMs;
    const audioClockDeltaMs=Math.abs(audioElapsed-observedElapsed);
    if(audioClockDeltaMs>alignmentToleranceMs)return failClosed("played_audio_clock_drift");
    lastAudioClockMs=audioClockMs;lastObservedAtMs=observedAtMs;events+=1;
    const {active,index}=activeCue(Math.min(audioClockMs,durationMs));
    return Object.freeze({type:"played-audio-viseme",epoch,audioClockMs,audioClockDeltaMs,
      cueIndex:index,viseme:active.viseme,confidence:active.confidence,
      mouthScaleY:active.viseme==="silence"?1:1.08,
      headRotateDeg:Math.sin(audioClockMs/900)*0.3,
      handOffsetY:Math.sin(audioClockMs/650)*0.6,
      productionApproved:false,humanFinalApproved:false});
  }
  function playbackEnd({audioClockMs,observedAtMs,eventType}={}){
    // A late end event may not overwrite Human STOP or a previous fail-closed state.
    if(!admitted||!started||stopped)return null;
    if(eventType!=="ended"||!finite(audioClockMs)||Math.abs(audioClockMs-durationMs)>alignmentToleranceMs)return failClosed("played_audio_end_unproven");
    const finalCue=playbackSample({audioClockMs,observedAtMs});
    if(!finalCue)return null;
    started=false;events+=1;
    return Object.freeze({type:"playback-end",epoch,audioClockMs,viseme:"silence",mouthScaleY:1,
      productionApproved:false,humanFinalApproved:false});
  }
  function humanStop({pointerAtMs,handledAtMs}={}){
    lastStopAcknowledgementMs=finite(pointerAtMs)&&finite(handledAtMs)&&handledAtMs>=pointerAtMs?handledAtMs-pointerAtMs:null;
    epoch+=1;started=false;stopped=true;events+=1;return snapshot();
  }
  function resetAfterHumanAction(approved){
    if(approved!==true||!stopped)return snapshot();
    epoch+=1;started=false;stopped=false;failedClosed=false;failReason=null;
    startAudioClockMs=-1;startObservedAtMs=-1;lastAudioClockMs=-1;lastObservedAtMs=-1;events+=1;
    return snapshot();
  }
  return Object.freeze({snapshot,playbackStart,playbackSample,playbackEnd,humanStop,resetAfterHumanAction});
}

module.exports=Object.freeze({SOURCE,ALIGNMENT_SOURCE,CLOCK_SOURCES,VISEMES,
  MAX_AUDIO_CLOCK_DELTA_MS,MIN_ALIGNMENT_CONFIDENCE,timelineSha256,inspectAlignment,createRealReplyBridge});
