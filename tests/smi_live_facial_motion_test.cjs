const assert=require("node:assert/strict");
const motion=require("../mission_control/static/smi_source_pixel_motion.js");

const idle=motion.motionFor("ready",1000,0);
const blink=motion.motionFor("ready",4300+67.5,0);
const speak=motion.motionFor("speaking",1500,1);
const paused=motion.motionFor("paused",1500,1);

assert.ok(idle.eyes[2]>.9,"eyes remain open outside blink window");
assert.ok(blink.eyes[2]<.5,"blink compresses the eye source pixels");
assert.ok(speak.mouth[2]>1.2,"speech pulse opens the mouth region");
assert.deepEqual(paused.mouth,[0,0,1],"pause freezes mouth motion");
assert.deepEqual(paused.head,[0,0,1],"pause freezes head motion");
assert.ok(Array.isArray(motion.REGIONS),"source regions stay canonical");
// Idle, listening, thinking and speaking use different bounded real-pixel poses.
const listen=motion.motionFor("listening",1700,0);
const think=motion.motionFor("thinking",1700,0);
assert.notDeepEqual(listen.head,think.head,"state influences body/face movement");
for(const state of ["ready","listening","thinking","speaking"]){
 const pose=motion.motionFor(state,1788,0);
 assert.ok(Math.abs(pose.head[0])<=1.5,"head movement is restrained");
 assert.ok(Math.abs(pose.eyes[0])<=2,"eye movement is restrained");
 assert.ok(Math.abs(pose.chest[1])<=.75,"breathing is restrained");
 assert.ok(Math.abs(pose.hands[0])<=.45,"hands use existing approved pixels");
}
assert.deepEqual(motion.motionFor("stopped",1700,1).head,[0,0,1],"STOP halts physical-looking motion");
assert.equal(motion.SHA256,"f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b");
console.log("SMI live facial motion contract passed");
