"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const api=require("../mission_control/static/smi_source_pixel_motion.js");
assert.equal(api.SHA256,"f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b");
assert.equal(api.SOURCE,"/static/oap/smi_live_chat_dashboard.jpg");
assert.deepEqual(Object.keys(api.motionFor("stopped",200)),["head","eyes","mouth","chest","hands"]);
assert.equal(api.motionFor("paused",220).head[0],0);
assert.ok(api.motionFor("listening",1020).head[0]!==0);
assert.equal(api.motionFor("stopped",220,1).mouth[2],1);
assert.equal(api.motionFor("paused",220,1).mouth[2],1);
assert.equal(api.motionFor("speaking",220,0).mouth[2],1);
assert.ok(api.motionFor("speaking",220,1).mouth[2]>1);
assert.ok(api.motionFor("thinking",220,1).mouth[2]===1);
assert.equal(api.boundedGaze({x:2,y:-3}).x,1);
assert.equal(api.boundedGaze({x:2,y:-3}).y,-1);
assert.equal(api.boundedGaze({x:NaN,y:0}),null);
assert.ok(api.blinkEnvelope(750)>0,"first nonuniform blink");
assert.ok(api.blinkEnvelope(3420)>0,"second nonuniform blink");
assert.ok(api.blinkEnvelope(3575)>0,"short follow-up blink");
assert.equal(api.blinkEnvelope(2000),0);
const neutral=api.motionFor("listening",1200,0);
const directed=api.motionFor("listening",1200,0,{x:1,y:-1});
assert.ok(directed.eyes[0]>neutral.eyes[0],"gaze moves eye pixels right");
assert.ok(directed.eyes[1]<neutral.eyes[1],"gaze moves eye pixels up");
assert.ok(directed.head[0]>neutral.head[0],"head coordinates with gaze");
assert.deepEqual(api.motionFor("stopped",1200,0,{x:1,y:1}),api.motionFor("stopped",1200,0),"STOP ignores gaze");
assert.deepEqual(api.motionFor("paused",1200,0,{x:1,y:1}),api.motionFor("paused",1200,0),"PAUSE ignores gaze");
const region={x:0,y:0,w:11,h:11,cx:5,cy:5,rx:5,ry:5};
const data=new Uint8ClampedArray(11*11*4);
for(let y=0;y<11;y++)for(let x=0;x<11;x++){
 const j=(y*11+x)*4;data[j]=x*16;data[j+1]=y*16;data[j+3]=255;
}
const original={width:11,height:11,data};
const rest=api.remapRegion(original,region,0,0,1);
assert.deepEqual(rest.data,data);
const moving=api.remapRegion(original,region,2,1,1);
assert.deepEqual([...moving.data.slice(0,4)],[...data.slice(0,4)]);
const center=(5*11+5)*4;
assert.notDeepEqual([...moving.data.slice(center,center+4)],[...data.slice(center,center+4)]);
assert.deepEqual(original.data,data);
const source=fs.readFileSync("mission_control/static/smi_source_pixel_motion.js","utf8");
const html=fs.readFileSync("mission_control/templates/ollama_chat.html","utf8");
assert.ok(source.includes("fullSceneSourcePixelMotion:played>0"));
assert.ok(source.includes("audioCues+=1"));
assert.ok(source.includes("fullBodyRigProven"));
assert.ok(source.includes("accurateSoftwareLipSyncProven"));
assert.ok(source.includes("rigLayerFrames"));
assert.ok(source.includes("maxAudioClockDeltaMs"));
assert.ok(html.includes("OAP_SMI_SOURCE_PIXEL_MOTION_SESSION=session"));
console.log("SMI_SOURCE_PIXEL_MOTION_PASS");

const controller=fs.readFileSync("mission_control/static/smi_canonical_controller.js","utf8");
const liveBlock=controller.slice(controller.indexOf("function oapSetLive("),controller.indexOf("function oapRequestListening("));
assert.ok(!liveBlock.includes("if(!oapRecognition){"),"visual Live SMI must not be blocked by missing speech recognition");
assert.ok(liveBlock.includes("if(oapRecognition){"),"microphone auto-listening remains conditional");
assert.ok(liveBlock.includes("visual motion active"),"Live status should confirm visual movement");
assert.ok(source.includes("explicitLiveMotion"),"explicit Live session must be represented in renderer state");
assert.ok(source.includes("reducedMotionPreference"),"renderer must report reduced-motion preference truthfully");
assert.ok(source.includes("!reducedPreference||explicitLiveMotion"),"explicit Live session may enable motion for that session");


assert.ok(source.includes("userReducedMotion=Boolean(win.OAP_SMI_REDUCED_MOTION?.read?.())"),
  "explicit SMI Reduced Motion preference must be read by the motion engine");
assert.ok(source.includes("!userReducedMotion&&(!reducedPreference||explicitLiveMotion)"),
  "explicit user Reduced Motion must override Live motion");
assert.ok(source.includes('win.addEventListener("oap-smi-reduced-motion-change"'),
  "motion engine must react to Settings changes");
assert.ok(source.includes("userReducedMotionPreference:userReducedMotion"),
  "proof snapshot must expose explicit Reduced Motion state");

assert.ok(source.includes('win.addEventListener("oap-smi-gaze-target"'),"gaze must use explicit event only");
assert.ok(source.includes("if(stoppedLatched)return;"),"STOP must latch against late state events");
assert.ok(source.includes("if(stoppedLatched||!live||userReducedMotion)return;"),"gaze respects STOP, live and reduced-motion state");

const uiController=fs.readFileSync("mission_control/static/smi_canonical_controller.js","utf8");
assert.ok(uiController.includes("oap-smi-human-motion-reset"),"controller must signal explicit resume");
assert.ok(source.includes("oap-smi-human-motion-reset"),"pixel renderer must allow explicit reset");
assert.ok(source.includes('["message",{x:0.3,y:0.75}]'),"composer focus supplies bounded gaze");
assert.ok(source.includes("if(stoppedLatched||!live||userReducedMotion)return;"),"STOP and reduced-motion gate gaze");
