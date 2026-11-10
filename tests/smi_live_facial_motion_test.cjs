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
assert.equal(motion.SHA256,"f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b");
console.log("SMI live facial motion contract passed");
