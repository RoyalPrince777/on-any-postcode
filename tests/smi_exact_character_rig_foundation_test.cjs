"use strict";
const assert=require("node:assert/strict");
const rigApi=require("../mission_control/static/smi_exact_character_rig.js");
const live=require("../mission_control/static/smi_live_character_state.js");
const expected=["eyes","head","breathing","mouth_visemes","face","hands","upper_body"];
const sha="f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b";
assert.deepEqual([...rigApi.layers],expected);
assert.equal(rigApi.asset.sha256,sha);
const rig=rigApi.create();
let snap=rig.snapshot();
assert.equal(snap.enabled,false);
assert.equal(snap.active,false);
assert.equal(snap.emitsFrames,false);
assert.equal(snap.fullRigProven,false);
assert.equal(snap.accurateSoftwareLipSyncProven,false);
assert.equal(snap.accurateHumanLipSyncProven,false);
assert.equal(snap.externalTelemetry,false);
assert.equal(snap.storesAudio,false);
assert.equal(snap.storesTranscript,false);
assert.equal(rig.frame(),null);

const hashes=Object.fromEntries(expected.map(name=>[name,"a".repeat(64)]));
const frames=Object.fromEntries(expected.map(name=>[name,7]));
const session={snapshot:()=>({
 sourceSha256:sha,evidenceLayerSha256:hashes,rigLayerFrames:frames,
 fullBodyRigProven:true,accurateSoftwareLipSyncProven:true,live:true
})};
snap=rig.bindMotionSession(session);
assert.equal(snap.enabled,true);
assert.equal(snap.active,true);
assert.equal(snap.proofState,"machine_proven");
assert.equal(snap.fullRigProven,true);
assert.equal(snap.accurateSoftwareLipSyncProven,true);
assert.equal(snap.accurateHumanLipSyncProven,false);
for(const name of expected)assert.equal(snap.layers[name],true);
assert.equal(snap.rendererOwner,"smi_source_pixel_motion");

const bad=rigApi.create();
bad.bindMotionSession({snapshot:()=>({sourceSha256:"b".repeat(64)})});
assert.equal(bad.snapshot().enabled,false);
assert.equal(bad.snapshot().fullRigProven,false);

for(const state of ["listening","thinking","speaking","paused"]){
  const result=rig.transition({state});
  assert.equal(result.state,state);
  assert.equal(rig.frame(),null);
}
const oldEpoch=rig.snapshot().epoch;
rig.transition({state:"stopped"});
snap=rig.snapshot();
assert.equal(snap.epoch,oldEpoch+1);
assert.equal(snap.stopped,true);
for(const next of ["speaking","listening","thinking","paused","ready","invalid"]){
  rig.transition({state:next});
  assert.equal(rig.snapshot().state,"stopped","late event resurrected STOP");
}
rig.resetAfterExplicitHumanAction(false);
assert.equal(rig.snapshot().stopped,true);
rig.resetAfterExplicitHumanAction(true);
assert.equal(rig.snapshot().state,"ready");

const listeners={};
const attached=rigApi.attachStateListener({addEventListener(name,fn){listeners[name]=fn;}});
assert.equal(typeof listeners["oap-smi-character-state"],"function");
let state=live.initialState();
for(const event of ["LIVE_ON","LISTEN_START","LISTEN_END","THINK_START","THINK_END","SPEAK_START","SPEAK_END","PAUSE","STOP"]){
  state=live.transition(state,{type:event});
  listeners["oap-smi-character-state"]({detail:state});
  assert.equal(attached.snapshot().state,state.state);
}
console.log("SMI_EXACT_RIG_LIVE_PROOF_PASS");
