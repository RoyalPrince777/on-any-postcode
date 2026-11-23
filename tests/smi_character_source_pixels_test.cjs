"use strict";
const assert=require("node:assert/strict");
const {extract}=require("../mission_control/static/smi_character_source_pixels.js");
const original=Uint8ClampedArray.from([
  10,20,30,255, 40,50,60,255, 70,80,90,255,
  11,21,31,255, 41,51,61,255, 71,81,91,255,
]);
const mask=new Uint8ClampedArray(original.length);
for(const p of [1,4]){
  mask.set([255,255,255,255],p*4);
}
const layer=extract(original,mask,3,2);
assert.deepEqual(layer.bbox_xyxy,[1,0,2,2]);
assert.deepEqual([...layer.rgba],[40,50,60,255,41,51,61,255]);
assert.equal(layer.selected_pixels,2);
assert.equal(layer.alpha_rule,"binary_threshold_128_draft");
assert.deepEqual([...original],[10,20,30,255,40,50,60,255,70,80,90,255,
  11,21,31,255,41,51,61,255,71,81,91,255]);
const transparent=new Uint8ClampedArray(mask);
transparent.fill(0);
assert.throws(()=>extract(original,transparent,3,2),/empty_original_pixel_layer/);
const coloured=new Uint8ClampedArray(mask);
coloured[4]=9;
assert.throws(()=>extract(original,coloured,3,2),/mask_must_be_white_alpha/);
assert.throws(()=>extract(original,mask,2,2),/source_or_mask_canvas_invalid/);
assert.throws(()=>extract(original,mask,16000001,1),/source_or_mask_canvas_invalid/);
const below=new Uint8ClampedArray(original.length);
below.set([255,255,255,127],4);
assert.throws(()=>extract(original,below,3,2),/empty_original_pixel_layer/);
below.set([255,255,255,128],4);
assert.equal(extract(original,below,3,2).selected_pixels,1);
const zip=require("../mission_control/static/smi_mask_zip.js");
const names=["eyes","head","breathing","mouth_visemes","face","hands","upper_body"];
const files=names.map((name,i)=>({name:name+".png",data:Uint8Array.from([137,80,78,71,13,10,26,10,i])}));
files.push({name:"source-package.json",data:new TextEncoder().encode('{"motion_proven":false}')});
const archive=zip.createSourceZip(files);
assert.equal(new DataView(archive.buffer).getUint32(0,true),0x04034b50);
assert.throws(()=>zip.createZip(files),/invalid_private_mask_bundle/);
assert.throws(()=>zip.createSourceZip([...files.slice(0,7),{
  name:"mask-bundle.json",data:files[7].data}]),/invalid_private_mask_bundle/);
console.log("SMI_PRIVATE_SOURCE_PIXEL_EXTRACTION_PASS");
