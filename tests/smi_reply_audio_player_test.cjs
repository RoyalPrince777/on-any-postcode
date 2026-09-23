"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const {create,validate}=require("../mission_control/static/smi_reply_audio_player.js");
const alignment={
 source:"decoded_audio_phoneme_timeline",audioSha256:"a".repeat(64),
 audioDecoded:true,predictedFromText:false,storesAudio:false,
 storesReplyText:false,audioDurationMs:1000,
 cues:[
  {atMs:0,viseme:"silence",confidence:1},
  {atMs:100,viseme:"wide",confidence:1},
  {atMs:1000,viseme:"silence",confidence:1}
 ]
};
assert.equal(validate(alignment,"a".repeat(64),1000),true);
for(const invalid of [
 {...alignment,audioSha256:"b".repeat(64)},
 {...alignment,predictedFromText:true},
 {...alignment,cues:[alignment.cues[0],{atMs:100,viseme:"invented",confidence:1},alignment.cues[2]]},
 {...alignment,cues:[alignment.cues[0],{atMs:0,viseme:"wide",confidence:1},alignment.cues[2]]}
])assert.equal(validate(invalid,"a".repeat(64),1000),false);
let resolveFetch;
const win={
 fetch:()=>new Promise(resolve=>{resolveFetch=resolve;}),
 crypto:{subtle:{}},AudioContext:class{},
 AbortController:class{abort(){this.aborted=true;}},
 cancelAnimationFrame(){}
};
const player=create(win);
let starts=0,cues=0;
const pending=player.play({
 url:"/mission/chat/reply-audio",csrf:"csrf",
 conversationId:"12345678-1234-4234-8234-123456789abc",
 requestId:"87654321-4321-4321-8321-abcdefabcdef",
 onStart:()=>starts++,onCue:()=>cues++
});
player.stop();
resolveFetch({ok:true,json:async()=>({mime:"audio/wav"})});
pending.then(result=>{
 assert.equal(result,false);
 assert.equal(starts,0);
 assert.equal(cues,0);
 assert.equal(player.snapshot().active,false);
 const html=fs.readFileSync("mission_control/templates/ollama_chat.html","utf8");
 const controller=fs.readFileSync("mission_control/static/smi_canonical_controller.js","utf8");
 const renderer=fs.readFileSync("mission_control/static/smi_source_pixel_motion.js","utf8");
 assert.ok(html.indexOf("smi_reply_audio_player.js")<html.indexOf("smi_canonical_controller.js"));
 assert.ok(controller.includes("oapSpeak(completeResult.response,completeResult)"));
 assert.ok(controller.includes("oap-smi-audio-cue"));
 assert.ok(renderer.includes('cue?.source!=="oap-first-party-pcm"'));
 assert.ok(fs.readFileSync("mission_control/static/smi_reply_audio_player.js","utf8").includes('if(context.state!=="running"){frame=win.requestAnimationFrame(tick);return;}'));
 assert.ok(controller.includes("oapLocalPlayer?.pause()"));
 assert.ok(controller.includes("oapLocalPlayer?.resume()"));
 assert.ok(controller.includes("oapLocalPlayer?.stop()"));
 console.log("SMI_LOCAL_AUDIO_CLOCK_STOP_AND_WIRING_PASS");
}).catch(error=>{console.error(error);process.exitCode=1});
