/* Private fail-closed provenance-first admission path, NOT loaded by Live SMI.
 * Validates the exact approved JPG bytes and visible source pixel identity
 * before consulting the draft audio-to-geometry contract. Never reconstructs
 * occluded anatomy or infers visemes from text.
 */
"use strict";
const {verifyOriginalJpg,verifyVisibleGeometry,ORIGINAL_JPG_SHA256}=
  require("./smi_private_source_provenance.js");
const {admit}=require("./smi_private_audio_geometry_contract.js");
// Bind the hashed geometry bytes to the very RGBA buffer checked for pixels.
// A digest of unrelated bytes must never pass visible-pixel provenance.
function sameGeometryBytes(bytes,rgba){
  if(!(bytes instanceof Uint8Array)||
     !(rgba instanceof Uint8ClampedArray)||
     bytes.byteLength===0||bytes.byteLength!==rgba.byteLength||
     bytes.byteLength>64000000)return false;
  for(let i=0;i<bytes.byteLength;i++)if(bytes[i]!==rgba[i])return false;
  return true;
}
function admitWithProvenance({originalJpgBytes,sourceRgba,maskRgba,
 geometryRgba,width,height,...contract}={}){
  if(contract.sourceSha256!==ORIGINAL_JPG_SHA256||
     !verifyOriginalJpg(originalJpgBytes)||
     !sameGeometryBytes(contract.geometryBytes,geometryRgba)||
     !verifyVisibleGeometry({sourceRgba,maskRgba,geometryRgba,width,height}))
    return null;
  // This checks visible pixels, not whether caller-supplied RGBA was
  // independently decoded from the verified JPEG. No actual SMI geometry
  // or live lip-sync is approved by this isolated candidate.
  return admit(contract);
}
module.exports=Object.freeze({admitWithProvenance,sameGeometryBytes});
