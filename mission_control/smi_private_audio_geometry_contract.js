/* Private contract only: never synthesise hidden anatomy or render a mouth.
 * Caller must supply independently reviewed source-backed mouth geometry.
 * No live-page import, network, storage, microphone or production approval.
 */
"use strict";
const crypto=require("node:crypto");
const HASH=/^[a-f0-9]{64}$/;
const VISEMES=new Set(["closed","wide","round","teeth","tongue"]);
function admit({audioBridge,characterRig,cue,geometry,replyId,sourceSha256,expectedEpoch}={}){
  if(!audioBridge||typeof audioBridge.snapshot!=="function"||
     !characterRig||typeof characterRig.snapshot!=="function")return null;
  const audio=audioBridge.snapshot(),body=characterRig.snapshot();
  if(audio.admitted!==true||audio.alignmentContractAccepted!==true||
     audio.started!==true||audio.stopped!==false||audio.failedClosed!==false||
     body.stopped!==false||body.geometryApproved!==false||
     !Number.isSafeInteger(expectedEpoch)||expectedEpoch<0||
     audio.epoch!==expectedEpoch||body.epoch!==expectedEpoch)return null;
  if(!cue||cue.type!=="played-audio-viseme"||cue.epoch!==expectedEpoch||
     !VISEMES.has(cue.viseme)||!Number.isFinite(cue.audioClockMs)||
     cue.audioClockMs<0||!Number.isFinite(cue.confidence)||
     cue.confidence<0.8||cue.confidence>1||
     cue.productionApproved!==false||cue.humanFinalApproved!==false)return null;
  // No user-origin text, model-inferred phonemes or placeholder geometry.
  if(typeof replyId!=="string"||!/^[A-Za-z0-9._:-]{8,128}$/.test(replyId)||
     !HASH.test(sourceSha256||"")||
     !geometry||geometry.reviewedByFounder!==true||
     geometry.sourceVerified!==true||geometry.sourceSha256!==sourceSha256||
     geometry.replyId!==replyId||geometry.viseme!==cue.viseme||
     geometry.nonNeutralSourceGeometryReviewed!==true||
     geometry.hiddenRegionsReconstructed!==true||
     !HASH.test(geometry.geometrySha256||"")||
     geometry.productionApproved!==false)return null;
  // The identifier is an integrity reference, not generated pixel data.
  return Object.freeze({type:"private-reviewed-viseme-reference",
    replyId,viseme:cue.viseme,audioClockMs:cue.audioClockMs,
    epoch:expectedEpoch,sourceSha256,geometrySha256:geometry.geometrySha256,
    attachedToLivePage:false,lipSyncProven:false,
    productionApproved:false,humanFinalApproved:false});
}
module.exports=Object.freeze({admit});
