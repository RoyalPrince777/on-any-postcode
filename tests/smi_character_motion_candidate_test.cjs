"use strict";
const assert=require("node:assert/strict");
const api=require("../mission_control/smi_character_motion_candidate.js");

const proof={approvedSourceSha256:api.APPROVED_SHA,pixelLineageProven:true,
  maskRegistrationProven:true,humanLayerReviewApproved:true,
  isolatedPrivateCandidate:true};
for(const missing of Object.keys(proof)){
  const forged={...proof}; delete forged[missing];
  const denied=api.createCandidate(forged);
  assert.equal(denied.snapshot().admitted,false);
  assert.equal(denied.start({humanAction:true,reducedMotion:false}).running,false);
  assert.equal(denied.frame(0),null);
}
const candidate=api.createCandidate(proof);
assert.equal(candidate.snapshot().attachedToLivePage,false);
assert.equal(candidate.snapshot().rendersPixels,false);
candidate.start({humanAction:true});
assert.equal(candidate.snapshot().reducedMotion,true);
assert.equal(candidate.frame(100),null);
candidate.transition("stopped");
assert.equal(candidate.frame(100),null);
candidate.resetAfterExplicitHumanAction(true);
candidate.start({humanAction:true,reducedMotion:false});
for(const state of ["ready","listening","thinking","speaking"]){
  candidate.transition(state);
  const frame=candidate.frame(120,{playedAudioMs:120,viseme:"AA",amplitude:0.8});
  assert.equal(frame.state,state);
  assert.equal(frame.productionApproved,false);
  assert.equal(frame.humanFinalApproved,false);
  assert.equal(frame.externalTelemetry,false);
}
candidate.transition("speaking");
assert.equal(candidate.frame(120,{playedAudioMs:400,viseme:"AA",amplitude:1}).mouth_visemes.viseme,"silence");
assert.equal(candidate.frame(120,{playedAudioMs:120,viseme:"AA",amplitude:4}).mouth_visemes.scaleY,1.12);
candidate.transition("paused");
assert.equal(candidate.frame(120),null);
candidate.transition("stopped");
const stopped=candidate.snapshot();
for(const late of ["ready","listening","thinking","speaking","paused"]){
  candidate.transition(late);
  assert.equal(candidate.snapshot().state,"stopped");
  assert.equal(candidate.snapshot().epoch,stopped.epoch);
  assert.equal(candidate.frame(120),null);
}
assert.equal(candidate.resetAfterExplicitHumanAction(false).stopped,true);
assert.equal(candidate.resetAfterExplicitHumanAction(true).state,"ready");
assert.equal(candidate.snapshot().running,false);
console.log("SMI_ISOLATED_MOTION_CANDIDATE_PASS");
