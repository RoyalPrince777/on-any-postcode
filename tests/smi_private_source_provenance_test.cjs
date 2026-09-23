"use strict";
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const {ORIGINAL_JPG_SHA256,verifyOriginalJpg,verifyVisibleGeometry}=
 require("../mission_control/smi_private_source_provenance.js");
assert.equal(ORIGINAL_JPG_SHA256,"f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b");
assert.equal(verifyOriginalJpg(),false);
assert.equal(verifyOriginalJpg(Uint8Array.from([1,2,3])),false);
const source=new Uint8ClampedArray([10,20,30,255,40,50,60,255]);
const mask=new Uint8ClampedArray([255,255,255,255,0,0,0,0]);
const geometry=new Uint8ClampedArray([10,20,30,255,0,0,0,0]);
const args={sourceRgba:source,maskRgba:mask,geometryRgba:geometry,width:2,height:1};
assert.equal(verifyVisibleGeometry(args),true);
assert.equal(verifyVisibleGeometry({...args,geometryRgba:new Uint8ClampedArray([10,20,31,255,0,0,0,0])}),false);
assert.equal(verifyVisibleGeometry({...args,geometryRgba:new Uint8ClampedArray([10,20,30,255,40,50,60,255])}),false);
assert.equal(verifyVisibleGeometry({...args,maskRgba:new Uint8ClampedArray(mask.length)}),false);
assert.equal(verifyVisibleGeometry({...args,maskRgba:new Uint8ClampedArray([2,255,255,255,0,0,0,0])}),false);
assert.equal(verifyVisibleGeometry({...args,width:3}),false);
console.log("SMI_PRIVATE_SOURCE_PROVENANCE_PASS");
