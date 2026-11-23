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
// Real time-based easing, not a fake FPS number or an alternate avatar.
// Check the first frame never jumps to an abrupt state-transition target.
const smoother=api.createPoseSmoother();
const neutral={
 head:[0,0,1],eyes:[0,0,1],mouth:[0,0,1],
 chest:[0,0,1],hands:[0,0,1]
};
const target={
 head:[2,1,1.1],eyes:[1,0.6,0.25],mouth:[1,1,1.3],
 chest:[0,1,1.01],hands:[0.8,-0.6,1]
};
const first=smoother.next(target,0);
assert.ok(first.head[0]>0&&first.head[0]<target.head[0]);
assert.ok(first.eyes[2]<1&&first.eyes[2]>target.eyes[2]);
assert.ok(first.mouth[2]>1&&first.mouth[2]<target.mouth[2]);
const second=smoother.next(target,16);
assert.ok(second.head[0]>first.head[0]&&second.head[0]<target.head[0]);
assert.ok(second.chest[1]>first.chest[1]);
const unchanged=smoother.next(target,16);
assert.deepEqual(unchanged,second,"same frame time must not add extra motion");
const longGap=smoother.next(target,10000);
assert.ok(longGap.head[0]<target.head[0],"background catch-up must be bounded");
assert.ok(longGap.head[0]>second.head[0]);
const reverseTarget={...target,head:[-2,-1,1]};
const reversing=smoother.next(reverseTarget,10016);
assert.ok(reversing.head[0]>-2&&reversing.head[0]<longGap.head[0],
 "state changes must ease without instantly snapping across the screen");
smoother.reset();
const reset=smoother.next(neutral,0);
assert.deepEqual(reset,neutral,"STOP/Reduced Motion must reset the pose to neutral");
assert.throws(()=>smoother.next({...target,head:[Infinity,1,1]},16),
 /invalid_smi_source_pose/);
assert.throws(()=>smoother.next(target,Infinity),/invalid_smi_pose_clock/);
// Child patches follow head translation while blink and mouth scale stay local.
assert.deepEqual(api.regionPose("eyes",target),[3,1.6,.25]);
assert.deepEqual(api.regionPose("mouth",target),[3,2,1.3]);
assert.deepEqual(api.regionPose("left-hand",target),target.hands);
assert.deepEqual(api.regionPose("mouth",neutral),[0,0,1]);
// Real submission intervals, bounded storage, no fabricated FPS for empty data.
const timing=api.createFrameWindow();
assert.equal(timing.snapshot().measuredFps,null);
timing.record(0,2,20);timing.record(20,3,20);timing.record(40,4,20);
timing.record(100,5,20);
assert.equal(timing.snapshot().sampleCount,3);
assert.equal(timing.snapshot().measuredFps,30);
assert.equal(timing.snapshot().frameP50Ms,20);
assert.equal(timing.snapshot().frameP95Ms,60);
assert.equal(timing.snapshot().overBudgetCount,1);
assert.equal(timing.snapshot().renderP95Ms,5);
timing.record(90,1,20);timing.record(NaN,1,20);timing.record(120,-1,20);
assert.equal(timing.snapshot().sampleCount,3,"invalid/backward clocks do not contaminate timing");
timing.boundary();
assert.equal(timing.snapshot().status,"completed");
timing.record(10000,1,20);timing.record(10020,1,20);
assert.equal(timing.snapshot().durationMs,20,"hidden/pause gaps never become frame measurements");
assert.equal(timing.snapshot().measuredFps,50);
for(let i=1;i<=650;i++)timing.record(10020+i*20,1,20);
assert.equal(timing.snapshot().sampleCount,600,"local measurement storage remains bounded");
assert.equal(timing.snapshot().physicalDeviceProven,false);
assert.equal(timing.snapshot().smoothnessApproved,false);
assert.equal(timing.snapshot().thermalStatus,"unknown");
timing.record(30000,1,33,"live");timing.record(30033,1,33,"live");
assert.equal(timing.snapshot().captureMode,"live");
timing.record(30050,1,50,"ambient");timing.record(30100,1,50,"ambient");
assert.equal(timing.snapshot().captureMode,"ambient");
assert.equal(timing.snapshot().durationMs,50,"idle and live samples must not be mixed");
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
assert.ok(source.includes("fullBodyRigProven=false"),"flattened pixels are not an independently reviewed rig");
assert.ok(source.includes("poseSmoother.next(motionFor(phase,ms,pulse),ms)"),
  "existing original source renderer must use bounded pose easing");
assert.ok(source.includes("fullArticulatedMotionProven:false"),
  "easing must not be misrepresented as a human-approved articulated rig");
assert.ok(source.includes('poseEasing:"bounded_time_based_source_pixel_only"'),
  "proof must explicitly limit the motion to original source pixels");
assert.ok(source.includes("if(doc.hidden)poseSmoother.reset()"),
  "background tab must clear stale pose history");
assert.ok(source.includes("poseSmoother.reset();draw(0)"),
  "STOP and Reduced Motion must clear residual pose state");
assert.ok(source.includes("sourcePixelRegionsObserved"),"preserve source-pixel activity evidence");
assert.ok(source.includes("accurateSoftwareLipSyncProven"));
assert.ok(source.includes("rigLayerFrames"));
assert.ok(source.includes('context=canvas.getContext("2d",{alpha:false})'),
  "sharp visible canvas must not enable readback-heavy software mode");
assert.ok(source.includes("evidenceCanvas.width=0;evidenceCanvas.height=0"),
  "temporary one-shot pixel provenance surface must release memory");
assert.ok(source.includes('context.imageSmoothingQuality="high"'),
  "the native image transform should retain high-quality resampling");
assert.ok(source.includes("frameRateTargetFps:renderActive()?(live?(lowPower?30:60):(lowPower?20:30)):0"),
  "FPS target must be zero when motion is stopped, paused or hidden");
assert.ok(source.includes("renderCostMs*1.8"),
  "frame pacing must adapt when native-resolution drawing runs slowly");
assert.ok(source.includes("observedFps:renderActive()?"),
  "observed FPS must be zero, never stale, while motion is inactive");
assert.ok(source.includes("resetFrameTelemetry();"),
  "the history of performance must reset when entering an inactive state");
assert.ok(source.includes('doc.addEventListener?.("visibilitychange",()=>{'),
  "tab sleep/resume must not count stale frame time");
assert.ok(source.includes('phase!=="paused"&&phase!=="stopped"'),
  "a paused or stopped live session must never be counted as animating");
assert.ok(source.includes('const featheredPatches=new Map(REGIONS.map(region=>{'),
  "reuse one source-derived feathered patch per region, not another renderer");
assert.ok(source.includes('pc.globalCompositeOperation="destination-in"'),
  "source-pixel overlays must fade out without a hard rectangle seam");
assert.ok(source.includes("pc.createRadialGradient(0,0,.77,0,0,1)"),
  "edge alpha fades to zero at region boundary");
assert.ok(source.includes('regionEdgeBlending:"source_pixel_feather_no_anatomy_approval"'),
  "proof reports an edge rendering technique, not approved anatomy");
assert.ok(source.includes("patch.width=0;patch.height=0"),
  "ephemeral textures must be discarded on exit");
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
