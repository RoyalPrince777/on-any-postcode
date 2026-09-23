/* Private original-source provenance evidence. No anatomical reconstruction.
 * A JPG digest binds the original file, while the pixel verifier checks
 * visible geometry bytes against separately decoded original pixels.
 * Neither operation approves a non-neutral mouth or live lip-sync.
 */
"use strict";
const crypto=require("node:crypto");
const ORIGINAL_JPG_SHA256="f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b";
function digest(bytes){
  if(!(bytes instanceof Uint8Array)||!bytes.byteLength)return null;
  return crypto.createHash("sha256").update(bytes).digest("hex");
}
function verifyOriginalJpg(bytes){
  return bytes instanceof Uint8Array&&bytes.byteLength>0&&
    bytes.byteLength<=32000000&&digest(bytes)===ORIGINAL_JPG_SHA256;
}
function verifyVisibleGeometry({sourceRgba,maskRgba,geometryRgba,width,height}={}){
  if(!Number.isSafeInteger(width)||!Number.isSafeInteger(height)||
     width<1||height<1||width*height>16000000)return false;
  const len=width*height*4;
  if(!(sourceRgba instanceof Uint8ClampedArray)||
     !(maskRgba instanceof Uint8ClampedArray)||
     !(geometryRgba instanceof Uint8ClampedArray)||
     sourceRgba.length!==len||maskRgba.length!==len||
     geometryRgba.length!==len)return false;
  let selected=0;
  for(let i=0;i<len;i+=4){
    const a=maskRgba[i+3],on=a>=128,ga=geometryRgba[i+3];
    if(a!==0&&(maskRgba[i]!==255||maskRgba[i+1]!==255||
       maskRgba[i+2]!==255))return false;
    if(!on){if(ga!==0)return false;continue;}
    selected++;
    if(ga!==255||geometryRgba[i]!==sourceRgba[i]||
       geometryRgba[i+1]!==sourceRgba[i+1]||
       geometryRgba[i+2]!==sourceRgba[i+2])return false;
  }
  return selected>0;
}
module.exports=Object.freeze({ORIGINAL_JPG_SHA256,verifyOriginalJpg,verifyVisibleGeometry});
