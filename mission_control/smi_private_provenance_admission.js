/* Private fail-closed provenance-first admission path, NOT loaded by Live SMI.
 * Validates the exact approved JPG bytes and visible source pixel identity
 * before consulting the draft audio-to-geometry contract. Never reconstructs
 * occluded anatomy or infers visemes from text.
 */
"use strict";
const crypto=require("node:crypto");
const {verifyOriginalJpg,verifyVisibleGeometry,ORIGINAL_JPG_SHA256}=
  require("./smi_private_source_provenance.js");
const {admit}=require("./smi_private_audio_geometry_contract.js");
// The exact bytes admitted by the geometry digest must be the same full-canvas
// RGBA bytes whose visible pixels passed the source-mask comparison.
function verifyGeometryPayload(geometryBytes,geometryRgba){
  return geometryBytes instanceof Uint8Array&&
    geometryRgba instanceof Uint8ClampedArray&&
    geometryBytes.byteLength>0&&geometryBytes.byteLength<=64000000&&
    geometryBytes.byteLength===geometryRgba.byteLength&&
    crypto.timingSafeEqual(Buffer.from(geometryBytes),
      Buffer.from(geometryRgba));
}
function admitWithProvenance({originalJpgBytes,sourceRgba,maskRgba,
 geometryRgba,width,height,...contract}={}){
  if(contract.sourceSha256!==ORIGINAL_JPG_SHA256||
     !verifyOriginalJpg(originalJpgBytes)||
     !verifyVisibleGeometry({sourceRgba,maskRgba,geometryRgba,width,height})||
     !verifyGeometryPayload(contract.geometryBytes,geometryRgba))
    return null;
  // This checks visible pixels, not whether caller-supplied RGBA was
  // independently decoded from the verified JPEG. No actual SMI geometry
  // or live lip-sync is approved by this isolated candidate.
  return admit(contract);
}
module.exports=Object.freeze({admitWithProvenance,verifyGeometryPayload});
