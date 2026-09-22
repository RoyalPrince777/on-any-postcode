"use strict";
const assert=require("node:assert/strict");
const {NAMES,create}=require("../mission_control/static/smi_private_source_frame.js");
const width=11,height=9,source=new Uint8ClampedArray(width*height*4);
for(let p=0;p<width*height;p++){
  source.set([p%251,(p*3)%251,(p*7)%251,255],p*4);
}
const masks={};
NAMES.forEach((name,i)=>{
  const bytes=new Uint8ClampedArray(source.length);
  bytes.set([255,255,255,255],((i+1)*width+(i+1))*4);
  masks[name]=bytes;
});
function args(overrides={}){return {source,masks,width,height,sourceVerified:true,
  layerOrder:[...NAMES],...overrides};}
assert.throws(()=>create(args({sourceVerified:false})),/verified_private_source/);
assert.throws(()=>create(args({layerOrder:["eyes"]})),/verified_private_source/);
assert.throws(()=>create(args({width:16000001,height:1})),/verified_private_source/);
const tampered={...masks,eyes:new Uint8ClampedArray(masks.eyes)};
tampered.eyes[(1*width+1)*4]=2;
assert.throws(()=>create(args({masks:tampered})),/white_alpha_mask_only/);
const empty={...masks,hands:new Uint8ClampedArray(masks.hands.length)};
assert.throws(()=>create(args({masks:empty})),/empty_private_source_mask/);
const rig=create(args()),current=rig.snapshot().epoch;
const neutral=rig.frame({expectedEpoch:current});
assert.equal(neutral.rgba.length,source.length);
assert.equal(neutral.motion_proven,false);
assert.equal(neutral.speech_sync_proven,false);
assert.equal(neutral.attached_to_live_page,false);
assert.deepEqual([...neutral.rgba.slice((1*width+1)*4,(1*width+1)*4+4)],
  [...source.slice((1*width+1)*4,(1*width+1)*4+3),255]);
assert.deepEqual([...source.slice(0,4)],[0,0,0,255]);
const moved=rig.frame({expectedEpoch:current,translations:{eyes:[1,0]}});
const from=(1*width+1)*4,to=(1*width+2)*4;
assert.deepEqual([...moved.rgba.slice(to,to+4)],
  [...source.slice(from,from+3),255]);
assert.equal(moved.rgba[from+3],0);
// Head, face, eyes and mouth inherit one inspection-only offset.
const grouped=rig.frame({expectedEpoch:current,headGroupTranslation:[1,0]});
for(const name of ["head","face","eyes","mouth_visemes"]){
  const n=NAMES.indexOf(name),from=((n+1)*width+n+1)*4,to=from+4;
  assert.deepEqual([...grouped.rgba.slice(to,to+4)],
    [...source.slice(from,from+3),255]);
}
assert.equal(grouped.motion_proven,false);
assert.equal(grouped.attached_to_live_page,false);
assert.throws(()=>rig.frame({headGroupTranslation:[3,0]}),
  /private_head_group_translation_invalid/);
assert.throws(()=>rig.frame({headGroupTranslation:[1,0],
  translations:{eyes:[1,0]}}),/private_head_group_translation_invalid/);
assert.throws(()=>rig.frame({translations:{mouth_visemes:[1,0]}}),/unapproved_or_unbounded/);
assert.throws(()=>rig.frame({translations:{eyes:[3,0]}}),/unapproved_or_unbounded/);
assert.throws(()=>rig.frame({translations:{eyes:[0.5,0]}}),/unapproved_or_unbounded/);
assert.throws(()=>rig.frame({translations:{shadow:[0,1]}}),/private_frame_offsets_invalid/);
const stop=rig.stop();
assert.equal(rig.frame({expectedEpoch:current}),null);
assert.equal(rig.restart(false).stopped,true);
assert.equal(rig.restart(true).stopped,false);
assert.equal(rig.frame({expectedEpoch:stop.epoch}),null);
assert.equal(rig.frame({expectedEpoch:rig.snapshot().epoch}).rgba.length,source.length);
const zip=require("../mission_control/static/smi_mask_zip.js");
const files=["frame-neutral.png","frame-offset.png"].map((name,i)=>({
  name,data:Uint8Array.from([137,80,78,71,13,10,26,10,i])
}));
files.push({name:"frame-evidence.json",
  data:new TextEncoder().encode('{"motion_proven":false}')});
const bytes=zip.createFrameZip(files);
assert.equal(new DataView(bytes.buffer).getUint32(0,true),0x04034b50);
assert.throws(()=>zip.createFrameZip(files.slice(0,2)),/exact_frame_bundle/);
assert.throws(()=>zip.createFrameZip([...files.slice(0,2),
  {name:"../frame-evidence.json",data:files[2].data}]),/invalid_private_mask_bundle/);
console.log("SMI_PRIVATE_REAL_PIXEL_FRAME_STOP_PASS");
