'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const gate=require('../mission_control/smi_reply_pcm_audio_gate.js');
const bridge=require('../mission_control/smi_real_reply_motion_bridge.js');
function fixture(){
 const samples=6400,rate=16000,b=Buffer.alloc(44+samples*2);
 b.write('RIFF',0);b.writeUInt32LE(b.length-8,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);
 b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);b.writeUInt32LE(rate,24);b.writeUInt32LE(rate*2,28);
 b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(samples*2,40);
 for(let i=0;i<samples;i++)b.writeInt16LE(Math.trunc(Math.sin(i/12)*14000),44+i*2);
 return b;
}
const wav=fixture(),receipt=gate.inspectPcmWav(wav);
assert.equal(receipt.accepted,true);assert.equal(receipt.audioDurationMs,400);
assert.equal(receipt.audioSha256,crypto.createHash('sha256').update(wav).digest('hex'));
assert.equal(receipt.retainsAudio,false);
const cues=[{atMs:0,viseme:'silence',confidence:1},{atMs:80,viseme:'closed',confidence:.98},{atMs:180,viseme:'wide',confidence:.96},{atMs:400,viseme:'silence',confidence:1}];
function alignment(overrides={}){
 const x={source:bridge.ALIGNMENT_SOURCE,audioSha256:receipt.audioSha256,audioDurationMs:400,clockSource:'audio-context',audioDecoded:true,predictedFromText:false,storesAudio:false,storesReplyText:false,productionApproved:false,humanFinalApproved:false,maxAlignmentErrorMs:40,cues,...overrides};
 x.timelineSha256=bridge.timelineSha256(x);return x;
}
const valid=gate.createByteBoundReplyBridge({replyId:'reply-real-audio',humanStart:true,audioWav:wav,alignment:alignment()});
assert.equal(valid.accepted,true);assert.equal(valid.bridge.snapshot().admitted,true);
assert.equal(valid.realSmiReplyProven,false);assert.equal(valid.phonemeProven,false);
assert.equal(valid.livePageConnected,false);assert.equal(valid.releaseApproved,false);
for(const bad of [null,{},Buffer.alloc(0),Buffer.alloc(55),Buffer.alloc(wav.length)])assert.equal(gate.inspectPcmWav(bad).accepted,false);
const tampered=Buffer.from(wav);tampered[50]^=1;
assert.equal(gate.createByteBoundReplyBridge({replyId:'reply-real-audio',humanStart:true,audioWav:tampered,alignment:alignment()}).reason,'actual_audio_alignment_mismatch');
const badHeader=Buffer.from(wav);badHeader[0]=0;
assert.equal(gate.inspectPcmWav(badHeader).reason,'wav_header_invalid');
const badLength=Buffer.from(wav);badLength.writeUInt32LE(0,4);
assert.equal(gate.inspectPcmWav(badLength).reason,'wav_length_invalid');
const silence=Buffer.from(wav);silence.fill(0,44);
assert.equal(gate.inspectPcmWav(silence).reason,'silent_audio_not_reply_proof');
assert.equal(gate.createByteBoundReplyBridge({replyId:'reply-real-audio',humanStart:true,audioWav:wav,alignment:alignment({audioSha256:'b'.repeat(64)})}).accepted,false);
assert.equal(gate.createByteBoundReplyBridge({replyId:'reply-real-audio',humanStart:true,audioWav:wav,alignment:alignment({predictedFromText:true})}).reason,'alignment_contract_rejected');
assert.equal(gate.createByteBoundReplyBridge({replyId:'reply-real-audio',humanStart:false,audioWav:wav,alignment:alignment()}).reason,'alignment_contract_rejected');
console.log('SMI_PCM_AUDIO_BYTE_GATE_PASS');
