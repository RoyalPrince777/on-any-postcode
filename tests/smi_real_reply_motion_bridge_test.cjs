"use strict";
const assert=require("node:assert/strict"),api=require("../mission_control/smi_real_reply_motion_bridge.js");
const audioSha256="a".repeat(64);
const cues=[
  {atMs:0,viseme:"silence",confidence:1},
  {atMs:20,viseme:"closed",confidence:.97},
  {atMs:80,viseme:"wide",confidence:.96},
  {atMs:140,viseme:"round",confidence:.95},
  {atMs:200,viseme:"teeth",confidence:.94},
  {atMs:260,viseme:"tongue",confidence:.93},
  {atMs:400,viseme:"silence",confidence:1},
];
function aligned(overrides={}){
  const value={source:api.ALIGNMENT_SOURCE,audioSha256,audioDurationMs:400,clockSource:"audio-context",
    audioDecoded:true,predictedFromText:false,storesAudio:false,storesReplyText:false,
    productionApproved:false,humanFinalApproved:false,maxAlignmentErrorMs:40,cues,...overrides};
  if(!Object.prototype.hasOwnProperty.call(overrides,"timelineSha256"))value.timelineSha256=api.timelineSha256(value);
  return value;
}
function bridge(overrides={}){return api.createRealReplyBridge({source:api.SOURCE,replyId:"reply-123",humanStart:true,audioSha256,alignment:aligned(),...overrides});}

for(const forged of [
  null,
  [],
  {},
  {source:api.SOURCE,replyId:"short",humanStart:true,audioSha256,alignment:aligned()},
  {source:"manual_text",replyId:"reply-123",humanStart:true,audioSha256,alignment:aligned()},
  {source:api.SOURCE,replyId:"reply-123",humanStart:false,audioSha256,alignment:aligned()},
  {source:api.SOURCE,replyId:"reply-123",humanStart:true,audioSha256:"0".repeat(64),alignment:aligned()},
  {source:api.SOURCE,replyId:"reply-123",humanStart:true,audioSha256,alignment:aligned(),replyText:"forbidden"},
]){
  const candidate=api.createRealReplyBridge(forged),snapshot=candidate.snapshot();assert.equal(snapshot.admitted,false);assert.ok(snapshot.identityReasons.length||snapshot.alignmentReasons.length);assert.equal(candidate.playbackStart({audioClockMs:0,observedAtMs:100,eventType:"playing",clockSource:"audio-context"}),null);
}

for(const invalidAlignment of [
  aligned({source:"predicted_text_timeline"}),aligned({audioDecoded:false}),aligned({predictedFromText:true}),
  aligned({storesAudio:true}),aligned({storesReplyText:true}),aligned({productionApproved:true}),aligned({humanFinalApproved:true}),
  aligned({maxAlignmentErrorMs:80.1}),aligned({clockSource:"wall-clock"}),aligned({audioSha256:"b".repeat(64)}),
  aligned({cues:[...cues.slice(0,-1),{atMs:400,viseme:"unknown",confidence:1}]}),
  aligned({cues:[...cues.slice(0,-1),{atMs:400,viseme:"silence",confidence:.79}]}),
  aligned({cues:[cues[0],{atMs:20,viseme:"closed",confidence:1,text:"reply leak"},...cues.slice(2)]}),
  aligned({replyText:"alignment-level reply leak"}),
  aligned({transcript:"alignment-level transcript leak"}),
  aligned({cues:[cues[0],{atMs:20,viseme:"closed",confidence:1},{atMs:19,viseme:"wide",confidence:1},...cues.slice(3)]}),
  aligned({timelineSha256:"0".repeat(64)}),
]){
  const candidate=bridge({alignment:invalidAlignment});assert.equal(candidate.snapshot().admitted,false);assert.ok(candidate.snapshot().alignmentReasons.length);
}

assert.equal(Object.prototype.hasOwnProperty.call(api,"visemeFor"),false);
const candidate=bridge(),initial=candidate.snapshot();
assert.equal(initial.admitted,true);assert.equal(initial.alignmentContractAccepted,true);
assert.deepEqual(initial.identityReasons,[]);
assert.equal(initial.version,"0.3-private-no-guess-strict-envelope");
assert.equal(initial.attachedToLivePage,false);assert.equal(initial.storesText,false);assert.equal(initial.storesAudio,false);
assert.equal(initial.accurateLipSyncProven,false);assert.equal(initial.physicalAndroidStopProven,false);
assert.equal(candidate.playbackSample({audioClockMs:20,observedAtMs:1020}),null);
assert.equal(candidate.playbackStart({audioClockMs:0,observedAtMs:1000,eventType:"boundary",clockSource:"audio-context"}),null);
assert.equal(candidate.playbackStart({audioClockMs:0,observedAtMs:1000,eventType:"playing",clockSource:"media-element"}),null);
assert.equal(candidate.playbackStart({audioClockMs:0,observedAtMs:1000,eventType:"playing",clockSource:"audio-context"}).type,"playback-start");
for(const [audioClockMs,expected] of [[20,"closed"],[80,"wide"],[140,"round"],[200,"teeth"],[260,"tongue"],[400,"silence"]]){
  const cue=candidate.playbackSample({audioClockMs,observedAtMs:1002+audioClockMs});
  assert.equal(cue.viseme,expected);assert.ok(cue.audioClockDeltaMs<=api.MAX_AUDIO_CLOCK_DELTA_MS);
  assert.equal(cue.productionApproved,false);assert.equal(cue.humanFinalApproved,false);
}
assert.equal(candidate.playbackEnd({audioClockMs:400,observedAtMs:1402,eventType:"ended"}).viseme,"silence");
assert.equal(candidate.playbackStart({audioClockMs:0,observedAtMs:2000,eventType:"playing",clockSource:"audio-context"}).type,"playback-start");
const stoppedEpoch=candidate.humanStop({pointerAtMs:2010,handledAtMs:2012}).epoch;
assert.equal(candidate.snapshot().lastStopAcknowledgementMs,2);assert.equal(candidate.snapshot().physicalAndroidStopProven,false);
assert.equal(candidate.playbackSample({audioClockMs:20,observedAtMs:2020}),null);
assert.equal(candidate.resetAfterHumanAction(false).stopped,true);
assert.equal(candidate.resetAfterHumanAction(true).epoch,stoppedEpoch+1);

const reversal=bridge();reversal.playbackStart({audioClockMs:0,observedAtMs:1000,eventType:"playing",clockSource:"audio-context"});
assert.equal(reversal.playbackSample({audioClockMs:100,observedAtMs:1100}).viseme,"wide");
assert.equal(reversal.playbackSample({audioClockMs:90,observedAtMs:1110}),null);assert.equal(reversal.snapshot().failedClosed,true);
assert.equal(reversal.snapshot().failReason,"played_audio_clock_invalid");
const drift=bridge();drift.playbackStart({audioClockMs:0,observedAtMs:1000,eventType:"playing",clockSource:"audio-context"});
assert.equal(drift.playbackSample({audioClockMs:10,observedAtMs:1051}),null);assert.equal(drift.snapshot().failReason,"played_audio_clock_drift");
console.log("SMI_REAL_REPLY_MOTION_BRIDGE_PASS");
