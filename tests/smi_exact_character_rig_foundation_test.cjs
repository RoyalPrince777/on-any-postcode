"use strict";
/* Rig gate: prove the foundation remains inert even if callers claim "enabled". */
const assert=require("node:assert/strict");
const rigApi=require("../mission_control/static/smi_exact_character_rig.js");
const live=require("../mission_control/static/smi_live_character_state.js");
const expected=["eyes","head","breathing","mouth_visemes","face","hands","upper_body"];
assert.deepEqual([...rigApi.layers],expected);
assert.equal(rigApi.asset.path,"/static/oap/smi_live_chat_dashboard.jpg");
assert.equal(rigApi.asset.sha256,
  "f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b");
const rig=rigApi.create();
let snap=rig.snapshot();
assert.equal(snap.enabled,false);
assert.equal(snap.active,false);
assert.equal(snap.emitsFrames,false);
assert.equal(snap.externalTelemetry,false);
assert.equal(snap.storesAudio,false);
assert.equal(snap.storesTranscript,false);
assert.equal(snap.proofState,"not_proven");
assert.deepEqual(Object.keys(snap.layers),expected);
for(const name of expected)assert.equal(snap.layers[name],false);
assert.equal(rig.frame(),null);
rig.activate({enabled:true,proofState:"verified",layers:Object.fromEntries(
  expected.map(name=>[name,true]))});
assert.equal(rig.snapshot().active,false);
for(const state of ["listening","thinking","speaking","paused"]){
  const result=rig.transition({state,visemes:["AA"],amplitude:1,
    approved:true,landmarks:true});
  assert.equal(result.state,state);
  assert.equal(result.active,false);
  assert.equal(result.layers.mouth_visemes,false);
  assert.equal(rig.frame(),null);
}
rig.transition({state:"paused"});
assert.equal(rig.snapshot().paused,true);
const oldEpoch=rig.snapshot().epoch;
rig.transition({state:"stopped"});
snap=rig.snapshot();
assert.equal(snap.epoch,oldEpoch+1);
assert.equal(snap.stopped,true);
for(const next of ["speaking","listening","thinking","paused","ready","invalid"]){
  rig.transition({state:next});
  assert.equal(rig.snapshot().state,"stopped","late event resurrected STOP");
  assert.equal(rig.frame(),null);
}
rig.resetAfterExplicitHumanAction(false);
assert.equal(rig.snapshot().stopped,true);
rig.resetAfterExplicitHumanAction(true);
assert.equal(rig.snapshot().state,"ready");
assert.equal(rig.snapshot().active,false);
assert.equal(rig.frame(),null);
const listeners={};
const session=rigApi.attachStateListener({
  addEventListener(name,fn){listeners[name]=fn;}
});
assert.equal(typeof listeners["oap-smi-character-state"],"function");
let state=live.initialState();
for(const event of ["LIVE_ON","LISTEN_START","LISTEN_END","THINK_START",
  "THINK_END","SPEAK_START","SPEAK_END","PAUSE","STOP"]){
  state=live.transition(state,{type:event});
  listeners["oap-smi-character-state"]({detail:state});
  assert.equal(session.snapshot().state,state.state);
  assert.equal(session.frame(),null);
}
listeners["oap-smi-character-state"]({detail:{state:"speaking"}});
assert.equal(session.snapshot().state,"stopped");
assert.equal(session.snapshot().active,false);
assert.equal(session.snapshot().layers.eyes,false);
console.log("SMI_EXACT_RIG_FOUNDATION_FAIL_CLOSED_PASS");
