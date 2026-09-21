"use strict";
const assert=require("node:assert/strict");
const zip=require("../mission_control/static/smi_mask_zip.js");
const names=["eyes","head","breathing","mouth_visemes","face","hands","upper_body"];
const source=names.map((name,i)=>({name:name+".png",
  data:Uint8Array.from([137,80,78,71,13,10,26,10,i+1])}));
source.push({name:"mask-bundle.json",
  data:new TextEncoder().encode('{"approval":"DRAFT_REQUIRES_FOUNDER_REVIEW"}')});
const bytes=zip.createZip(source);
const view=new DataView(bytes.buffer);
let cursor=0;
for(let i=0;i<source.length;i++){
  const item=source[i];
  assert.equal(view.getUint32(cursor,true),0x04034b50);
  const crc=view.getUint32(cursor+14,true);
  assert.equal(crc,zip.crc32(item.data));
  assert.equal(view.getUint32(cursor+18,true),item.data.length);
  const nameLen=view.getUint16(cursor+26,true);
  const name=new TextDecoder().decode(bytes.slice(cursor+30,cursor+30+nameLen));
  assert.equal(name,item.name);
  const begin=cursor+30+nameLen;
  assert.deepEqual(bytes.slice(begin,begin+item.data.length),item.data);
  cursor=begin+item.data.length;
}
const directory=cursor;
for(let i=0;i<source.length;i++){
  assert.equal(view.getUint32(cursor,true),0x02014b50);
  const len=view.getUint16(cursor+28,true);
  assert.equal(new TextDecoder().decode(bytes.slice(cursor+46,cursor+46+len)),
    source[i].name);
  cursor+=46+len;
}
assert.equal(view.getUint32(cursor,true),0x06054b50);
assert.equal(view.getUint16(cursor+10,true),8);
assert.equal(view.getUint32(cursor+12,true),cursor-directory);
assert.equal(view.getUint32(cursor+16,true),directory);
assert.equal(cursor+22,bytes.length);
assert.throws(()=>zip.createZip(source.slice(0,7)),/exact_eight/);
assert.throws(()=>zip.createZip([...source.slice(0,7),source[0]]),/invalid_private/);
assert.throws(()=>zip.createZip([...source.slice(0,7),
  {name:"../mask-bundle.json",data:source[7].data}]),/invalid_private/);
assert.throws(()=>zip.createZip([...source.slice(0,7),
  {name:"mask-bundle.json",data:new Uint8Array(0)}]),/invalid_private/);
console.log("SMI_SEVEN_MASK_LOCAL_ZIP_PASS");
