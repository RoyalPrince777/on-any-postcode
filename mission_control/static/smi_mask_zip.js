/* First-party local ZIP writer for seven manually painted draft PNG masks.
 * ZIP STORE only: PNG is already compressed. No dependencies or network.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OAP_SMI_MASK_ZIP=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const MAX_BYTES=120*1024*1024;
  const ALLOWED=new Set(["eyes.png","head.png","breathing.png",
    "mouth_visemes.png","face.png","hands.png","upper_body.png",
    "mask-bundle.json"]);
  const SOURCE_ALLOWED=new Set(["eyes.png","head.png","breathing.png",
    "mouth_visemes.png","face.png","hands.png","upper_body.png",
    "source-package.json"]);
  const FRAME_ALLOWED=new Set(["frame-neutral.png","frame-offset.png",
    "frame-evidence.json"]);
  const table=new Uint32Array(256);
  for(let n=0;n<256;n++){
    let c=n;
    for(let i=0;i<8;i++)c=c&1?0xedb88320^(c>>>1):c>>>1;
    table[n]=c>>>0;
  }
  function crc32(bytes){
    let crc=0xffffffff;
    for(const x of bytes)crc=table[(crc^x)&255]^(crc>>>8);
    return (crc^0xffffffff)>>>0;
  }
  function makeZip(entries,allowed){
    if(!Array.isArray(entries)||entries.length!==allowed.size)
      throw Error(allowed.size===8?"exact_eight_bundle_entries_required":"exact_frame_bundle_entries_required");
    const encoder=new TextEncoder(),seen=new Set(),files=[];
    let total=22;
    for(const entry of entries){
      if(!entry||!allowed.has(entry.name)||seen.has(entry.name)
        ||!(entry.data instanceof Uint8Array)||entry.data.length===0){
        throw Error("invalid_private_mask_bundle");
      }
      seen.add(entry.name);
      const name=encoder.encode(entry.name);
      if(name.length>65535)throw Error("invalid_mask_filename");
      files.push({name,data:entry.data,encoded:name,crc:crc32(entry.data)});
      total+=30+name.length+entry.data.length+46+name.length;
      if(total>MAX_BYTES)throw Error("mask_bundle_too_large");
    }
    if(seen.size!==allowed.size)throw Error("incomplete_mask_bundle");
    const output=new Uint8Array(total),dv=new DataView(output.buffer);
    let offset=0;
    const central=[];
    for(const file of files){
      const at=offset,name=file.encoded,data=file.data;
      dv.setUint32(offset,0x04034b50,true);dv.setUint16(offset+4,20,true);
      dv.setUint16(offset+6,0,true);dv.setUint16(offset+8,0,true);
      dv.setUint32(offset+14,file.crc,true);
      dv.setUint32(offset+18,data.length,true);
      dv.setUint32(offset+22,data.length,true);
      dv.setUint16(offset+26,name.length,true);
      dv.setUint16(offset+28,0,true);offset+=30;
      output.set(name,offset);offset+=name.length;
      output.set(data,offset);offset+=data.length;
      central.push({file,local:at});
    }
    const centralStart=offset;
    for(const {file,local} of central){
      const name=file.encoded,data=file.data;
      dv.setUint32(offset,0x02014b50,true);
      dv.setUint16(offset+4,20,true);dv.setUint16(offset+6,20,true);
      dv.setUint16(offset+8,0,true);dv.setUint16(offset+10,0,true);
      dv.setUint32(offset+16,file.crc,true);
      dv.setUint32(offset+20,data.length,true);
      dv.setUint32(offset+24,data.length,true);
      dv.setUint16(offset+28,name.length,true);
      dv.setUint16(offset+30,0,true);dv.setUint16(offset+32,0,true);
      dv.setUint16(offset+34,0,true);dv.setUint16(offset+36,0,true);
      dv.setUint32(offset+38,0,true);dv.setUint32(offset+42,local,true);
      offset+=46;output.set(name,offset);offset+=name.length;
    }
    const centralSize=offset-centralStart;
    dv.setUint32(offset,0x06054b50,true);
    dv.setUint16(offset+4,0,true);dv.setUint16(offset+6,0,true);
    dv.setUint16(offset+8,files.length,true);
    dv.setUint16(offset+10,files.length,true);
    dv.setUint32(offset+12,centralSize,true);
    dv.setUint32(offset+16,centralStart,true);
    dv.setUint16(offset+20,0,true);
    if(offset+22!==total)throw Error("mask_zip_length_mismatch");
    return output;
  }
  return Object.freeze({
    createZip:entries=>makeZip(entries,ALLOWED),
    createSourceZip:entries=>makeZip(entries,SOURCE_ALLOWED),
    createFrameZip:entries=>makeZip(entries,FRAME_ALLOWED),crc32
  });
});
