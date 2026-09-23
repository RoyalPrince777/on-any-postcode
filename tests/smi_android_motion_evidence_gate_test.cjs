"use strict";
const assert=require("node:assert/strict"),gate=require("../mission_control/smi_android_motion_evidence_gate.js");
const now=Date.parse("2026-09-21T12:00:00Z"),hash="a".repeat(64);
const valid={evidenceType:"physical_android_human_test",platform:"Android",deviceModel:"25028RN03A",androidVersion:"15",
  approvedSourceSha256:gate.APPROVED_SHA,layerSha256:Object.fromEntries(gate.LAYERS.map(x=>[x,hash])),exactCharacterIntact:true,
  playedAudioObserved:true,maxAudioClockDeltaMs:79.9,motionStopped:true,audioStopped:true,stopAcknowledgementMs:49.9,
  backgroundStopPassed:true,humanVisualApproved:true,productionApproved:false,humanFinalApproved:false,
  testedAt:"2026-09-21T11:59:00Z",humanNote:"Exact character and bounded motion visually approved."};
const passed=gate.evaluateAndroidReceipt(valid,{nowMs:now});assert.equal(passed.accepted,true);assert.equal(passed.aegis75Ready,true);
assert.equal(passed.productionApproved,false);assert.match(passed.receiptSha256,/^[a-f0-9]{64}$/);
for(const mutation of [
  {evidenceType:"browser_simulation"},{platform:"Desktop"},{approvedSourceSha256:"0".repeat(64)},{exactCharacterIntact:false},
  {maxAudioClockDeltaMs:80.1},{playedAudioObserved:false},{stopAcknowledgementMs:50.1},{motionStopped:false},{audioStopped:false},
  {backgroundStopPassed:false},{humanVisualApproved:false},{productionApproved:true},{humanFinalApproved:true},
  {testedAt:"2026-09-19T11:00:00Z"},{humanNote:""}
]){
  const result=gate.evaluateAndroidReceipt({...valid,...mutation},{nowMs:now});assert.equal(result.accepted,false);assert.equal(result.aegis75Ready,false);
  assert.equal(result.productionApproved,false);assert.ok(result.reasons.length);
}
for(const layer of gate.LAYERS){const layerSha256={...valid.layerSha256};delete layerSha256[layer];assert.equal(gate.evaluateAndroidReceipt({...valid,layerSha256},{nowMs:now}).accepted,false);}
const inherited=Object.create({eyes:hash});for(const layer of gate.LAYERS.filter(x=>x!=="eyes"))inherited[layer]=hash;
assert.equal(gate.evaluateAndroidReceipt({...valid,layerSha256:inherited},{nowMs:now}).accepted,false);
assert.equal(gate.evaluateAndroidReceipt({...valid,layerSha256:gate.LAYERS.map(()=>hash)},{nowMs:now}).accepted,false);
assert.equal(gate.evaluateAndroidReceipt({...valid,layerSha256:"not-a-layer-map"},{nowMs:now}).accepted,false);
assert.equal(gate.evaluateAndroidReceipt(null,{nowMs:now}).accepted,false);
console.log("SMI_ANDROID_MOTION_EVIDENCE_GATE_PASS");
