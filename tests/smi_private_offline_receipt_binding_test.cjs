"use strict";
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const {inspectOfflineReceipt}=require("../mission_control/smi_private_offline_receipt_binding.js");
const {ORIGINAL_JPG_SHA256}=require("../mission_control/smi_private_source_provenance.js");
const maskRgba=Uint8ClampedArray.from([255,255,255,255,0,0,0,0]);
const geometryBytes=Uint8Array.from([10,20,30,255,0,0,0,0]);
const sha=bytes=>crypto.createHash("sha256").update(bytes).digest("hex");
const receipt={version:"source-pixel-lineage-v1",source_sha256:ORIGINAL_JPG_SHA256,
 mask_sha256:sha(maskRgba),geometry_sha256:sha(geometryBytes),
 width:2,height:1,anatomy_proven:false,speech_sync_proven:false,
 human_authority_approved:false};
const args={receipt,maskRgba,geometryBytes,width:2,height:1};
const match=inspectOfflineReceipt(args);
assert.equal(match.type,"private-payload-identity-match");
assert.equal(match.provenanceIssuerAuthenticated,false);
assert.equal(match.anatomyProven,false);
assert.equal(match.speechSyncProven,false);
assert.equal(match.attachedToLivePage,false);
for(const changed of [
 {receipt:null},
 {receipt:{...receipt,source_sha256:"a".repeat(64)}},
 {receipt:{...receipt,mask_sha256:"a".repeat(64)}},
 {receipt:{...receipt,geometry_sha256:"b".repeat(64)}},
 {receipt:{...receipt,human_authority_approved:true}},
 {receipt:{...receipt,anatomy_proven:true}},
 {receipt:{...receipt,speech_sync_proven:true}},
 {maskRgba:Uint8ClampedArray.from([255,255,255,255,0,0,0,255])},
 {geometryBytes:Uint8Array.from([10,20,31,255,0,0,0,0])},
 {geometryBytes:geometryBytes.subarray(0,4)},
 {height:2},
])assert.equal(inspectOfflineReceipt({...args,...changed}),null);
console.log("SMI_PRIVATE_OFFLINE_RECEIPT_BINDING_PASS");
