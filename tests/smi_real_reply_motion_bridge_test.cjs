"use strict";
const assert=require("node:assert/strict"),api=require("../mission_control/smi_real_reply_motion_bridge.js");
for(const forged of [{},{source:api.SOURCE,replyId:"short",humanStart:true},{source:"manual_text",replyId:"reply-123",humanStart:true},{source:api.SOURCE,replyId:"reply-123",humanStart:false}]){
  const bridge=api.createRealReplyBridge(forged);assert.equal(bridge.snapshot().admitted,false);assert.equal(bridge.playbackStart({elapsedMs:0}),null);
}
const bridge=api.createRealReplyBridge({source:api.SOURCE,replyId:"reply-123",humanStart:true});
assert.equal(bridge.snapshot().attachedToLivePage,false);assert.equal(bridge.snapshot().storesText,false);assert.equal(bridge.snapshot().storesAudio,false);
assert.equal(bridge.playbackBoundary({elapsedMs:0,fragment:"a",boundaryObservedAtMs:1}),null);
assert.equal(bridge.playbackStart({elapsedMs:0}).type,"playback-start");
const cues=[[20,"m","closed"],[80,"a","wide"],[140,"o","round"],[200,"f","teeth"],[260,"l","tongue"],[320," ","silence"]];
for(const [elapsedMs,fragment,expected] of cues){const cue=bridge.playbackBoundary({elapsedMs,fragment,boundaryObservedAtMs:elapsedMs+2});assert.equal(cue.viseme,expected);assert.equal(cue.productionApproved,false);assert.equal(cue.humanFinalApproved,false);}
assert.equal(bridge.playbackBoundary({elapsedMs:100,fragment:"a",boundaryObservedAtMs:400}),null);
assert.equal(bridge.playbackEnd({elapsedMs:400}).viseme,"silence");
bridge.playbackStart({elapsedMs:0});const stoppedEpoch=bridge.humanStop().epoch;
assert.equal(bridge.playbackBoundary({elapsedMs:20,fragment:"a",boundaryObservedAtMs:500}),null);assert.equal(bridge.playbackEnd({elapsedMs:500}),null);
assert.equal(bridge.resetAfterHumanAction(false).stopped,true);assert.equal(bridge.resetAfterHumanAction(true).epoch,stoppedEpoch+1);
assert.equal(bridge.playbackStart({elapsedMs:0}).type,"playback-start");
console.log("SMI_REAL_REPLY_MOTION_BRIDGE_PASS");
