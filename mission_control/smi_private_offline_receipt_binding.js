/* Compare an offline lineage receipt with the exact private payloads.
 * Hash agreement is not authentication of who issued a receipt, anatomical
 * review or authorization to run Live SMI. Never calls admit()/renders.
 */
"use strict";
const crypto=require("node:crypto");
const {ORIGINAL_JPG_SHA256}=require("./smi_private_source_provenance.js");
const HASH=/^[a-f0-9]{64}$/;
function inspectOfflineReceipt({receipt,maskRgba,geometryBytes,width,height}={}){
  if(!receipt||typeof receipt!=="object"||Array.isArray(receipt)||
     receipt.version!=="source-pixel-lineage-v1"||
     receipt.source_sha256!==ORIGINAL_JPG_SHA256||
     receipt.anatomy_proven!==false||
     receipt.speech_sync_proven!==false||
     receipt.human_authority_approved!==false||
     !Number.isSafeInteger(width)||!Number.isSafeInteger(height)||
     width<1||height<1||width*height>16000000||
     receipt.width!==width||receipt.height!==height||
     !(maskRgba instanceof Uint8ClampedArray)||
     !(geometryBytes instanceof Uint8Array)||
     maskRgba.byteLength!==width*height*4||
     geometryBytes.byteLength!==width*height*4||
     !HASH.test(receipt.mask_sha256||"")||
     !HASH.test(receipt.geometry_sha256||""))return null;
  const maskHash=crypto.createHash("sha256").update(maskRgba).digest("hex");
  const geometryHash=crypto.createHash("sha256").update(geometryBytes).digest("hex");
  if(maskHash!==receipt.mask_sha256||geometryHash!==receipt.geometry_sha256)return null;
  return Object.freeze({type:"private-payload-identity-match",
    sourceSha256:ORIGINAL_JPG_SHA256,maskSha256:maskHash,
    geometrySha256:geometryHash,width,height,
    provenanceIssuerAuthenticated:false,anatomyProven:false,
    speechSyncProven:false,productionApproved:false,
    humanFinalApproved:false,attachedToLivePage:false});
}
module.exports=Object.freeze({inspectOfflineReceipt});
