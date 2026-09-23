"use strict";
const assert=require("node:assert/strict");
const api=require("../mission_control/static/smi_source_pixel_motion.js");
assert.equal(api.SHA256,"f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b");
assert.equal(api.SOURCE,"/static/oap/smi_live_chat_dashboard.jpg");
assert.deepEqual(Object.keys(api.motionFor("stopped",200)),["head","eyes","chest","hands"]);
assert.equal(api.motionFor("paused",220).head[0],0);
assert.ok(api.motionFor("listening",1020).head[0]!==0);
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
console.log("SMI_SOURCE_PIXEL_MOTION_PASS");
