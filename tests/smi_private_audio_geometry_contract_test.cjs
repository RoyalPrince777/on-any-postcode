"use strict";
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const {admit}=require("../mission_control/smi_private_audio_geometry_contract.js");
const sha="a".repeat(64),geometryBytes=Uint8Array.from([1,2,3,4]);
const geometrySha=crypto.createHash("sha256").update(geometryBytes).digest("hex");
let audio={admitted:true,alignmentContractAccepted:true,started:true,stopped:false,failedClosed:false,epoch:0};
let body={stopped:false,geometryApproved:false,epoch:0};
const audioBridge={snapshot:()=>({...audio}),acceptsIssuedCue:issued=>issued===cue},characterRig={snapshot:()=>({...body})};
const cue={type:"played-audio-viseme",epoch:0,viseme:"wide",audioClockMs:80,confidence:.96,
 productionApproved:false,humanFinalApproved:false};
const geometry={reviewedByFounder:true,sourceVerified:true,sourceSha256:sha,replyId:"reply-123",
 viseme:"wide",nonNeutralSourceGeometryReviewed:true,hiddenRegionsReconstructed:true,
 geometrySha256:geometrySha,productionApproved:false};
const args={audioBridge,characterRig,cue,geometry,geometryBytes,replyId:"reply-123",sourceSha256:sha,expectedEpoch:0};
const accepted=admit(args);
assert.equal(accepted.type,"private-reviewed-viseme-reference");
assert.equal(accepted.attachedToLivePage,false);
assert.equal(accepted.lipSyncProven,false);
assert.equal(accepted.productionApproved,false);
assert.equal(Object.hasOwn(accepted,"pixels"),false);
for(const override of [
 {geometry:null},{geometryBytes:null},{geometryBytes:new Uint8Array(0)},
 {geometryBytes:Uint8Array.from([1,2,3,5])},
 {geometry:{...geometry,geometrySha256:"b".repeat(64)}},
 {geometry:{...geometry,reviewedByFounder:false}},
 {geometry:{...geometry,hiddenRegionsReconstructed:false}},
 {geometry:{...geometry,nonNeutralSourceGeometryReviewed:false}},
 {geometry:{...geometry,sourceSha256:"c".repeat(64)}},
 {geometry:{...geometry,viseme:"closed"}},
 {geometry:{...geometry,replyId:"reply-124"}},
 {geometry:{...geometry,productionApproved:true}},
 {cue:{...cue}},
 {audioBridge:{snapshot:()=>({...audio})}},
 {audioBridge:{snapshot:()=>({...audio}),acceptsIssuedCue:()=>false}},
 {cue:{...cue,viseme:"silence"}},
 {cue:{...cue,epoch:1}},
 {cue:{...cue,confidence:.79}},
 {cue:{...cue,productionApproved:true}},
 {sourceSha256:"bad"}, {expectedEpoch:1}
])assert.equal(admit({...args,...override}),null);
audio={...audio,stopped:true,started:false,epoch:1};
assert.equal(admit(args),null);
audio={...audio,stopped:false,started:true,epoch:0,failedClosed:true};
assert.equal(admit(args),null);
audio={...audio,failedClosed:false};
body={...body,stopped:true,epoch:1};
assert.equal(admit(args),null);
body={...body,stopped:false,epoch:0,geometryApproved:true};
assert.equal(admit(args),null);
// A real digest never proves that synthetic bytes represent approved SMI anatomy.
assert.equal(accepted.lipSyncProven,false);
// STOP may arrive during integrity validation; final snapshots must win.
audio={admitted:true,alignmentContractAccepted:true,started:true,stopped:false,failedClosed:false,epoch:0};
body={stopped:false,geometryApproved:false,epoch:0};
let audioReads=0;
const stopDuringVerification={acceptsIssuedCue:issued=>issued===cue,snapshot:()=>{
  audioReads++;
  if(audioReads===2)audio={...audio,started:false,stopped:true,epoch:1};
  return {...audio};
}};
assert.equal(admit({...args,audioBridge:stopDuringVerification}),null);
assert.equal(audioReads,2);
audio={admitted:true,alignmentContractAccepted:true,started:true,stopped:false,failedClosed:false,epoch:0};
let bodyReads=0;
const bodyStopsDuringVerification={acceptsIssuedCue:issued=>issued===cue,snapshot:()=>{
  bodyReads++;
  if(bodyReads===2)body={...body,stopped:true,epoch:1};
  return {...body};
}};
assert.equal(admit({...args,characterRig:bodyStopsDuringVerification}),null);
assert.equal(bodyReads,2);
console.log("SMI_PRIVATE_AUDIO_GEOMETRY_CONTRACT_PASS");
